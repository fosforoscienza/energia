#!/usr/bin/env python3
"""
Telecomando per "Fonte di Energia" — versione senza internet.

Lancia un piccolo server sul computer della regia: la stessa pagina aperta sul
computer (proiettore) e sull'iPad resta sincronizzata, quindi le carte scoperte
dal palco compaiono sul proiettore e viceversa.

Uso:
    python3 telecomando.py            # porta 8000
    python3 telecomando.py --porta 9000

Poi:
  - sul computer apri l'indirizzo "Proiettore" e vai a schermo intero (F11);
  - sull'iPad, collegato alla STESSA rete Wi-Fi (va bene anche l'hotspot del
    telefono), apri l'indirizzo "iPad".

Serve solo Python 3: nessuna libreria da installare, nessuna connessione a
internet. Fermalo con Ctrl+C.
"""

import argparse
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

CARTELLA = Path(__file__).resolve().parent
# nomi accettati: quello del repository e quello del file scaricato dal sito
NOMI_PAGINA = ("index.html", "fonte-di-energia-offline.html")
ATTESA_LONGPOLL = 25      # secondi di attesa prima di rispondere "nessuna novita'"
LIMITE_CORPO = 64 * 1024  # una richiesta di stato non supera qualche centinaio di byte


def trova_pagina(indicata=None):
    """Il file del gioco da servire: quello indicato, o il primo nome noto."""
    if indicata:
        percorso = Path(indicata).expanduser()
        if not percorso.is_absolute():
            percorso = CARTELLA / percorso
        if not percorso.exists():
            raise SystemExit(f"Non trovo {percorso}.")
        return percorso
    for nome in NOMI_PAGINA:
        if (CARTELLA / nome).exists():
            return CARTELLA / nome
    raise SystemExit(
        "Non trovo la pagina del gioco.\n"
        f"Metti {NOMI_PAGINA[0]} (o il file scaricato dal sito) nella cartella "
        f"{CARTELLA}, oppure indicalo con --pagina."
    )


class StatoCondiviso:
    """Elenco delle carte scoperte, con numero di versione e attesa bloccante."""

    def __init__(self):
        self._condizione = threading.Condition()
        self._carte = []
        self._da = ""
        self._versione = 1

    def leggi(self):
        with self._condizione:
            return self._versione, list(self._carte), self._da

    def scrivi(self, carte, da):
        with self._condizione:
            self._carte = carte
            self._da = da
            self._versione += 1
            self._condizione.notify_all()
            return self._versione

    def attendi_oltre(self, versione, timeout):
        """Ritorna lo stato appena supera `versione`, o quello attuale allo scadere."""
        with self._condizione:
            if self._versione <= versione:
                self._condizione.wait_for(lambda: self._versione > versione, timeout)
            return self._versione, list(self._carte), self._da


stato = StatoCondiviso()

COLLEGATI = set()
COLLEGATI_LOCK = threading.Lock()


def pagina_con_modalita_locale(pagina, indirizzo):
    """La pagina del gioco con il flag che accende la sincronizzazione.

    Il flag va nel <head>: lo script della pagina gira durante il parsing del
    <body>, quindi un flag messo piu' in basso arriverebbe troppo tardi.
    """
    html = pagina.read_text(encoding="utf-8")
    iniezione = (
        "<script data-modo-locale>window.__MODO_LOCALE__ = "
        + json.dumps({"url": indirizzo})
        + ";</script>\n</head>"
    )
    if "</head>" not in html:
        raise SystemExit(f"{pagina.name} non ha </head>: impossibile attivare la modalita' locale.")
    return html.replace("</head>", iniezione, 1).encode("utf-8")


