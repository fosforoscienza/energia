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
   **"Scarica per uso offline"**: salva `fonte-di-energia-offline.html` nella
   cartella Download e mostra le istruzioni.
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

Ogni carta scoperta produce il fruscio della carta girata e, appena questo è
finito, una campanellina (i due suoni non si sovrappongono); richiudendola si
sente solo il fruscio. Con "Scopri tutte" si sente solo il fruscio, più tenue,
e la campanellina arriva una volta sola con l'ultima carta.

I suoni sono **sintetizzati al volo** con la Web Audio API: non ci sono file
audio da scaricare, quindi funzionano anche offline. Il pulsante
**"Suono ON / OFF"** li disattiva e la scelta viene ricordata sul dispositivo.

## Struttura

| File | Contenuto |
| --- | --- |
| `index.html` | Il gioco completo: markup, CSS, JavaScript, immagini e font incorporati |
| `genera_energia.py` | Script storico di ritaglio delle celle dalla griglia originale (non più allineato a `index.html`) |
| `vercel.json` | Header di sicurezza del deploy (CSP, X-Frame-Options, ecc.) |
