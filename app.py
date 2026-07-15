"""
Système de Surveillance IoT - ESP32S2
Application Streamlit pour monitoring et contrôle
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import math

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="IoT Surveillance ESP32S2",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CONSTANTES THINGSPEAK ====================
THINGSPEAK_CHANNEL_ID = "3428306"
THINGSPEAK_READ_API_KEY = "UIWSRR7X029RCD5V"
THINGSPEAK_WRITE_API_KEY = "P1FHXPEIAOB3GI6T"

THINGSPEAK_CONFIG_CHANNEL_ID = "3428310"
THINGSPEAK_CONFIG_READ_API_KEY = "F54BNJ6PACIS3OKD"
THINGSPEAK_CONFIG_WRITE_API_KEY = "K7TDWWD0WEQN97RR"

THINGSPEAK_API_URL = "https://api.thingspeak.com"

# ==================== FONCTIONS API ====================
def get_latest_data():
    """Récupère les dernières données du ESP32"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json"
        params = {"api_key": THINGSPEAK_READ_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            f1 = data.get("field1")
            f2 = data.get("field2")
            has_data = (f1 is not None and f1 != "" and f1 != "0" and
                       f2 is not None and f2 != "" and f2 != "0")
            if not has_data:
                return None
            return {
                "voltage": float(f1),
                "current": float(f2),
                "power": float(data.get("field3") or 0),
                "relay": bool(int(data.get("field4") or 0)),
                "timestamp": data.get("created_at", "")
            }
        return None
    except:
        return None

def get_historical_data(days=7):
    """Récupère les données historiques"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
        params = {"api_key": THINGSPEAK_READ_API_KEY, "days": days}
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            feeds = response.json().get("feeds", [])
            if feeds:
                df = pd.DataFrame(feeds)
                df["created_at"] = pd.to_datetime(df["created_at"])
                df["voltage"] = pd.to_numeric(df["field1"], errors="coerce")
                df["current"] = pd.to_numeric(df["field2"], errors="coerce")
                df["power"] = pd.to_numeric(df["field3"], errors="coerce")
                df["relay"] = pd.to_numeric(df["field4"], errors="coerce")
                df["date"] = df["created_at"].dt.date
                return df
        return None
    except:
        return None

def send_config_to_thingspeak(voltage_threshold, current_threshold, power_threshold, relay_state):
    """Envoie la configuration au ESP32"""
    try:
        url = f"{THINGSPEAK_API_URL}/update"
        data = {
            "api_key": THINGSPEAK_CONFIG_WRITE_API_KEY,
            "field1": voltage_threshold,
            "field2": current_threshold,
            "field3": power_threshold,
            "field4": "1" if relay_state else "0"
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_current_config():
    """Récupère la configuration actuelle depuis ThingSpeak"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CONFIG_CHANNEL_ID}/feeds/last.json"
        params = {"api_key": THINGSPEAK_CONFIG_READ_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            f1 = data.get("field1")
            f2 = data.get("field2")
            has_config = (f1 is not None and f1 != "" and f2 is not None and f2 != "")
            if not has_config:
                return None
            return {
                "voltage_threshold": float(f1),
                "current_threshold": float(f2),
                "power_threshold": float(data.get("field3") or 3000),
                "relay_command": bool(int(data.get("field4") or 0))
            }
        return None
    except:
        return None

# ==================== CSS Lovable-inspired ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg: #0a0e17;
    --surface: rgba(17, 24, 39, 0.75);
    --surface-2: #1f2937;
    --border: rgba(255,255,255,0.06);
    --accent: #22d3ee;
    --accent-dim: rgba(34, 211, 238, 0.15);
    --success: #34d399;
    --success-dim: rgba(52, 211, 153, 0.12);
    --warning: #fbbf24;
    --warning-dim: rgba(251, 191, 36, 0.12);
    --danger: #f87171;
    --danger-dim: rgba(248, 113, 113, 0.12);
    --text: #f1f5f9;
    --text-dim: #64748b;
    --radius: 16px;
}

.stApp {
    background: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
}

.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(60rem 40rem at 90% -10%, rgba(34, 211, 238, 0.08), transparent),
        radial-gradient(50rem 30rem at -10% 110%, rgba(251, 191, 36, 0.04), transparent);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stMain"] { position: relative; z-index: 1; }
[data-testid="stSidebar"] { background: rgba(10, 14, 23, 0.95) !important; border-right: 1px solid var(--border) !important; backdrop-filter: blur(20px); }
[data-testid="stSidebar"] [data-testid="stMarkdown"] { color: var(--text-dim); font-size: 13px; }
[data-testid="stSidebar"] label { color: var(--text) !important; font-family: 'Inter', sans-serif !important; font-size: 12px !important; }
[data-testid="stSidebar"] [data-testid="stMarkdown"] h3 { color: var(--accent) !important; font-size: 11px !important; letter-spacing: 0.15em; text-transform: uppercase; font-weight: 600; }

h1, h2, h3, h4, h5, h6, p, span, div, label { color: var(--text) !important; }
.stMarkdown p { color: var(--text-dim) !important; font-size: 13px; }

.panel {
    background: var(--surface);
    backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
}

.stat-chip {
    background: var(--surface);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    text-align: center;
}
.stat-chip .label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-dim);
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    margin-bottom: 4px;
}
.stat-chip .value {
    font-size: 1.25rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
}
.stat-chip .value.accent { color: var(--accent); }
.stat-chip .value.warning { color: var(--warning); }
.stat-chip .value.success { color: var(--success); }
.stat-chip .value.danger { color: var(--danger); }

