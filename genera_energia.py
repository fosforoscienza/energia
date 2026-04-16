#!/usr/bin/env python3
"""
Genera il file energia.html — gioco interattivo "Fonte di Energia" per Fosforo.
Ritaglia le celle dalla griglia e le incorpora come base64 in un singolo HTML.

Uso: python3 tools/genera_energia.py
Input: Downloads/energia OFFLINE/1.png (rivelata) e 2.png (coperta)
Output: energia.html nella root del progetto
"""

import base64
import io
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Errore: Pillow non installato. Esegui: pip3 install Pillow")
    sys.exit(1)

# === Percorsi ===
BASE_DIR = Path(__file__).resolve().parent.parent
IMG_REVEALED = Path.home() / "Downloads" / "energia OFFLINE" / "1.png"
IMG_COVERED = Path.home() / "Downloads" / "energia OFFLINE" / "2.png"
OUTPUT_HTML = BASE_DIR / "energia.html"

# === Coordinate griglia (pixel) ===
# Determinate dall'analisi delle transizioni di luminosita'
COL_RANGES = [
    (575, 766),   # Elettrica
    (776, 966),   # Meccanica
    (977, 1167),  # Chimica
    (1178, 1367), # Termica
    (1378, 1568), # Luminosa
]
ROW_RANGES = [
    (263, 411),   # Elettrica
    (417, 564),   # Meccanica
    (571, 718),   # Chimica
    (725, 872),   # Termica
    (879, 1026),  # Luminosa
]

ENERGY_TYPES = ["Elettrica", "Meccanica", "Chimica", "Termica", "Luminosa"]
INSET = 6  # pixel di margine per evitare i bordi della griglia

# Descrizioni accessibili di ogni cella (riga, colonna)
CELL_DESCRIPTIONS = {
    (0,1): "Dinamo a manovella",
    (0,2): "Batteria",
    (0,3): "Termocoppia",
    (0,4): "Pannello solare",
    (1,0): "Motore elettrico",
    (1,2): "Muscolo (braccio)",
    (1,3): "Macchina a vapore",
    (1,4): "Radiometro di Crookes",
    (2,0): "Caricabatterie / Elettrolisi",
    (2,1): "Barile di petrolio",
    (2,3): "Siringa / Reazione endotermica",
    (2,4): "Fotosintesi",
    (3,0): "Stufetta elettrica",
    (3,1): "Lampadina",
    (3,2): "Fuoco / Combustione",
    (3,4): "Termometro al sole",
    (4,0): "Torcia elettrica",
    (4,1): "Acciarino / Pietra focaia",
    (4,2): "Candela",
    (4,3): "Fuochi d'artificio",
}


def crop_cell(img, row, col):
    """Ritaglia una cella dalla griglia con margine interno."""
    x1, x2 = COL_RANGES[col]
    y1, y2 = ROW_RANGES[row]
    return img.crop((x1 + INSET, y1 + INSET, x2 - INSET, y2 - INSET))


