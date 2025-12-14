# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import time
import requests
from io import BytesIO
import smtplib
import ssl
from email.mime.text import MIMEText

# ------------------------------------------------------------
# CONFIG GÉNÉRALE
# ------------------------------------------------------------
st.set_page_config(page_title="Smart Sentinel", layout="wide")

# URL de base Firebase (sans .json à la fin)
FIREBASE_BASE_URL = "https://gng1503projet-default-rtdb.firebaseio.com"

# ------------------------------------------------------------
# CONFIG EMAIL (Gmail + mot de passe d’application)
# ------------------------------------------------------------
EMAIL_SENDER = "angeyvanmugisha@gmail.com"

EMAIL_PASSWORD = "wpzydztrfyaktcul"

EMAIL_RECIPIENT = "angeyvanmugisha@gmail.com"

# ------------------------------------------------------------
# AUTHENTIFICATION SIMPLE (ADMIN)
# ------------------------------------------------------------
ADMIN_PASSWORD = "admin123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_role" not in st.session_state:
    st.session_state.user_role = "admin"  # prêt pour rôles futurs

# flag pour éviter d'envoyer 1000 mails pendant un épisode critique
if "alert_email_sent" not in st.session_state:
    st.session_state.alert_email_sent = False

# ------------------------------------------------------------
# ÉTAT GLOBAL (valeurs par défaut)
# ------------------------------------------------------------
def init_state_if_absent(key, value):
    if key not in st.session_state:
        st.session_state[key] = value


# mode par défaut = Simulation
init_state_if_absent("mode", "Simulation")
init_state_if_absent("refresh_rate", 2)
init_state_if_absent("temp_min", 10)
init_state_if_absent("temp_max", 60)
# seulement un seuil haut pour le niveau
init_state_if_absent("lvl_max", 80)
init_state_if_absent(
    "history",
    pd.DataFrame(
        columns=["timestamp", "temperature", "level", "state_temp", "state_level"]
    ),
)
init_state_if_absent("esp_status", "Inconnu")
init_state_if_absent("esp_latency_ms", None)
init_state_if_absent("last_error", "")
init_state_if_absent("theme", "Sombre")  # Sombre ou Clair

# ------------------------------------------------------------
# CSS DYNAMIQUE (clair / sombre)
# ------------------------------------------------------------
css_dark = """
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400&display=swap" rel="stylesheet">
<style>
    * {
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 300 !important;
        letter-spacing: -0.01em;
    }

    html, body, .stApp {
        background: #020617 !important;
        color: #e5e7eb !important;
    }

    h1 {
        font-size: 3.2rem !important;
        font-weight: 300 !important;
        margin-bottom: 0.4rem !important;
        color: #f9fafb !important;
    }

    h2 {
        font-size: 2rem !important;
        font-weight: 300 !important;
        color: #e5e7eb !important;
    }

    h3 {
        font-size: 1.4rem !important;
        font-weight: 300 !important;
        color: #e5e7eb !important;
    }

    .login-title {
        font-size: 3.2rem !important;
        font-weight: 300 !important;
        margin-bottom: 0.4rem !important;
        color: #f9fafb !important;
    }

    .card {
        background: #020617;
        border-radius: 4px;
        padding: 18px 20px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
        border: 1px solid rgba(30, 64, 175, 0.4);
    }

    .soft-divider {
        border-bottom: 1px solid rgba(148, 163, 184, 0.35);
        margin: 0.6rem 0 1.2rem 0;
    }

    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        border: 1px solid rgba(148,163,184,0.5);
        margin-left: 8px;
    }

    .status-ok {
        background: rgba(22, 163, 74, 0.18);
        color: #bbf7d0;
        border-color: rgba(74, 222, 128, 0.8);
    }

    .status-warn {
        background: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border-color: rgba(250, 204, 21, 0.9);
    }

    .status-error {
        background: rgba(248, 113, 113, 0.2);
        color: #fecaca;
        border-color: rgba(248, 113, 113, 0.9);
    }

    .status-neutral {
        background: rgba(148, 163, 184, 0.16);
        color: #e5e7eb;
    }

    .small-label {
        font-size: 0.85rem;
        color: #9ca3af;
    }
</style>
"""

