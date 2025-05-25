import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
import json

# Ścieżki do plików
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CARTS_FILE = os.path.join(DATA_DIR, 'carts.json')

# Dane konta nadawcy
EMAIL_SENDER = "anomalie.cenowe.rta@wp.pl"
EMAIL_PASSWORD = "ano-cen-rta"
SMTP_SERVER = "smtp.wp.pl"
SMTP_PORT = 587

#Tworzenie maila
def send_email(subject, body, to_email):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Wysłano e-mail do {to_email} – temat: {subject}")
    except Exception as e:
        print(f"Błąd wysyłania e-maila: {e}")

#Skrypt na pobranie emaila użytkownika poprzez id klienta przypisane do koszyka
def get_email_from_cart(cart_id):
    try:
        with open(CARTS_FILE, 'r', encoding='utf-8') as f:
            carts = json.load(f)
        cart = next((c for c in carts if c["id"] == cart_id), None)
        if cart:
            user_id = cart.get("userId")
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
            user = next((u for u in users if u["id"] == user_id), None)
            return user.get("email") if user else None
    except Exception as e:
        print(f"Błąd przy pobieraniu adresu e-mail: {e}")
        return None

#Mail w przypadku zablokowania koszyka
def send_block_notification(cart_id):
    email = get_email_from_cart(cart_id)
    if email:
        send_email(
            subject="Zablokowanie koszyka",
            body=f"Twój koszyk nr {cart_id} został tymczasowo zablokowany z powodu wykrycia anomalii cenowej.",
            to_email=email
        )

#Mail w przypadku odblokowania koszyka
def send_unlock_notification(cart_id):
    email = get_email_from_cart(cart_id)
    if email:
        send_email(
            subject="Odblokowanie koszyka",
            body=f"Twój koszyk nr {cart_id} został właśnie odblokowany i możesz kontynuować zakupy.",
            to_email=email
        )