.hero-power {
    background: var(--surface);
    backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-power .big-value {
    font-size: 4rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: var(--accent);
    line-height: 1;
    text-shadow: 0 0 30px rgba(34, 211, 238, 0.3);
}
.hero-power .unit {
    font-size: 1.5rem;
    color: var(--text-dim);
    margin-left: 8px;
    font-weight: 500;
}
.hero-power .subtitle {
    font-size: 11px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 8px;
}
.hero-power .status-line {
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 12px;
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 8px;
}
.live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success);
    animation: pulse-ring 2s ease-out infinite;
}
@keyframes pulse-ring {
    0%, 100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.6); }
    50% { box-shadow: 0 0 0 8px rgba(52, 211, 153, 0); }
}

.gauge-card {
    background: var(--surface);
    backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    text-align: center;
}
.gauge-card .gauge-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    font-weight: 600;
    margin-bottom: 12px;
}
.gauge-card .gauge-value {
    font-size: 1.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text);
}

.relay-panel {
    background: var(--surface);
    backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    border-left: 3px solid var(--danger);
}
.relay-panel.relay-on {
    border-left-color: var(--success);
}
.relay-panel .relay-status {
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 8px;
    display: inline-block;
}
.relay-panel .relay-status.on {
    background: var(--success-dim);
    color: var(--success);
}
.relay-panel .relay-status.off {
    background: var(--danger-dim);
    color: var(--danger);
}

.alert-box {
    background: var(--danger-dim);
    border: 1px solid rgba(248, 113, 113, 0.3);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    color: var(--danger);
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    color: var(--text-dim);
    font-weight: 600;
    margin-bottom: 12px;
}

.threshold-field {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.threshold-field .field-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-dim);
    font-weight: 500;
}
.threshold-field input {
    background: transparent;
    border: none;
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 600;
    width: 100%;
    outline: none;
}

.stButton > button {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent-dim) !important;
    border-color: rgba(34, 211, 238, 0.3) !important;
    color: var(--accent) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(34, 211, 238, 0.25) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-dim) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface-2) !important;
    color: var(--accent) !important;
}

