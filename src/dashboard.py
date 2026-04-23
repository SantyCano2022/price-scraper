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
    page_title="pricewatch · scraper console",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ──────────────────────────────────────────────────────────────
_defaults = {
    "last_refresh": time.time(),
    "refresh_count": 0,
    "pages": 3,
    "tweaks_open": False,
    "theme": "dark",
    "accent_hue": 55,
    "density": "regular",
    "category": "Todas",
    "success_rate": 88,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Category keyword map ───────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Televisores": ["televisor", "tv ", " tv", "qled", "oled", "neo qled", "crystal uhd", "smart tv"],
    "Computo":     ["laptop", "computador", "notebook", "chromebook", "pc desktop", "monitor ", "teclado", "impresora"],
    "Línea Blanca":["nevera", "lavadora", "secadora", "horno", "microondas", "estufa", "refrigerador", "lavavajillas"],
    "Audio":       ["parlante", "audífono", "audifonos", "auricular", "soundbar", "bocina", "altavoz", "headphone"],
    "Celulares":   ["celular", "smartphone", "iphone", "galaxy a", "galaxy s", "xiaomi", "motorola", "redmi"],
}
CATEGORIES = ["Todas"] + list(CATEGORY_KEYWORDS.keys())

def infer_category(nombre: str) -> str:
    n = nombre.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in n for k in kws):
            return cat
    return "Otros"

# ── Static CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

/* ── Typography ───────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Geist', ui-sans-serif, system-ui, -apple-system, sans-serif !important;
    font-feature-settings: 'ss01', 'cv11';
    letter-spacing: -0.005em;
}

/* ── App chrome ───────────────────────────────────── */
.stApp { background: var(--bg) !important; }
#MainMenu, footer, header { visibility: hidden !important; }

/* ── Grain texture overlay ────────────────────────── */
.stApp::after {
    content: '';
    position: fixed; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.035'/%3E%3C/svg%3E");
    pointer-events: none; z-index: 9999; opacity: 0.5;
}

/* ── Accent top stripe ────────────────────────────── */
.stApp::before {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent-strong), transparent);
    z-index: 9998; pointer-events: none;
}

/* ── Sidebar ──────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-dim) !important;
    font-size: 12px !important;
}

/* ── Sidebar branding ─────────────────────────────── */
.brand-header {
    display: flex; align-items: center; gap: 10px;
    padding: 14px 16px 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 4px;
}
.brand-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--accent), var(--accent-strong));
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
    box-shadow: 0 2px 8px var(--accent-dim);
}
.brand-text { display: flex; flex-direction: column; gap: 1px; }
.brand-name {
    font-size: 13px; font-weight: 700; color: var(--text);
    letter-spacing: -0.02em; line-height: 1;
}
.brand-sub {
    font-size: 10px; color: var(--text-dimmer);
    font-family: 'Geist Mono', monospace;
    letter-spacing: 0.02em;
}

/* ── Sidebar section label ────────────────────────── */
.side-label {
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--text-dimmer);
    margin: 14px 0 6px;
}

/* ── Buttons ──────────────────────────────────────── */
div[data-testid="stButton"] > button,
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent-strong)) !important;
    color: oklch(0.18 0.02 60) !important;
    border: 1px solid var(--accent-border) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: -0.005em !important;
    box-shadow: 0 1px 0 oklch(1 0 0 / 0.2) inset, 0 4px 12px var(--accent-dim) !important;
    transition: all 0.15s ease !important;
    height: 36px !important;
}
div[data-testid="stButton"] > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    filter: brightness(1.08) !important;
}

/* ── Stepper buttons (pages ± ) ───────────────────── */
.stepper-btn > div > button {
    background: var(--bg-elev) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    height: 34px !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    box-shadow: none !important;
    border-radius: 6px !important;
}
.stepper-btn > div > button:hover {
    background: var(--bg-elev-2) !important;
    border-color: var(--accent-border) !important;
    transform: none !important;
}
.stepper-display {
    text-align: center;
    font-family: 'Geist Mono', monospace;
    font-size: 14px; font-weight: 600;
    color: var(--text);
    padding: 7px 0;
    background: var(--bg-elev);
    border: 1px solid var(--border);
    border-radius: 6px;
}

