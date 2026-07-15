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

# ==================== CONFIGURATION ====================
st.set_page_config(
    page_title="IoT Surveillance ESP32S2",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONSTANTES THINGSPEAK ====================
# Channel de données (mesures)
THINGSPEAK_CHANNEL_ID = "3428306"
THINGSPEAK_READ_API = "https://api.thingspeak.com/channels/3428306/feeds.json?api_key=UIWSRR7X029RCD5V&results=2"
THINGSPEAK_WRITE_API = "https://api.thingspeak.com/update?api_key=P1FHXPEIAOB3GI6T&field1=0"

# Channel de configuration (seuils)
THINGSPEAK_CONFIG_CHANNEL_ID = "3428310"
THINGSPEAK_CONFIG_READ_API = "https://api.thingspeak.com/channels/3428310/feeds.json?api_key=F54BNJ6PACIS3OKD&results=2"
THINGSPEAK_CONFIG_WRITE_API = "https://api.thingspeak.com/update?api_key=K7TDWWD0WEQN97RR&field1=0"

# URLs ThingSpeak
THINGSPEAK_API_URL = "https://api.thingspeak.com"

# ==================== FONCTIONS API ====================
def get_latest_data():
    """Récupère les dernières données du ESP32"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json"
        params = {"api_key": THINGSPEAK_READ_API}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "voltage": float(data.get("field1", 0) or 0),
                "current": float(data.get("field2", 0) or 0),
                "power": float(data.get("field3", 0) or 0),
                "relay": bool(int(data.get("field4", 0) or 0)),
                "timestamp": data.get("created_at", "")
            }
        return None
    except Exception as e:
        st.error(f"Erreur récupération données: {e}")
        return None

def get_historical_data(hours=24):
    """Récupère les données historiques"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"
        params = {
            "api_key": THINGSPEAK_READ_API,
            "results": min(hours * 4, 8000)  # 4 mesures/heure
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
            "api_key": THINGSPEAK_CONFIG_WRITE_API,
            "field1": voltage_threshold,
            "field2": current_threshold,
            "field3": power_threshold,
            "field4": "1" if relay_state else "0"
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Erreur envoi configuration: {e}")
        return False

def get_current_config():
    """Récupère la configuration actuelle"""
    try:
        url = f"{THINGSPEAK_API_URL}/channels/{THINGSPEAK_CONFIG_CHANNEL_ID}/feeds/last.json"
        params = {"api_key": THINGSPEAK_CONFIG_READ_API}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "voltage_threshold": float(data.get("field1", 240) or 240),
                "current_threshold": float(data.get("field2", 15) or 15),
                "power_threshold": float(data.get("field3", 3000) or 3000),
                "relay_command": bool(int(data.get("field4", 0) or 0))
            }
        return None
    except Exception as e:
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
    .success-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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
st.markdown("---")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Statut connexion
    st.subheader("📡 Statut Système")
    data = get_latest_data()
    
    if data:
        st.success("✅ ESP32S2 Connecté")
        st.caption(f"Dernière mise à jour: {data['timestamp']}")
    else:
        st.error("❌ ESP32S2 Déconnecté")
    
    st.divider()
    
    # Configuration seuils
    st.subheader("🔧 Seuils de Découpage")
    
    config = get_current_config()
    
    voltage_threshold = st.slider(
        "⚡ Seuil Tension (V)",
        min_value=0.0,
        max_value=260.0,
        value=config["voltage_threshold"] if config else 240.0,
        step=1.0,
        help="Coupe le relais si tension > seuil"
    )
    
    current_threshold = st.slider(
        "🔌 Seuil Courant (A)",
        min_value=0.0,
        max_value=30.0,
        value=config["current_threshold"] if config else 15.0,
        step=0.5,
        help="Coupe le relais si courant > seuil"
    )
    
    power_threshold = st.slider(
        "📊 Seuil Puissance (W)",
        min_value=0,
        max_value=5000,
        value=int(config["power_threshold"]) if config else 3000,
        step=100,
        help="Coupe le relais si puissance > seuil"
    )
    
    st.divider()
    
    # Contrôle relais
    st.subheader("🔌 Contrôle Relais")
    
    relay_command = st.toggle(
        "Relais Marche/Arrêt",
        value=config["relay_command"] if config else False,
        help="Active/désactive manuellement le relais"
    )
    
    if st.button("📤 Appliquer Configuration", type="primary", use_container_width=True):
        with st.spinner("Envoi en cours..."):
            success = send_config_to_thingspeak(
                voltage_threshold,
                current_threshold,
                power_threshold,
                relay_command
            )
            if success:
                st.success("Configuration envoyée!")
                st.rerun()
            else:
                st.error("Erreur d'envoi")
    
    st.divider()
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()

# ==================== MAIN CONTENT ====================
if data:
    # Vérification des alertes
    alerts = []
    if data["voltage"] > voltage_threshold:
        alerts.append(f"⚠️ Tension trop élevée: {data['voltage']:.1f}V > {voltage_threshold:.1f}V")
    if data["current"] > current_threshold:
        alerts.append(f"⚠️ Courant trop élevé: {data['current']:.2f}A > {current_threshold:.2f}A")
    if data["power"] > power_threshold:
        alerts.append(f"⚠️ Puissance trop élevée: {data['power']:.1f}W > {power_threshold:.1f}W")
    
    if alerts:
        for alert in alerts:
            st.markdown(f'<div class="alert-box">{alert}</div>', unsafe_allow_html=True)
    
    # Métriques principales
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
    
    # Graphiques
    tab1, tab2, tab3 = st.tabs(["📈 Temps Réel", "📊 Historique", "📉 Analyse"])
    
    with tab1:
        st.subheader("Données en Temps Réel")
        
        # Gauge charts
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
        st.subheader("Données Historiques")
        
        hours = st.selectbox("Période", [6, 12, 24, 48, 72], index=2)
        
        df = get_historical_data(hours)
        
        if df is not None and not df.empty:
            # Graphique tension
            fig_v = px.line(df, x="created_at", y="voltage", 
                           title="Évolution de la Tension",
                           labels={"created_at": "Temps", "voltage": "Tension (V)"},
                           color_discrete_sequence=["#FF6B35"])
            fig_v.add_hline(y=voltage_threshold, line_dash="dash", 
                           line_color="red", annotation_text="Seuil")
            st.plotly_chart(fig_v, use_container_width=True)
            
            # Graphique courant
            fig_i = px.line(df, x="created_at", y="current",
                           title="Évolution du Courant",
                           labels={"created_at": "Temps", "current": "Courant (A)"},
                           color_discrete_sequence=["#4ECDC4"])
            fig_i.add_hline(y=current_threshold, line_dash="dash",
                           line_color="red", annotation_text="Seuil")
            st.plotly_chart(fig_i, use_container_width=True)
            
            # Graphique puissance
            fig_p = px.line(df, x="created_at", y="power",
                           title="Évolution de la Puissance",
                           labels={"created_at": "Temps", "power": "Puissance (W)"},
                           color_discrete_sequence=["#9B59B6"])
            fig_p.add_hline(y=power_threshold, line_dash="dash",
                           line_color="red", annotation_text="Seuil")
            st.plotly_chart(fig_p, use_container_width=True)
            
            # Statistiques
            st.subheader("📊 Statistiques")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tension Moyenne", f"{df['voltage'].mean():.1f} V")
            with col2:
                st.metric("Courant Moyen", f"{df['current'].mean():.2f} A")
            with col3:
                st.metric("Puissance Moyenne", f"{df['power'].mean():.1f} W")
            with col4:
                st.metric("Nombre de mesures", len(df))
        else:
            st.info("Aucune donnée historique disponible")
    
    with tab3:
        st.subheader("Analyse Détaillée")
        
        # Puissance vs Temps avec zones
        if df is not None and not df.empty:
            fig_analysis = go.Figure()
            
            fig_analysis.add_trace(go.Scatter(
                x=df["created_at"],
                y=df["power"],
                mode="lines",
                name="Puissance",
                line=dict(color="#9B59B6", width=2)
            ))
            
            fig_analysis.add_hrect(
                y0=0, y1=power_threshold,
                fillcolor="green", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Zone normale"
            )
            
            fig_analysis.add_hrect(
                y0=power_threshold, y1=5000,
                fillcolor="red", opacity=0.1,
                layer="below", line_width=0,
                annotation_text="Zone dangereuse"
            )
            
            fig_analysis.update_layout(
                title="Analyse de Puissance avec Zones",
                xaxis_title="Temps",
                yaxis_title="Puissance (W)",
                height=400
            )
            
            st.plotly_chart(fig_analysis, use_container_width=True)
            
            # Courbe V-I
            fig_vi = px.scatter(df, x="voltage", y="current",
                               title="Relation Tension-Courant",
                               labels={"voltage": "Tension (V)", "current": "Courant (A)"},
                               color="power",
                               color_continuous_scale="Viridis")
            st.plotly_chart(fig_vi, use_container_width=True)

else:
    # Écran de connexion
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
<div style='text-align: center; color: #666;'>
    <p>IoT Surveillance System | ESP32S2 + ZMPT101B + SCT-013</p>
    <p>Développé avec Streamlit | Données via ThingSpeak</p>
</div>
""", unsafe_allow_html=True)
