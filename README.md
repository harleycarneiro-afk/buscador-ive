# Buscador de Textos — Instituto del Verbo Encarnado

## Cómo publicar en Netlify (3 pasos)

### Paso 1 — Preparar la carpeta
Coloca tus 23 archivos PDF dentro de la carpeta `pdfs/` con exactamente estos nombres:

- Dirección Espiritual TEXT.pdf
- Ecumenismo TEXT.pdf
- Ejercicios Espirituales Completo.pdf
- Evangelización de la cultura TEXT.pdf
- Formación intelectual TEXT.pdf
- Gobierno TEXT.pdf
- Hermanos religiosos.pdf
- Misión Ad Gentes TEXT.pdf
- Misiones populares TEXT.pdf
- Noviciados TEXT.pdf
- Obras de misericordia TEXT.pdf
- Oratorio TEXT.pdf
- Parroquias TEXT.pdf
- Predicación de la Palabra de Dios TEXT.pdf
- Rama oriental TEXT.pdf
- Seminarios Mayores TEXT.pdf
- Seminarios menores TEXT.pdf
- Tercera orden TEXT.pdf
- Vida consagrada TEXT.pdf
- Vida contemplativa TEXT.pdf
- Vida fraterna TEXT.pdf
- Vida liturgica TEXT.pdf
- Vocaciones TEXT.pdf

### Paso 2 — Subir a Netlify
1. Ve a https://netlify.com y crea una cuenta gratuita
2. En el panel, busca "Sites" y luego "Add new site"
3. Elige "Deploy manually"
4. Arrastra toda la carpeta `buscador-ive` al área indicada
5. Espera unos segundos — Netlify te dará una URL

### Paso 3 — Compartir
Comparte la URL con quien quieras. Nadie necesita instalar nada.

---

## Estructura de la carpeta

```
buscador-ive/
├── index.html        ← la aplicación
├── pdfs/             ← aquí van tus 23 PDFs
│   ├── Dirección Espiritual TEXT.pdf
│   ├── Ecumenismo TEXT.pdf
│   └── ... (todos los demás)
└── README.md         ← este archivo
```

## Tipos de búsqueda

| Ejemplo | Resultado |
|---------|-----------|
| `eucarist*` | Eucaristía, Eucarístico, Eucarística... |
| `"Jesús Eucarístico"` | Frase exacta |
| `gracia misión` | Ambas palabras dentro de la distancia configurada |
| `vida amor esperanza` | Las tres palabras cercanas |

- No distingue acentos ni mayúsculas
- Se puede ajustar la distancia máxima entre palabras (por defecto: 10)
- Se pueden seleccionar solo algunos documentos para buscar
