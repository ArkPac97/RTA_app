import os
import json
import pandas as pd
from flask import Flask, jsonify, request
from datetime import datetime
from email_utils import send_block_notification, send_unlock_notification

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
print("BASE_DIR:", BASE_DIR)
print("DATA_DIR:", DATA_DIR)
print("Czy products.json istnieje?", os.path.exists(os.path.join(DATA_DIR, 'products.json')))
# Tworzymy folder data, jeśli nie istnieje
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CSV_FILE = os.path.join(DATA_DIR, 'anomalies.csv')

df_unlock_log = pd.DataFrame()
UNLOCK_LOG_FILE = os.path.join(DATA_DIR, 'unlock_log.csv')

# Wczytaj dane z plików JSON
with open(os.path.join(DATA_DIR, 'products.json'), 'r', encoding='utf-8') as f:
    products = json.load(f)

with open(os.path.join(DATA_DIR, 'users.json'), 'r', encoding='utf-8') as f:
    users = json.load(f)

with open(os.path.join(DATA_DIR, 'carts.json'), 'r', encoding='utf-8') as f:
    carts = json.load(f)

# Na potrzeby testowania systemu - Reset statusu blokady w każdym koszyku w pliku carts.json
for cart in carts:
    cart["blocked"] = False

with open(os.path.join(DATA_DIR, 'carts.json'), 'w', encoding='utf-8') as f:
    json.dump(carts, f, indent=2, ensure_ascii=False)

# Mapy dla szybszego dostępu
product_map = {p['id']: p for p in products}
user_map = {u['id']: u for u in users}
cart_map = {c['id']: c for c in carts}

live_anomalies = []
df_anomalies = pd.DataFrame()

@app.route('/')
def home():
    return jsonify({"message": "RTA App API działa!"})

# Endpointy dla produktów
@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = product_map.get(product_id)
    if product:
        return jsonify(product)
    return jsonify({"error": "Produkt nie znaleziony"}), 404

# Endpointy dla użytkowników
@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = user_map.get(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "Użytkownik nie znaleziony"}), 404

# Endpointy dla koszyków
@app.route('/carts', methods=['GET'])
def get_carts():
    return jsonify(carts)

@app.route('/carts/<int:cart_id>', methods=['GET'])
def get_cart(cart_id):
    cart = cart_map.get(cart_id)
    if not cart:
        return jsonify({"error": "Koszyk nie znaleziony"}), 404

    is_blocked = cart.get("blocked", False)
    response = {
        "blocked": is_blocked,
        "cart": cart
    }

    if is_blocked:
        #znajduje i zwraca dane na temat anomalii, którą zaobserwowano w koszyku
        matching = next((a for a in reversed(live_anomalies) if a.get("cartId") == cart_id), None)

        if matching:
            response["message"] = "Koszyk został zablokowany z powodu wykrytej anomalii."
            response["anomaly"] = {
                "type": matching.get("source"),
                "value": matching.get("margin") if matching.get("source") == "margin" else matching.get("discount"),
                "comment": matching.get("comment"),
                "product_title": matching.get("title")
            }

    return jsonify(response)

# Endpoint z listą zablokowanych koszykó
@app.route('/carts/blocked', methods=['GET'])
def get_blocked_carts():
    blocked = [cart for cart in carts if cart.get("blocked")]
    return jsonify(blocked)

# Endpoint do odbierania anomalii (POST)
@app.route('/anomalies/live', methods=['POST'])
def anomalies_live():
    global df_anomalies

    anomaly = request.json
    live_anomalies.append(anomaly)

    # Dodaj nową anomalię do DataFrame
    df_anomalies = pd.concat([df_anomalies, pd.DataFrame([anomaly])], ignore_index=True)

    # Zapisz DataFrame do pliku CSV (nadpisuje plik przy każdej zmianie)
    df_anomalies.to_csv(CSV_FILE, index=False, encoding='utf-8')

    print(f"Otrzymano anomalię: {anomaly.get('title', 'brak tytułu')} ({anomaly.get('anomaly_type', 'brak typu')})")
    print(f"Liczba anomalii w DataFrame: {len(df_anomalies)}")
    print(f"Zapisano anomalie do: {CSV_FILE}")

    #Zapisywanie id koszyków z anomaliami
    cart_id = anomaly.get("cartId")
    if cart_id:

        #aktualizacja statusu koszyka w carts.json
        for c in carts:
            if c["id"] == cart_id:
                c["blocked"] = True
                break

        with open(os.path.join(DATA_DIR, 'carts.json'), 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=2, ensure_ascii=False)

        #send_block_notification(cart_id) #<- funckja zakomentowana, ze względu na koniecznosc 2etapowej weryfikacji skrzynki
    
    return jsonify({"status": "ok"}), 200

# Endpoint do pobierania wszystkich anomalii (GET)
@app.route('/anomalies', methods=['GET'])
def get_anomalies():
    return jsonify(live_anomalies)

# Endpoint do odblokowania koszyka

# kod wymagany do odblokowania koszyka
ADMIN_ACCESS_CODE = "admin123"  

@app.route('/carts/<int:cart_id>/unlock', methods=['POST'])
def unlock_cart(cart_id):
    data = request.get_json()
    access_code = data.get("access_code") if data else None

    if access_code != ADMIN_ACCESS_CODE:
        return jsonify({"error": "Nieautoryzowany dostęp."}), 401

    updated = False
    for cart in carts:
        if cart["id"] == cart_id:
            if cart.get("blocked"):
                cart["blocked"] = False
                updated = True
            break

    if updated:

        #zmiana statusu koszyka w carts.json
        with open(os.path.join(DATA_DIR, 'carts.json'), 'w', encoding='utf-8') as f:
            json.dump(carts, f, indent=2, ensure_ascii=False)

        # Dokumentowanie odblokowania koszyka do csv
        global df_unlock_log

        log_entry = {
            "cartId": cart_id,
            "timestamp": datetime.now().isoformat(),
            "unlocked_by": "admin"
        }

        df_unlock_log = pd.concat([df_unlock_log, pd.DataFrame([log_entry])], ignore_index=True)
        df_unlock_log.to_csv(UNLOCK_LOG_FILE, index=False, encoding='utf-8')


        print(f"Odblokowano koszyk {cart_id} przez administratora.")

        #send_unlock_notification(cart_id) # <- funckja zakomentowana, ze względu na koniecznosc 2etapowej weryfikacji skrzynki

        return jsonify({"status": "unlocked", "cartId": cart_id}), 200
    else:
        return jsonify({"status": "not_modified", "reason": "Koszyk nie był zablokowany lub nie istnieje."}), 400


# Endpoint do historii odblokowań koszyków
@app.route('/admin/unlock-log', methods=['GET'])
def get_unlock_log():
    log_path = os.path.join(DATA_DIR, 'unlock_log.csv')
    if os.path.exists(log_path):
        df = pd.read_csv(log_path)
        return jsonify(df.to_dict(orient='records'))
    else:
        return jsonify([])


if __name__ == '__main__':
    app.run(debug=True)
