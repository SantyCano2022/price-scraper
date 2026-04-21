import sys
import io
import time
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent))
from scraper import scrape

st.set_page_config(
    page_title="Alkosto Price Tracker",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

# ── Global CSS + Animations ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* === BASE === */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* === ANIMATED BACKGROUND === */
.stApp {
    background: #050505;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(227,6,19,0.06) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(180,0,15,0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 60% 80%, rgba(100,0,8,0.05) 0%, transparent 50%);
    color: #f0f0f0;
    position: relative;
}

/* Grid lines background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(227,6,19,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(227,6,19,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
    animation: gridPulse 8s ease-in-out infinite;
}

@keyframes gridPulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background: rgba(10,10,10,0.95) !important;
    border-right: 1px solid rgba(227,6,19,0.2) !important;
    backdrop-filter: blur(20px);
}
section[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #E30613, transparent);
    animation: scanline 3s linear infinite;
}

@keyframes scanline {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* === BUTTONS === */
div[data-testid="stButton"] > button,
.stDownloadButton > button {
    background: linear-gradient(135deg, #E30613 0%, #9b0010 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    box-shadow: 0 4px 20px rgba(227,6,19,0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    position: relative !important;
    overflow: hidden !important;
}
div[data-testid="stButton"] > button::after,
.stDownloadButton > button::after {
    content: '';
    position: absolute;
    top: -50%; left: -60%;
    width: 40%; height: 200%;
    background: rgba(255,255,255,0.15);
    transform: skewX(-20deg);
    transition: left 0.4s ease;
}
div[data-testid="stButton"] > button:hover::after,
.stDownloadButton > button:hover::after {
    left: 130%;
}
div[data-testid="stButton"] > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 30px rgba(227,6,19,0.6), 0 0 40px rgba(227,6,19,0.2) !important;
}
div[data-testid="stButton"] > button:active,
.stDownloadButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}

/* === INPUTS === */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(227,6,19,0.25) !important;
    border-radius: 10px !important;
    color: #f9fafb !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #E30613 !important;
    box-shadow: 0 0 0 3px rgba(227,6,19,0.15), 0 0 20px rgba(227,6,19,0.1) !important;
    background: rgba(227,6,19,0.04) !important;
}

/* === SLIDER === */
div[data-testid="stSlider"] > div > div > div {
    background: #E30613 !important;
}

/* === DATAFRAME === */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(227,6,19,0.2) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: 0 0 30px rgba(227,6,19,0.05) !important;
}

/* === DIVIDER === */
hr { border-color: rgba(227,6,19,0.15) !important; margin: 24px 0 !important; }

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #050505; }
::-webkit-scrollbar-thumb { background: linear-gradient(#E30613, #9b0010); border-radius: 10px; }

/* === KPI CARD ANIMATIONS === */
@keyframes countUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 20px rgba(227,6,19,0.2), inset 0 1px 0 rgba(255,255,255,0.05); }
    50% { box-shadow: 0 0 40px rgba(227,6,19,0.35), inset 0 1px 0 rgba(255,255,255,0.05); }
}

@keyframes livePulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes borderGlow {
    0%, 100% { border-color: rgba(227,6,19,0.3); }
    50% { border-color: rgba(227,6,19,0.7); }
}

/* === HERO === */
.hero {
    background: linear-gradient(135deg, #0d0000 0%, #1a0003 30%, #0d0000 60%, #050000 100%);
    border: 1px solid rgba(227,6,19,0.3);
    border-radius: 20px;
    padding: 40px 48px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    animation: borderGlow 4s ease-in-out infinite;
}

.hero::before {
    content: '';
    position: absolute;
    top: 0; left: -100%; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(227,6,19,0.06), transparent);
    animation: heroShimmer 4s ease-in-out infinite;
}

@keyframes heroShimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

.hero-glow {
    position: absolute;
    top: -80px; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 200px;
    background: radial-gradient(ellipse, rgba(227,6,19,0.15) 0%, transparent 70%);
    pointer-events: none;
}

.hero-title {
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1.1;
    background: linear-gradient(135deg, #ffffff 0%, #ff6b6b 50%, #E30613 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 8px 0;
}

.hero-sub {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.5);
    font-weight: 400;
    letter-spacing: 0.3px;
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(227,6,19,0.1);
    border: 1px solid rgba(227,6,19,0.4);
    color: #ff4757;
    padding: 8px 18px;
    border-radius: 50px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    backdrop-filter: blur(10px);
}