/* ── Category pills (radio as pills) ─────────────── */
div[data-testid="stRadio"][data-category-pills] > div {
    display: flex; flex-wrap: wrap; gap: 5px;
}
.cat-pill-wrap div[data-testid="stRadio"] > label { display: none; }
.cat-pill-wrap div[data-testid="stRadio"] > div {
    display: flex; flex-wrap: wrap; gap: 5px; margin-top: 2px;
}
.cat-pill-wrap div[data-testid="stRadio"] > div > label {
    background: var(--bg-elev) !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    padding: 3px 11px !important;
    font-size: 11.5px !important;
    cursor: pointer !important;
    color: var(--text-dim) !important;
    transition: all 0.12s !important;
    white-space: nowrap !important;
}
.cat-pill-wrap div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: var(--accent-dim) !important;
    border-color: var(--accent-border) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
}
.cat-pill-wrap div[data-testid="stRadio"] > div > label > div:first-child {
    display: none !important;
}

/* ── Inputs ───────────────────────────────────────── */
div[data-testid="stTextInput"] input {
    background: var(--bg-elev) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 13px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--accent-border) !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
}

/* ── Slider ───────────────────────────────────────── */
div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="TrackHighlight"],
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="InnerTrack"] {
    background: var(--accent) !important;
}
div[data-testid="stSlider"] [data-baseweb="slider"] div[class*="Track"] {
    background: var(--border) !important;
}

/* ── Checkbox ─────────────────────────────────────── */
[data-testid="stCheckbox"] { background: transparent !important; }
[data-baseweb="checkbox"] [data-checked="true"] {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
}
[data-baseweb="checkbox"] [data-checked="false"] {
    background-color: transparent !important;
    border-color: var(--border-strong) !important;
}

/* ── Status bar ───────────────────────────────────── */
.status-bar {
    display: flex; align-items: center; gap: 0;
    padding: 0 4px 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
    flex-wrap: wrap; gap: 8px;
}
.breadcrumb {
    font-family: 'Geist Mono', monospace;
    font-size: 11px; color: var(--text-dimmer);
    display: flex; align-items: center; gap: 4px;
    margin-right: auto;
}
.breadcrumb span { color: var(--text-dim); }
.breadcrumb b { color: var(--text); font-weight: 500; }
.stat-pill {
    display: inline-flex; flex-direction: column; gap: 1px;
    padding: 4px 12px;
    border-left: 1px solid var(--border);
}
.stat-label {
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--text-dimmer);
    font-family: 'Geist Mono', monospace;
}
.stat-value {
    font-size: 12px; font-weight: 600; color: var(--text);
    font-family: 'Geist Mono', monospace; letter-spacing: -0.01em;
    display: flex; align-items: center; gap: 5px;
}
.run-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--good); box-shadow: 0 0 6px var(--good);
    display: inline-block;
    animation: pulse 1.8s ease-in-out infinite;
}
.bar-btn {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 5px 12px;
    background: var(--bg-elev); border: 1px solid var(--border);
    border-radius: 7px; font-size: 11.5px; font-weight: 500;
    color: var(--text-dim); cursor: pointer;
    font-family: 'Geist', sans-serif;
    transition: all 0.15s;
}
.bar-btn:hover { border-color: var(--accent-border); color: var(--accent); }

/* ── Page header ──────────────────────────────────── */
.page-head {
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 24px; margin: 4px 0 20px;
    animation: fadeUp 0.4s ease;
}
.eyebrow {
    font-family: 'Geist Mono', monospace;
    font-size: 11px; color: var(--text-dimmer);
    letter-spacing: 0.02em; margin-bottom: 6px;
}
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 36px; font-weight: 800;
    letter-spacing: -0.04em; margin: 0;
    line-height: 1.05; color: var(--text);
}
.title-dim { color: var(--text-dim); font-weight: 400; }
.page-sub { font-size: 13px; color: var(--text-dim); margin-top: 8px; }
.live-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 12px; border-radius: 999px;
    background: var(--accent-dim); border: 1px solid var(--accent-border);
    color: var(--accent); font-size: 10.5px; font-weight: 600;
    letter-spacing: 0.1em; font-family: 'Geist Mono', monospace;
    white-space: nowrap;
}
.live-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 8px var(--accent);
    animation: pulse 1.5s ease-in-out infinite;
}

