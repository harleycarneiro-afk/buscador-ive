"""
Convierte los PDFs del IVE a .txt filtrando notas al pie.
Ejecutar desde la carpeta raíz del buscador (donde está index.html):
    python convertir_pdfs_ive.py
"""

import pdfplumber
from pathlib import Path
import re

BASE    = Path(__file__).parent
PDF_DIR = BASE / "pdfs"
TXT_DIR = BASE / "pdfs_txt"

TXT_DIR.mkdir(exist_ok=True)

def es_nota_al_pie(linea, altura_pagina, bbox):
    """Detecta si una línea es nota al pie por posición y patrón."""
    if bbox and bbox[3] < altura_pagina * 0.20:
        return True
    texto = linea.strip()
    # Línea que empieza con número seguido de texto corto (referencia)
    if re.match(r'^\d{1,4}\s+\S', texto) and len(texto) < 200:
        return True
    # Solo número
    if re.match(r'^\d{1,4}\.?\s*$', texto):
        return True
    return False

def extraer_texto_limpio(pdf_path):
    """Extrae texto de un PDF filtrando notas al pie por posición."""
    paginas = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                altura = page.height

                # Extraer palabras con sus coordenadas
                words = page.extract_words(
                    x_tolerance=3, y_tolerance=3,
                    keep_blank_chars=False,
                    use_text_flow=True
                )

                if not words:
                    texto = page.extract_text()
                    if texto:
                        paginas.append(texto.strip())
                    continue

                # Determinar el límite inferior del texto principal
                # Las notas al pie suelen estar en el 18% inferior de la página
                limite_inferior = altura * 0.82

                # Agrupar palabras por línea (tolerancia vertical de 3pts)
                lineas = {}
                for w in words:
                    y = round(w['top'] / 3) * 3
                    if y not in lineas:
                        lineas[y] = []
                    lineas[y].append(w)

                texto_principal = []
                notas = []

                for y in sorted(lineas.keys()):
                    palabras_linea = lineas[y]
                    texto_linea = ' '.join(w['text'] for w in palabras_linea).strip()

                    if not texto_linea:
                        continue

                    # Posición vertical de esta línea
                    top = palabras_linea[0]['top']

                    if top > limite_inferior:
                        # Está en la zona de notas al pie
                        notas.append(texto_linea)
                    else:
                        # Limpiar números de referencia inline (superíndices)
                        # Ej: "texto523 ." → "texto."
                        texto_limpio = re.sub(r'(\w)(\d{1,4})(\s|[.,;:]|$)', r'\1\3', texto_linea)
                        texto_principal.append(texto_limpio)

                if texto_principal:
                    paginas.append(' '.join(texto_principal))

    except Exception as e:
        print(f"  ✗  Error: {e}")
        return None

    return '\n\n'.join(paginas)

pdfs = sorted(PDF_DIR.glob("*.pdf"))
if not pdfs:
    print(f"\n⚠  No se encontraron PDFs en {PDF_DIR}")
    exit(1)

print(f"\n── Convirtiendo {len(pdfs)} PDFs del IVE ────────────────────────\n")

ok = 0
for pdf in pdfs:
    txt_out = TXT_DIR / (pdf.stem + ".txt")
    print(f"  Procesando: {pdf.name}")
    texto = extraer_texto_limpio(pdf)
    if texto:
        txt_out.write_text(texto, encoding='utf-8')
        print(f"  ✓  {pdf.stem}.txt  ({len(texto):,} caracteres)\n")
        ok += 1
    else:
        print(f"  ✗  No se pudo convertir\n")

print(f"────────────────────────────────────────────────────────")
print(f"  Convertidos: {ok}/{len(pdfs)}")
print(f"  Guardados en: {TXT_DIR}")
print(f"\n  Avisale a Claude para continuar con el index.html\n")