.live-dot {
    width: 8px; height: 8px;
    background: #E30613;
    border-radius: 50%;
    animation: livePulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 8px #E30613;
}

.hero-stats {
    display: flex;
    gap: 32px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid rgba(255,255,255,0.06);
}

.hero-stat {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.hero-stat-val {
    font-size: 1.4rem;
    font-weight: 800;
    color: #f9fafb;
}

.hero-stat-lbl {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* === KPI === */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin: 24px 0;
}

.kpi-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(227,6,19,0.2);
    border-radius: 16px;
    padding: 24px 20px;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.6s ease forwards, glowPulse 4s ease-in-out infinite;
    cursor: default;
    transition: transform 0.3s ease, border-color 0.3s ease;
}

.kpi-card:hover {
    transform: translateY(-4px);
    border-color: rgba(227,6,19,0.5);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #E30613, transparent);
}

.kpi-card::after {
    content: '';
    position: absolute;
    bottom: -30px; right: -30px;
    width: 80px; height: 80px;
    background: radial-gradient(circle, rgba(227,6,19,0.1) 0%, transparent 70%);
    border-radius: 50%;
}

.kpi-icon { font-size: 1.6rem; margin-bottom: 10px; }
.kpi-label {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #f9fafb;
    letter-spacing: -1px;
    font-variant-numeric: tabular-nums;
}
.kpi-delta {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.35);
    margin-top: 4px;
}

/* === SECTION HEADER === */
.sec-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 32px 0 16px;
    animation: fadeInUp 0.5s ease;
}
.sec-icon { font-size: 1.1rem; }
.sec-title {
    font-size: 1rem;
    font-weight: 700;
    color: #f9fafb;
    letter-spacing: -0.2px;
    white-space: nowrap;
}
.sec-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(227,6,19,0.3), transparent);
}
.sec-count {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.3);
    white-space: nowrap;
}

/* === PRODUCT CARDS === */
.product-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 8px;
}

.product-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    animation: fadeInUp 0.5s ease forwards;
    transition: all 0.3s ease;
}
.product-card:hover {
    border-color: rgba(227,6,19,0.4);
    background: rgba(227,6,19,0.04);
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(227,6,19,0.15);
}
.product-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, transparent 60%, rgba(227,6,19,0.04));
    pointer-events: none;
}

.product-rank {
    position: absolute;
    top: 14px; right: 14px;
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #E30613, #9b0010);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem;
    font-weight: 800;
    color: white;
    box-shadow: 0 4px 12px rgba(227,6,19,0.5);
}

.product-brand {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #E30613;
    font-weight: 700;
    margin-bottom: 6px;
}

.product-name {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.85);
    font-weight: 500;
    line-height: 1.4;
    margin-bottom: 14px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 2.4em;
}

.product-price-row {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}

.product-price {
    font-size: 1.3rem;
    font-weight: 800;
    color: #f9fafb;
    letter-spacing: -0.5px;
}

.product-old {
    font-size: 0.75rem;
    text-decoration: line-through;
    color: rgba(255,255,255,0.3);
    margin-bottom: 2px;
}

.discount-badge {
    background: linear-gradient(135deg, #E30613, #9b0010);
    color: white;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 20px;
    letter-spacing: 0.3px;
    box-shadow: 0 4px 12px rgba(227,6,19,0.4);
    white-space: nowrap;
}

.rating-row {
    margin-top: 10px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.35);
}

/* === DISCOUNT BARS === */
.disc-bar-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 4px 0;
}

.disc-item {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    align-items: center;
    animation: fadeInUp 0.4s ease forwards;
}

.disc-name {
    font-size: 0.82rem;
    color: rgba(255,255,255,0.75);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.disc-bar-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 220px;
}

.disc-bar-bg {
    flex: 1;
    height: 8px;
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    overflow: hidden;
}

.disc-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, #9b0010, #E30613, #ff4757);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 10px rgba(227,6,19,0.6);
    animation: barLoad 1s ease forwards;
}

@keyframes barLoad {
    from { width: 0% !important; }
}

.disc-pct {
    font-size: 0.8rem;
    font-weight: 700;
    color: #ff4757;
    min-width: 36px;
    text-align: right;
}