.stNumberInput > div > div > input {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stNumberInput label {
    color: var(--text-dim) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

.stToggle > div > div > button {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
}
.stToggle > div > div > button[aria-checked="true"] {
    background: var(--accent-dim) !important;
    border-color: var(--accent) !important;
}

.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

.stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden;
}

.js-plotly-plot .plotly .modebar { display: none !important; }

.footer-text {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--text-dim);
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ==================== HEADER (Top Nav) ====================
data = get_latest_data()
config = get_current_config()
now = datetime.now().strftime("%H:%M:%S")

relay_on = config["relay_command"] if config else False

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; padding:0.75rem 1.5rem; background:rgba(10,14,23,0.85); backdrop-filter:blur(20px); border-bottom:1px solid var(--border); border-radius:0; margin:-1rem -1rem 1.5rem -1rem; position:sticky; top:0; z-index:100;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="width:36px; height:36px; background:var(--accent-dim); border:1px solid rgba(34,211,238,0.3); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px;">⚡</div>
        <div>
            <div style="font-size:14px; font-weight:600; color:var(--text); letter-spacing:-0.02em;">EnergyGuard</div>
            <div style="font-size:10px; color:var(--text-dim); font-family:monospace; text-transform:uppercase; letter-spacing:0.15em;">ESP32S2 SURVEILLANCE</div>
        </div>
    </div>
    <div style="display:flex; align-items:center; gap:16px; font-size:11px; color:var(--text-dim);">
        <div style="display:flex; align-items:center; gap:6px;">
            <span style="width:6px; height:6px; border-radius:50%; background:{'var(--success)' if data else 'var(--danger)'}; box-shadow:0 0 8px {'var(--success)' if data else 'var(--danger)'};"></span>
            <span style="color:{'var(--success)' if data else 'var(--danger)'};">{'EN LIGNE' if data else 'HORS LIGNE'}</span>
        </div>
        <div style="display:flex; align-items:center; gap:4px;">
            <span style="padding:4px 10px; background:var(--surface-2); border:1px solid var(--border); border-radius:6px; font-size:10px; text-transform:uppercase; letter-spacing:0.1em;">Relais</span>
            <span style="padding:4px 10px; font-size:11px; font-weight:600; color:{'var(--success)' if relay_on else 'var(--danger)'};">{'ACTIF' if relay_on else 'COUPÉ'}</span>
        </div>
        <div style="font-family:monospace; font-size:11px; color:var(--text-dim);">{now}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== MAIN CONTENT ====================
if data:
    # Alertes
    alerts = []
    v_thresh = config["voltage_threshold"] if config else 240
    i_thresh = config["current_threshold"] if config else 15
    p_thresh = config["power_threshold"] if config else 3000
    
    if v_thresh > 0 and data["voltage"] > v_thresh:
        alerts.append(f"Tension trop élevée: {data['voltage']:.1f}V > {v_thresh:.1f}V")
    if i_thresh > 0 and data["current"] > i_thresh:
        alerts.append(f"Courant trop élevé: {data['current']:.2f}A > {i_thresh:.2f}A")
    if p_thresh > 0 and data["power"] > p_thresh:
        alerts.append(f"Puissance trop élevée: {data['power']:.1f}W > {p_thresh:.1f}W")
    
    for alert in alerts:
        st.markdown(f'<div class="alert-box">⚠ {alert}</div>', unsafe_allow_html=True)

    # Header row
    col_title, col_chips = st.columns([3, 2])
    with col_title:
        st.markdown("""
        <div>
            <h2 style="font-size:1.5rem; font-weight:600; letter-spacing:-0.02em; margin:0;">Supervision temps réel</h2>
            <p style="font-size:12px; color:var(--text-dim); margin-top:4px;">ZMPT101B + SCT-013 · Échantillonnage 3s · ESP32S2</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_chips:
        st.markdown(f"""
        <div style="display:flex; gap:12px; justify-content:flex-end;">
            <div class="stat-chip">
                <div class="label">Énergie session</div>
                <div class="value accent">—</div>
            </div>
            <div class="stat-chip">
                <div class="label">Coût session</div>
                <div class="value warning">—</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Hero Power + Live indicator
    st.markdown(f"""
    <div class="hero-power" style="margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <div class="subtitle">Puissance instantanée</div>
                <div>
                    <span class="big-value">{data['power']:.1f}</span>
                    <span class="unit">W</span>
                </div>
                <div class="status-line">Fonctionnement nominal — mise à jour {data['timestamp'][-8:] if len(data['timestamp']) > 8 else now}</div>
            </div>
            <div class="live-badge">
                <span class="live-dot"></span>
                <span style="font-size:10px; color:var(--success); text-transform:uppercase; letter-spacing:0.1em; font-weight:500;">Flux en direct</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Grid layout
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Gauges
        g_col1, g_col2, g_col3 = st.columns(3)
        
        with g_col1:
            pct_v = min(1, data["voltage"] / 260) if v_thresh == 0 else min(1, data["voltage"] / v_thresh)
            st.markdown(f"""
            <div class="gauge-card">
                <div class="gauge-label">⚡ Tension</div>
                <svg viewBox="0 0 100 55" style="width:100%; max-width:160px;">
                    <path d="M 8 50 A 42 42 0 0 1 92 50" stroke="var(--surface-2)" stroke-width="8" fill="none" stroke-linecap="round"/>
                    <path d="M 8 50 A 42 42 0 0 1 92 50" stroke="var(--accent)" stroke-width="8" fill="none" stroke-linecap="round"
                        stroke-dasharray="{132 * pct_v} 132" style="filter:drop-shadow(0 0 6px var(--accent))"/>
                    <circle cx="50" cy="50" r="3" fill="var(--accent)"/>
                </svg>
                <div class="gauge-value" style="color:var(--accent);">{data['voltage']:.1f} <span style="font-size:12px; color:var(--text-dim);">V</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        with g_col2:
            pct_i = min(1, data["current"] / max(i_thresh, 30))
            st.markdown(f"""
            <div class="gauge-card">
                <div class="gauge-label">🔌 Courant</div>
                <svg viewBox="0 0 100 55" style="width:100%; max-width:160px;">
                    <path d="M 8 50 A 42 42 0 0 1 92 50" stroke="var(--surface-2)" stroke-width="8" fill="none" stroke-linecap="round"/>
                    <path d="M 8 50 A 42 42 0 0 1 92 50" stroke="var(--warning)" stroke-width="8" fill="none" stroke-linecap="round"
                        stroke-dasharray="{132 * pct_i} 132" style="filter:drop-shadow(0 0 6px var(--warning))"/>
                    <circle cx="50" cy="50" r="3" fill="var(--warning)"/>
                </svg>
                <div class="gauge-value" style="color:var(--warning);">{data['current']:.2f} <span style="font-size:12px; color:var(--text-dim);">A</span></div>
            </div>
            """, unsafe_allow_html=True)
        
        with g_col3:
            pct_p = min(1, data["power"] / max(p_thresh, 5000))
            st.markdown(f"""
            <div class="gauge-card">
                <div class="gauge-label">📊 Puissance</div>
                <svg viewBox="0 0 100 55" style="width:100%; max-width:160px;">
                    <path d="M 8 50 A 42 42 0 0 1 92 50" stroke="var(--surface-2)" stroke-width="8" fill="none" stroke-linecap="round"/>
                    <path d="M 8 50 A 42 42 0 0 1 92 50" stroke="var(--success)" stroke-width="8" fill="none" stroke-linecap="round"
                        stroke-dasharray="{132 * pct_p} 132" style="filter:drop-shadow(0 0 6px var(--success))"/>
                    <circle cx="50" cy="50" r="3" fill="var(--success)"/>
                </svg>
                <div class="gauge-value" style="color:var(--success);">{data['power']:.1f} <span style="font-size:12px; color:var(--text-dim);">W</span></div>
            </div>
            """, unsafe_allow_html=True)

        # Tabs
        tab1, tab2 = st.tabs(["📈 Temps Réel", "📊 Historique"])

        with tab1:
            df_hist = get_historical_data(1)
            if df_hist is not None and not df_hist.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_hist["created_at"], y=df_hist["power"],
                    mode="lines", name="Puissance",
                    line=dict(color="#22d3ee", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(34, 211, 238, 0.1)"
                ))
                fig.add_hline(y=p_thresh, line_dash="dash", line_color="#fbbf24", annotation_text="Seuil P")
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=40, r=20, t=10, b=30),
                    height=320,
                    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#64748b")),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#64748b")),
                    font=dict(family="Inter, sans-serif", color="#94a3b8"),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chargement des données temps réel...")

        with tab2:
            days = st.selectbox("Période (jours)", [1, 3, 7, 14, 30], index=2)
            df = get_historical_data(days)
            if df is not None and not df.empty:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Scatter(
                    x=df["created_at"], y=df["voltage"],
                    mode="lines", name="Tension (V)",
                    line=dict(color="#22d3ee", width=1.5),
                ), secondary_y=False)
                fig.add_trace(go.Scatter(
                    x=df["created_at"], y=df["power"],
                    mode="lines", name="Puissance (W)",
                    line=dict(color="#fbbf24", width=1.5, dash="dot"),
                ), secondary_y=True)
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=40, r=40, t=10, b=30),
                    height=350,
                    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#64748b")),
                    font=dict(family="Inter, sans-serif", color="#94a3b8"),
                    legend=dict(orientation="h", y=1.12, font=dict(size=10)),
                )
                fig.update_yaxes(title_text="Tension (V)", gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#22d3ee"), secondary_y=False)
                fig.update_yaxes(title_text="Puissance (W)", gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10, color="#fbbf24"), secondary_y=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune donnée historique disponible")

    # Right sidebar
    with col_side:
        # Relay control
        st.markdown(f"""
        <div class="relay-panel {'relay-on' if relay_on else ''}" style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                <div>
                    <div style="font-size:14px; font-weight:600; color:var(--text);">Gestion du circuit</div>
                    <div style="font-size:11px; color:var(--text-dim); margin-top:2px;">Override manuel actif</div>
                </div>
                <div style="width:40px; height:40px; border-radius:50%; background:{'var(--success-dim)' if relay_on else 'var(--danger-dim)'}; display:flex; align-items:center; justify-content:center; font-size:18px;">⚡</div>
            </div>
            <div style="text-align:center; margin-bottom:8px;">
                <span class="relay-status {'on' if relay_on else 'off'}">{'RELAY ACTIF' if relay_on else 'RELAY COUPÉ'}</span>
            </div>
            <div style="font-size:10px; color:var(--text-dim); text-align:center; font-family:monospace; text-transform:uppercase; letter-spacing:0.1em;">Lecture ThingSpeak ≈ 3s</div>
        </div>
        """, unsafe_allow_html=True)

        # Buttons relay
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("⚡ Allumer", type="primary", use_container_width=True):
                if config:
                    send_config_to_thingspeak(
                        config["voltage_threshold"], config["current_threshold"],
                        config["power_threshold"], True
                    )
                    st.rerun()
        with b_col2:
            if st.button("🔴 Couper", use_container_width=True):
                if config:
                    send_config_to_thingspeak(
                        config["voltage_threshold"], config["current_threshold"],
                        config["power_threshold"], False
                    )
                    st.rerun()

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

        # Thresholds
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span class="section-title" style="margin:0;">⚙ Seuils de sécurité</span>
        </div>
        """, unsafe_allow_html=True)

        v_thresh_input = st.number_input("U MAX (V)", value=float(config["voltage_threshold"]) if config else 240.0, step=1.0, format="%.1f")
        i_thresh_input = st.number_input("I MAX (A)", value=float(config["current_threshold"]) if config else 15.0, step=0.1, format="%.2f")
        p_thresh_input = st.number_input("P MAX (W)", value=int(config["power_threshold"]) if config else 3000, step=10)

        if st.button("💾 Enregistrer les seuils", use_container_width=True):
            relay_state = config["relay_command"] if config else False
            if send_config_to_thingspeak(v_thresh_input, i_thresh_input, p_thresh_input, relay_state):
                st.success("Seuils enregistrés!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Erreur d'envoi")

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

        # Historical table
        if df is not None and not df.empty:
            st.markdown('<div class="section-title">📋 Historique</div>', unsafe_allow_html=True)
            display_df = df[["created_at", "voltage", "current", "power", "relay"]].tail(20).copy()
            display_df["created_at"] = display_df["created_at"].dt.strftime("%H:%M:%S")
            display_df.columns = ["Heure", "U (V)", "I (A)", "P (W)", "Relay"]
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=300)

else:
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem;">
        <div style="font-size:4rem; margin-bottom:1rem;">📡</div>
        <h2 style="font-size:1.5rem; font-weight:600; color:var(--danger);">Hors ligne</h2>
        <p style="color:var(--text-dim); font-size:13px; max-width:400px; margin:1rem auto;">
            Impossible de récupérer les données du ESP32S2. Vérifiez que l'appareil est alimenté et connecté au WiFi.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("""
<div class="footer-text" style="margin-top:2rem; padding:1rem 0 0.5rem; border-top:1px solid var(--border);">
    <span>EnergyGuard · ESP32S2 · ZMPT101B + SCT-013 · ThingSpeak Cloud</span>
</div>
""", unsafe_allow_html=True)