def img_to_base64(pil_img, fmt="PNG", quality=85):
    """Converte un'immagine PIL in stringa base64."""
    buf = io.BytesIO()
    if fmt == "JPEG":
        pil_img = pil_img.convert("RGB")
        pil_img.save(buf, format=fmt, quality=quality, optimize=True)
    else:
        pil_img.save(buf, format=fmt, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def generate_html(cell_images_b64, cover_b64):
    """Genera il file HTML completo."""

    # Costruisci le data URI per ogni cella
    cell_data = {}
    for (r, c), b64 in cell_images_b64.items():
        cell_data[f"{r}-{c}"] = b64

    cells_js = ",\n    ".join(
        f'"{k}": "{v}"' for k, v in sorted(cell_data.items())
    )

    descs_js = ",\n    ".join(
        f'"{r}-{c}": "{desc}"'
        for (r, c), desc in sorted(CELL_DESCRIPTIONS.items())
    )

    return f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fonte di Energia — Fosforo</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #0a1420;
    color: #e8dcc8;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px 20px;
    overflow-x: hidden;
  }}

  h1 {{
    font-size: clamp(1.4rem, 3vw, 2.2rem);
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 4px;
    color: #f0e6d4;
    text-shadow: 0 2px 12px rgba(240,200,120,0.15);
  }}

  .subtitle {{
    font-size: clamp(0.75rem, 1.5vw, 0.95rem);
    color: #8a7e6e;
    text-align: center;
    margin-bottom: 10px;
  }}

  .grid-wrapper {{
    display: grid;
    grid-template-columns: auto repeat(5, 1fr);
    grid-template-rows: auto repeat(5, 1fr);
    gap: 3px;
    max-width: min(900px, calc(100vh * 1.1));
    width: 100%;
  }}

  /* Header cella vuota (angolo) */
  .corner {{
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  /* Header colonne */
  .col-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6px 4px;
    text-align: center;
    font-size: clamp(0.55rem, 1.1vw, 0.8rem);
    line-height: 1.2;
    color: #c0b8a8;
  }}
  .col-header .label-small {{
    font-size: clamp(0.45rem, 0.9vw, 0.65rem);
    color: #7a7060;
    margin-bottom: 2px;
  }}
  .col-header .label-big {{
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  /* Header righe */
  .row-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4px 8px;
    text-align: center;
    font-size: clamp(0.55rem, 1.1vw, 0.8rem);
    line-height: 1.2;
    color: #c0b8a8;
    min-width: 80px;
  }}
  .row-header .label-small {{
    font-size: clamp(0.45rem, 0.9vw, 0.65rem);
    color: #7a7060;
    margin-bottom: 2px;
  }}
  .row-header .label-big {{
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  /* Cella della griglia */
  .cell {{
    position: relative;
    width: 100%;
    aspect-ratio: 191 / 135;
    perspective: 800px;
    cursor: pointer;
    border-radius: 6px;
    overflow: hidden;
  }}

  .cell.diagonal {{
    background: #0e2a3e;
    cursor: default;
    border: 1px solid #1a3a52;
  }}

  .cell-inner {{
    position: relative;
    width: 100%;
    height: 100%;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
  }}

  .cell.flipped .cell-inner {{
    transform: rotateY(180deg);
  }}

  .cell-front, .cell-back {{
    position: absolute;
    inset: 0;
    backface-visibility: hidden;
    border-radius: 6px;
    overflow: hidden;
  }}

  .cell-front {{
    background: #d4b896;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #b89a70;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.15);
  }}

  .cell-front .question-mark {{
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 900;
    color: #6b5a42;
    text-shadow: 2px 2px 0 rgba(0,0,0,0.1);
    user-select: none;
    font-style: italic;
    font-family: Georgia, "Times New Roman", serif;
  }}

  .cell-back {{
    transform: rotateY(180deg);
    background: #1a2a3a;
    border: 2px solid #2a4a62;
  }}

  .cell-back img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}

  .cell:not(.diagonal):not(.flipped):hover .cell-front {{
    background: #dcc8a8;
    border-color: #c8a870;
    box-shadow: 0 0 15px rgba(200,168,112,0.3), inset 0 2px 8px rgba(0,0,0,0.1);
  }}

  .cell:not(.diagonal):not(.flipped):hover .question-mark {{
    color: #5a4832;
    transform: scale(1.1);
    transition: transform 0.2s;
  }}

  /* Controlli */
  .controls {{
    display: flex;
    gap: 12px;
    align-items: center;
    margin-top: 12px;
    flex-wrap: wrap;
    justify-content: center;
  }}

  .counter {{
    font-size: clamp(0.85rem, 1.5vw, 1.1rem);
    color: #a09080;
    font-variant-numeric: tabular-nums;
    min-width: 100px;
    text-align: center;
  }}
  .counter strong {{
    color: #f0d8a0;
    font-size: 1.3em;
  }}

  button {{
    background: #1a3048;
    color: #c8b89a;
    border: 1px solid #2a4a60;
    padding: 8px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-size: clamp(0.75rem, 1.2vw, 0.9rem);
    font-family: inherit;
    transition: all 0.2s;
  }}
  button:hover {{
    background: #243e58;
    border-color: #3a6080;
    color: #f0e0c0;
  }}
  button:active {{
    transform: scale(0.97);
  }}

  /* Messaggio completamento */
  .complete-msg {{
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(10,20,32,0.85);
    z-index: 100;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.4s;
  }}
  .complete-msg.show {{
    opacity: 1;
    pointer-events: auto;
  }}
  .complete-msg .inner {{
    text-align: center;
    padding: 40px;
    background: #12283e;
    border: 2px solid #2a5070;
    border-radius: 16px;
    box-shadow: 0 0 40px rgba(42,80,112,0.4);
    max-width: 400px;
  }}
  .complete-msg h2 {{
    font-size: 1.8rem;
    color: #f0d8a0;
    margin-bottom: 12px;
  }}
  .complete-msg p {{
    color: #a0b0c0;
    margin-bottom: 20px;
    line-height: 1.5;
  }}

  /* Side labels */
  .side-label {{
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%) rotate(-90deg);
    font-size: clamp(0.6rem, 1vw, 0.85rem);
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6a6050;
    white-space: nowrap;
    pointer-events: none;
    display: none;
  }}

  @media (min-width: 700px) {{
    .side-label {{ display: block; }}
  }}

  .fosforo-credit {{
    margin-top: 16px;
    font-size: 0.7rem;
    color: #504838;
    text-align: center;
  }}