/* === AUTO REFRESH COUNTER === */
.refresh-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 10px 18px;
    margin-bottom: 24px;
    font-size: 0.78rem;
    color: rgba(255,255,255,0.4);
}

.refresh-timer {
    font-weight: 700;
    color: #E30613;
    font-variant-numeric: tabular-nums;
}

/* === FOOTER === */
.footer {
    text-align: center;
    padding: 32px 0 16px;
    border-top: 1px solid rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.2);
    font-size: 0.75rem;
    letter-spacing: 0.5px;
    margin-top: 40px;
}

.footer span { color: #E30613; }
</style>
""", unsafe_allow_html=True)

# ── Auto-refresh JS (cada 5 min) ──────────────────────────────────────────────
st.markdown("""
<script>
(function() {
    var refreshSecs = 300;
    var timerEl = null;

    function findTimer() {
        timerEl = document.getElementById('refresh-timer');
        return timerEl;
    }

    function tick() {
        if (!findTimer()) { setTimeout(tick, 500); return; }
        if (refreshSecs <= 0) { location.reload(); return; }
        var m = Math.floor(refreshSecs / 60);
        var s = refreshSecs % 60;
        timerEl.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        refreshSecs--;
        setTimeout(tick, 1000);
    }

    window.addEventListener('load', function() { setTimeout(tick, 800); });
})();
</script>
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
@st.cache_data(show_spinner="⚡ Consultando Alkosto en tiempo real...")
def load_data(q: str, pages: int) -> pd.DataFrame:
    return pd.DataFrame(scrape(query=q, max_pages=pages))

if run_btn:
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.session_state.refresh_count += 1

df = load_data(query, max_pages)

if df.empty:
    st.error("❌ No se encontraron productos.")
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
    now_str = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="font-size:0.75rem; color:rgba(255,255,255,0.3); line-height:1.8">
        🕒 Última actualización: <b style="color:#E30613">{now_str}</b><br>
        🔄 Actualizaciones: <b style="color:#E30613">{st.session_state.refresh_count}</b><br>
        📡 Fuente: <b style="color:rgba(255,255,255,0.5)">Algolia API</b>
    </div>
    """, unsafe_allow_html=True)

# ── Apply filters ─────────────────────────────────────────────────────────────
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
    st.warning("⚠️ Ningún producto coincide con los filtros.")
    st.stop()

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_discount(d):
    try:
        return abs(int(str(d).replace("%", "").replace("-", "").strip()))
    except:
        return 0

filtered2 = filtered.copy()
filtered2["desc_pct"] = filtered2["descuento"].apply(parse_discount)
total     = len(filtered2)
avg_price = filtered2.precio_cop.mean()
min_price = filtered2.precio_cop.min()
max_price = filtered2.precio_cop.max()
in_stock  = (filtered2.disponibilidad == "En stock").sum()

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-glow"></div>
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:16px">
        <div>
            <div class="hero-title">Alkosto Price Tracker</div>
            <div class="hero-sub">Monitoreo de precios en tiempo real · Alkosto Colombia 🇨🇴</div>
            <div class="hero-stats">
                <div class="hero-stat">
                    <span class="hero-stat-val">{total}</span>
                    <span class="hero-stat-lbl">Productos</span>
                </div>
                <div class="hero-stat">
                    <span class="hero-stat-val">{in_stock}</span>
                    <span class="hero-stat-lbl">En stock</span>
                </div>
                <div class="hero-stat">
                    <span class="hero-stat-val">${avg_price:,.0f}</span>
                    <span class="hero-stat-lbl">Precio prom.</span>
                </div>
                <div class="hero-stat">
                    <span class="hero-stat-val">{(filtered2.desc_pct > 0).sum()}</span>
                    <span class="hero-stat-lbl">Con descuento</span>
                </div>
            </div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:12px">
            <div class="live-badge">
                <div class="live-dot"></div>
                LIVE
            </div>
            <div style="font-size:0.75rem; color:rgba(255,255,255,0.3); text-align:right">
                Auto-refresh en <span class="refresh-timer" id="refresh-timer" style="color:#E30613; font-weight:700">5:00</span>
            </div>
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
        <div class="kpi-delta">Búsqueda: "{query}"</div>
    </div>
    <div class="kpi-card" style="animation-delay:0.1s">
        <div class="kpi-icon">💰</div>
        <div class="kpi-label">Precio promedio</div>
        <div class="kpi-value">${avg_price:,.0f}</div>
        <div class="kpi-delta">COP</div>
    </div>
    <div class="kpi-card" style="animation-delay:0.15s">
        <div class="kpi-icon">⚡</div>
        <div class="kpi-label">Precio mínimo</div>
        <div class="kpi-value">${min_price:,.0f}</div>
        <div class="kpi-delta">Mejor oferta</div>
    </div>
    <div class="kpi-card" style="animation-delay:0.2s">
        <div class="kpi-icon">🔥</div>
        <div class="kpi-label">Mayor descuento</div>
        <div class="kpi-value">{filtered2.desc_pct.max() if (filtered2.desc_pct > 0).any() else 0}%</div>
        <div class="kpi-delta">vs precio original</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-header">
    <span class="sec-icon">📉</span>
    <span class="sec-title">Análisis de precios</span>
    <div class="sec-line"></div>
</div>
""", unsafe_allow_html=True)

