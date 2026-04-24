# Price Scraper — Alkosto

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://price-scraper-for-alkosto.streamlit.app/)

Scraper de precios automatizado que extrae productos de Alkosto Colombia, los visualiza en un dashboard interactivo y envía alertas por email cuando hay descuentos.

## Demo

**<a href="https://price-scraper-for-alkosto.streamlit.app/" target="_blank">https://price-scraper-for-alkosto.streamlit.app/</a>**

## Arquitectura

```
price-scraper/
├── src/
│   ├── scraper.py      # Scraping vía Algolia API
│   ├── dashboard.py    # Dashboard Streamlit
│   ├── notifier.py     # Alertas por Gmail
│   ├── scheduler.py    # Verificación periódica
│   └── exporter.py     # Exportación a CSV
├── data/               # CSVs generados (ignorados por git)
├── tests/
├── .env                # Variables de entorno (no subir a git)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Tecnologías

| Herramienta | Uso |
|---|---|
| `requests` | HTTP requests a la API de Algolia |
| `streamlit` | Dashboard interactivo |
| `pandas` | Procesamiento de datos |
| `python-dotenv` | Variables de entorno |
| `apscheduler` | Scheduler de alertas |
| `pytest` | Tests unitarios |
| `Docker` | Empaquetado y despliegue |

## Instalación local

```bash
git clone https://github.com/SantyCano2022/price-scraper
cd price-scraper

python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

## Configuración

Edita `.env` para ajustar parámetros (todos opcionales, tienen valores por defecto):

```env
SEARCH_QUERY=laptop           # Qué buscar (default: laptop)
MAX_PAGES=5                   # Páginas a scrapear (default: 5)
REQUEST_DELAY=0.5             # Segundos entre requests (default: 0.5)
CHECK_INTERVAL_HOURS=6        # Frecuencia de alertas en horas (default: 6)
MIN_DISCOUNT_PCT=30           # Descuento mínimo para alertar (default: 30%)

# Gmail — notificaciones de descuentos
GMAIL_USER=tu@gmail.com
GMAIL_APP_PASSWORD=xxxx
NOTIFY_EMAIL=destino@gmail.com
```

## Cómo correrlo

### Dashboard local

```bash
streamlit run src/dashboard.py
```

### Scheduler de alertas

```bash
python src/scheduler.py
```

### Con Docker

```bash
docker-compose up --build
```

## Tests

```bash
pytest tests/ -v --cov=src
```

## Commits semánticos

Este proyecto usa [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `refactor:` mejora sin cambiar comportamiento
- `docs:` cambios en documentación
- `test:` agregar o modificar tests
