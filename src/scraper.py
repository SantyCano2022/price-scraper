import logging
import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

ALGOLIA_APP_ID = "QX5IPS1B1Q"
ALGOLIA_API_KEY = "7a8800d62203ee3a9ff1cdf74f99b268"
ALGOLIA_INDEX = "alkostoIndexAlgoliaPRD"
ALKOSTO_BASE_URL = "https://www.alkosto.com"

SEARCH_QUERY = os.getenv("SEARCH_QUERY") or "laptop"
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY") or "0.5")
MAX_PAGES = int(os.getenv("MAX_PAGES") or "5")
RESULTS_PER_PAGE = 48

ALGOLIA_URL = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{ALGOLIA_INDEX}/query"
HEADERS = {
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "Content-Type": "application/json",
}


def fetch_page(query: str, page: int) -> dict | None:
    payload = {
        "query": query,
        "hitsPerPage": RESULTS_PER_PAGE,
        "page": page,
    }
    try:
        r = requests.post(ALGOLIA_URL, headers=HEADERS, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP error: %s", e)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error")
    except requests.exceptions.Timeout:
        logger.error("Timeout")
    return None


def parse_products(data: dict) -> list[dict]:
    products = []
    for item in data.get("hits", []):
        try:
            name = item.get("name_text_es", "Sin nombre")
            price = item.get("discountprice_double") or item.get("lowestprice_double", 0)
            original_price = float(item.get("baseprice_cop_string", 0) or 0)
            discount = item.get("percentagediscount_string", "")
            brand = (item.get("brand_string_mv") or [""])[0]
            in_stock = item.get("instockflag_boolean", False)
            rating = item.get("reviewavgrating_double", 0.0)
            url_path = item.get("url_es_string", "")

            products.append({
                "nombre": name,
                "precio_cop": price,
                "precio_original_cop": original_price if original_price > price else None,
                "descuento": discount,
                "marca": brand,
                "rating": round(rating, 1),
                "disponibilidad": "En stock" if in_stock else "Sin stock",
                "url": f"{ALKOSTO_BASE_URL}{url_path}" if url_path else "",
            })
        except (KeyError, TypeError, ValueError) as e:
            logger.warning("Skipping malformed item: %s", e)
    return products


def scrape(query: str = SEARCH_QUERY, max_pages: int = MAX_PAGES) -> list[dict]:
    all_products: list[dict] = []

    for page in range(max_pages):
        logger.info("Fetching page %d for '%s'", page + 1, query)

        data = fetch_page(query, page)
        if data is None:
            logger.warning("Could not fetch page %d, stopping", page + 1)
            break

        total_pages = data.get("nbPages", 0)
        total_hits = data.get("nbHits", 0)
        products = parse_products(data)

        if not products:
            logger.info("No products on page %d, stopping", page + 1)
            break

        all_products.extend(products)
        logger.info(
            "Page %d/%d: %d products (acumulado: %d / %d disponibles)",
            page + 1, total_pages, len(products), len(all_products), total_hits,
        )

        if page + 1 >= total_pages:
            logger.info("Se alcanzó el final de los resultados")
            break

        if page < max_pages - 1:
            time.sleep(REQUEST_DELAY)

    return all_products


if __name__ == "__main__":
    results = scrape()
    logger.info("Scraping completo. Total productos: %d", len(results))
    for p in results[:5]:
        print(p)
