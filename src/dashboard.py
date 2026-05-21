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
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=Space+Mono:wght@400;700&display=swap');
@import url('https://cdn-uicons.flaticon.com/uicons-thin-rounded/css/uicons-thin-rounded.css');

:root {
    --bg:           #060912;
    --surface:      #0C0F20;
    --surface2:     #111528;
    --border:       rgba(255,255,255,0.07);
    --accent:       #F47920;
    --accent-dim:   rgba(244,121,32,0.12);
    --accent-glow:  rgba(244,121,32,0.28);
    --gold:         #FFD166;
    --green:        #34D399;
    --red:          #FF6B6B;
    --text:         #DCE1F2;
    --muted:        rgba(220,225,242,0.36);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}
.fi { display:inline-block; line-height:1; vertical-align:middle; flex-shrink:0; }

/* App background — subtle dot grid for depth */
.stApp {
    background-color: var(--bg) !important;
    background-image: radial-gradient(circle, rgba(244,121,32,0.055) 1px, transparent 1px);
    background-size: 30px 30px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid rgba(244,121,32,0.18) !important;
}

/* Buttons */
div[data-testid="stButton"] > button,
.stDownloadButton > button {
    background: linear-gradient(135deg, #F47920, #C85A00) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 4px 20px rgba(244,121,32,0.3) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(244,121,32,0.5) !important;
}

/* Inputs */
div[data-testid="stTextInput"] input {
    background: var(--surface2) !important;
    border: 1px solid rgba(244,121,32,0.2) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
}

/* Labels */
label, .stMarkdown p, .stMarkdown li { color: var(--muted) !important; }

/* Slider */
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: var(--accent) !important; border-color: var(--accent) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="InnerTrack"] {
    background: var(--accent) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="Track"] {
    background: rgba(244,121,32,0.15) !important;
}