</style>
</head>
<body>

<h1>Fonte di Energia</h1>
<p class="subtitle">Clicca sulle caselle per scoprire come si trasforma l'energia</p>

<div class="grid-wrapper" role="grid" aria-label="Tabella trasformazioni energetiche">
  <!-- Corner -->
  <div class="corner" role="columnheader"></div>
  <!-- Column headers -->
  <div class="col-header" role="columnheader"><span class="label-small">energia</span><span class="label-big">Elettrica</span></div>
  <div class="col-header" role="columnheader"><span class="label-small">energia</span><span class="label-big">Meccanica</span></div>
  <div class="col-header" role="columnheader"><span class="label-small">energia</span><span class="label-big">Chimica</span></div>
  <div class="col-header" role="columnheader"><span class="label-small">energia</span><span class="label-big">Termica</span></div>
  <div class="col-header" role="columnheader"><span class="label-small">energia</span><span class="label-big">Luminosa</span></div>
</div>

<div class="controls">
  <div class="counter"><strong id="count">0</strong> / 20</div>
  <button id="btn-reveal" type="button">Scopri tutte</button>
  <button id="btn-reset" type="button">Reset</button>
</div>

<!-- Completamento overlay -->
<div class="complete-msg" id="complete-overlay">
  <div class="inner">
    <h2>Complimenti!</h2>
    <p>Hai scoperto tutte le 20 trasformazioni energetiche!</p>
    <button id="btn-close" type="button">Chiudi</button>
  </div>
</div>

<p class="fosforo-credit">fosforo: la festa della scienza</p>

<script>
// === Dati celle (base64) ===
const CELL_IMAGES = {{
    {cells_js}
}};

const CELL_DESCS = {{
    {descs_js}
}};

const ENERGY = ["Elettrica", "Meccanica", "Chimica", "Termica", "Luminosa"];
const TOTAL = 20;
let revealed = new Set();

const grid = document.querySelector(".grid-wrapper");
const counter = document.getElementById("count");
const overlay = document.getElementById("complete-overlay");

// Genera righe
for (let r = 0; r < 5; r++) {{
  // Row header
  const rh = document.createElement("div");
  rh.className = "row-header";
  rh.setAttribute("role", "rowheader");
  rh.innerHTML = '<span class="label-small">energia</span><span class="label-big">' + ENERGY[r] + '</span>';
  grid.appendChild(rh);

  // 5 celle
  for (let c = 0; c < 5; c++) {{
    const cell = document.createElement("div");
    cell.className = "cell" + (r === c ? " diagonal" : "");
    cell.dataset.row = r;
    cell.dataset.col = c;
    const key = r + "-" + c;
    const desc = CELL_DESCS[key] || "";

    if (r === c) {{
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-label", "Stessa energia: " + ENERGY[r]);
    }} else {{
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-label", "Da " + ENERGY[c] + " a " + ENERGY[r] + ": " + desc + " (coperta)");
      cell.setAttribute("tabindex", "0");

      const inner = document.createElement("div");
      inner.className = "cell-inner";

      const front = document.createElement("div");
      front.className = "cell-front";
      front.innerHTML = '<span class="question-mark">?</span>';

      const back = document.createElement("div");
      back.className = "cell-back";
      const img = document.createElement("img");
      img.src = "data:image/jpeg;base64," + CELL_IMAGES[key];
      img.alt = desc;
      img.loading = "lazy";
      back.appendChild(img);

      inner.appendChild(front);
      inner.appendChild(back);
      cell.appendChild(inner);

      cell.addEventListener("click", () => revealCell(cell, key, desc));
      cell.addEventListener("keydown", (e) => {{
        if (e.key === "Enter" || e.key === " ") {{
          e.preventDefault();
          revealCell(cell, key, desc);
        }}
      }});
    }}

    grid.appendChild(cell);
  }}
}}

