import pytest
import pandas as pd
from pathlib import Path
from src.exporter import export_to_csv

SAMPLE_PRODUCTS = [
    {"nombre": "Laptop LENOVO IdeaPad", "precio_cop": 2599070, "precio_original_cop": 3999000, "descuento": "-35%", "marca": "LENOVO", "rating": 4.5, "disponibilidad": "En stock", "url": "https://www.alkosto.com/p/123"},
    {"nombre": "Laptop HP 15", "precio_cop": 2100000, "precio_original_cop": None, "descuento": "", "marca": "HP", "rating": 0.0, "disponibilidad": "En stock", "url": "https://www.alkosto.com/p/456"},
    {"nombre": "Laptop DELL Inspiron", "precio_cop": 3500000, "precio_original_cop": 4200000, "descuento": "-17%", "marca": "DELL", "rating": 4.2, "disponibilidad": "Sin stock", "url": "https://www.alkosto.com/p/789"},
]


@pytest.fixture
def tmp_export_dir(tmp_path):
    return tmp_path / "data"


def test_csv_is_created(tmp_export_dir):
    path = export_to_csv(SAMPLE_PRODUCTS, output_dir=tmp_export_dir)
    assert path.exists(), "CSV file was not created"


def test_csv_has_correct_columns(tmp_export_dir):
    path = export_to_csv(SAMPLE_PRODUCTS, output_dir=tmp_export_dir)
    df = pd.read_csv(path)
    expected_columns = {"fecha_scraping", "nombre", "precio_cop", "marca", "disponibilidad", "url"}
    assert expected_columns.issubset(set(df.columns)), f"Missing columns: {expected_columns - set(df.columns)}"


def test_csv_is_not_empty(tmp_export_dir):
    path = export_to_csv(SAMPLE_PRODUCTS, output_dir=tmp_export_dir)
    df = pd.read_csv(path)
    assert len(df) > 0, "CSV file is empty"


def test_csv_row_count_matches_input(tmp_export_dir):
    path = export_to_csv(SAMPLE_PRODUCTS, output_dir=tmp_export_dir)
    df = pd.read_csv(path)
    assert len(df) == len(SAMPLE_PRODUCTS)


def test_export_raises_on_empty_list(tmp_export_dir):
    with pytest.raises(ValueError, match="No products to export"):
        export_to_csv([], output_dir=tmp_export_dir)


def test_files_are_not_overwritten(tmp_export_dir):
    import time
    path1 = export_to_csv(SAMPLE_PRODUCTS, output_dir=tmp_export_dir)
    time.sleep(1)
    path2 = export_to_csv(SAMPLE_PRODUCTS, output_dir=tmp_export_dir)
    assert path1 != path2, "Two exports produced the same filename — file was overwritten"
