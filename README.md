# Fonte di Energia — fosforo: la festa della scienza

Gioco interattivo sulle trasformazioni dell'energia: una griglia 5×5 in cui ogni
casella coperta nasconde l'immagine di un dispositivo che trasforma l'energia
della colonna (fonte) in quella della riga (energia ottenuta).

## Online

Versione pubblicata: <https://energia-nine.vercel.app/>
Il deploy avviene in automatico da `main` (vedi `vercel.json` per gli header di
sicurezza).

## Uso in locale (senza internet)

`index.html` è un **file unico e autonomo**: immagini (PNG in base64) e font
(Poppins in woff2 base64) sono incorporati, quindi non serve alcuna connessione
né un server web.

Due modi per averlo sul proprio computer:

1. **Dal sito** — apri <https://energia-nine.vercel.app/> e premi il pulsante
   **"Scarica per uso offline"**, che propone due possibilità:
   - *Solo la pagina*: salva `fonte-di-energia-offline.html`, un file unico;
   - *Cartella completa*: salva `energia-telecomando.zip`, che contiene la
     pagina come `index.html`, lo script `telecomando.py` e `ISTRUZIONI.txt`.
     Lo zip viene costruito nel browser, senza scaricare nulla dalla rete.
2. **Da questo repository** — scarica `index.html` (bottone *Download raw file*
   su GitHub) oppure clona il repo.

Poi:

- **doppio clic** sul file: si apre nel browser e il gioco parte subito;
- se si apre con il programma sbagliato: tasto destro → *Apri con* → Chrome
  (o Edge, Firefox, Safari);
- `F11` (su Mac `Ctrl+Cmd+F`) per lo schermo intero;
- il file si può copiare su chiavetta USB o inviare via mail: è uno solo.

La tabella si ridimensiona da sola per riempire lo schermo, da monitor grandi a
tablet e telefoni.

## Suoni

Ogni carta scoperta suona una campanellina; richiudendo una carta non si sente
nulla. Con "Scopri tutte" la campanellina arriva una volta sola, con l'ultima
carta, invece di squillare venti volte.

Il suono è **sintetizzato al volo** con la Web Audio API: non ci sono file
audio da scaricare, quindi funziona anche offline. Il pulsante
**"Suono ON / OFF"** lo disattiva e la scelta viene ricordata sul dispositivo.

## Icona

L'icona (fulmine bianco su fondo oro) è incorporata nell'HTML come data URI
nelle misure 16, 32, 180 (schermata Home iOS) e 192 px, quindi vale per la
scheda del browser, i preferiti e la copia offline. La sorgente a 512 px è
`icona.png`: per sostituirla basta rigenerare le quattro misure e rimpiazzare
i `<link rel="icon">` nel `<head>` di `index.html`.

## Telecomando dall'iPad (senza internet)

Per proiettare dal computer e scoprire le carte dall'iPad, sulla stessa rete
Wi-Fi (va bene l'hotspot del telefono) e senza alcuna connessione a internet:

```bash
python3 telecomando.py          # oppure: python3 telecomando.py --porta 9000
```

Lo script stampa due indirizzi: apri quello "Proiettore" sul computer e quello
"iPad" sul tablet. Da quel momento le due pagine condividono lo stato: una
carta scoperta dall'iPad compare sul proiettore (e viceversa), come pure
"Scopri tutte" e "Reset". Possono collegarsi anche più dispositivi, e chi
arriva dopo si allinea da solo.

Servono solo Python 3 e i due file nella stessa cartella (`telecomando.py` e
`index.html`); va bene anche il file scaricato dal sito col pulsante "Scarica
per uso offline", che lo script riconosce da solo — oppure indicalo con
`--pagina nome-file.html`. Nessuna libreria da installare e nessuna
connessione a internet.

Lo stato viaggia con un long-poll su `/api/stato`, quindi le carte compaiono
sull'altro schermo in un paio di decimi di secondo. Ctrl+C per fermare il
server; se la porta è occupata, usa `--porta 8001`.

### Se dall'iPad la pagina non si apre

Lo script stampa una riga `+ collegato: <indirizzo>` ogni volta che un
dispositivo apre la pagina: è la spia da guardare in regia.

- **Nel terminale non compare nulla** → la richiesta non arriva al computer.
  Controlla che sull'iPad tu abbia aperto l'indirizzo *iPad* e non quello
  *Proiettore* (`localhost` sull'iPad significa "l'iPad stesso"); che i due
  dispositivi siano sulla stessa rete Wi-Fi, con i dati cellulare spenti; che
  il firewall del computer non stia bloccando Python (su macOS:
  Impostazioni → Rete → Firewall). Sulle reti pubbliche i dispositivi sono
  spesso isolati fra loro: in quel caso usa l'hotspot del telefono e collegaci
  anche il computer.
- **Il computer ha più indirizzi** (VPN, Docker, più schede di rete): lo script
  li elenca tutti, prova gli altri.
- **La riga compare ma la pagina resta bianca** → è un problema della pagina,
  non della rete: segnalalo con il modello di iPad e la versione di iPadOS.

## Struttura

| File | Contenuto |
| --- | --- |
| `index.html` | Il gioco completo: markup, CSS, JavaScript, immagini e font incorporati |
| `genera_energia.py` | Script storico di ritaglio delle celle dalla griglia originale (non più allineato a `index.html`) |
| `telecomando.py` | Server locale che sincronizza proiettore e iPad senza internet |
| `icona.png` | Sorgente a 512 px dell'icona incorporata nella pagina |
| `vercel.json` | Header di sicurezza del deploy (CSP, X-Frame-Options, ecc.) |
