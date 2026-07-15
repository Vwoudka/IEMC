"""
Système de Surveillance IoT - ESP32S2
Application Streamlit pour monitoring et contrôle
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import os

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="IoT Surveillance ESP32S2",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONSTANTES THINGSPEAK ====================
# IMPORTANT: Juste les API keys, PAS les URLs complètes!

# Channel 1 - Données (mesures ESP32)
THINGSPEAK_CHANNEL_ID = "3428306"
THINGSPEAK_READ_API_KEY = "UIWSRR7X029RCD5V"
THINGSPEAK_WRITE_API_KEY = "P1FHXPEIAOB3GI6T"

# Channel 2 - Configuration (seuils)
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
            
            # ThingSpeak retourne TOUJOURS un JSON, même sans données
            # Vérifier si field1 et field2 sont vides, nuls, ou "0"
            f1 = data.get("field1")
            f2 = data.get("field2")
            
            # Pas de données si les champs sont None, vides, ou "0"
            has_data = (
                f1 is not None and 
                f1 != "" and 
                f1 != "0" and
                f2 is not None and 
                f2 != "" and
                f2 != "0"
            )
            
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
    except Exception as e:
        st.error(f"Erreur récupération données: {e}")
        return None

def get_historical_data(days=7):
    """Récupère les données historiques par jour"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
        params = {
            "api_key": THINGSPEAK_READ_API_KEY,
            "days": days
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            feeds = data.get("feeds", [])
            
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
    except Exception as e:
        st.error(f"Erreur récupération historique: {e}")
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
        
        print(f"[DEBUG] Sending to ThingSpeak: {data}")  # Debug console
        
        response = requests.post(url, data=data, timeout=10)
        
        print(f"[DEBUG] Response: {response.status_code} - {response.text}")  # Debug console
        
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")  # Debug console
        st.error(f"Erreur envoi configuration: {e}")
        return False

def get_current_config():
    """Récupère la configuration actuelle depuis ThingSpeak"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CONFIG_CHANNEL_ID}/feeds/last.json"
        params = {"api_key": THINGSPEAK_CONFIG_READ_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Même logique: vérifier si les données sont réelles
            f1 = data.get("field1")
            f2 = data.get("field2")
            
            has_config = (
                f1 is not None and 
                f1 != "" and
                f2 is not None and 
                f2 != ""
            )
            
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

# ==================== CSS CUSTOM ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .alert-box {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    .relay-on {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .relay-off {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown('<div class="main-header">⚡ Système de Surveillance IoT ESP32S2</div>', unsafe_allow_html=True)
st.markdown("**Capteurs:** ZMPT101B (Tension) + SCT-013 (Courant) | **Contrôle:** Relais GPIO 18")
st.markdown("**Architecture:** ESP32S2 → ThingSpeak → Streamlit (ce site)")
st.markdown("---")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📡 Statut Système")
    data = get_latest_data()
    
    if data:
        st.success("✅ ESP32S2 Connecté")
        st.caption(f"Dernière: {data['timestamp']}")
    else:
        st.error("❌ ESP32S2 Déconnecté")
    
    st.divider()
    
    st.subheader("🔧 Seuils de Découpage")
    st.caption("Entrez les valeurs puis cliquez Appliquer")
    
    config = get_current_config()
    
    voltage_threshold = st.number_input(
        "⚡ Seuil Tension (V)",
        min_value=0.0,
        max_value=260.0,
        value=float(config["voltage_threshold"]) if config else 240.0,
        step=1.0,
        format="%.1f"
    )
    
    current_threshold = st.number_input(
        "🔌 Seuil Courant (A)",
        min_value=0.0,
        max_value=100.0,
        value=float(config["current_threshold"]) if config else 15.0,
        step=0.1,
        format="%.2f"
    )
    
    power_threshold = st.number_input(
        "📊 Seuil Puissance (W)",
        min_value=0,
        max_value=50000,
        value=int(config["power_threshold"]) if config else 3000,
        step=10
    )
    
    st.divider()
    
    st.subheader("🔌 Contrôle Relais")
    
    relay_command = st.toggle(
        "Relais Marche/Arrêt",
        value=bool(config["relay_command"]) if config else False
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⚡ Allumer Relais", type="primary", use_container_width=True):
            with st.spinner("Envoi..."):
                success = send_config_to_thingspeak(
                    voltage_threshold,
                    current_threshold,
                    power_threshold,
                    True
                )
                if success:
                    st.success("Relais ON envoyé!")
                else:
                    st.error("Erreur")
    
    with col2:
        if st.button("🔴 Éteindre Relais", use_container_width=True):
            with st.spinner("Envoi..."):
                success = send_config_to_thingspeak(
                    voltage_threshold,
                    current_threshold,
                    power_threshold,
                    False
                )
                if success:
                    st.success("Relais OFF envoyé!")
                else:
                    st.error("Erreur")
    
    if st.button("📤 Appliquer Tout", use_container_width=True):
        with st.spinner("Envoi en cours..."):
            success = send_config_to_thingspeak(
                voltage_threshold,
                current_threshold,
                power_threshold,
                relay_command
            )
            if success:
                st.success("Configuration envoyée!")
            else:
                st.error("Erreur d'envoi")
    
    st.divider()
    
    auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()

# ==================== MAIN CONTENT ====================
if data:
    alerts = []
    if voltage_threshold > 0 and data["voltage"] > voltage_threshold:
        alerts.append(f"⚠️ Tension trop élevée: {data['voltage']:.1f}V > {voltage_threshold:.1f}V")
    if current_threshold > 0 and data["current"] > current_threshold:
        alerts.append(f"⚠️ Courant trop élevé: {data['current']:.2f}A > {current_threshold:.2f}A")
    if power_threshold > 0 and data["power"] > power_threshold:
        alerts.append(f"⚠️ Puissance trop élevée: {data['power']:.1f}W > {power_threshold:.1f}W")
    
    for alert in alerts:
        st.markdown(f'<div class="alert-box">{alert}</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⚡ Tension</div>
            <div class="metric-value">{data['voltage']:.1f} V</div>
            <div class="metric-label">Seuil: {voltage_threshold:.1f}V</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🔌 Courant</div>
            <div class="metric-value">{data['current']:.2f} A</div>
            <div class="metric-label">Seuil: {current_threshold:.2f}A</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 Puissance</div>
            <div class="metric-value">{data['power']:.1f} W</div>
            <div class="metric-label">Seuil: {power_threshold:.1f}W</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        relay_status = "🟢 RELAIS ON" if data["relay"] else "🔴 RELAIS OFF"
        relay_class = "relay-on" if data["relay"] else "relay-off"
        st.markdown(f"""
        <div class="{relay_class}">
            {relay_status}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📈 Temps Réel", "📊 Historique (par Jour)", "📉 Analyse"])
    
    with tab1:
        st.subheader("Données en Temps Réel")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_voltage = go.Figure(go.Indicator(
                mode="gauge+number",
                value=data["voltage"],
                title={"text": "Tension (V)"},
                gauge={
                    "axis": {"range": [0, 260]},
                    "bar": {"color": "#FF6B35"},
                    "steps": [
                        {"range": [0, voltage_threshold], "color": "#90EE90"},
                        {"range": [voltage_threshold, 260], "color": "#FF6B6B"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": voltage_threshold
                    }
                }
            ))
            fig_voltage.update_layout(height=300)
            st.plotly_chart(fig_voltage, use_container_width=True)
        
        with col2:
            fig_current = go.Figure(go.Indicator(
                mode="gauge+number",
                value=data["current"],
                title={"text": "Courant (A)"},
                gauge={
                    "axis": {"range": [0, 30]},
                    "bar": {"color": "#4ECDC4"},
                    "steps": [
                        {"range": [0, current_threshold], "color": "#90EE90"},
                        {"range": [current_threshold, 30], "color": "#FF6B6B"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": current_threshold
                    }
                }
            ))
            fig_current.update_layout(height=300)
            st.plotly_chart(fig_current, use_container_width=True)
        
        with col3:
            fig_power = go.Figure(go.Indicator(
                mode="gauge+number",
                value=data["power"],
                title={"text": "Puissance (W)"},
                gauge={
                    "axis": {"range": [0, 5000]},
                    "bar": {"color": "#9B59B6"},
                    "steps": [
                        {"range": [0, power_threshold], "color": "#90EE90"},
                        {"range": [power_threshold, 5000], "color": "#FF6B6B"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": power_threshold
                    }
                }
            ))
            fig_power.update_layout(height=300)
            st.plotly_chart(fig_power, use_container_width=True)
    
    with tab2:
        st.subheader("Données Historiques par Jour")
        
        days = st.selectbox("Période (jours)", [1, 3, 7, 14, 30], index=2)
        
        df = get_historical_data(days)
        
        if df is not None and not df.empty:
            unique_dates = sorted(df["date"].unique())
            
            st.info(f"📊 {len(unique_dates)} jour(s) de données | {len(df)} mesures au total")
            
            for date in unique_dates:
                day_df = df[df["date"] == date]
                
                st.markdown(f"### 📅 {date}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tension Moy.", f"{day_df['voltage'].mean():.1f} V")
                with col2:
                    st.metric("Courant Moy.", f"{day_df['current'].mean():.2f} A")
                with col3:
                    st.metric("Puissance Moy.", f"{day_df['power'].mean():.1f} W")
                with col4:
                    st.metric("Mesures", len(day_df))
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=day_df["created_at"],
                    y=day_df["voltage"],
                    name="Tension (V)",
                    line=dict(color="#FF6B35", width=2),
                    yaxis="y"
                ))
                
                fig.add_trace(go.Scatter(
                    x=day_df["created_at"],
                    y=day_df["current"],
                    name="Courant (A)",
                    line=dict(color="#4ECDC4", width=2),
                    yaxis="y2"
                ))
                
                fig.add_trace(go.Scatter(
                    x=day_df["created_at"],
                    y=day_df["power"],
                    name="Puissance (W)",
                    line=dict(color="#9B59B6", width=2, dash="dot"),
                    yaxis="y3"
                ))
                
                fig.update_layout(
                    title=f"Mesures du {date}",
                    xaxis_title="Heure",
                    yaxis=dict(
                        title="Tension (V)",
                        titlefont=dict(color="#FF6B35"),
                        tickfont=dict(color="#FF6B35")
                    ),
                    yaxis2=dict(
                        title="Courant (A)",
                        titlefont=dict(color="#4ECDC4"),
                        tickfont=dict(color="#4ECDC4"),
                        overlaying="y",
                        side="right"
                    ),
                    yaxis3=dict(
                        title="Puissance (W)",
                        titlefont=dict(color="#9B59B6"),
                        tickfont=dict(color="#9B59B6"),
                        overlaying="y",
                        side="right"
                    ),
                    height=350,
                    legend=dict(x=0, y=1.12, orientation="h")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander(f"📋 Voir les données du {date}"):
                    display_df = day_df[["created_at", "voltage", "current", "power", "relay"]].copy()
                    display_df["created_at"] = display_df["created_at"].dt.strftime("%H:%M:%S")
                    display_df.columns = ["Heure", "Tension (V)", "Courant (A)", "Puissance (W)", "Relais"]
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
        else:
            st.warning("Aucune donnée historique disponible")
            st.info("Vérifiez que l'ESP32 envoie des données à ThingSpeak")
    
    with tab3:
        st.subheader("Analyse Détaillée")
        
        if df is not None and not df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig_power = go.Figure()
                
                fig_power.add_trace(go.Scatter(
                    x=df["created_at"],
                    y=df["power"],
                    mode="lines",
                    name="Puissance",
                    line=dict(color="#9B59B6", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(155, 89, 182, 0.2)"
                ))
                
                fig_power.add_hline(y=power_threshold, line_dash="dash",
                                   line_color="red", annotation_text="Seuil")
                
                fig_power.update_layout(
                    title="Puissance avec Seuil",
                    xaxis_title="Temps",
                    yaxis_title="Puissance (W)",
                    height=400
                )
                
                st.plotly_chart(fig_power, use_container_width=True)
            
            with col2:
                fig_vi = px.scatter(
                    df, 
                    x="voltage", 
                    y="current",
                    title="Relation Tension-Courant",
                    labels={"voltage": "Tension (V)", "current": "Courant (A)"},
                    color="power",
                    color_continuous_scale="Viridis",
                    opacity=0.6
                )
                fig_vi.update_layout(height=400)
                st.plotly_chart(fig_vi, use_container_width=True)
            
            st.subheader("📊 Statistiques Globales")
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("Tension Min", f"{df['voltage'].min():.1f} V")
            with col2:
                st.metric("Tension Max", f"{df['voltage'].max():.1f} V")
            with col3:
                st.metric("Courant Min", f"{df['current'].min():.2f} A")
            with col4:
                st.metric("Courant Max", f"{df['current'].max():.2f} A")
            with col5:
                st.metric("Puissance Max", f"{df['power'].max():.1f} W")
            with col6:
                st.metric("Total Mesures", len(df))
        else:
            st.warning("Données insuffisantes pour l'analyse")

else:
    st.error("❌ Impossible de récupérer les données du ESP32S2")
    st.info("Vérifiez que:")
    st.markdown("""
    1. Le ESP32S2 est alimenté et connecté au WiFi
    2. Les IDs et API Keys ThingSpeak sont corrects
    3. Le ESP32 envoie bien les données (vérifiez le moniteur série)
    """)
    
    st.markdown("---")
    st.subheader("🔧 Configuration ThingSpeak")
    
    with st.expander("Instructions de configuration"):
        st.markdown("""
        ### 1. Créer un compte ThingSpeak
        - Allez sur [thingspeak.com](https://thingspeak.com)
        - Créez un compte gratuit
        
        ### 2. Créer le Channel de données
        - Channel > New Channel
        - Nom: "ESP32 Surveillance"
        - Fields: Tension, Courant, Puissance, Relais
        - Notez le Channel ID et Write API Key
        
        ### 3. Créer le Channel de configuration
        - Créez un 2ème channel
        - Fields: Seuil Tension, Seuil Courant, Seuil Puissance, Commande Relais
        - Notez le Channel ID et Write API Key
        
        ### 4. Mettre à jour le code
        - Dans le firmware ESP32, remplissez les constantes
        - Dans cette app, remplissez les constantes THINGSPEAK_*
        """)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p><strong>IoT Surveillance System</strong> | ESP32S2 + ZMPT101B + SCT-013</p>
    <p>Streamlit | ThingSpeak Cloud</p>
</div>
""", unsafe_allow_html=True)