BG = "rgba(0,0,0,0)"
GRID = "rgba(255,255,255,0.04)"
FONT = "rgba(255,255,255,0.4)"
FONT_TITLE = "rgba(255,255,255,0.85)"

col1, col2 = st.columns(2)

with col1:
    fig1 = go.Figure()
    fig1.add_trace(go.Histogram(
        x=filtered2.precio_cop, nbinsx=25,
        marker=dict(
            color="#E30613",
            line=dict(color="#9b0010", width=1),
            opacity=0.85,
        ),
        name="Precio",
        hovertemplate="<b>Rango:</b> $%{x:,.0f}<br><b>Productos:</b> %{y}<extra></extra>",
    ))
    fig1.update_layout(
        title=dict(text="Distribución de precios", font=dict(color=FONT_TITLE, size=13, family="Inter"), x=0.01),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=FONT, family="Inter"),
        margin=dict(t=40, b=20, l=10, r=10),
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10), tickprefix="$", tickformat=",.0f"),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="#1a0003", bordercolor="#E30613", font=dict(color="white")),
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    top_brands = filtered2.marca.value_counts().head(10).reset_index()
    top_brands.columns = ["marca", "cantidad"]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=top_brands["marca"], y=top_brands["cantidad"],
        marker=dict(
            color=top_brands["cantidad"],
            colorscale=[[0, "#3d0008"], [0.5, "#9b0010"], [1, "#E30613"]],
            line=dict(color="#9b0010", width=1),
        ),
        hovertemplate="<b>%{x}</b><br>Productos: %{y}<extra></extra>",
    ))
    fig2.update_layout(
        title=dict(text="Top 10 marcas", font=dict(color=FONT_TITLE, size=13, family="Inter"), x=0.01),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=FONT, family="Inter"),
        margin=dict(t=40, b=20, l=10, r=10),
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="#1a0003", bordercolor="#E30613", font=dict(color="white")),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Top Discounts Bars ────────────────────────────────────────────────────────
top_disc = filtered2[filtered2["desc_pct"] > 0].nlargest(10, "desc_pct")

if not top_disc.empty:
    max_disc = top_disc["desc_pct"].max()
    st.markdown(f"""
    <div class="sec-header">
        <span class="sec-icon">🔥</span>
        <span class="sec-title">Top descuentos activos</span>
        <div class="sec-line"></div>
        <span class="sec-count">{len(top_disc)} productos</span>
    </div>
    """, unsafe_allow_html=True)

    bars_html = '<div class="disc-bar-container">'
    for _, row in top_disc.iterrows():
        pct = row["desc_pct"]
        width = int((pct / max_disc) * 100)
        name = str(row["nombre"])[:60] + ("…" if len(str(row["nombre"])) > 60 else "")
        bars_html += f"""
        <div class="disc-item">
            <span class="disc-name">{name}</span>
            <div class="disc-bar-wrap">
                <div class="disc-bar-bg">
                    <div class="disc-bar-fill" style="width:{width}%"></div>
                </div>
                <span class="disc-pct">-{pct}%</span>
            </div>
        </div>"""
    bars_html += "</div>"
    st.markdown(bars_html, unsafe_allow_html=True)