css_light = """
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400&display=swap" rel="stylesheet">
<style>
    * {
        font-family: 'Quicksand', sans-serif !important;
        font-weight: 300 !important;
        letter-spacing: -0.01em;
    }

    html, body, .stApp {
        background: #f3f4f6 !important;
        color: #111827 !important;
    }

    h1 {
        font-size: 3.2rem !important;
        font-weight: 300 !important;
        margin-bottom: 0.4rem !important;
        color: #030712 !important;
    }

    h2 {
        font-size: 2rem !important;
        font-weight: 300 !important;
        color: #111827 !important;
    }

    h3 {
        font-size: 1.4rem !important;
        font-weight: 300 !important;
        color: #111827 !important;
    }

    .login-title {
        font-size: 3.2rem !important;
        font-weight: 300 !important;
        margin-bottom: 0.4rem !important;
        color: #030712 !important;
    }

    .card {
        background: #ffffff;
        border-radius: 4px;
        padding: 18px 20px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.18);
        border: 1px solid rgba(148, 163, 184, 0.35);
    }

    .soft-divider {
        border-bottom: 1px solid rgba(148, 163, 184, 0.5);
        margin: 0.6rem 0 1.2rem 0;
    }

    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        border: 1px solid rgba(148,163,184,0.7);
        margin-left: 8px;
    }

    .status-ok {
        background: rgba(22, 163, 74, 0.10);
        color: #166534;
        border-color: rgba(22, 163, 74, 0.7);
    }

    .status-warn {
        background: rgba(234, 179, 8, 0.10);
        color: #854d0e;
        border-color: rgba(202, 138, 4, 0.7);
    }

    .status-error {
        background: rgba(248, 113, 113, 0.15);
        color: #991b1b;
        border-color: rgba(220, 38, 38, 0.8);
    }

    .status-neutral {
        background: rgba(148, 163, 184, 0.18);
        color: #111827;
    }

    .small-label {
        font-size: 0.85rem;
        color: #4b5563;
    }
</style>
"""

# ------------------------------------------------------------
# ÉCRAN DE LOGIN
# ------------------------------------------------------------
def login_screen():
    # Titre de connexion
    st.markdown("<h1 class='login-title'>Smart Sentinel – Connexion</h1>",
                unsafe_allow_html=True)
    st.write("Veuillez entrer le mot de passe pour accéder au tableau de bord.")

    password = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):
        if password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.user_role = "admin"
            st.success("Connexion réussie.")
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")


if st.session_state.theme == "Sombre":
    st.markdown(css_dark, unsafe_allow_html=True)
