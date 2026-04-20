import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def export_to_csv(products: list[dict], output_dir: Path = DATA_DIR) -> Path:
    if not products:
        raise ValueError("No products to export")

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"precios_{timestamp}.csv"

    df = pd.DataFrame(products)
    df.insert(0, "fecha_scraping", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    df.to_csv(filename, index=False, encoding="utf-8-sig")

    logger.info("Exported %d products to %s", len(df), filename)
    return filename


if __name__ == "__main__":
    from scraper import scrape

    logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
    products = scrape()
    if products:
        path = export_to_csv(products)
        print(f"Saved to: {path}")
    else:
        print("No products scraped.")
