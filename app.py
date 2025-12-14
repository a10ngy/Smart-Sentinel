# -*- coding: utf-8 -*-
import webview
import threading

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
APP_TITLE = "Smart Sentinel"
APP_URL = "http://127.0.0.1:8501"  
# ← Le tableau de bord Streamlit doit tourner en local OU en ligne !

# ------------------------------------------------------------
# LANCER STREAMLIT EN ARRIÈRE PLAN
# ------------------------------------------------------------

import subprocess
import sys
import os

def run_streamlit():
    """
    Démarre ton interface Streamlit dans un processus séparé.
    Change 'dashboard.py' par le nom réel de ton fichier Streamlit.
    """
    dashboard_file = "projet_app.py"   # ← ton fichier actuel Streamlit

    cmd = [
        sys.executable,
        "-m", "streamlit", "run", dashboard_file,
        "--server.port", "8501",
        "--server.headless", "true"
    ]
    subprocess.Popen(cmd)


# ------------------------------------------------------------
# APPLICATION MOBILE (WebView)
# ------------------------------------------------------------
def open_mobile_app():
    """
    Ouvre ton dashboard Streamlit dans une application.
    """
    webview.create_window(APP_TITLE, APP_URL)
    webview.start()


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    # Lance Streamlit dans un thread séparé
    t = threading.Thread(target=run_streamlit)
    t.daemon = True
    t.start()

    # Lance l'application mobile
    open_mobile_app()