/* ── KPI grid ─────────────────────────────────────── */
.kpi-grid {
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 1px;
    background: var(--border);
    border: 1px solid var(--border); border-radius: 12px;
    overflow: hidden; margin-bottom: 20px;
}
.kpi {
    background: var(--bg-elev);
    display: flex; flex-direction: column; gap: 4px;
    transition: background 0.2s, box-shadow 0.2s;
    animation: fadeUp 0.5s cubic-bezier(0.22,1,0.36,1) both;
    position: relative;
}
.kpi::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0;
    height: 2px; background: var(--accent);
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.25s cubic-bezier(0.22,1,0.36,1);
}
.kpi:hover { background: var(--bg-elev-2); }
.kpi:hover::after { transform: scaleX(1); }
.kpi-label {
    font-size: 10.5px; color: var(--text-dimmer);
    text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500;
}
.kpi-value {
    font-size: 26px; font-weight: 700;
    letter-spacing: -0.03em;
    font-family: 'Syne', sans-serif;
    color: var(--text);
    text-shadow: 0 0 40px var(--accent-dim);
}
.kpi-foot { display: flex; gap: 8px; align-items: center; font-size: 11px; color: var(--text-dimmer); }
.kpi-delta {
    font-family: 'Geist Mono', monospace; font-size: 10.5px;
    padding: 1px 5px; border-radius: 4px;
}
.kpi-delta.good { color: var(--good); background: var(--good-dim); }
.kpi-delta.bad  { color: var(--bad);  background: var(--bad-dim); }

/* ── Panel ────────────────────────────────────────── */
.panel {
    background: var(--bg-elev); border: 1px solid var(--border);
    border-radius: 12px; overflow: hidden; margin-bottom: 16px;
}
.panel-head {
    padding: 12px 16px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
}
.panel-title { font-size: 12px; font-weight: 600; color: var(--text); letter-spacing: -0.005em; }
.panel-sub { font-size: 11px; color: var(--text-dimmer); font-family: 'Geist Mono', monospace; }
.panel-body { padding: 14px 16px; }

/* ── Discount bars ────────────────────────────────── */
.disc-list { display: flex; flex-direction: column; gap: 8px; padding: 12px 16px; }
.disc-row {
    display: grid; grid-template-columns: 1fr 160px 44px;
    align-items: center; gap: 12px;
    animation: fadeUp 0.35s ease forwards;
}
.disc-name { font-size: 12px; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.disc-track { height: 6px; background: var(--bg-elev-2); border-radius: 3px; overflow: hidden; }
.disc-fill {
    height: 100%; border-radius: 3px;
    background: linear-gradient(90deg, var(--accent-strong), var(--accent));
    animation: barFill 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.disc-pct {
    font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 600;
    color: var(--good); background: var(--good-dim);
    padding: 2px 6px; border-radius: 4px; text-align: center;
}

/* ── Product cards ────────────────────────────────── */
.prod-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; padding: 14px 16px; }
.prod-card {
    background: var(--bg-elev-2); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 16px; position: relative;
    transition: border-color 0.2s, transform 0.2s cubic-bezier(0.22,1,0.36,1), box-shadow 0.2s;
    animation: fadeUp 0.5s cubic-bezier(0.22,1,0.36,1) both;
    overflow: hidden;
}
.prod-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-border), transparent);
    opacity: 0; transition: opacity 0.2s;
}
.prod-card:hover {
    border-color: var(--accent-border); transform: translateY(-3px);
    box-shadow: 0 12px 32px var(--accent-dim), 0 2px 8px rgba(0,0,0,0.3);
}
.prod-card:hover::before { opacity: 1; }
a.prod-link { text-decoration: none !important; display: block; color: inherit !important; }
.prod-rank {
    position: absolute; top: 10px; right: 10px;
    width: 22px; height: 22px;
    background: var(--accent-dim); border: 1px solid var(--accent-border);
    color: var(--accent); border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; font-family: 'Geist Mono', monospace;
}
.prod-brand {
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--accent); font-weight: 600; margin-bottom: 6px;
}
.prod-name {
    font-size: 12.5px; color: var(--text); line-height: 1.4; margin-bottom: 12px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; min-height: 2.3em; font-weight: 500;
}
.prod-bottom { display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; }
.prod-price-block { display: flex; flex-direction: column; }
.prod-old { font-family: 'Geist Mono', monospace; font-size: 10.5px; text-decoration: line-through; color: var(--text-dimmer); }
.prod-price { font-family: 'Geist Mono', monospace; font-size: 16px; font-weight: 600; letter-spacing: -0.01em; color: var(--text); }
.badge-discount {
    background: var(--good); color: oklch(0.18 0.02 60);
    font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 700;
    padding: 3px 7px; border-radius: 5px;
}
.prod-rating { margin-top: 8px; font-size: 11px; color: var(--text-dim); font-family: 'Geist Mono', monospace; }

