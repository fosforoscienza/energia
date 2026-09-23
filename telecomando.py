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

PAGINA = Path(__file__).resolve().parent / "index.html"
ATTESA_LONGPOLL = 25      # secondi di attesa prima di rispondere "nessuna novita'"
LIMITE_CORPO = 64 * 1024  # una richiesta di stato non supera qualche centinaio di byte


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


def pagina_con_modalita_locale(indirizzo):
    """index.html con il flag che accende la sincronizzazione nel browser.

    Va nel <head>: lo script della pagina gira durante il parsing del <body>,
    quindi un flag messo piu' in basso arriverebbe troppo tardi.
    """
    html = PAGINA.read_text(encoding="utf-8")
    iniezione = (
        "<script data-modo-locale>window.__MODO_LOCALE__ = "
        + json.dumps({"url": indirizzo})
        + ";</script>\n</head>"
    )
    if "</head>" not in html:
        raise SystemExit("index.html non ha </head>: impossibile attivare la modalita' locale.")
    return html.replace("</head>", iniezione, 1).encode("utf-8")


class Gestore(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "Energia"

    def log_message(self, *args):
        pass  # niente rumore nel terminale della regia

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
            self._rispondi(pagina_con_modalita_locale(self.server.indirizzo_ipad),
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


def ip_locale():
    """Indirizzo della macchina sulla rete locale (senza contattare nessuno)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # nessun pacchetto esce davvero
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    parser = argparse.ArgumentParser(description="Telecomando locale per Fonte di Energia")
    parser.add_argument("--porta", type=int, default=8000, help="porta del server (default 8000)")
    argomenti = parser.parse_args()

    if not PAGINA.exists():
        raise SystemExit(f"Manca {PAGINA.name}: metti questo script nella stessa cartella.")

    indirizzo_ipad = f"http://{ip_locale()}:{argomenti.porta}"
    server = ThreadingHTTPServer(("0.0.0.0", argomenti.porta), Gestore)
    server.daemon_threads = True
    server.indirizzo_ipad = indirizzo_ipad

    print()
    print("  Fonte di Energia — telecomando locale (niente internet)")
    print("  " + "-" * 52)
    print(f"  Proiettore (questo computer):  http://localhost:{argomenti.porta}")
    print(f"  iPad (stessa rete Wi-Fi):      {indirizzo_ipad}")
    print()
    print("  Le carte scoperte da un dispositivo compaiono su tutti gli altri.")
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
