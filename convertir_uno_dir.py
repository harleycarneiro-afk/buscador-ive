import pdfplumber
import re
from pathlib import Path

BASE    = Path(r"C:\Users\P Harley Carneiro\Documents\buscador-ive")
PDF_DIR = BASE / "pdfs"
TXT_DIR = BASE / "pdfs_txt"

def extraer_pagina_limpia(page):
    altura = page.height
    limite_sup = altura * 0.06
    limite_inf = altura * 0.80
    words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False, use_text_flow=True)
    if not words:
        return []
    lineas = {}
    for w in words:
        if w['top'] < limite_sup or w['top'] > limite_inf:
            continue
        y = round(w['top'] / 4) * 4
        if y not in lineas:
            lineas[y] = []
        lineas[y].append(w['text'])
    return [' '.join(lineas[y]) for y in sorted(lineas.keys())]

def limpiar_superindices(texto):
    texto = re.sub(r'([a-záéíóúüñA-ZÁÉÍÓÚÜÑ»"\'])(\d{1,3})(\s|[.,;:!?\)»"\']|$)', r'\1\3', texto)
    return texto.strip()

patron_num = re.compile(r'^(\d+)\s*\.\s+(\S.*)', re.DOTALL)
pagina_inicio = 8  # página 9 en índice 0

pdf_path = PDF_DIR / "Direccion-Espiritual-TEXT.pdf"
txt_path = TXT_DIR / "Direccion-Espiritual-TEXT.txt"

elementos = []
parrafo_actual = None

with pdfplumber.open(pdf_path) as pdf:
    total = len(pdf.pages)
    for i, page in enumerate(pdf.pages):
        if i < pagina_inicio:
            continue
        lineas = extraer_pagina_limpia(page)
        for linea in lineas:
            linea = limpiar_superindices(linea.strip())
            if not linea:
                continue
            m = patron_num.match(linea)
            if m:
                if parrafo_actual:
                    elementos.append(parrafo_actual)
                parrafo_actual = [m.group(1), [m.group(2).strip()]]
            elif parrafo_actual:
                parrafo_actual[1].append(linea)
        if (i+1) % 10 == 0:
            print(f"  {i+1}/{total} páginas...")

if parrafo_actual:
    elementos.append(parrafo_actual)

lineas_out = []
for num, contenido in elementos:
    texto = ' '.join(contenido).strip()
    if texto:
        lineas_out.append(f'§{num}. {texto}')
        lineas_out.append('')

contenido_final = '\n'.join(lineas_out)
txt_path.write_text(contenido_final, encoding='utf-8')
print(f'Listo: {len(elementos)} párrafos ({len(contenido_final):,} chars)')