/* ── Section divider ──────────────────────────────── */
.sec { display: flex; align-items: center; gap: 10px; margin: 28px 0 12px; }
.sec-title {
    font-size: 10px; font-weight: 700; color: var(--text-dimmer);
    text-transform: uppercase; letter-spacing: 0.12em; white-space: nowrap;
    font-family: 'Geist Mono', monospace;
}
.sec-line { flex: 1; height: 1px; background: linear-gradient(90deg, var(--accent-border), transparent); }
.sec-count { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--text-dimmer); padding: 2px 8px; border-radius: 999px; background: var(--bg-elev); border: 1px solid var(--border); white-space: nowrap; }

/* ── Tweaks panel ─────────────────────────────────── */
.tweaks-panel {
    background: var(--bg-elev-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 14px 16px; margin-bottom: 16px;
}
.tweaks-title {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--text-dimmer); margin-bottom: 12px;
    font-family: 'Geist Mono', monospace;
}
.tweaks-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; font-size: 12px; color: var(--text-dim); }

/* ── Status chip ──────────────────────────────────── */
.status-chip {
    background: var(--bg-elev); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px;
    font-size: 11px; line-height: 1.8; color: var(--text-dim);
    font-family: 'Geist Mono', monospace;
}
.status-chip b { color: var(--accent); font-weight: 600; }
.status-dot {
    display: inline-block; width: 6px; height: 6px; border-radius: 50%;
    background: var(--good); box-shadow: 0 0 6px var(--good);
    margin-right: 6px; animation: pulse 2s ease-in-out infinite;
    vertical-align: middle;
}