# ── Top Product Cards ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sec-header" style="margin-top:32px">
    <span class="sec-icon">⭐</span>
    <span class="sec-title">Mejores ofertas destacadas</span>
    <div class="sec-line"></div>
</div>
""", unsafe_allow_html=True)

highlight = filtered2[filtered2["desc_pct"] > 0].nlargest(6, "desc_pct")
if highlight.empty:
    highlight = filtered2.nsmallest(6, "precio_cop")

cards_html = '<div class="product-grid">'
for i, (_, row) in enumerate(highlight.iterrows()):
    brand = str(row.get("marca", "")).strip() or "—"
    name = str(row.get("nombre", ""))
    price = row.get("precio_cop", 0)
    old_price = row.get("precio_original_cop", 0)
    disc = str(row.get("descuento", "")).strip()
    rating = row.get("rating", 0)
    stars = "★" * round(rating) + "☆" * (5 - round(rating)) if rating else ""

    old_html = f'<div class="product-old">${old_price:,.0f}</div>' if old_price and old_price > price else ""
    badge_html = f'<span class="discount-badge">{disc}</span>' if disc else ""
    rating_html = f'<div class="rating-row">{stars} {rating:.1f}</div>' if rating and rating > 0 else ""

    cards_html += f"""
    <div class="product-card" style="animation-delay:{i*0.07}s">
        <div class="product-rank">#{i+1}</div>
        <div class="product-brand">{brand}</div>
        <div class="product-name">{name}</div>
        <div class="product-price-row">
            <div>
                {old_html}
                <div class="product-price">${price:,.0f}</div>
            </div>
            {badge_html}
        </div>
        {rating_html}
    </div>"""

cards_html += "</div>"
st.markdown(cards_html, unsafe_allow_html=True)

# ── Full Table ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sec-header" style="margin-top:32px">
    <span class="sec-icon">🗂️</span>
    <span class="sec-title">Catálogo completo</span>
    <div class="sec-line"></div>
    <span class="sec-count">{len(filtered2)} resultados</span>
</div>
""", unsafe_allow_html=True)

display_df = filtered2[["nombre", "marca", "precio_cop", "precio_original_cop", "descuento", "rating", "disponibilidad"]].copy()
display_df["precio_cop"] = display_df["precio_cop"].apply(lambda x: f"${x:,.0f}")
display_df["precio_original_cop"] = display_df["precio_original_cop"].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) and x else "—"
)
display_df["rating"] = display_df["rating"].apply(lambda x: f"⭐ {x:.1f}" if x and x > 0 else "—")
display_df["disponibilidad"] = display_df["disponibilidad"].apply(
    lambda x: "✅ En stock" if x == "En stock" else "❌ Sin stock"
)
display_df = display_df.rename(columns={
    "nombre": "Producto", "marca": "Marca", "precio_cop": "Precio",
    "precio_original_cop": "Precio antes", "descuento": "Descuento",
    "rating": "Rating", "disponibilidad": "Stock",
})
st.dataframe(display_df, use_container_width=True, hide_index=True,
    column_config={
        "Producto": st.column_config.TextColumn(width="large"),
        "Precio": st.column_config.TextColumn(width="small"),
        "Precio antes": st.column_config.TextColumn(width="small"),
        "Descuento": st.column_config.TextColumn(width="small"),
    }
)

# ── Downloads ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-header" style="margin-top:24px">
    <span class="sec-icon">⬇️</span>
    <span class="sec-title">Exportar datos</span>
    <div class="sec-line"></div>
</div>
""", unsafe_allow_html=True)

d1, d2 = st.columns(2)
with d1:
    st.download_button(
        "⬇️ Descargar CSV",
        data=filtered2.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"alkosto_{query}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with d2:
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        filtered2.to_excel(writer, index=False, sheet_name="Productos")
        ws = writer.sheets["Productos"]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(
                len(str(c.value or "")) for c in col) + 4
    st.download_button(
        "⬇️ Descargar Excel",
        data=excel_buf.getvalue(),
        file_name=f"alkosto_{query}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Alkosto Price Tracker &nbsp;·&nbsp; Datos en tiempo real vía <span>Algolia API</span>
    &nbsp;·&nbsp; 🇨🇴 Colombia &nbsp;·&nbsp; Hecho con <span>♥</span>
</div>
""", unsafe_allow_html=True)