else:
    st.markdown(css_light, unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# ------------------------------------------------------------
# TITRE + ONGLETS
# ------------------------------------------------------------
st.markdown("<h1>Smart Sentinel</h1>", unsafe_allow_html=True)
st.write(
    "Tableau de bord de surveillance des capteurs pour la gestion des déchets de laboratoire."
)

tab_dashboard, tab_history, tab_tests, tab_params = st.tabs(
    ["Tableau de bord", "Historique", "Capteurs", "Paramètres"]
)

# ------------------------------------------------------------
# FONCTION EMAIL D'ALERTE
# ------------------------------------------------------------
def send_alert_email(temp, level, temp_state, lvl_state, timestamp):
    """Envoie un email d'alerte si la température ou le niveau est critique."""
    try:
        subject = "Alerte critique – Smart Sentinel 🚨🚨🚨"
        body = (
            "Une alerte critique a été détectée sur Smart Sentinel.\n\n"
            f"Date / heure : {timestamp}\n"
            f"Température : {temp:.1f} °C (état : {temp_state})\n"
            f"Niveau : {level:.1f} % (état : {lvl_state})\n\n"
            "Veuillez vérifier le contenant au plus vite."
        )

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECIPIENT

        context = ssl.create_default_context()

        #  On utilise SMTP_SSL sur le port 465 → identique au test_email.py qui marche
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

        print("Alerte email envoyée ")

    except Exception as e:
        st.session_state.last_error = f"Erreur email : {e}"
        print(" Erreur email :", e)

# ------------------------------------------------------------
# FONCTIONS DE DONNÉES & ALERTES
# ------------------------------------------------------------
def get_data():
    """
    Retourne temperature + niveau
    - Simulation
    - Capteur réel via Firebase (noeud senseurs).
    """
    mode = st.session_state.mode

    # ----- SIMULATION -----
    if mode == "Simulation":
        temp = float(np.random.normal(35, 6))
        level = float(np.random.normal(55, 15))
        temp = max(0, min(95, temp))
        level = max(0, min(100, level))
        st.session_state.esp_status = "Simulation"
        st.session_state.esp_latency_ms = None
        st.session_state.last_error = ""
        return {"temperature": temp, "level": level}

    # ----- CAPTEUR RÉEL : FIREBASE -----
    t0 = time.time()
    try:
        temp_resp = requests.get(
            f"{FIREBASE_BASE_URL}/senseurs/temperature.json",
            timeout=2,
        )
        lvl_resp = requests.get(
            f"{FIREBASE_BASE_URL}/senseurs/remplissage.json",
            timeout=2,
        )

        latency = (time.time() - t0) * 1000
        st.session_state.esp_latency_ms = int(latency)

        if temp_resp.status_code != 200 or lvl_resp.status_code != 200:
            st.session_state.esp_status = "Erreur Firebase"
            st.session_state.last_error = (
                f"HTTP temp={temp_resp.status_code}, lvl={lvl_resp.status_code}"
            )
            return {"temperature": np.nan, "level": np.nan}

        temp = float(temp_resp.json())
        level = float(lvl_resp.json())

        st.session_state.esp_status = "Connecté (Firebase)"
        st.session_state.last_error = ""
        return {"temperature": temp, "level": level}

    except Exception as e:
        st.session_state.esp_status = "Déconnecté"
        st.session_state.last_error = str(e)
        st.session_state.esp_latency_ms = None
        return {"temperature": np.nan, "level": np.nan}


def alert_status_temp(value, min_limit, max_limit):
    """Alertes pour la température : bas + haut."""
    if np.isnan(value):
        return "Indisponible", "gray"
    if value < min_limit or value > max_limit:
        return "Critique", "#fb7185"
    elif value < min_limit + 5 or value > max_limit - 5:
        return "Attention", "#facc15"
    return "Normal", "#4ade80"


def alert_status_level(value, max_limit):
    """Alertes pour le niveau : uniquement seuil haut."""
    if np.isnan(value):
        return "Indisponible", "gray"
    if value > max_limit:
        return "Critique", "#fb7185"
    elif value > max_limit - 5:
        return "Attention", "#facc15"
    return "Normal", "#4ade80"


def gauge(title, value, min_val, max_val, color, band_min=None, band_max=None):
    band_min = band_min if band_min is not None else min_val
    band_max = band_max if band_max is not None else max_val

    steps = [
        {"range": [min_val, band_min], "color": "rgba(148,163,184,0.18)"},
        {"range": [band_min, band_max], "color": "rgba(45,212,191,0.22)"},
        {"range": [band_max, max_val], "color": "rgba(248,113,113,0.28)"},
    ]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value if not np.isnan(value) else min_val,
            gauge={
                "axis": {"range": [min_val, max_val]},
                "bar": {"color": color},
                "borderwidth": 0,
                "bgcolor": "rgba(15,23,42,0.0)",
                "steps": steps,
            },
            number={"font": {"size": 34}},
            title={"text": title, "font": {"size": 22}},
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def push_firebase_history(temp, level, timestamp):
    """
    Historique Firebase : chaque mesure réelle (capteur) est poussée dans /mesures.
    """
    if np.isnan(temp) or np.isnan(level):
        return

    payload = {
        "timestamp": timestamp,
        "temperature": float(temp),
        "remplissage": float(level),
    }

    try:
        url = f"{FIREBASE_BASE_URL}/mesures.json"
        requests.post(url, json=payload, timeout=2)
    except Exception as e:
        st.session_state.last_error = f"Firebase history: {e}"


# ------------------------------------------------------------
# RÉCUPÉRATION DES DONNÉES + HISTORIQUE LOCAL + HISTO FIREBASE
# ------------------------------------------------------------
new_data = get_data()
timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

# Historique Firebase (cloud) si capteur réel
if st.session_state.mode == "Capteur réel":
    push_firebase_history(new_data["temperature"], new_data["level"], timestamp)

temp_state, temp_color = alert_status_temp(
    new_data["temperature"],
    st.session_state.temp_min,
    st.session_state.temp_max,
)
lvl_state, lvl_color = alert_status_level(
    new_data["level"],
    st.session_state.lvl_max,
)

new_row = {
    "timestamp": timestamp,
    "temperature": new_data["temperature"],
    "level": new_data["level"],
    "state_temp": temp_state,
    "state_level": lvl_state,
}
st.session_state.history.loc[len(st.session_state.history)] = new_row

# ------------------------------------------------------------
# ONGLET TESTS : mode + fréquence
# ------------------------------------------------------------
with tab_tests:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Modes de fonctionnement")
    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    mode_options = ["Simulation", "Capteur réel"]

    # sécurité si un ancien mode est encore stocké
    if st.session_state.mode not in mode_options:
        st.session_state.mode = "Simulation"

    current_index = mode_options.index(st.session_state.mode)

    st.session_state.mode = st.radio(
        "Mode de fonctionnement",
        mode_options,
        index=current_index,
    )

    st.session_state.refresh_rate = st.slider(
        "Fréquence d’actualisation (simulation / capteur réel) (secondes)",
        min_value=1,
        max_value=10,
        value=st.session_state.refresh_rate,
    )

    st.write(
        f"Mode actuel : {st.session_state.mode}, "
        f"fréquence : {st.session_state.refresh_rate} secondes."
    )

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# ONGLET PARAMÈTRES : seuils + thème + DÉCONNEXION
# ------------------------------------------------------------
with tab_params:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Paramètres système")
    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    st.write("Les données réelles proviennent du capteur connecté à Firebase.")

    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)
    st.write("Seuils d’alerte")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.temp_min = st.slider(
            "Température – seuil critique bas (°C)",
            0,
            100,
            st.session_state.temp_min,
        )
        st.session_state.temp_max = st.slider(
            "Température – seuil critique haut (°C)",
            0,
            200,
            st.session_state.temp_max,
        )

    with c2:
        st.session_state.lvl_max = st.slider(
            "Niveau – seuil critique haut (%)",
            0,
            100,
            st.session_state.lvl_max,
        )

    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    st.write("Apparence de l’interface")
    theme_choice = st.selectbox(
        "Thème",
        ["Sombre", "Clair"],
        index=0 if st.session_state.theme == "Sombre" else 1,
    )
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    # Bouton de déconnexion
    st.write("Session")
    if st.button("Se déconnecter"):
        st.session_state.logged_in = False
        st.session_state.user_role = "admin"
        st.session_state.alert_email_sent = False
        st.success("Vous avez été déconnecté.")
        time.sleep(0.5)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# ONGLET TABLEAU DE BORD