/* ── Dataframe ────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important; border-radius: 12px !important;
    overflow: hidden !important; background: var(--bg-elev) !important;
}

/* ── Misc ─────────────────────────────────────────── */
hr { border-color: var(--border) !important; opacity: 0.8 !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
h1, h2, h3 { color: var(--text) !important; letter-spacing: -0.02em !important; }

/* ── Animations ───────────────────────────────────── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}
@keyframes barFill { from { width: 0 !important; } }
</style>
""", unsafe_allow_html=True)


# ── Dynamic CSS (theme / accent hue / density) ─────────────────────────────────
def inject_theme():
    hue = st.session_state.accent_hue
    theme = st.session_state.theme
    density = st.session_state.density

    dens_pad = {"compact": "10px 14px", "regular": "16px 18px", "comfy": "22px 26px"}[density]

    if theme == "dark":
        t = f"""
        --bg: oklch(0.16 0.008 {hue});
        --bg-elev: oklch(0.195 0.009 {hue});
        --bg-elev-2: oklch(0.225 0.01 {hue});
        --bg-sidebar: oklch(0.14 0.008 {hue});
        --border: oklch(0.3 0.01 {hue} / 0.5);
        --border-strong: oklch(0.4 0.012 {hue} / 0.55);
        --text: oklch(0.96 0.004 {hue});
        --text-dim: oklch(0.72 0.008 {hue});
        --text-dimmer: oklch(0.52 0.008 {hue});
        """
    else:
        t = f"""
        --bg: oklch(0.97 0.005 {hue});
        --bg-elev: oklch(0.93 0.006 {hue});
        --bg-elev-2: oklch(0.89 0.007 {hue});
        --bg-sidebar: oklch(0.95 0.005 {hue});
        --border: oklch(0.78 0.01 {hue} / 0.6);
        --border-strong: oklch(0.65 0.012 {hue} / 0.7);
        --text: oklch(0.18 0.01 {hue});
        --text-dim: oklch(0.38 0.01 {hue});
        --text-dimmer: oklch(0.55 0.01 {hue});
        """

    h2 = max(0, hue - 10)
    st.markdown(f"""
    <style>
    :root {{
        {t}
        --accent: oklch(0.76 0.15 {hue});
        --accent-dim: oklch(0.76 0.15 {hue} / 0.15);
        --accent-border: oklch(0.76 0.15 {hue} / 0.38);
        --accent-strong: oklch(0.65 0.17 {h2});
        --good: oklch(0.72 0.14 155);
        --good-dim: oklch(0.72 0.14 155 / 0.14);
        --bad: oklch(0.68 0.16 25);
        --bad-dim: oklch(0.68 0.16 25 / 0.14);
    }}
    .kpi {{ padding: {dens_pad} !important; }}
    </style>
    """, unsafe_allow_html=True)

inject_theme()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <div class="brand-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
                 style="color:oklch(0.18 0.02 60)">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
        </div>
        <div class="brand-text">
            <span class="brand-name">pricewatch</span>
            <span class="brand-sub">scraper console</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="side-label">Query</div>', unsafe_allow_html=True)
    query = st.text_input("Producto", value="laptop", placeholder="celular, televisor…", label_visibility="collapsed")

    st.markdown('<div class="side-label">Páginas</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        st.markdown('<div class="stepper-btn">', unsafe_allow_html=True)
        if st.button("−", key="pages_minus", use_container_width=True):
            st.session_state.pages = max(1, st.session_state.pages - 1)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stepper-display">{st.session_state.pages}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="stepper-btn">', unsafe_allow_html=True)
        if st.button("+", key="pages_plus", use_container_width=True):
            st.session_state.pages = min(15, st.session_state.pages + 1)
        st.markdown('</div>', unsafe_allow_html=True)

    max_pages = st.session_state.pages

    run_btn = st.button("⚡ Scrape ahora", use_container_width=True, key="run_btn")

    st.markdown('<div class="side-label">Categoría</div>', unsafe_allow_html=True)
    st.markdown('<div class="cat-pill-wrap">', unsafe_allow_html=True)
    cat_sel = st.radio("cat", CATEGORIES, index=CATEGORIES.index(st.session_state.category),
                       horizontal=False, label_visibility="collapsed", key="cat_radio")
    st.session_state.category = cat_sel
    st.markdown('</div>', unsafe_allow_html=True)

# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⚡ Consultando Alkosto…")
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

# Infer category column
df["categoria"] = df["nombre"].apply(infer_category)

# ── Sidebar: remaining filters ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="side-label">Precio (COP)</div>', unsafe_allow_html=True)
    min_p0, max_p0 = float(df.precio_cop.min()), float(df.precio_cop.max())
    price_range = st.slider("Precio", min_p0, max_p0, (min_p0, max_p0), format="$%.0f", label_visibility="collapsed")

    st.markdown('<div class="side-label">Marca</div>', unsafe_allow_html=True)
    marcas = sorted(df.marca.dropna().unique())
    marcas_sel = st.multiselect("Marca", options=marcas, default=[], label_visibility="collapsed")

    st.markdown('<div class="side-label">Filtros</div>', unsafe_allow_html=True)
    solo_stock = st.checkbox("Solo en stock", value=False)
    solo_dto   = st.checkbox("Solo con descuento", value=False)

    st.markdown("<br>", unsafe_allow_html=True)
    ts_chip = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="status-chip">
        <span class="status-dot"></span> scraper <b>online</b><br>
        última <b>{ts_chip}</b><br>
        búsquedas <b>{st.session_state.refresh_count}</b><br>
        fuente <b>Algolia</b>
    </div>
    """, unsafe_allow_html=True)

    # ── Tweaks ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("⚙ Tweaks", expanded=st.session_state.tweaks_open):
        st.session_state.tweaks_open = True

        st.markdown('<div class="tweaks-title">Theme</div>', unsafe_allow_html=True)
        theme_new = st.radio("Modo", ["dark", "light"], index=0 if st.session_state.theme == "dark" else 1,
                              horizontal=True, label_visibility="collapsed")
        if theme_new != st.session_state.theme:
            st.session_state.theme = theme_new
            st.rerun()

        st.markdown('<div style="margin-top:10px" class="tweaks-title">Accent hue</div>', unsafe_allow_html=True)
        hue_new = st.slider("Hue", 0, 360, st.session_state.accent_hue, label_visibility="collapsed")
        if hue_new != st.session_state.accent_hue:
            st.session_state.accent_hue = hue_new
            st.rerun()

        st.markdown('<div style="margin-top:10px" class="tweaks-title">Densidad</div>', unsafe_allow_html=True)
        dens_new = st.radio("Densidad", ["compact", "regular", "comfy"],
                             index=["compact", "regular", "comfy"].index(st.session_state.density),
                             horizontal=True, label_visibility="collapsed")
        if dens_new != st.session_state.density:
            st.session_state.density = dens_new
            st.rerun()

# ── Apply filters ──────────────────────────────────────────────────────────────
marca_filter = marcas_sel if marcas_sel else marcas
filtered = df[
    (df.precio_cop >= price_range[0]) &
    (df.precio_cop <= price_range[1]) &
    (df.marca.isin(marca_filter))
].copy()

if cat_sel != "Todas":
    filtered = filtered[filtered.categoria == cat_sel]
if solo_stock:
    filtered = filtered[filtered.disponibilidad == "En stock"]

def parse_disc(d):
    try: return abs(int(str(d).replace("%", "").replace("-", "").strip()))
    except Exception: return 0

filtered["desc_pct"] = filtered["descuento"].apply(parse_disc)

if solo_dto:
    filtered = filtered[filtered.desc_pct > 0]

if filtered.empty:
    st.warning("⚠️ Ningún producto coincide con los filtros.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────────
total      = len(filtered)
avg_p      = filtered.precio_cop.median()
min_p      = filtered.precio_cop.min()
in_stock   = (filtered.disponibilidad == "En stock").sum()
max_disc   = filtered.desc_pct.max() if (filtered.desc_pct > 0).any() else 0
with_disc  = (filtered.desc_pct > 0).sum()
stock_pct  = round(in_stock / total * 100) if total else 0
success    = round((df.precio_cop > 0).sum() / len(df) * 100) if len(df) else 0
st.session_state.success_rate = success

def fmt_cop(n):
    if n is None or pd.isna(n): return "—"
    if n >= 1e6: return f"${n/1e6:.2f}M"
    if n >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:.0f}"

# ── Status bar ─────────────────────────────────────────────────────────────────
elapsed = int((time.time() - st.session_state.last_refresh) / 60)
elapsed_str = f"{elapsed}m" if elapsed < 60 else f"{elapsed//60}h"
cat_label = cat_sel if cat_sel != "Todas" else "Todas las categorías"

st.markdown(f"""
<div class="status-bar">
    <div class="breadcrumb">
        <span>/</span> <span>Dashboard</span> <span>/</span> <b>Overview</b>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Scraper</span>
        <span class="stat-value"><span class="run-dot"></span> running</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Último job</span>
        <span class="stat-value">{elapsed_str} · {_html.escape(query)}</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Éxito 24h</span>
        <span class="stat-value">{success}%</span>
    </div>
    <div class="stat-pill">
        <span class="stat-label">Filtrado</span>
        <span class="stat-value">{total} / {len(df)}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Page header ────────────────────────────────────────────────────────────────
ts_short = datetime.fromtimestamp(st.session_state.last_refresh).strftime("%H:%M")
st.markdown(f"""
<div class="page-head" style="position:relative;overflow:hidden;padding:20px 24px;
    background:radial-gradient(ellipse 60% 80% at 10% 50%, var(--accent-dim) 0%, transparent 70%);
    border:1px solid var(--border);border-radius:14px;margin-bottom:20px;">
    <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;
        background:radial-gradient(circle, var(--accent-dim) 0%, transparent 70%);
        pointer-events:none;"></div>
    <div>
        <div class="eyebrow">/ overview</div>
        <h1 class="page-title">{total} <span class="title-dim">productos rastreados</span></h1>
        <div class="page-sub">
            {_html.escape(cat_label)} · actualizado <span style="font-family:Geist Mono,monospace;color:var(--text)">{ts_short}</span>
            {"· " + str(len(marcas_sel)) + " marca" + ("s" if len(marcas_sel) != 1 else "") if marcas_sel else ""}
            {"· solo con descuento" if solo_dto else ""}
        </div>
    </div>
    <div class="live-badge"><span class="live-dot"></span> LIVE · Algolia</div>
</div>
""", unsafe_allow_html=True)

# ── KPI grid ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi" style="animation-delay:0.02s">
        <div class="kpi-label">Productos</div>
        <div class="kpi-value">{total:,}</div>
        <div class="kpi-foot"><span>de {len(df):,}</span></div>
    </div>
    <div class="kpi" style="animation-delay:0.06s">
        <div class="kpi-label">Precio promedio</div>
        <div class="kpi-value">{fmt_cop(avg_p)}</div>
        <div class="kpi-foot"><span>mediana filtrada</span></div>
    </div>
    <div class="kpi" style="animation-delay:0.10s">
        <div class="kpi-label">Mejor oferta</div>
        <div class="kpi-value">{fmt_cop(min_p)}</div>
        <div class="kpi-foot"><span class="kpi-delta good">mín. filtrado</span></div>
    </div>
    <div class="kpi" style="animation-delay:0.14s">
        <div class="kpi-label">Mayor dto.</div>
        <div class="kpi-value">{max_disc}%</div>
        <div class="kpi-foot"><span>{with_disc} con descuento</span></div>
    </div>
    <div class="kpi" style="animation-delay:0.18s">
        <div class="kpi-label">En stock</div>
        <div class="kpi-value">{in_stock}/{total}</div>
        <div class="kpi-foot"><span>{stock_pct}% disponible</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
BG, GRID = "rgba(0,0,0,0)", "rgba(255,255,255,0.05)"
FONT, FONT_T = "rgba(255,255,255,0.4)", "rgba(255,255,255,0.85)"
hue = st.session_state.accent_hue
ACCENT = f"oklch(0.76 0.15 {hue})"
ACCENT_HEX = "#F4A855" if hue == 55 else f"hsl({hue}, 80%, 60%)"
ACCENT_DARK = f"hsl({max(0,hue-10)}, 70%, 40%)"

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="panel" style="margin-bottom:0">
        <div class="panel-head">
            <span class="panel-title">Distribución de precios</span>
            <span class="panel-sub">{total} items · 24 bins</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    fig1 = go.Figure(go.Histogram(
        x=filtered.precio_cop, nbinsx=24,
        marker=dict(color=ACCENT_HEX, line=dict(color=ACCENT_DARK, width=1), opacity=0.9),
        hovertemplate="<b>$%{x:,.0f}</b><br>%{y} productos<extra></extra>",
    ))
    fig1.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=FONT, family="Geist Mono", size=10),
        margin=dict(t=8, b=8, l=8, r=8), height=220,
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickprefix="$", tickformat=",.0f"),
        yaxis=dict(gridcolor=GRID, linecolor=GRID),
        hoverlabel=dict(bgcolor="#2a1b08", bordercolor=ACCENT_HEX, font=dict(color="white", family="Geist Mono")),
    )
    st.plotly_chart(fig1, width="stretch", config={"displayModeBar": False})

with col2:
    st.markdown("""
    <div class="panel" style="margin-bottom:0">
        <div class="panel-head">
            <span class="panel-title">Top marcas</span>
            <span class="panel-sub">por cantidad</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    top_brands = filtered.marca.value_counts().head(10).reset_index()
    top_brands.columns = ["marca", "cantidad"]
    fig2 = go.Figure(go.Bar(
        y=top_brands["marca"], x=top_brands["cantidad"],
        orientation="h",
        marker=dict(
            color=top_brands["cantidad"],
            colorscale=[[0, ACCENT_DARK], [1, ACCENT_HEX]],
            line=dict(color=ACCENT_DARK, width=1),
        ),
        hovertemplate="<b>%{y}</b><br>%{x} productos<extra></extra>",
    ))
    fig2.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=FONT, family="Geist Mono", size=10),
        margin=dict(t=8, b=8, l=8, r=8), height=220,
        xaxis=dict(gridcolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, autorange="reversed"),
        hoverlabel=dict(bgcolor="#2a1b08", bordercolor=ACCENT_HEX, font=dict(color="white", family="Geist Mono")),
    )
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

# ── Top descuentos ─────────────────────────────────────────────────────────────
top_disc = filtered[filtered.desc_pct > 0].nlargest(10, "desc_pct")
if not top_disc.empty:
    max_d = top_disc.desc_pct.max()
    st.markdown(f"""
    <div class="sec">
        <span class="sec-title">Top descuentos activos</span>
        <div class="sec-line"></div>
        <span class="sec-count">{len(top_disc)} productos</span>
    </div>
    """, unsafe_allow_html=True)
    bars_html = '<div class="panel"><div class="disc-list">'
    for i, (_, r) in enumerate(top_disc.iterrows()):
        name = _html.escape(str(r["nombre"])[:70] + ("…" if len(str(r["nombre"])) > 70 else ""))
        w = int((r.desc_pct / max_d) * 100)
        bars_html += f"""
        <div class="disc-row" style="animation-delay:{i*0.03:.2f}s">
            <span class="disc-name">{name}</span>
            <div class="disc-track"><div class="disc-fill" style="width:{w}%"></div></div>
            <span class="disc-pct">-{r.desc_pct}%</span>
        </div>"""
    bars_html += "</div></div>"
    st.markdown(bars_html, unsafe_allow_html=True)

# ── Mejores ofertas ────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec"><span class="sec-title">Mejores ofertas</span><div class="sec-line"></div></div>
""", unsafe_allow_html=True)

highlights = (filtered[filtered.desc_pct > 0].nlargest(6, "desc_pct")
              if (filtered.desc_pct > 0).any()
              else filtered.nsmallest(6, "precio_cop"))

cards_html = '<div class="panel"><div class="prod-grid">'
for i, (_, r) in enumerate(highlights.iterrows()):
    old_h = (f'<div class="prod-old">${r.get("precio_original_cop", 0):,.0f}</div>'
             if r.get("precio_original_cop", 0) and r.get("precio_original_cop", 0) > r.precio_cop else "")
    badge_h = (f'<span class="badge-discount">{_html.escape(str(r.get("descuento","")).strip())}</span>'
               if str(r.get("descuento", "")).strip() else "")
    rat = r.get("rating", 0)
    rat_h = f'<div class="prod-rating">★ {rat:.1f}</div>' if rat and rat > 0 else ""
    cards_html += f"""
    <a class="prod-link" href="{_html.escape(str(r.get('url',''))).strip()}" target="_blank" rel="noopener noreferrer">
        <div class="prod-card" style="animation-delay:{i*0.05:.2f}s">
            <div class="prod-rank">#{i+1}</div>
            <div class="prod-brand">{_html.escape(str(r.get('marca','') or '—').strip())}</div>
            <div class="prod-name">{_html.escape(str(r.get('nombre','')))}</div>
            <div class="prod-bottom">
                <div class="prod-price-block">{old_h}<div class="prod-price">${r.precio_cop:,.0f}</div></div>
                {badge_h}
            </div>{rat_h}
        </div>
    </a>"""
cards_html += "</div></div>"
st.markdown(cards_html, unsafe_allow_html=True)

# ── Catálogo completo ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="sec">
    <span class="sec-title">Catálogo completo</span>
    <div class="sec-line"></div>
    <span class="sec-count">{total} resultados</span>
</div>
""", unsafe_allow_html=True)

disp = filtered[["nombre", "marca", "precio_cop", "precio_original_cop", "descuento", "rating", "disponibilidad"]].copy()
disp["precio_cop"] = disp["precio_cop"].apply(lambda x: f"${x:,.0f}")
disp["precio_original_cop"] = disp["precio_original_cop"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x else "—")
disp["rating"] = disp["rating"].apply(lambda x: f"★ {x:.1f}" if x and x > 0 else "—")
disp["disponibilidad"] = disp["disponibilidad"].apply(lambda x: "✓ stock" if x == "En stock" else "✗ agotado")
disp.columns = ["Producto", "Marca", "Precio", "Precio antes", "Descuento", "Rating", "Stock"]
st.dataframe(disp, use_container_width=True, hide_index=True,
             column_config={"Producto": st.column_config.TextColumn(width="large")})

# ── Export ─────────────────────────────────────────────────────────────────────
st.markdown("""<div class="sec"><span class="sec-title">Exportar</span><div class="sec-line"></div></div>""",
            unsafe_allow_html=True)

d1, d2 = st.columns(2)
with d1:
    st.download_button("⬇ CSV", data=filtered.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"alkosto_{query}.csv", mime="text/csv", use_container_width=True)
with d2:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        filtered.to_excel(w, index=False, sheet_name="Productos")
        for col in w.sheets["Productos"].columns:
            w.sheets["Productos"].column_dimensions[col[0].column_letter].width = (
                max(len(str(c.value or "")) for c in col) + 4)
    st.download_button("⬇ Excel", data=buf.getvalue(), file_name=f"alkosto_{query}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:28px 0 12px;border-top:1px solid var(--border);
color:var(--text-dimmer);font-size:11px;margin-top:36px;font-family:'Geist Mono',monospace">
    pricewatch · scraper console &nbsp;·&nbsp; <b style="color:var(--accent)">Algolia API</b> &nbsp;·&nbsp; 🇨🇴 Colombia
</div>
""", unsafe_allow_html=True)