function revealCell(cell, key, desc) {{
  if (cell.classList.contains("flipped")) return;
  cell.classList.add("flipped");
  revealed.add(key);
  counter.textContent = revealed.size;

  // Aggiorna aria-label
  const r = parseInt(cell.dataset.row);
  const c = parseInt(cell.dataset.col);
  cell.setAttribute("aria-label", "Da " + ENERGY[c] + " a " + ENERGY[r] + ": " + desc);

  if (revealed.size === TOTAL) {{
    setTimeout(() => overlay.classList.add("show"), 600);
  }}
}}

function revealAll() {{
  const cells = document.querySelectorAll(".cell:not(.diagonal):not(.flipped)");
  const total = cells.length;
  cells.forEach((cell, i) => {{
    setTimeout(() => {{
      const key = cell.dataset.row + "-" + cell.dataset.col;
      const desc = CELL_DESCS[key] || "";
      revealCell(cell, key, desc);
      if (i === total - 1 && revealed.size === TOTAL) {{
        setTimeout(() => overlay.classList.add("show"), 600);
      }}
    }}, i * 80);
  }});
}}

function resetAll() {{
  overlay.classList.remove("show");
  revealed.clear();
  counter.textContent = "0";
  document.querySelectorAll(".cell.flipped").forEach(cell => {{
    cell.classList.remove("flipped");
    const r = parseInt(cell.dataset.row);
    const c = parseInt(cell.dataset.col);
    const key = r + "-" + c;
    const desc = CELL_DESCS[key] || "";
    cell.setAttribute("aria-label", "Da " + ENERGY[c] + " a " + ENERGY[r] + ": " + desc + " (coperta)");
  }});
}}

document.getElementById("btn-reveal").addEventListener("click", revealAll);
document.getElementById("btn-reset").addEventListener("click", resetAll);
document.getElementById("btn-close").addEventListener("click", () => overlay.classList.remove("show"));
</script>
</body>
</html>'''


def main():
    if not IMG_REVEALED.exists():
        print(f"Errore: immagine rivelata non trovata: {IMG_REVEALED}")
        sys.exit(1)
    if not IMG_COVERED.exists():
        print(f"Errore: immagine coperta non trovata: {IMG_COVERED}")
        sys.exit(1)

    print("Caricamento immagini...")
    img_revealed = Image.open(IMG_REVEALED)
    print(f"  Rivelata: {img_revealed.size}")

    print("Ritaglio celle...")
    cell_images = {}
    for r in range(5):
        for c in range(5):
            if r == c:
                continue  # salta diagonale
            crop = crop_cell(img_revealed, r, c)
            # Ridimensiona per dimensione consistente e file piu' leggero
            crop = crop.resize((280, 220), Image.LANCZOS)
            b64 = img_to_base64(crop, fmt="JPEG", quality=82)
            cell_images[(r, c)] = b64
            desc = CELL_DESCRIPTIONS.get((r, c), "?")
            print(f"  [{r},{c}] {desc}: {len(b64)} chars")

    print(f"\nGenerazione HTML ({len(cell_images)} celle)...")
    html = generate_html(cell_images, None)

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"\nSalvato: {OUTPUT_HTML}")
    print(f"Dimensione: {size_kb:.0f} KB")
    print("\nApri il file con doppio click nel browser!")


if __name__ == "__main__":
    main()