class Gestore(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Energia"

    def log_message(self, *args):
        pass  # niente rumore nel terminale della regia

    def segnala_collegamento(self):
        """Stampa una riga la prima volta che un dispositivo apre la pagina.

        E' la spia che serve in regia: se apri l'indirizzo sull'iPad e qui non
        compare nulla, la richiesta non sta nemmeno arrivando al computer
        (rete diversa, oppure firewall).
        """
        ip = self.client_address[0]
        with COLLEGATI_LOCK:
            nuovo = ip not in COLLEGATI
            COLLEGATI.add(ip)
        if nuovo:
            print(f"  + collegato: {ip}")

    def _rispondi(self, corpo, tipo="application/json; charset=utf-8", codice=200):
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(corpo)
        except (BrokenPipeError, ConnectionResetError):
            pass  # scheda chiusa mentre rispondevamo

    def _json(self, versione, carte, da, codice=200):
        self._rispondi(json.dumps({"v": versione, "carte": carte, "da": da}).encode("utf-8"),
                       codice=codice)

    def do_GET(self):
        percorso = urlparse(self.path)

        if percorso.path in ("/", "/index.html"):
            self.segnala_collegamento()
            self._rispondi(
                pagina_con_modalita_locale(self.server.pagina, self.server.indirizzo_ipad),
                tipo="text/html; charset=utf-8")
            return

        if percorso.path == "/api/stato":
            parametri = parse_qs(percorso.query)
            try:
                da_versione = int(parametri.get("v", ["0"])[0])
            except ValueError:
                da_versione = 0
            versione, carte, da = stato.attendi_oltre(da_versione, ATTESA_LONGPOLL)
            self._json(versione, carte, da)
            return

        self._rispondi(b'{"errore":"non trovato"}', codice=404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/stato":
            self._rispondi(b'{"errore":"non trovato"}', codice=404)
            return

        try:
            lunghezza = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            lunghezza = 0
        if lunghezza <= 0 or lunghezza > LIMITE_CORPO:
            self._rispondi(b'{"errore":"richiesta non valida"}', codice=400)
            return

        try:
            dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
            carte = [str(c) for c in dati.get("carte", [])][:25]
            da = str(dati.get("da", ""))[:64]
        except (ValueError, UnicodeDecodeError):
            self._rispondi(b'{"errore":"richiesta non valida"}', codice=400)
            return

        versione = stato.scrivi(carte, da)
        self._json(versione, carte, da)


def ip_principale():
    """Indirizzo usato per uscire verso la rete (senza contattare nessuno)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # nessun pacchetto esce davvero
        return s.getsockname()[0]
    except OSError:
        return ""
    finally:
        s.close()


def indirizzi_locali():
    """Tutti gli IPv4 della macchina, il piu' probabile per primo.

    Con VPN, Docker o piu' schede di rete attive il computer ha piu'
    indirizzi: elencarli tutti evita di far provare all'iPad quello sbagliato.
    """
    trovati = []

    def aggiungi(ip):
        if ip and ip not in trovati and not ip.startswith("127."):
            trovati.append(ip)

    aggiungi(ip_principale())
    try:
        for dati in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            aggiungi(dati[4][0])
    except (socket.gaierror, OSError):
        pass

    # le reti di casa/hotspot (192.168.x, 10.x, 172.16-31.x) prima delle altre
    def priorita(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if ip.startswith("172."):
            return 2
        if ip.startswith("169.254."):
            return 4  # indirizzo di ripiego: quasi sempre inutile
        return 3

    trovati.sort(key=priorita)
    return trovati or ["127.0.0.1"]


def main():
    parser = argparse.ArgumentParser(description="Telecomando locale per Fonte di Energia")
    parser.add_argument("--porta", type=int, default=8000, help="porta del server (default 8000)")
    parser.add_argument("--pagina", default=None,
                        help="file del gioco da servire (default: index.html nella cartella)")
    argomenti = parser.parse_args()

    pagina = trova_pagina(argomenti.pagina)
    indirizzi = indirizzi_locali()
    indirizzo_ipad = f"http://{indirizzi[0]}:{argomenti.porta}"
    try:
        server = ThreadingHTTPServer(("0.0.0.0", argomenti.porta), Gestore)
    except OSError as errore:
        raise SystemExit(
            f"Non riesco ad aprire la porta {argomenti.porta}: {errore}.\n"
            "Probabilmente e' gia' in uso: riprova con --porta 8001."
        )
    server.daemon_threads = True
    server.indirizzo_ipad = indirizzo_ipad
    server.pagina = pagina

    print()
    print("  Fonte di Energia — telecomando locale (niente internet)")
    print("  " + "-" * 56)
    print(f"  Proiettore (questo computer):  http://localhost:{argomenti.porta}")
    print(f"  iPad (stessa rete Wi-Fi):      {indirizzo_ipad}")
    if len(indirizzi) > 1:
        print()
        print("  Se sull'iPad non si apre, prova gli altri indirizzi di questo")
        print("  computer (ne ha piu' di uno: VPN, Docker o piu' schede di rete):")
        for altro in indirizzi[1:]:
            print(f"      http://{altro}:{argomenti.porta}")
    print()
    print(f"  Pagina servita: {pagina.name}")
    print()
    print("  Qui sotto compare una riga a ogni dispositivo che apre la pagina.")
    print("  Se apri l'indirizzo sull'iPad e non compare nulla:")
    print("    - iPad e computer devono essere sulla STESSA rete Wi-Fi")
    print("      (sull'iPad disattiva i dati cellulare per esserne sicuro);")
    print("    - scrivi l'indirizzo per intero, con http:// e i :"
          f"{argomenti.porta} finali;")
    print("    - se il computer chiede di autorizzare Python nel firewall,")
    print("      rispondi Consenti (macOS: Impostazioni > Rete > Firewall);")
    print("    - sul Wi-Fi pubblico i dispositivi sono spesso isolati fra loro:")
    print("      usa l'hotspot del telefono e collegaci anche il computer.")
    print()
    print("  Ctrl+C per fermare.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Telecomando fermato.\n")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
