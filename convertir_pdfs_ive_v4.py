"""
Convierte los PDFs del IVE a TXT limpio:
- Elimina encabezados de página (primeras líneas)
- Elimina notas al pie (zona inferior + patrones de referencia)
- Elimina números superíndice del texto
- Conserva párrafos numerados exactos y títulos
Ejecutar desde la carpeta del buscador:
    python convertir_pdfs_ive_v4.py
"""

import pdfplumber
import re
from pathlib import Path

BASE    = Path(__file__).parent
PDF_DIR = BASE / "pdfs"
TXT_DIR = BASE / "pdfs_txt"
TXT_DIR.mkdir(exist_ok=True)

USA_CORCHETES = ['ConstitucionesDir', 'Direccion-Espiritual']

# Página de inicio del texto real (índice 0 = primera página del PDF)
PAGINA_INICIO = {
    'ConstitucionesDir-Espiritualidad':          22,
    'Direccion-Espiritual-TEXT':                  8,
    'Ecumenismo-TEXT':                            8,
    'Ejercicios-Espirituales-Completo':          12,
    'Evangelizacion-de-la-cultura-TEXT':          8,
    'Formacion-intelectual-TEXT':                 8,
    'Gobierno-TEXT':                              8,
    'Hermanos-religiosos':                        1,
    'Mision-Ad-Gentes-TEXT':                      8,
    'Misiones-populares-TEXT':                   10,
    'Noviciados-TEXT':                            8,
    'Obras-de-misericordia-TEXT':                 8,
    'Oratorio-TEXT':                              8,
    'Parroquias-TEXT':                            8,
    'Predicacion-de-la-Palabra-de-Dios-TEXT':     8,
    'Rama-oriental-TEXT':                        10,
    'Seminarios-Mayores-TEXT':                    8,
    'Seminarios-menores-TEXT':                   10,
    'Tercera-orden-TEXT':                         8,
    'Vida-consagrada-TEXT':                       8,
    'Vida-contemplativa-TEXT':                    8,
    'Vida-fraterna-TEXT':                         8,
    'Vida-liturgica-TEXT':                       10,
    'Vocaciones-TEXT':                            8,
}

def extraer_pagina_limpia(page):
    """
    Extrae texto de la zona principal de la página:
    - Ignora encabezado (5% superior)
    - Ignora notas al pie (20% inferior)
    - Agrupa por líneas
    """
    altura = page.height
    limite_sup = altura * 0.06   # ignorar encabezado
    limite_inf = altura * 0.80   # ignorar notas al pie

    words = page.extract_words(
        x_tolerance=3, y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=True
    )
    if not words:
        return []

    # Agrupar por línea
    lineas = {}
    for w in words:
        if w['top'] < limite_sup or w['top'] > limite_inf:
            continue
        y = round(w['top'] / 4) * 4
        if y not in lineas:
            lineas[y] = []
        lineas[y].append(w['text'])

    return [' '.join(lineas[y]) for y in sorted(lineas.keys())]

def es_nota_al_pie(linea):
    """
    Detecta líneas que son notas al pie o referencias bibliográficas.
    Patrón: empiezan con número seguido de texto de referencia corto.
    """
    texto = linea.strip()
    # Número solo
    if re.match(r'^\d{1,3}\.?\s*$', texto):
        return True
    # Número + referencia bibliográfica (Cf., ibid., autor, etc.)
    if re.match(r'^\d{1,3}\s+(Cf\.|Ibidem|Ibid\.|CIC|LG|SC|GS|AG|PO|PC|AA|UR|NA|DV|OT|CD|GE|IM|ES|SP|EN|CT|RH|DM|LE|SRS|CA|VS|EV|TMA|NMI|DCE|SPE|CV|LS|AL|GE|VG|QA)', texto):
        return True
    if re.match(r'^\d{1,3}\s+[A-ZÁÉÍÓÚÜÑ]{2,}', texto) and len(texto) < 250:
        return True
    return False

def es_indice(linea):
    """Detecta líneas de índice (texto con puntos y número de página)."""
    return bool(re.search(r'\.{3,}\s*\d+\s*$', linea)) or \
           bool(re.match(r'^[\d\s\.\-]+$', linea.strip()) and len(linea.strip()) < 20)

def limpiar_superindices(texto):
    """Elimina números superíndice pegados a palabras."""
    # Número al final de palabra antes de espacio o puntuación
    texto = re.sub(r'([a-záéíóúüñA-ZÁÉÍÓÚÜÑ»"\'])(\d{1,3})(\s|[.,;:!?\)»"\']|$)', r'\1\3', texto)
    # Número solo entre espacios que parece referencia
    texto = re.sub(r'\s(\d{1,3})\s', ' ', texto)
    return texto.strip()

