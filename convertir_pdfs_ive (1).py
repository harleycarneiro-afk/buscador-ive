"""
Convierte los PDFs del IVE a .txt estructurado por párrafos numerados,
filtrando las notas al pie.
Ejecutar desde la carpeta raíz del buscador:
    python convertir_pdfs_ive.py
"""

import pdfplumber
from pathlib import Path
import re
import json

BASE    = Path(__file__).parent
PDF_DIR = BASE / "pdfs"
TXT_DIR = BASE / "pdfs_txt"

TXT_DIR.mkdir(exist_ok=True)

def extraer_bloques(pdf_path):
    """Extrae texto página por página separando cuerpo y notas al pie."""
    bloques = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                altura = page.height
                # Zona principal: parte superior del 80% de la página
                limite = altura * 0.80
                words = page.extract_words(x_tolerance=3, y_tolerance=3, use_text_flow=True)
                if not words:
                    continue
                principales = [w['text'] for w in words if w['top'] < limite]
                if principales:
                    bloques.append(' '.join(principales))
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None
    return '\n'.join(bloques)

def limpiar_notas_inline(texto):
    """Elimina números de referencia pegados a palabras (superíndices convertidos)."""
    # Número pegado al final de una palabra antes de espacio o puntuación
    texto = re.sub(r'(\w)(\d{1,3})(\s|[.,;:!?"\'])', r'\1\3', texto)
    # Número solo al inicio de línea seguido de texto corto = nota
    lineas = texto.split('\n')
    limpias = []
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        # Detectar línea de nota: empieza con 1-3 dígitos seguidos de texto
        if re.match(r'^\d{1,3}\s+[A-ZÁÉÍÓÚÜÑCF]', linea) and len(linea) < 300:
            continue  # es una nota al pie, la omitimos
        if re.match(r'^\d{1,3}$', linea):
            continue  # solo un número, omitir
        limpias.append(linea)
    return ' '.join(limpias)

def segmentar_parrafos(texto):
    """
    Divide el texto en párrafos numerados.
    Detecta patrones como: '5.', '6.', '10.' al inicio de un segmento.
    Devuelve lista de dicts: {num, texto}
    """
    # Insertar saltos antes de cada número de párrafo
    # Patrón: número seguido de punto y espacio, con mayúscula después
    texto_marcado = re.sub(r'(\s)(\d{1,3})\.\s+([A-ZÁÉÍÓÚÜÑ])', r'\n§\2. \3', texto)

    segmentos = texto_marcado.split('\n§')
    parrafos = []

    for seg in segmentos:
        seg = seg.strip()
        if not seg:
            continue
        # Extraer número inicial si existe
        m = re.match(r'^(\d{1,3})\.\s+(.*)', seg, re.DOTALL)
        if m:
            num = int(m.group(1))
            cuerpo = m.group(2).strip()
            parrafos.append({'num': num, 'texto': cuerpo})
        else:
            # Texto sin número (intro, títulos, etc.)
            if parrafos:
                # Agregarlo al párrafo anterior
                parrafos[-1]['texto'] += ' ' + seg
            else:
                parrafos.append({'num': 0, 'texto': seg})

    return parrafos

pdfs = sorted(PDF_DIR.glob("*.pdf"))
if not pdfs:
    print(f"\n⚠  No se encontraron PDFs en {PDF_DIR}")
    exit(1)

print(f"\n── Convirtiendo {len(pdfs)} PDFs del IVE ────────────────────────\n")

ok = 0
for pdf in pdfs:
    txt_out = TXT_DIR / (pdf.stem + ".txt")
    print(f"  Procesando: {pdf.name}")

    texto_crudo = extraer_bloques(pdf)
    if not texto_crudo:
        print(f"  ✗  Sin texto extraído\n")
        continue

    texto_limpio = limpiar_notas_inline(texto_crudo)
    parrafos = segmentar_parrafos(texto_limpio)

    if not parrafos:
        # Guardar texto plano si no hay párrafos detectados
        txt_out.write_text(texto_limpio, encoding='utf-8')
        print(f"  ✓  (sin párrafos numerados)  {len(texto_limpio):,} chars\n")
        ok += 1
        continue

    # Guardar como JSON estructurado para que el buscador pueda usarlo
    # Formato: [{"num": 5, "texto": "..."}, ...]
    # También guardar versión plana para compatibilidad
    lineas = []
    for p in parrafos:
        if p['num'] > 0:
            lineas.append(f"§{p['num']}. {p['texto']}")
        else:
            lineas.append(p['texto'])

    contenido = '\n\n'.join(lineas)
    txt_out.write_text(contenido, encoding='utf-8')
    print(f"  ✓  {pdf.stem}.txt  —  {len(parrafos)} párrafos  ({len(contenido):,} chars)\n")
    ok += 1

print(f"────────────────────────────────────────────────────────")
print(f"  Convertidos: {ok}/{len(pdfs)}")
print(f"  Guardados en: pdfs_txt/")
print(f"\n  Avisale a Claude para actualizar el index.html\n")