/* Multiselect tags */
[data-baseweb="tag"] {
    background: var(--accent-dim) !important;
    border: 1px solid rgba(244,121,32,0.4) !important;
    color: #FF9A45 !important;
    border-radius: 5px !important;
}
[data-baseweb="tag"] span { color: #FF9A45 !important; }
[data-baseweb="tag"] button svg { fill: #FF9A45 !important; }

/* Checkbox */
[data-testid="stCheckbox"] { background: transparent !important; }
[data-testid="stCheckbox"] label { background: transparent !important; }
[data-baseweb="checkbox"] [data-checked="true"] {
    background-color: var(--accent) !important; border-color: var(--accent) !important;
}
[data-baseweb="checkbox"] [data-checked="false"] {
    background-color: transparent !important;
    border-color: rgba(244,121,32,0.45) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(244,121,32,0.18) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Chart containers */
[data-testid="stPlotlyChart"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

hr { border-color: rgba(255,255,255,0.06) !important; }

::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius:10px; }

/* ── Keyframes ── */
@keyframes fadeUp {
    from { opacity:0; transform:translateY(20px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes pulse {
    0%,100% { opacity:1; }
    50%      { opacity:0.3; }
}
@keyframes shimmer {
    0%   { transform:translateX(-100%); }
    100% { transform:translateX(250%); }
}
@keyframes barFill {
    from { width:0 !important; }
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0A0614 0%, #130A00 55%, #080510 100%);
    border: 1px solid rgba(244,121,32,0.22);
    border-radius: 16px;
    padding: 40px 48px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    animation: fadeUp 0.5s ease;
}
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 78% 40%, rgba(244,121,32,0.08) 0%, transparent 60%);
    pointer-events: none;
}
.hero-watermark {
    position: absolute;
    right: -12px; top: 50%;
    transform: translateY(-50%);
    font-family: 'Bebas Neue', sans-serif;
    font-size: 9.5rem;
    letter-spacing: 8px;
    color: rgba(244,121,32,0.035);
    line-height: 1;
    user-select: none;
    pointer-events: none;
    white-space: nowrap;
}
.hero-shine {
    position: absolute; top: 0; left: -60%; width: 30%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.025), transparent);
    animation: shimmer 9s ease-in-out infinite;
    pointer-events: none;
}
.hero-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.hero-eyebrow::before {
    content: '';
    width: 20px; height: 1px;
    background: var(--accent);
    display: inline-block;
    flex-shrink: 0;
}
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem;
    letter-spacing: 3px;
    color: white;
    line-height: 0.92;
    margin: 0 0 10px;
}
.hero-title span {
    background: linear-gradient(90deg, #FFD166, #F47920);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 0.83rem;
    color: var(--muted);
    font-weight: 400;
    margin-bottom: 18px;
}
.live-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(244,121,32,0.08);
    border: 1px solid rgba(244,121,32,0.3);
    color: #FF9A45;
    padding: 6px 14px;
    border-radius: 50px;
    font-size: 0.68rem;
    font-family: 'Space Mono', monospace;
    letter-spacing: 1.5px;
}
.live-dot {
    width: 7px; height: 7px;
    background: #F47920;
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 8px #F47920;
}
.hero-stats {
    display: flex; gap: 28px;
    margin-top: 18px; padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.06);
    flex-wrap: wrap;
}
.hero-stat { display: flex; flex-direction: column; gap: 2px; }
.hero-stat-val {
    font-family: 'Space Mono', monospace;
    font-size: 1.1rem; font-weight: 700;
    color: white;
}
.hero-stat-lbl {
    font-size: 0.6rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 12px;
    margin: 0 0 28px;
}
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 22px 20px;
    position: relative; overflow: hidden;
    animation: fadeUp 0.5s ease forwards;
    transition: border-color 0.3s, transform 0.3s;
}
.kpi-card:hover {
    border-color: rgba(244,121,32,0.4);
    transform: translateY(-3px);
}
.kpi-card::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.kpi-card.c-orange::after { background: linear-gradient(90deg, transparent, #F47920, transparent); }
.kpi-card.c-gold::after   { background: linear-gradient(90deg, transparent, #FFD166, transparent); }
.kpi-card.c-green::after  { background: linear-gradient(90deg, transparent, #34D399, transparent); }
.kpi-card.c-red::after    { background: linear-gradient(90deg, transparent, #FF6B6B, transparent); }

.kpi-icon { font-size: 1.1rem; margin-bottom: 12px; }
.kpi-card.c-orange .kpi-icon { color: #F47920; }
.kpi-card.c-gold   .kpi-icon { color: #FFD166; }
.kpi-card.c-green  .kpi-icon { color: #34D399; }
.kpi-card.c-red    .kpi-icon { color: #FF6B6B; }

.kpi-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.58rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 400;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem;
    letter-spacing: 1px;
    color: white;
    line-height: 1;
}
.kpi-sub {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: var(--muted);
    margin-top: 6px;
}

/* ── Section headers ── */
.sec {
    display: flex; align-items: center; gap: 12px;
    margin: 28px 0 16px;
}
.sec-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text);
    white-space: nowrap;
    display: flex; align-items: center; gap: 7px;
}
.sec-title .fi { font-size: 0.78rem; color: var(--accent); }
.sec-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(244,121,32,0.22), transparent);
}
.sec-count {
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    white-space: nowrap;
}

/* ── Sidebar headings ── */
.sb-heading {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem; font-weight: 700;
    color: var(--muted);
    text-transform: uppercase; letter-spacing: 2px;
    display: flex; align-items: center; gap: 8px;
    margin: 6px 0 12px;
}
.sb-heading .fi { color: var(--accent); font-size: 0.75rem; }
.sb-info {
    font-family: 'Space Mono', monospace;
    font-size: 0.66rem;
    color: var(--muted);
    display: flex; flex-direction: column; gap: 7px;
}
.sb-info-row { display: flex; align-items: center; gap: 8px; }
.sb-info-row .fi { color: var(--accent); font-size: 0.66rem; flex-shrink: 0; }

/* ── Discount bars ── */
.disc-row {
    display: flex; align-items: center; gap: 14px;
    animation: fadeUp 0.4s ease forwards;
}
.disc-name {
    font-size: 0.76rem; color: rgba(220,225,242,0.6);
    flex: 1; min-width: 0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.disc-track {
    width: 170px; height: 4px;
    background: rgba(255,255,255,0.04);
    border-radius: 2px; overflow: hidden; flex-shrink: 0;
}
.disc-fill {
    height: 100%; border-radius: 2px;
    background: linear-gradient(90deg, #7B3200, #F47920, #FFD166);
    box-shadow: 0 0 5px rgba(244,121,32,0.35);
    animation: barFill 1.1s cubic-bezier(0.4,0,0.2,1) forwards;
}
.disc-pct {
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem; font-weight: 700;
    color: #FFD166; min-width: 40px; text-align: right;
}

/* ── Product cards ── */
.prod-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid transparent;
    border-radius: 10px;
    padding: 18px 20px;
    position: relative; overflow: hidden;
    animation: fadeUp 0.5s ease forwards;
    transition: border-left-color 0.25s, transform 0.25s, box-shadow 0.25s;
}
.prod-card:hover {
    border-left-color: var(--accent);
    transform: translateX(3px);
    box-shadow: 0 8px 30px rgba(244,121,32,0.08);
}
a.prod-link { text-decoration: none !important; display: block; color: inherit !important; }
a.prod-link:hover { text-decoration: none !important; }

.prod-rank {
    position: absolute; top: 14px; right: 14px;
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem; font-weight: 700;
    color: var(--muted);
}
.prod-brand {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.05rem;
    letter-spacing: 2px;
    color: var(--accent);
    margin-bottom: 4px;
}
.prod-name {
    font-size: 0.78rem;
    color: rgba(220,225,242,0.72);
    line-height: 1.45;
    margin-bottom: 14px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
    min-height: 2.3em;
}
.prod-bottom {
    display: flex; align-items: flex-end;
    justify-content: space-between; gap: 8px; flex-wrap: wrap;
}
.prod-price {
    font-family: 'Space Mono', monospace;
    font-size: 1rem; font-weight: 700;
    color: white;
}
.prod-old {
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    text-decoration: line-through;
    color: rgba(220,225,242,0.22);
    margin-bottom: 2px;
}
.badge {
    background: rgba(255,209,102,0.1);
    border: 1px solid rgba(255,209,102,0.32);
    color: #FFD166;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem; font-weight: 700;
    padding: 2px 7px; border-radius: 4px;
}
.prod-rating {
    margin-top: 10px;
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    padding-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.05);
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 28px 0 16px;
    border-top: 1px solid rgba(255,255,255,0.05);
    color: var(--muted);
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    margin-top: 40px;
    letter-spacing: 0.5px;
}
.footer b { color: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-heading"><i class="fi fi-tr-search"></i> Búsqueda</div>', unsafe_allow_html=True)
    query = st.text_input("Producto", value="", placeholder="celular, televisor, nevera...")
    max_pages = st.slider("Páginas", 1, 10, 3, help="~48 resultados por página")
    run_btn = st.button("Buscar ahora", use_container_width=True)
    st.markdown("---")
    st.markdown('<div class="sb-heading"><i class="fi fi-tr-sliders-v"></i> Filtros</div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Consultando Alkosto...")
def load_data(q: str, pages: int) -> pd.DataFrame:
    return pd.DataFrame(scrape(query=q, max_pages=pages))

if run_btn:
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_count += 1

df = load_data(query, max_pages)

if df.empty:
    st.error("No se encontraron productos. Intenta con otro término.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    search_name = st.text_input("Filtrar nombre", placeholder="Samsung, 15 pulgadas...")
    min_p, max_p = float(df.precio_cop.min()), float(df.precio_cop.max())
    price_range = st.slider("Precio (COP)", min_p, max_p, (min_p, max_p), format="$%.0f")
    marcas = sorted(df.marca.dropna().unique())
    marcas_sel = st.multiselect("Marca", options=marcas, default=[])
    solo_stock = st.checkbox("Solo en stock", value=False)
    st.markdown("---")
    ts = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="sb-info">
        <div class="sb-info-row"><i class="fi fi-tr-clock-twelve"></i> Última vez: <b style="color:#F47920">{ts}</b></div>
        <div class="sb-info-row"><i class="fi fi-tr-arrows-repeat"></i> Búsquedas: <b style="color:#F47920">{st.session_state.refresh_count}</b></div>
        <div class="sb-info-row"><i class="fi fi-tr-signal-stream"></i> Fuente: <b style="color:rgba(220,225,242,0.35)">Algolia API</b></div>
    </div>
    """, unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
marca_filter = marcas_sel if marcas_sel else marcas
filtered = df[
    (df.precio_cop >= price_range[0]) &
    (df.precio_cop <= price_range[1]) &
    (df.marca.isin(marca_filter))
].copy()
if solo_stock:
    filtered = filtered[filtered.disponibilidad == "En stock"]
if search_name:
    filtered = filtered[filtered.nombre.str.contains(search_name, case=False, na=False)]

if filtered.empty:
    st.warning("Ningún producto coincide con los filtros.")
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
    <div class="hero-watermark">TRACKER</div>
    <div class="hero-shine"></div>
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px">
        <div>
            <div class="hero-eyebrow">Alkosto Colombia · Live Data</div>
            <div class="hero-title">PRICE<br><span>TRACKER</span></div>
            <div class="hero-sub">Monitoreo de precios en tiempo real · Algolia API</div>
            <div class="hero-stats">
                <div class="hero-stat"><span class="hero-stat-val">{total}</span><span class="hero-stat-lbl">Productos</span></div>
                <div class="hero-stat"><span class="hero-stat-val">{in_stock}</span><span class="hero-stat-lbl">En stock</span></div>
                <div class="hero-stat"><span class="hero-stat-val">${avg_p:,.0f}</span><span class="hero-stat-lbl">Precio prom.</span></div>
                <div class="hero-stat"><span class="hero-stat-val">{max_disc}%</span><span class="hero-stat-lbl">Max desc.</span></div>
            </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:12px">
            <div class="live-badge"><div class="live-dot"></div>LIVE</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.62rem;color:rgba(220,225,242,0.22)">{now_str}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card c-orange" style="animation-delay:0.05s">
        <div class="kpi-icon"><i class="fi fi-tr-box-open"></i></div>
        <div class="kpi-label">Total productos</div>
        <div class="kpi-value">{total:,}</div>
        <div class="kpi-sub">"{query}"</div>
    </div>
    <div class="kpi-card c-gold" style="animation-delay:0.1s">
        <div class="kpi-icon"><i class="fi fi-tr-coins"></i></div>
        <div class="kpi-label">Precio promedio</div>
        <div class="kpi-value">${avg_p:,.0f}</div>
        <div class="kpi-sub">COP</div>
    </div>
    <div class="kpi-card c-green" style="animation-delay:0.15s">
        <div class="kpi-icon"><i class="fi fi-tr-bolt"></i></div>
        <div class="kpi-label">Precio mínimo</div>
        <div class="kpi-value">${min_p:,.0f}</div>
        <div class="kpi-sub">Mejor oferta</div>
    </div>
    <div class="kpi-card c-red" style="animation-delay:0.2s">
        <div class="kpi-icon"><i class="fi fi-tr-fire"></i></div>
        <div class="kpi-label">Mayor descuento</div>
        <div class="kpi-value">{max_disc}%</div>
        <div class="kpi-sub">vs precio original</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("""<div class="sec"><span class="sec-title"><i class="fi fi-tr-chart-line-up"></i> Análisis de precios</span><div class="sec-line"></div></div>""", unsafe_allow_html=True)

BG   = "rgba(0,0,0,0)"
GRID = "rgba(255,255,255,0.05)"
FONT = "rgba(220,225,242,0.38)"
FONT_T = "rgba(220,225,242,0.9)"

col1, col2 = st.columns(2)
with col1:
    fig1 = go.Figure(go.Histogram(
        x=filtered.precio_cop, nbinsx=25,
        marker=dict(color="#F47920", line=dict(color="#C85A00", width=1), opacity=0.85),
        hovertemplate="<b>$%{x:,.0f}</b><br>%{y} productos<extra></extra>",
    ))
    fig1.update_layout(
        title=dict(text="Distribución de precios", font=dict(color=FONT_T, size=13, family="DM Sans"), x=0.01),
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=FONT, family="DM Sans"),
        margin=dict(t=44,b=20,l=10,r=10),
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickprefix="$", tickformat=",.0f", tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="#111528", bordercolor="#F47920", font=dict(color="white")),
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    top_brands = filtered.marca.value_counts().head(10).reset_index()
    top_brands.columns = ["marca", "cantidad"]
    fig2 = go.Figure(go.Bar(
        x=top_brands["marca"], y=top_brands["cantidad"],
        marker=dict(
            color=top_brands["cantidad"],
            colorscale=[[0,"#1a0a00"],[0.5,"#C85A00"],[1,"#F47920"]],
            line=dict(color="#C85A00", width=1),
        ),
        hovertemplate="<b>%{x}</b><br>%{y} productos<extra></extra>",
    ))
    fig2.update_layout(
        title=dict(text="Top 10 marcas", font=dict(color=FONT_T, size=13, family="DM Sans"), x=0.01),
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=FONT, family="DM Sans"),
        margin=dict(t=44,b=20,l=10,r=10), coloraxis_showscale=False,
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="#111528", bordercolor="#F47920", font=dict(color="white")),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Discount Bars ─────────────────────────────────────────────────────────────
top_disc = filtered[filtered.desc_pct > 0].nlargest(10, "desc_pct")
if not top_disc.empty:
    max_d = top_disc.desc_pct.max()
    st.markdown(f"""<div class="sec"><span class="sec-title"><i class="fi fi-tr-fire"></i> Top descuentos activos</span><div class="sec-line"></div><span class="sec-count">{len(top_disc)} productos</span></div>""", unsafe_allow_html=True)
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
st.markdown("""<div class="sec" style="margin-top:28px"><span class="sec-title"><i class="fi fi-tr-star"></i> Mejores ofertas</span><div class="sec-line"></div></div>""", unsafe_allow_html=True)

highlights = filtered[filtered.desc_pct > 0].nlargest(6, "desc_pct") if (filtered.desc_pct > 0).any() else filtered.nsmallest(6, "precio_cop")
rows_list = list(highlights.iterrows())
for row_start in range(0, len(rows_list), 3):
    chunk = rows_list[row_start:row_start+3]
    cols = st.columns(3)
    for col_idx, (_, r) in enumerate(chunk):
        i = row_start + col_idx
        old_h   = f'<div class="prod-old">${r.get("precio_original_cop",0):,.0f}</div>' if r.get("precio_original_cop", 0) > r.precio_cop else ""
        badge_h = f'<span class="badge">{_html.escape(str(r.get("descuento","")).strip())}</span>' if str(r.get("descuento","")).strip() else ""
        rat     = r.get("rating", 0)
        rat_h   = f'<div class="prod-rating">{"★"*round(rat)}{"☆"*(5-round(rat))} {rat:.1f}</div>' if rat and rat > 0 else ""
        name_s  = _html.escape(str(r.get("nombre","")))
        brand_s = _html.escape(str(r.get("marca","")).strip() or "—")
        url_s   = _html.escape(str(r.get("url","")).strip())
        with cols[col_idx]:
            st.markdown(f"""
            <a class="prod-link" href="{url_s}" target="_blank" rel="noopener noreferrer">
            <div class="prod-card">
                <div class="prod-rank">#{i+1}</div>
                <div class="prod-brand">{brand_s}</div>
                <div class="prod-name">{name_s}</div>
                <div class="prod-bottom">
                    <div>{old_h}<div class="prod-price">${r.precio_cop:,.0f}</div></div>
                    {badge_h}
                </div>
                {rat_h}
            </div></a>""", unsafe_allow_html=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.markdown(f"""<div class="sec" style="margin-top:28px"><span class="sec-title"><i class="fi fi-tr-rectangle-list"></i> Catálogo completo</span><div class="sec-line"></div><span class="sec-count">{total} resultados</span></div>""", unsafe_allow_html=True)

disp = filtered[["nombre","marca","precio_cop","precio_original_cop","descuento","rating","disponibilidad"]].copy()
disp["precio_cop"]          = disp["precio_cop"].apply(lambda x: f"${x:,.0f}")
disp["precio_original_cop"] = disp["precio_original_cop"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x else "—")
disp["rating"]              = disp["rating"].apply(lambda x: f"{x:.1f}" if x and x > 0 else "—")
disp["disponibilidad"]      = disp["disponibilidad"].apply(lambda x: "En stock" if x == "En stock" else "Sin stock")
disp.columns = ["Producto","Marca","Precio","Precio antes","Descuento","Rating","Stock"]
st.dataframe(disp, use_container_width=True, hide_index=True,
    column_config={"Producto": st.column_config.TextColumn(width="large")})

# ── Downloads ─────────────────────────────────────────────────────────────────
st.markdown("""<div class="sec" style="margin-top:20px"><span class="sec-title"><i class="fi fi-tr-file-export"></i> Exportar</span><div class="sec-line"></div></div>""", unsafe_allow_html=True)
d1, d2 = st.columns(2)
with d1:
    st.download_button("Descargar CSV", data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"alkosto_{query}.csv", mime="text/csv", use_container_width=True)
with d2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        filtered.to_excel(w, index=False, sheet_name="Productos")
        for col in w.sheets["Productos"].columns:
            w.sheets["Productos"].column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 4
    st.download_button("Descargar Excel", data=buf.getvalue(),
        file_name=f"alkosto_{query}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)

st.markdown("""<div class="footer">Alkosto Price Tracker &nbsp;·&nbsp; <b>Algolia API</b> &nbsp;·&nbsp; Colombia</div>""", unsafe_allow_html=True)
