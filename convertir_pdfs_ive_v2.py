"""
Convierte los PDFs del IVE a TXT estructurado por párrafos numerados.
Detecta dos patrones:
  - "5. Texto..." (mayoría de documentos)
  - "[5] Texto..." (Constituciones y Dir. Espiritualidad)
Ejecutar desde la carpeta raíz del buscador:
    python convertir_pdfs_ive_v2.py
"""

import pdfplumber
import re
from pathlib import Path

BASE    = Path(__file__).parent
PDF_DIR = BASE / "pdfs"
TXT_DIR = BASE / "pdfs_txt"
TXT_DIR.mkdir(exist_ok=True)

# Documentos que usan [N] en vez de N.
USA_CORCHETES = ['ConstitucionesDir', 'Direccion-Espiritual']

def extraer_lineas_pagina(page):
    """Extrae líneas de texto de una página, filtrando zona de notas al pie."""
    altura = page.height
    limite = altura * 0.83  # ignorar el 17% inferior (notas al pie)

    words = page.extract_words(
        x_tolerance=3, y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=True
    )
    if not words:
        return []

    # Agrupar palabras por línea (misma posición vertical ±3pts)
    lineas = {}
    for w in words:
        if w['top'] > limite:
            continue  # nota al pie, ignorar
        y = round(w['top'] / 4) * 4
        if y not in lineas:
            lineas[y] = []
        lineas[y].append(w['text'])

    return [' '.join(lineas[y]) for y in sorted(lineas.keys())]

def procesar_documento(pdf_path, usa_corchetes=False):
    """
    Extrae y estructura el texto de un PDF en párrafos numerados.
    Retorna lista de (num, texto) donde num es el número de párrafo.
    """
    if usa_corchetes:
        # Patrón: [5] o [5a] al inicio
        patron = re.compile(r'^\[(\d+[a-z]?)\]\s*(.*)', re.DOTALL)
    else:
        # Patrón: 5. o 5 . al inicio de línea
        patron = re.compile(r'^(\d+)\s*\.\s+(.*)', re.DOTALL)

    parrafos = []  # lista de [num, lineas[]]
    intro_buffer = []  # texto antes del primer párrafo numerado
    encontro_primero = False

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                lineas = extraer_lineas_pagina(page)

                for linea in lineas:
                    linea = linea.strip()
                    if not linea:
                        continue

                    m = patron.match(linea)
                    if m:
                        encontro_primero = True
                        num = m.group(1)
                        resto = m.group(2).strip()
                        parrafos.append([num, [resto] if resto else []])
                    else:
                        # Limpiar números de referencia bibliográfica inline
                        # Ej: "texto5 ." → "texto."
                        linea_limpia = re.sub(r'(\w)(\d{1,3})(\s|[.,;:]|$)', r'\1\3', linea)

                        if encontro_primero and parrafos:
                            parrafos[-1][1].append(linea_limpia)
                        else:
                            intro_buffer.append(linea_limpia)

                if i % 20 == 0:
                    print(f"    página {i}/{total}...")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, None

    return intro_buffer, parrafos

def convertir(pdf_path, txt_path, usa_corchetes=False):
    print(f"  Procesando: {pdf_path.name}")
    intro, parrafos = procesar_documento(pdf_path, usa_corchetes)

    if intro is None:
        return 0

    lineas_out = []

    # Texto introductorio antes del primer párrafo
    if intro:
        lineas_out.append(' '.join(intro))
        lineas_out.append('')

    # Párrafos numerados
    for num, lineas in parrafos:
        texto = ' '.join(lineas).strip()
        if texto:
            lineas_out.append(f'§{num}. {texto}')
            lineas_out.append('')

    contenido = '\n'.join(lineas_out)
    txt_path.write_text(contenido, encoding='utf-8')
    print(f"  ✓  {txt_path.stem}  —  {len(parrafos)} párrafos  ({len(contenido):,} chars)\n")
    return len(parrafos)

# ══════════════════════════════════════════════════════════
# EJECUTAR
# ══════════════════════════════════════════════════════════

pdfs = sorted(PDF_DIR.glob("*.pdf"))
if not pdfs:
    print(f"\n⚠  No se encontraron PDFs en {PDF_DIR}")
    exit(1)

print(f"\n── Convirtiendo {len(pdfs)} PDFs del IVE (v2) ───────────────────\n")

ok = 0
for pdf in pdfs:
    txt_out = TXT_DIR / (pdf.stem + ".txt")
    usa_c = any(p in pdf.stem for p in USA_CORCHETES)
    n = convertir(pdf, txt_out, usa_corchetes=usa_c)
    if n > 0:
        ok += 1

print(f"────────────────────────────────────────────────────────")
print(f"  Convertidos: {ok}/{len(pdfs)}")
print(f"  Guardados en: pdfs_txt/")
print(f"\n  Avisale a Claude para subir a GitHub.\n")
