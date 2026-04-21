import sys
import io
import time
import html as _html
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent))
from scraper import scrape

st.set_page_config(
    page_title="Alkosto Price Tracker",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp { background: #050505 !important; }

section[data-testid="stSidebar"] {
    background: #08080f !important;
    border-right: 1px solid rgba(244,121,32,0.25) !important;
}

/* Botones */
div[data-testid="stButton"] > button,
.stDownloadButton > button {
    background: linear-gradient(135deg, #F47920, #C85A00) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 20px rgba(244,121,32,0.35) !important;
    transition: all 0.25s ease !important;
}
div[data-testid="stButton"] > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(244,121,32,0.55) !important;
}

/* Inputs */
div[data-testid="stTextInput"] input {
    background: #0e0e18 !important;
    border: 1px solid rgba(244,121,32,0.25) !important;
    border-radius: 8px !important;
    color: #f0f0f0 !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #F47920 !important;
    box-shadow: 0 0 0 3px rgba(244,121,32,0.15) !important;
}

/* Labels y texto del sidebar */
label, .stMarkdown p, .stMarkdown li { color: #c0c0cc !important; }

/* Slider */
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: #F47920 !important;
    border-color: #F47920 !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBarMin"],
div[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stTickBarMax"] {
    color: #F47920 !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="TrackHighlight"] {
    background: #F47920 !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="Track"] {
    background: rgba(244,121,32,0.2) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="InnerTrack"] {
    background: #F47920 !important;
}

/* Multiselect tags */
[data-baseweb="tag"] {
    background: rgba(244,121,32,0.18) !important;
    border: 1px solid rgba(244,121,32,0.45) !important;
    color: #FF9A45 !important;
    border-radius: 6px !important;
}
[data-baseweb="tag"] span { color: #FF9A45 !important; }
[data-baseweb="tag"] [data-testid="stMultiSelectDeleteButton"] svg,
[data-baseweb="tag"] button svg { fill: #FF9A45 !important; }

/* Checkbox — sin fondo en el label, chulito naranja visible */
[data-testid="stCheckbox"] { background: transparent !important; }
[data-testid="stCheckbox"] label { background: transparent !important; }
[data-testid="stCheckbox"] label:hover { background: transparent !important; }
[data-testid="stCheckbox"] p { background: transparent !important; }

/* cuadrito naranja con chulito cuando está marcado */
[data-baseweb="checkbox"] [data-checked="true"] {
    background-color: #F47920 !important;
    border-color: #F47920 !important;
}
[data-baseweb="checkbox"] [data-checked="false"] {
    background-color: transparent !important;
    border-color: rgba(244,121,32,0.5) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(244,121,32,0.2) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Divider */
hr { border-color: rgba(244,121,32,0.15) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #050505; }
::-webkit-scrollbar-thumb { background: #F47920; border-radius: 10px; }

/* Animaciones */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}
@keyframes glow {
    0%, 100% { box-shadow: 0 0 16px rgba(244,121,32,0.2); }
    50%       { box-shadow: 0 0 36px rgba(244,121,32,0.45); }
}
@keyframes barFill {
    from { width: 0 !important; }
}
@keyframes shimmer {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #0f0a00 0%, #1a0e00 40%, #100800 100%);
    border: 1px solid rgba(244,121,32,0.3);
    border-radius: 18px;
    padding: 36px 44px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    animation: fadeUp 0.5s ease, glow 4s ease-in-out infinite;
}
.hero-shine {
    position: absolute;
    top: 0; left: -60%; width: 40%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
    animation: shimmer 5s ease-in-out infinite;
    pointer-events: none;
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #fff 0%, #FFD4A8 50%, #F47920 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 6px;
}
.hero-sub { font-size: 0.9rem; color: rgba(255,255,255,0.45); font-weight: 400; }
.live-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(244,121,32,0.12);
    border: 1px solid rgba(244,121,32,0.4);
    color: #FF9A45; padding: 7px 16px; border-radius: 50px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;
}
.live-dot {
    width: 8px; height: 8px; background: #F47920; border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 8px #F47920;
}
.hero-stats { display: flex; gap: 32px; margin-top: 20px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,0.06); flex-wrap: wrap; }
.hero-stat { display: flex; flex-direction: column; gap: 2px; }
.hero-stat-val { font-size: 1.35rem; font-weight: 800; color: #f9fafb; }
.hero-stat-lbl { font-size: 0.68rem; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.8px; }

/* KPI cards */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin: 20px 0 28px; }
.kpi-card {
    background: #0c0c14;
    border: 1px solid rgba(244,121,32,0.18);
    border-radius: 14px; padding: 22px 18px;
    position: relative; overflow: hidden;
    animation: fadeUp 0.5s ease forwards;
    transition: border-color 0.3s, transform 0.3s;
}
.kpi-card:hover { border-color: rgba(244,121,32,0.5); transform: translateY(-3px); }
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #F47920, transparent);
}
.kpi-icon { font-size: 1.5rem; margin-bottom: 8px; }
.kpi-label { font-size: 0.68rem; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; margin-bottom: 4px; }
.kpi-value { font-size: 1.7rem; font-weight: 800; color: #f9fafb; letter-spacing: -0.5px; }
.kpi-sub { font-size: 0.72rem; color: rgba(255,255,255,0.25); margin-top: 4px; }

/* Section header */
.sec { display: flex; align-items: center; gap: 10px; margin: 28px 0 14px; }
.sec-title { font-size: 0.95rem; font-weight: 700; color: #f0f0f0; white-space: nowrap; }
.sec-line { flex: 1; height: 1px; background: linear-gradient(90deg, rgba(244,121,32,0.3), transparent); }
.sec-count { font-size: 0.72rem; color: rgba(255,255,255,0.25); white-space: nowrap; }

/* Discount bars */
.disc-list { display: flex; flex-direction: column; gap: 11px; }
.disc-row { display: flex; align-items: center; gap: 12px; animation: fadeUp 0.4s ease forwards; }
.disc-name { font-size: 0.8rem; color: rgba(255,255,255,0.7); flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.disc-track { width: 200px; height: 7px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; flex-shrink: 0; }
.disc-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #9E4500, #F47920, #FF9A45); box-shadow: 0 0 8px rgba(244,121,32,0.5); animation: barFill 1s cubic-bezier(0.4,0,0.2,1) forwards; }
.disc-pct { font-size: 0.78rem; font-weight: 700; color: #FF9A45; min-width: 34px; text-align: right; }

/* Product cards */
.prod-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; }
.prod-card {
    background: #0c0c14; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 13px; padding: 16px 18px;
    position: relative; overflow: hidden;
    animation: fadeUp 0.5s ease forwards;
    transition: border-color 0.3s, transform 0.3s, box-shadow 0.3s;
}
.prod-card:hover { border-color: rgba(244,121,32,0.45); transform: translateY(-3px); box-shadow: 0 10px 28px rgba(244,121,32,0.12); }
.prod-rank {
    position: absolute; top: 12px; right: 12px;
    width: 26px; height: 26px;
    background: linear-gradient(135deg, #F47920, #C85A00);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 0.68rem; font-weight: 800; color: white;
    box-shadow: 0 3px 10px rgba(244,121,32,0.5);
}
.prod-brand { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; color: #F47920; font-weight: 700; margin-bottom: 5px; }
.prod-name { font-size: 0.82rem; color: rgba(255,255,255,0.8); line-height: 1.4; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 2.3em; }
.prod-bottom { display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
.prod-price { font-size: 1.2rem; font-weight: 800; color: #f9fafb; letter-spacing: -0.4px; }
.prod-old { font-size: 0.7rem; text-decoration: line-through; color: rgba(255,255,255,0.28); margin-bottom: 2px; }
.badge {
    background: linear-gradient(135deg, #F47920, #C85A00);
    color: white; font-size: 0.72rem; font-weight: 800;
    padding: 3px 9px; border-radius: 20px;
    box-shadow: 0 3px 10px rgba(244,121,32,0.4);
}
.prod-rating { margin-top: 9px; font-size: 0.72rem; color: rgba(255,255,255,0.3); }

/* Footer */
.footer { text-align: center; padding: 28px 0 12px; border-top: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.2); font-size: 0.72rem; margin-top: 36px; }
.footer b { color: #F47920; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔎 Búsqueda")
    query = st.text_input("Producto", value="laptop", placeholder="celular, televisor, nevera...")
    max_pages = st.slider("Páginas", 1, 10, 3, help="~48 resultados por página")
    run_btn = st.button("⚡ Buscar ahora", use_container_width=True)
    st.markdown("---")
    st.markdown("### 🎛️ Filtros")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⚡ Consultando Alkosto...")
def load_data(q: str, pages: int) -> pd.DataFrame:
    return pd.DataFrame(scrape(query=q, max_pages=pages))

if run_btn:
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_count += 1

df = load_data(query, max_pages)

if df.empty:
    st.error("❌ No se encontraron productos. Intenta con otro término.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    search_name = st.text_input("Filtrar nombre", placeholder="Samsung, 15 pulgadas...")
    min_p, max_p = float(df.precio_cop.min()), float(df.precio_cop.max())
    price_range = st.slider("Precio (COP)", min_p, max_p, (min_p, max_p), format="$%.0f")
    marcas = sorted(df.marca.dropna().unique())
    marcas_sel = st.multiselect("Marca", options=marcas, default=marcas)
    solo_stock = st.checkbox("Solo en stock", value=True)
    st.markdown("---")
    ts = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="font-size:0.75rem;color:rgba(255,255,255,0.3);line-height:2">
        🕒 Última vez: <b style="color:#F47920">{ts}</b><br>
        🔄 Búsquedas: <b style="color:#F47920">{st.session_state.refresh_count}</b><br>
        📡 Fuente: <b style="color:rgba(255,255,255,0.4)">Algolia API</b>
    </div>
    """, unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
filtered = df[
    (df.precio_cop >= price_range[0]) &
    (df.precio_cop <= price_range[1]) &
    (df.marca.isin(marcas_sel))
].copy()
if solo_stock:
    filtered = filtered[filtered.disponibilidad == "En stock"]
if search_name:
    filtered = filtered[filtered.nombre.str.contains(search_name, case=False, na=False)]

if filtered.empty:
    st.warning("⚠️ Ningún producto coincide con los filtros.")
    st.stop()

def parse_disc(d):
    try:
        return abs(int(str(d).replace("%","").replace("-","").strip()))
    except:
        return 0

filtered["desc_pct"] = filtered["descuento"].apply(parse_disc)
total    = len(filtered)
avg_p    = filtered.precio_cop.mean()
min_p    = filtered.precio_cop.min()
in_stock = (filtered.disponibilidad == "En stock").sum()
max_disc = filtered.desc_pct.max() if (filtered.desc_pct > 0).any() else 0

# ── Hero ──────────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
st.markdown(f"""
<div class="hero">
    <div class="hero-shine"></div>
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">
        <div>
            <div class="hero-title">Alkosto Price Tracker</div>
            <div class="hero-sub">Monitoreo de precios en tiempo real · Alkosto Colombia 🇨🇴</div>
            <div class="hero-stats">
                <div class="hero-stat"><span class="hero-stat-val">{total}</span><span class="hero-stat-lbl">Productos</span></div>
                <div class="hero-stat"><span class="hero-stat-val">{in_stock}</span><span class="hero-stat-lbl">En stock</span></div>
                <div class="hero-stat"><span class="hero-stat-val">${avg_p:,.0f}</span><span class="hero-stat-lbl">Precio prom.</span></div>
                <div class="hero-stat"><span class="hero-stat-val">{max_disc}%</span><span class="hero-stat-lbl">Max descuento</span></div>
            </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:10px">
            <div class="live-badge"><div class="live-dot"></div>LIVE</div>
            <div style="font-size:0.72rem;color:rgba(255,255,255,0.25)">{now_str}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card" style="animation-delay:0.05s">
        <div class="kpi-icon">📦</div>
        <div class="kpi-label">Total productos</div>
        <div class="kpi-value">{total:,}</div>
        <div class="kpi-sub">"{query}"</div>
    </div>
    <div class="kpi-card" style="animation-delay:0.1s">
        <div class="kpi-icon">💰</div>
        <div class="kpi-label">Precio promedio</div>
        <div class="kpi-value">${avg_p:,.0f}</div>
        <div class="kpi-sub">COP</div>
    </div>
    <div class="kpi-card" style="animation-delay:0.15s">
        <div class="kpi-icon">⚡</div>
        <div class="kpi-label">Precio mínimo</div>
        <div class="kpi-value">${min_p:,.0f}</div>
        <div class="kpi-sub">Mejor oferta</div>
    </div>
    <div class="kpi-card" style="animation-delay:0.2s">
        <div class="kpi-icon">🔥</div>
        <div class="kpi-label">Mayor descuento</div>
        <div class="kpi-value">{max_disc}%</div>
        <div class="kpi-sub">vs precio original</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("""<div class="sec"><span class="sec-title">📉 Análisis de precios</span><div class="sec-line"></div></div>""", unsafe_allow_html=True)

BG, GRID, FONT = "rgba(0,0,0,0)", "rgba(255,255,255,0.04)", "rgba(255,255,255,0.4)"
FONT_T = "rgba(255,255,255,0.85)"

col1, col2 = st.columns(2)
with col1:
    fig1 = go.Figure(go.Histogram(
        x=filtered.precio_cop, nbinsx=25,
        marker=dict(color="#F47920", line=dict(color="#C85A00", width=1), opacity=0.85),
        hovertemplate="<b>$%{x:,.0f}</b><br>%{y} productos<extra></extra>",
    ))
    fig1.update_layout(
        title=dict(text="Distribución de precios", font=dict(color=FONT_T, size=13, family="Inter"), x=0.01),
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=FONT, family="Inter"),
        margin=dict(t=40,b=20,l=10,r=10),
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickprefix="$", tickformat=",.0f", tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="#1a0e00", bordercolor="#F47920", font=dict(color="white")),
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    top_brands = filtered.marca.value_counts().head(10).reset_index()
    top_brands.columns = ["marca", "cantidad"]
    fig2 = go.Figure(go.Bar(
        x=top_brands["marca"], y=top_brands["cantidad"],
        marker=dict(
            color=top_brands["cantidad"],
            colorscale=[[0,"#2a1800"],[0.5,"#C85A00"],[1,"#F47920"]],
            line=dict(color="#C85A00", width=1),
        ),
        hovertemplate="<b>%{x}</b><br>%{y} productos<extra></extra>",
    ))
    fig2.update_layout(
        title=dict(text="Top 10 marcas", font=dict(color=FONT_T, size=13, family="Inter"), x=0.01),
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=FONT, family="Inter"),
        margin=dict(t=40,b=20,l=10,r=10), coloraxis_showscale=False,
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="#1a0e00", bordercolor="#F47920", font=dict(color="white")),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Discount Bars ─────────────────────────────────────────────────────────────
top_disc = filtered[filtered.desc_pct > 0].nlargest(10, "desc_pct")
if not top_disc.empty:
    max_d = top_disc.desc_pct.max()
    st.markdown(f"""<div class="sec"><span class="sec-title">🔥 Top descuentos activos</span><div class="sec-line"></div><span class="sec-count">{len(top_disc)} productos</span></div>""", unsafe_allow_html=True)
    for _, r in top_disc.iterrows():
        name = _html.escape(str(r["nombre"])[:65] + ("…" if len(str(r["nombre"])) > 65 else ""))
        w = int((r.desc_pct / max_d) * 100)
        st.markdown(f"""
        <div class="disc-row">
            <span class="disc-name">{name}</span>
            <div class="disc-track"><div class="disc-fill" style="width:{w}%"></div></div>
            <span class="disc-pct">-{r.desc_pct}%</span>
        </div>""", unsafe_allow_html=True)

# ── Product Cards ─────────────────────────────────────────────────────────────
st.markdown("""<div class="sec" style="margin-top:28px"><span class="sec-title">⭐ Mejores ofertas</span><div class="sec-line"></div></div>""", unsafe_allow_html=True)

highlights = filtered[filtered.desc_pct > 0].nlargest(6, "desc_pct") if (filtered.desc_pct > 0).any() else filtered.nsmallest(6, "precio_cop")
rows_list = list(highlights.iterrows())
for row_start in range(0, len(rows_list), 3):
    chunk = rows_list[row_start:row_start+3]
    cols = st.columns(3)
    for col_idx, (_, r) in enumerate(chunk):
        i = row_start + col_idx
        old_h    = f'<div class="prod-old">${r.get("precio_original_cop",0):,.0f}</div>' if r.get("precio_original_cop", 0) > r.precio_cop else ""
        badge_h  = f'<span class="badge">{_html.escape(str(r.get("descuento","")).strip())}</span>' if str(r.get("descuento","")).strip() else ""
        rat      = r.get("rating", 0)
        rat_h    = f'<div class="prod-rating">{"★"*round(rat)}{"☆"*(5-round(rat))} {rat:.1f}</div>' if rat and rat > 0 else ""
        name_s   = _html.escape(str(r.get("nombre","")))
        brand_s  = _html.escape(str(r.get("marca","")).strip() or "—")
        with cols[col_idx]:
            st.markdown(f"""
            <div class="prod-card">
                <div class="prod-rank">#{i+1}</div>
                <div class="prod-brand">{brand_s}</div>
                <div class="prod-name">{name_s}</div>
                <div class="prod-bottom">
                    <div>{old_h}<div class="prod-price">${r.precio_cop:,.0f}</div></div>
                    {badge_h}
                </div>
                {rat_h}
            </div>""", unsafe_allow_html=True)
# ── Table ─────────────────────────────────────────────────────────────────────
st.markdown(f"""<div class="sec" style="margin-top:28px"><span class="sec-title">🗂️ Catálogo completo</span><div class="sec-line"></div><span class="sec-count">{total} resultados</span></div>""", unsafe_allow_html=True)

disp = filtered[["nombre","marca","precio_cop","precio_original_cop","descuento","rating","disponibilidad"]].copy()
disp["precio_cop"] = disp["precio_cop"].apply(lambda x: f"${x:,.0f}")
disp["precio_original_cop"] = disp["precio_original_cop"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x else "—")
disp["rating"] = disp["rating"].apply(lambda x: f"⭐ {x:.1f}" if x and x > 0 else "—")
disp["disponibilidad"] = disp["disponibilidad"].apply(lambda x: "✅ En stock" if x == "En stock" else "❌ Sin stock")
disp.columns = ["Producto","Marca","Precio","Precio antes","Descuento","Rating","Stock"]
st.dataframe(disp, use_container_width=True, hide_index=True,
    column_config={"Producto": st.column_config.TextColumn(width="large")})

# ── Downloads ─────────────────────────────────────────────────────────────────
st.markdown("""<div class="sec" style="margin-top:20px"><span class="sec-title">⬇️ Exportar</span><div class="sec-line"></div></div>""", unsafe_allow_html=True)
d1, d2 = st.columns(2)
with d1:
    st.download_button("⬇️ CSV", data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"alkosto_{query}.csv", mime="text/csv", use_container_width=True)
with d2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        filtered.to_excel(w, index=False, sheet_name="Productos")
        for col in w.sheets["Productos"].columns:
            w.sheets["Productos"].column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 4
    st.download_button("⬇️ Excel", data=buf.getvalue(),
        file_name=f"alkosto_{query}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)

st.markdown("""<div class="footer">Alkosto Price Tracker &nbsp;·&nbsp; <b>Algolia API</b> &nbsp;·&nbsp; 🇨🇴 Colombia</div>""", unsafe_allow_html=True)