# ------------------------------------------------------------
with tab_dashboard:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Résumé du système")
    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    cols = st.columns([2, 2, 2, 2])
    with cols[0]:
        st.write("Source de données")
        st.write(st.session_state.mode)
    with cols[1]:
        st.write("Statut capteur")
        status = st.session_state.esp_status
        if "Connecté" in status:
            badge_class = "status-badge status-ok"
        elif status == "Simulation":
            badge_class = "status-badge status-neutral"
        elif status in ("Déconnecté", "Erreur Firebase", "Erreur"):
            badge_class = "status-badge status-error"
        else:
            badge_class = "status-badge status-neutral"

        st.markdown(
            f"<span class='{badge_class}'>{status}</span>",
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.write("Latence (Firebase)")
        if st.session_state.esp_latency_ms is not None:
            st.write(f"{st.session_state.esp_latency_ms} ms")
        else:
            st.write("Non disponible")
    with cols[3]:
        st.write("Nombre de mesures (session)")
        st.write(len(st.session_state.history))

    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")

    # Cards jauges
    colA, colB = st.columns(2)

    with colA:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Température du contenant")
        st.plotly_chart(
            gauge(
                "Température (°C)",
                new_data["temperature"],
                0,
                100,
                temp_color,
                band_min=st.session_state.temp_min,
                band_max=st.session_state.temp_max,
            ),
            use_container_width=True,
        )
        st.write(f"État : {temp_state}")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Niveau de remplissage")
        st.plotly_chart(
            gauge(
                "Niveau (%)",
                new_data["level"],
                0,
                100,
                lvl_color,
                band_min=0,
                band_max=st.session_state.lvl_max,
            ),
            use_container_width=True,
        )
        st.write(f"État : {lvl_state}")
        st.markdown("</div>", unsafe_allow_html=True)

    # Notifications intelligentes + email
    if temp_state == "Critique" or lvl_state == "Critique":
        st.error("Attention, une mesure se trouve en zone critique.")
        try:
            st.toast("Alerte critique détectée sur un capteur.")
        except Exception:
            pass

        # Envoi d'email UNE SEULE FOIS tant que la situation reste critique
        if not st.session_state.alert_email_sent:
            send_alert_email(
                new_data["temperature"],
                new_data["level"],
                temp_state,
                lvl_state,
                timestamp,
            )
            st.session_state.alert_email_sent = True
    elif temp_state == "Attention" or lvl_state == "Attention":
        st.warning("Une mesure se trouve proche des seuils critiques.")
        # On ne reset pas le flag ici, seulement quand tout est redevenu normal
    else:
        # si tout revient à la normale, on réarme l'envoi d'email
        st.session_state.alert_email_sent = False

    # Graphique temps réel (session)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Évolution des données (session)")

    df_chart = st.session_state.history.copy()
    df_chart["timestamp"] = pd.to_datetime(df_chart["timestamp"])

    base = alt.Chart(df_chart).encode(
        x=alt.X("timestamp:T", title="Temps"),
    )

    temp_line = base.mark_line().encode(
        y=alt.Y("temperature:Q", title="Valeur mesurée", scale=alt.Scale(zero=False)),
        color=alt.value("#67e8f9"),
        tooltip=["timestamp:T", "temperature:Q"],
    )

    lvl_line = base.mark_line().encode(
        y=alt.Y("level:Q", title=""),
        color=alt.value("#a855f7"),
        tooltip=["timestamp:T", "level:Q"],
    )

    chart = alt.layer(temp_line, lvl_line).resolve_scale(
        y="independent"
    ).properties(height=360)

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# ONGLET HISTORIQUE : LOCAL + FIREBASE + VUE BRUTE
# ------------------------------------------------------------
with tab_history:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Historique des mesures")
    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    tab_local, tab_firebase, tab_raw = st.tabs(
        ["Historique local (session)", "Historique Firebase (cloud)", "Vue brute Firebase"]
    )

    # ---------- Historique local ----------
    with tab_local:
        df_hist = st.session_state.history.copy()
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])

        if not df_hist.empty:
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                start_date = st.date_input(
                    "Date de début",
                    value=df_hist["timestamp"].min().date(),
                    key="local_start_date",
                )
            with col_filter2:
                end_date = st.date_input(
                    "Date de fin",
                    value=df_hist["timestamp"].max().date(),
                    key="local_end_date",
                )

            mask = (
                (df_hist["timestamp"].dt.date >= start_date)
                & (df_hist["timestamp"].dt.date <= end_date)
            )
            df_filtered = df_hist.loc[mask].copy()
        else:
            df_filtered = df_hist.copy()

        st.write(f"Nombre de mesures dans l’intervalle (session) : {len(df_filtered)}")

        st.dataframe(df_filtered, use_container_width=True)

        st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)
        st.write("Exports (session)")

        # CSV
        csv = df_filtered.to_csv(index=False).encode("utf-8")

        # Excel (openpyxl si dispo)
        excel_data = None
        try:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df_filtered.to_excel(writer, index=False, sheet_name="SmartSentinel")
            excel_data = excel_buffer.getvalue()
        except ModuleNotFoundError:
            st.info("Export Excel indisponible (module 'openpyxl' manquant).")

        # JSON
        json_data = df_filtered.to_json(orient="records", date_format="iso")

        c_exp1, c_exp2, c_exp3 = st.columns(3)
        with c_exp1:
            st.download_button(
                label="Télécharger CSV",
                data=csv,
                file_name="historique_smart_sentinel.csv",
                mime="text/csv",
            )
        with c_exp2:
            if excel_data is not None:
                st.download_button(
                    label="Télécharger Excel",
                    data=excel_data,
                    file_name="historique_smart_sentinel.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        with c_exp3:
            st.download_button(
                label="Télécharger JSON",
                data=json_data,
                file_name="historique_smart_sentinel.json",
                mime="application/json",
            )

        st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

        if not df_filtered.empty:
            temp_mean = df_filtered["temperature"].mean()
            temp_min = df_filtered["temperature"].min()
            temp_max = df_filtered["temperature"].max()

            lvl_mean = df_filtered["level"].mean()
            lvl_min = df_filtered["level"].min()
            lvl_max = df_filtered["level"].max()

            c_stats1, c_stats2 = st.columns(2)
            with c_stats1:
                st.write("Statistiques température (session)")
                st.write(f"Moyenne : {temp_mean:.1f} °C")
                st.write(f"Min : {temp_min:.1f} °C")
                st.write(f"Max : {temp_max:.1f} °C")
            with c_stats2:
                st.write("Statistiques niveau (session)")
                st.write(f"Moyenne : {lvl_mean:.1f} %")
                st.write(f"Min : {lvl_min:.1f} %")
                st.write(f"Max : {lvl_max:.1f} %")

    # ---------- Historique Firebase ----------
    with tab_firebase:
        st.write("Historique stocké dans Firebase (/mesures).")

        try:
            resp = requests.get(f"{FIREBASE_BASE_URL}/mesures.json", timeout=3)
            if resp.status_code == 200 and resp.json() is not None:
                data = resp.json()

                rows = []
                for key, entry in data.items():
                    ts = entry.get("timestamp")
                    temp = entry.get("temperature")
                    lvl = entry.get("remplissage", entry.get("level"))
                    rows.append(
                        {
                            "firebase_key": key,
                            "timestamp": ts,
                            "temperature": temp,
                            "level": lvl,
                        }
                    )

                if rows:
                    df_fb = pd.DataFrame(rows)
                    df_fb["timestamp"] = pd.to_datetime(df_fb["timestamp"])

                    st.write(f"Nombre de mesures dans Firebase : {len(df_fb)}")
                    st.dataframe(df_fb.sort_values("timestamp"), use_container_width=True)

                    # Graphique Firebase
                    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)
                    st.write("Évolution (Firebase)")
                    base_fb = alt.Chart(df_fb).encode(
                        x=alt.X("timestamp:T", title="Temps"),
                    )
                    temp_fb = base_fb.mark_line().encode(
                        y=alt.Y("temperature:Q", title="Température (°C)"),
                        color=alt.value("#22d3ee"),
                        tooltip=["timestamp:T", "temperature:Q"],
                    )
                    lvl_fb = base_fb.mark_line().encode(
                        y=alt.Y("level:Q", title="Niveau (%)"),
                        color=alt.value("#a855f7"),
                        tooltip=["timestamp:T", "level:Q"],
                    )
                    chart_fb = alt.layer(temp_fb, lvl_fb).resolve_scale(
                        y="independent"
                    ).properties(height=320)
                    st.altair_chart(chart_fb, use_container_width=True)
                else:
                    st.info("Aucune mesure enregistrée dans Firebase pour l’instant.")
            else:
                st.error("Impossible de lire /mesures dans Firebase.")
        except Exception as e:
            st.error(f"Erreur lors de la lecture Firebase : {e}")

    # ---------- Vue brute Firebase ----------
    with tab_raw:
        st.write("Vue brute de toute la base Realtime Database.")
        try:
            resp = requests.get(f"{FIREBASE_BASE_URL}/.json", timeout=3)
            if resp.status_code == 200:
                st.json(resp.json())
            else:
                st.error(f"Erreur HTTP {resp.status_code}")
        except Exception as e:
            st.error(f"Erreur lors de la lecture Firebase : {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# MISE À JOUR CONTINUE : SIMULATION + CAPTEUR RÉEL
# ------------------------------------------------------------
if st.session_state.mode in ["Simulation", "Capteur réel"]:
    time.sleep(st.session_state.refresh_rate)
    st.rerun()
