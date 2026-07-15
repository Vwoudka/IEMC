# Système de Surveillance IoT ESP32S2

## Architecture

```
┌─────────────┐    Analog    ┌─────────────┐    WiFi HTTP    ┌─────────────┐    API     ┌─────────────┐
│  ZMPT101B   │─────────────▶│             │────────────────▶│  ThingSpeak │◀───────────│  Streamlit  │
│  (Tension)  │              │   ESP32S2   │    POST Data    │   (Cloud)   │   GET Data │  (Web App)  │
├─────────────┤              │             │◀────────────────┤             │◀───────────┤             │
│  SCT-013    │─────────────▶│  Firmware   │    GET Config   │             │   POST     │  xxx.       │
│  (Courant)  │              │             │                 │             │   Config   │  streamlit  │
├─────────────┤              │             │                 └─────────────┘            │  .app       │
│   Relais    │◀─────────────│  GPIO 18    │                                            └─────────────┘
│  (Découpage)│              │             │
└─────────────┘              └─────────────┘
```

## Matériel Requis

| Composant | Quantité | Connexion ESP32S2 |
|-----------|----------|-------------------|
| ESP32S2 | 1 | - |
| ZMPT101B (Capteur Tension AC) | 1 | GPIO 1 (ADC1_CH0) |
| SCT-013 (Capteur Courant CT) | 1 | GPIO 2 (ADC1_CH1) |
| Module Relais 5V | 1 | GPIO 18 |
| Alimentation 5V | 1 | - |

## Schéma de Câblage

```
ESP32S2              Capteurs
─────────────────────────────────
GPIO 1 (ADC) ◄──── ZMPT101B (Tension)
GPIO 2 (ADC) ◄──── SCT-013 (Courant)
GPIO 18      ────▶ Module Relais
GND          ◄───► GND commun
3.3V         ────► Alimentation capteurs
```

## Configuration ThingSpeak

### Étape 1: Créer un compte
1. Allez sur https://thingspeak.com
2. Créez un compte gratuit

### Étape 2: Channel de données (Mesures)
1. **Channels > New Channel**
2. Nom: "ESP32 Surveillance Data"
3. Description: "Mesures tension, courant, puissance ESP32S2"
4. Fields:
   - Field 1: Tension (V)
   - Field 2: Courant (A)
   - Field 3: Puissance (W)
   - Field 4: État Relais (0/1)
5. Cliquez **Save Channel**
6. Notez: **Channel ID** et **Write API Key**

### Étape 3: Channel de configuration (Seuils)
1. Créez un 2ème channel
2. Nom: "ESP32 Configuration"
3. Fields:
   - Field 1: Seuil Tension Max (V)
   - Field 2: Seuil Courant Max (A)
   - Field 3: Seuil Puissance Max (W)
   - Field 4: Commande Relais (0/1)
4. Notez: **Channel ID** et **Write API Key**

### Étape 4: Générer une Read API Key
1. Sur chaque channel, allez dans **API Keys**
2. Notez la **Read API Key**

## Configuration du Firmare ESP32S2

Ouvrez `esp32_surveillance.ino` dans Arduino IDE et modifiez:

```cpp
// WiFi
const char* ssid = "VOTRE_SSID_WIFI";
const char* password = "VOTRE_MOT_DE_PASSE_WIFI";

// ThingSpeak - Channel de données
const char* THINGSPEAK_CHANNEL_ID = "123456";
const char* THINGSPEAK_READ_API = "VOTRE_READ_API_KEY";
const char* THINGSPEAK_WRITE_API = "VOTRE_WRITE_API_KEY";

// ThingSpeak - Channel de configuration
const char* THINGSPEAK_CONFIG_CHANNEL_ID = "789012";
const char* THINGSPEAK_CONFIG_READ_API = "VOTRE_CONFIG_READ_API_KEY";
const char* THINGSPEAK_CONFIG_WRITE_API = "VOTRE_CONFIG_WRITE_API_KEY";
```

## Installation du Firmare

### Prérequis
- Arduino IDE 2.x
- Support ESP32 installé

### Étapes
1. Ouvrez Arduino IDE
2. **Fichier > Exemple > ESP32 > Blink** (pour vérifier)
3. **Outils > Carte > ESP32 Arduino > ESP32S2 Dev Module**
4. Ouvrez `esp32_surveillance.ino`
5. Modifiez les constantes WiFi et ThingSpeak
6. **Vérifier et Compiler**
7. **Uploader**

## Déploiement Streamlit Cloud

### Étape 1: GitHub
1. Créez un dépôt GitHub
2. Poussez le dossier `streamlit_app/`
3. Vérifiez que `requirements.txt` est présent

### Étape 2: Streamlit Cloud
1. Allez sur https://share.streamlit.io
2. Connectez votre compte GitHub
3. Sélectionnez le dépôt et le fichier `app.py`
4. Cliquez **Deploy**
5. Votre app sera disponible sur `xxx.streamlit.app`

### Étape 3: Configuration
1. Dans `app.py`, modifiez les constantes ThingSpeak
2. Streamlit redéploye automatiquement

## Utilisation

### Dashboard Principal
- **Métriques en temps réel**: Tension, Courant, Puissance
- **État du relais**: ON/OFF avec indicateur visuel
- **Alertes**: Notifications si seuils dépassés

### Configuration des Seuils
1. Dans le panneau latéral, ajustez les curseurs
2. Cliquez **Appliquer Configuration**
3. Le ESP32 reçoit les nouveaux seuils sous 5 secondes

### Contrôle du Relais
1. Utilisez le bouton **Relais Marche/Arrêt**
2. Le changement est appliqué immédiatement
3. Le relais coupe automatiquement si seuil dépassé

### Historique
- Onglet **Historique**: Graphiques sur 6h, 12h, 24h, 48h, 72h
- Onglet **Analyse**: Relation tension-courant, zones de puissance

## Fonctionnement du Relais

Le relais se coupe automatiquement si:
- Tension > Seuil tension configuré
- COURANT > Seuil courant configuré
- Puissance > Seuil puissance configuré

Pour réactiver:
1. Corrigez la cause du dépassement
2. Réactivez via l'interface Streamlit
3. Le relais se réactive sous 5 secondes

## Dépannage

### ESP32 ne se connecte pas au WiFi
- Vérifiez le SSID et mot de passe
- Vérifiez la portée du routeur
- Regardez le moniteur série (115200 baud)

### Pas de données ThingSpeak
- Vérifiez les API Keys
- Vérifiez le Channel ID
- Vérifiez la connexion WiFi ESP32

### Streamlit ne se connecte pas
- Vérifiez les API Keys dans `app.py`
- Vérifiez que le ESP32 envoie des données
- Regardez les logs Streamlit Cloud

### Valeurs aberrantes
- Calibrez ZMPT101B: Ajustez `ZMPT101B_CALIBRATION`
- Calibrez SCT-013: Ajustez `SCT013_CALIBRATION`
- Vérifiez les connexions physiques

## Calibration des Capteurs

### ZMPT101B (Tension)
1. Mesurez la tension réelle avec un multimètre
2. Ajustez `ZMPT101B_CALIBRATION` dans le code
3. Formule: calibration = tension_reelle / lecture_brute

### SCT-013 (Courant)
1. Mesurez le courant réel avec une pince ampèremétrique
2. Ajustez `SCT013_CALIBRATION` dans le code
3. Formule: calibration = courant_reelle / lecture_brute

## License

Projet IoT - Système de Surveillance ESP32S2
