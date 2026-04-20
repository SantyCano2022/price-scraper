import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from scraper import scrape
from notifier import send_discount_digest

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SEARCH_QUERY = os.getenv("SEARCH_QUERY", "laptop")
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "6"))
MIN_DISCOUNT_PCT = int(os.getenv("MIN_DISCOUNT_PCT", "30"))


def parse_discount(discount_str: str) -> int:
    try:
        return abs(int(discount_str.replace("%", "").replace("-", "").strip()))
    except (ValueError, AttributeError):
        return 0


def get_top_discounts(products: list[dict], min_pct: int) -> list[dict]:
    with_discount = []
    for p in products:
        pct = parse_discount(p.get("descuento", ""))
        if pct >= min_pct:
            with_discount.append({**p, "descuento_pct": pct})
    return sorted(with_discount, key=lambda x: x["descuento_pct"], reverse=True)


def check_prices() -> None:
    logger.info("=== Verificación iniciada [%s] ===", datetime.now().strftime("%Y-%m-%d %H:%M"))

    products = scrape(query=SEARCH_QUERY)
    if not products:
        logger.warning("No se encontraron productos")
        return

    top = get_top_discounts(products, MIN_DISCOUNT_PCT)
    logger.info("%d producto(s) con descuento >= %d%%", len(top), MIN_DISCOUNT_PCT)

    if top:
        send_discount_digest(top, SEARCH_QUERY, MIN_DISCOUNT_PCT)
    else:
        logger.info("Ningún producto supera el %d%% de descuento hoy", MIN_DISCOUNT_PCT)

    logger.info("Próxima verificación en %d hora(s)", CHECK_INTERVAL_HOURS)


if __name__ == "__main__":
    logger.info("Scheduler iniciado — cada %dh | búsqueda: '%s' | descuento mínimo: %d%%",
                CHECK_INTERVAL_HOURS, SEARCH_QUERY, MIN_DISCOUNT_PCT)

    check_prices()

    scheduler = BlockingScheduler()
    scheduler.add_job(check_prices, "interval", hours=CHECK_INTERVAL_HOURS)

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler detenido")
