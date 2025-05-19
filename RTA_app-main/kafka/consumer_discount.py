from kafka import KafkaConsumer
import json
import os
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CARTS_FILE = os.path.join(DATA_DIR, "carts.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

with open(CARTS_FILE, "r", encoding="utf-8") as f:
    carts = json.load(f)
with open(USERS_FILE, "r", encoding="utf-8") as f:
    users = json.load(f)

cart_map = {c["id"]: c for c in carts}
user_map = {u["id"]: u for u in users}

# konsument
consumer = KafkaConsumer(
    'products',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("Nasłuchiwanie anomalii rabatowych")

for message in consumer:
    product = message.value
    price = product["price"]
    cost = product.get("cost_price", 0)
    discount = product.get("discount", 0)
    margin = round((price - cost) / price, 4) if price > 0 else -1

    if discount > 45:
        for cart in carts:
            for item in cart["products"]:
                if item["productId"] == product["id"]:
                    user = user_map.get(cart["userId"], {})
                    payload = {
                        "cartId": cart["id"],
                        "productId": product["id"],
                        "title": product["title"],
                        "margin": margin,
                        "discount": discount,
                        "user": user,
                        "source": "discount",
                        "anomaly_type": "alert_discount",
                        "comment": f"Rabat przekracza 45% ({discount}%)"
                    }
                    try:
                        r = requests.post("http://localhost:5000/anomalies/live", json=payload)
                        print(f"Anomalia rabatowa {payload['title']} ({discount}%)")
                    except Exception as e:
                        print(f"Błąd wysyłania {e}")