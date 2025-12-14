import smtplib
import ssl
from email.mime.text import MIMEText

EMAIL_SENDER = "angeyvanmugisha@gmail.com"
EMAIL_PASSWORD = "wpzydztrfyaktcul"   # <-- ton mot de passe app SANS espaces
EMAIL_RECIPIENT = "angeyvanmugisha@gmail.com"

def test_email():
    msg = MIMEText("Test Smart Sentinel – Si tu vois ce mail, SMTP fonctionne !")
    msg["Subject"] = "TEST SMTP"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        print("✓ Email envoyé !")
    except Exception as e:
        print("❌ Erreur :", e)

test_email()
