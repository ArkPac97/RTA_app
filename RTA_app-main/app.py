import os
import json
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Tworzymy folder data, jeśli nie istnieje
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CSV_FILE = os.path.join(DATA_DIR, 'anomalies.csv')

# Wczytaj dane z plików JSON
with open(os.path.join(DATA_DIR, 'products.json'), 'r', encoding='utf-8') as f:
    products = json.load(f)

with open(os.path.join(DATA_DIR, 'users.json'), 'r', encoding='utf-8') as f:
    users = json.load(f)

with open(os.path.join(DATA_DIR, 'carts.json'), 'r', encoding='utf-8') as f:
    carts = json.load(f)

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
    if cart:
        return jsonify(cart)
    return jsonify({"error": "Koszyk nie znaleziony"}), 404

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

    return jsonify({"status": "ok"}), 200

# Endpoint do pobierania wszystkich anomalii (GET)
@app.route('/anomalies', methods=['GET'])
def get_anomalies():
    return jsonify(live_anomalies)

if __name__ == '__main__':
    app.run(debug=True)
