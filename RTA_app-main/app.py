from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime
from flask import Response
import os

app = Flask(__name__)
CORS(app)

# bufor na dane anomalii
anomalie_bufor = []

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
CARTS_FILE = os.path.join(DATA_DIR, "carts.json")

def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# endpointy danych bazowych
@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(load_data(PRODUCTS_FILE))

@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(load_data(USERS_FILE))

@app.route("/carts", methods=["GET"])
def get_carts():
    return jsonify(load_data(CARTS_FILE))

# endpoint logowania
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    name = data.get("username")
    password = data.get("password")
    tokens = load_data(os.path.join(DATA_DIR, "tokens.json"))
    if name in tokens and tokens[name]["password"] == password:
        return jsonify({"token": tokens[name]["token"]})
    return jsonify({"error": "Nieprawidłowe dane logowania"}), 401

# endpoint dodawania anomalii
@app.route("/anomalies/live", methods=["POST"])
def post_anomalies():
    anomalia = request.get_json()
    anomalia["timestamp"] = datetime.now().isoformat()
    anomalie_bufor.append(anomalia)
    return jsonify({"status": "wykryto anomalie", "liczba": len(anomalie_bufor)})

# endpoint pobierania anomalii
@app.route("/anomalies/live", methods=["GET"])
def get_anomalies():
    return Response(
        json.dumps(anomalie_bufor, indent=2, ensure_ascii=False),
        mimetype="application/json"
    )

if __name__ == "__main__":
    app.run(debug=True)