def es_titulo(linea):
    """Detecta títulos reales descartando notas al pie y referencias."""
    texto = linea.strip()
    if not texto or len(texto) < 3 or len(texto) > 100:
        return False
    # Descartar si termina en punto (es texto normal o nota)
    if texto.endswith('.') or texto.endswith(',') or texto.endswith(';'):
        return False
    # Descartar si contiene abreviaciones bibliográficas
    biblios = ['S.Th.', 'ISBN', 'Cf.', 'Ibid', 'ibid', 'CIC,', 'Ph.', 'Fax',
               'http', 'www', '.org', '.com', 'Press', 'New York', 'Inc.',
               'Copyright', '©', 'Library', 'Congress', 'Manufactured']
    if any(b in texto for b in biblios):
        return False
    # Descartar si empieza con número (párrafo o nota)
    if re.match(r'^\d', texto):
        return False
    # Descartar líneas muy cortas sin sentido
    palabras = texto.split()
    if len(palabras) < 1:
        return False
    # Aceptar patrones de título válidos:
    # TODO MAYÚSCULAS corto
    letras = [c for c in texto if c.isalpha()]
    if len(letras) >= 2 and sum(1 for c in letras if c.isupper()) / len(letras) > 0.85 and len(texto) < 80:
        return True
    # A) Título... / B) Título...
    if re.match(r'^[A-Z]\)\s+\w', texto) and len(texto) < 80:
        return True
    # Artículo N: Título
    if re.match(r'^Art[ií]culo\s+\d+', texto, re.IGNORECASE):
        return True
    # PARTE I, II, etc.
    if re.match(r'^(PARTE|CAPÍTULO|CAPITULO|SECCIÓN|SECCION)\s+', texto):
        return True
    return False

def procesar_pdf(pdf_path, usa_corchetes=False):
    if usa_corchetes:
        patron_num = re.compile(r'^\[(\d+[a-z]?)\]\s*(.*)', re.DOTALL)
    else:
        patron_num = re.compile(r'^(\d+)\s*\.\s+(\S.*)', re.DOTALL)

    elementos = []
    parrafo_actual = None
    intro_lines = []
    encontro_primero = False

    # Obtener página de inicio del mapa predefinido
    primera_pagina_texto = PAGINA_INICIO.get(pdf_path.stem, 0)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                if i - 1 < primera_pagina_texto:
                    continue  # saltar portada e índice
                lineas = extraer_pagina_limpia(page)

                for linea in lineas:
                    linea = linea.strip()
                    if not linea:
                        continue

                    # Filtrar índices
                    if es_indice(linea):
                        continue

                    # Filtrar notas al pie
                    if es_nota_al_pie(linea):
                        continue

                    # Limpiar superíndices
                    linea = limpiar_superindices(linea)
                    if not linea:
                        continue

                    # ¿Es número de párrafo?
                    m = patron_num.match(linea)
                    if m:
                        encontro_primero = True
                        num = m.group(1)
                        resto = m.group(2).strip() if m.group(2) else ''
                        if parrafo_actual is not None:
                            elementos.append(parrafo_actual)
                        parrafo_actual = ['parrafo', num, [resto] if resto else []]
                        continue

                    # ¿Es título?
                    if es_titulo(linea):
                        if parrafo_actual is not None:
                            elementos.append(parrafo_actual)
                            parrafo_actual = None
                        elementos.append(['titulo', None, linea])
                        if not encontro_primero:
                            encontro_primero = False  # títulos antes del primer párrafo OK
                        continue

                    # Texto normal
                    if parrafo_actual is not None:
                        parrafo_actual[2].append(linea)
                    elif not encontro_primero:
                        intro_lines.append(linea)

                if i % 10 == 0 or i == total:
                    print(f"    {i}/{total} páginas...")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, None

    if parrafo_actual is not None:
        elementos.append(parrafo_actual)

    return intro_lines, elementos

def convertir(pdf_path, txt_path, usa_corchetes=False):
    print(f"\n  ── {pdf_path.name}")
    intro, elementos = procesar_pdf(pdf_path, usa_corchetes)
    if elementos is None:
        return 0

    lineas_out = []

    if intro:
        texto_intro = ' '.join(intro).strip()
        if texto_intro:
            lineas_out.append(texto_intro)
            lineas_out.append('')

    n_parrafos = 0
    for tipo, num, contenido in elementos:
        if tipo == 'titulo':
            lineas_out.append(f'§TÍTULO§ {contenido}')
            lineas_out.append('')
        elif tipo == 'parrafo':
            texto = ' '.join(contenido).strip()
            # Limpieza final de superíndices residuales
            texto = limpiar_superindices(texto)
            if texto:
                lineas_out.append(f'§{num}. {texto}')
                lineas_out.append('')
                n_parrafos += 1

    contenido_final = '\n'.join(lineas_out)
    txt_path.write_text(contenido_final, encoding='utf-8')
    print(f"  ✓  {n_parrafos} párrafos  ({len(contenido_final):,} chars)")
    return n_parrafos

# ══════════════════════════════════════════════════════════
pdfs = sorted(PDF_DIR.glob("*.pdf"))
if not pdfs:
    print(f"\n⚠  No se encontraron PDFs en {PDF_DIR}")
    exit(1)

print(f"\n── Convirtiendo {len(pdfs)} PDFs (v4 — texto limpio) ───────────\n")
ok = 0
for pdf in pdfs:
    txt_out = TXT_DIR / (pdf.stem + ".txt")
    usa_c = any(p in pdf.stem for p in USA_CORCHETES)
    n = convertir(pdf, txt_out, usa_corchetes=usa_c)
    if n > 0:
        ok += 1

print(f"\n────────────────────────────────────────────────────────")
print(f"  Convertidos correctamente: {ok}/{len(pdfs)}")
print(f"\n  Listo. Subí los cambios a GitHub.\n")
