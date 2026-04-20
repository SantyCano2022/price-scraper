import sys
import io
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent))
from scraper import scrape
from exporter import export_to_csv

st.set_page_config(
    page_title="Price Scraper — Alkosto",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Price Scraper — Alkosto Colombia")
st.caption("Datos extraídos en tiempo real de Alkosto.com")

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuración")
    query = st.text_input("Producto a buscar", value="laptop", placeholder="ej: celular, televisor, nevera...")
    max_pages = st.slider("Páginas a buscar", 1, 10, 3, help="Cada página trae ~48 resultados")
    run_btn = st.button("🔄 Buscar", use_container_width=True)

# ── Load / scrape data ────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Consultando Alkosto...")
def load_data(q: str, pages: int) -> pd.DataFrame:
    products = scrape(query=q, max_pages=pages)
    return pd.DataFrame(products)

if run_btn:
    st.cache_data.clear()

df = load_data(query, max_pages)

if df.empty:
    st.error("No se encontraron productos. Intenta con otro término de búsqueda.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filtros")

    search_name = st.text_input("Filtrar por nombre", placeholder="ej: Samsung, 15 pulgadas...")

    min_price, max_price = float(df.precio_cop.min()), float(df.precio_cop.max())
    price_range = st.slider(
        "Rango de precio (COP)",
        min_price, max_price, (min_price, max_price),
        format="$%.0f",
    )

    marcas = sorted(df.marca.dropna().unique())
    marcas_sel = st.multiselect("Marca", options=marcas, default=marcas)

    solo_stock = st.checkbox("Solo productos en stock", value=True)

filtered = df[
    (df.precio_cop >= price_range[0]) &
    (df.precio_cop <= price_range[1]) &
    (df.marca.isin(marcas_sel))
]
if solo_stock:
    filtered = filtered[filtered.disponibilidad == "En stock"]
if search_name:
    filtered = filtered[filtered.nombre.str.contains(search_name, case=False, na=False)]

if filtered.empty:
    st.warning("No hay productos con los filtros seleccionados.")
    st.stop()

# ── KPI cards ─────────────────────────────────────────────────────────────────
st.subheader("Resumen")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total productos", len(filtered))
c2.metric("Precio promedio", f"${filtered.precio_cop.mean():,.0f}")
c3.metric("Más barato", f"${filtered.precio_cop.min():,.0f}")
c4.metric("Más caro", f"${filtered.precio_cop.max():,.0f}")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribución de precios")
    fig1 = px.histogram(
        filtered, x="precio_cop", nbins=20,
        color_discrete_sequence=["#E30613"],
        labels={"precio_cop": "Precio (COP)", "count": "Cantidad"},
    )
    fig1.update_layout(showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Productos por marca (Top 10)")
    top_brands = filtered.marca.value_counts().head(10).reset_index()
    top_brands.columns = ["marca", "cantidad"]
    fig2 = px.bar(
        top_brands, x="marca", y="cantidad",
        color_discrete_sequence=["#E30613"],
        labels={"marca": "Marca", "cantidad": "Cantidad"},
    )
    fig2.update_layout(showlegend=False, margin=dict(t=10))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
st.subheader(f"Listado de productos ({len(filtered)})")

display_df = filtered[["nombre", "marca", "precio_cop", "precio_original_cop", "descuento", "disponibilidad"]].copy()
display_df["precio_cop"] = display_df["precio_cop"].apply(lambda x: f"${x:,.0f}")
display_df["precio_original_cop"] = display_df["precio_original_cop"].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) and x else ""
)
display_df = display_df.rename(columns={
    "nombre": "Nombre",
    "marca": "Marca",
    "precio_cop": "Precio",
    "precio_original_cop": "Precio antes",
    "descuento": "Descuento",
    "disponibilidad": "Disponibilidad",
})

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── Download buttons ──────────────────────────────────────────────────────────
st.subheader("Descargar datos")
d1, d2 = st.columns(2)

with d1:
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Descargar CSV",
        data=csv_bytes,
        file_name=f"alkosto_{query}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with d2:
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        filtered.to_excel(writer, index=False, sheet_name="Productos")
        ws = writer.sheets["Productos"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(
                len(str(cell.value or "")) for cell in col
            ) + 4
    st.download_button(
        "⬇️ Descargar Excel",
        data=excel_buf.getvalue(),
        file_name=f"alkosto_{query}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
