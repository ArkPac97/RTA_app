from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

def load_data(file_name):
    with open(f"data/{file_name}", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(load_data("products.json"))

@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(load_data("users.json"))

@app.route("/carts", methods=["GET"])
def get_carts():
    return jsonify(load_data("carts.json"))

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    tokens = load_data("tokens.json")
    if username in tokens and tokens[username]["password"] == password:
        return jsonify({"token": tokens[username]["token"]})
    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == "__main__":
    app.run(debug=True)
