# Price Scraper —  Alkosto

Scraper de precios automatizado que extrae productos de MercadoLibre Colombia y exporta los resultados a CSV. Proyecto de portafolio para ingeniería de software / automatizaciones.

## Arquitectura

```
price-scraper/
├── src/
│   ├── scraper.py      # Lógica de scraping (requests + BeautifulSoup)
│   └── exporter.py     # Exportación a CSV con pandas
├── data/               # CSVs generados (ignorados por git)
├── tests/
│   └── test_exporter.py
├── .env                # Variables de entorno (no subir a git)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Tecnologías

| Herramienta | Uso |
|---|---|
| `requests` | HTTP requests al sitio |
| `BeautifulSoup4` | Parsing del HTML |
| `pandas` | Generación de CSV |
| `python-dotenv` | Variables de entorno |
| `pytest` | Tests unitarios |
| `Docker` | Empaquetado y despliegue |

## Instalación local

```bash
# Clonar el repo
git clone <repo-url>
cd price-scraper

# Crear y activar virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Edita `.env` para ajustar parámetros:

```env
SEARCH_QUERY=xxxxxxxx       # Qué buscar
MAX_PAGES=xxxxxxx          # Páginas a scrapear
REQUEST_DELAY=xxxxxxx           # Segundos entre requests
```

## Cómo correrlo

### Local

```bash
python src/exporter.py
```

El CSV se guarda en `data/precios_YYYYMMDD_HHMMSS.csv`.

### Con Docker

```bash
docker-compose up --build
```

Los CSVs se montan en `./data/` de tu máquina local.

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
