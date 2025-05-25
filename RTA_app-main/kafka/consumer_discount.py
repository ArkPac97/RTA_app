from kafka import KafkaConsumer
import json
import os
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARTS_PATH = os.path.join(BASE_DIR, 'data', 'carts.json')
USERS_PATH = os.path.join(BASE_DIR, 'data', 'users.json')

#zdefiniowanie funkcji load_carts, która służy do wczytywanie pliku z aktualnymi statusami blokady koszyków
def load_carts():
    with open(CARTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

with open(USERS_PATH, 'r', encoding='utf-8') as f:
    users = json.load(f)

user_map = {u["id"]: u for u in users}

consumer = KafkaConsumer(
    'products',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("[DISCOUNT] Nasłuchiwanie anomalii rabatowych...")

for message in consumer:
    product = message.value
    carts = load_carts()
    discount = product.get("discount", 0)

    if discount > 45:
        for cart in carts:
            # jeśli koszyk jest zablokowany, consumer nie pozwoli na dodanie kolejnego produktu do niego
            if cart.get("blocked"):
                continue

            for item in cart["products"]:
                if item["productId"] == product["id"]:
                    user = user_map.get(cart["userId"], {})
                    payload = {
                        "cartId": cart["id"],
                        "productId": product["id"],
                        "title": product["title"],
                        "margin": round((product["price"] - product.get("cost_price", 0)) / product["price"], 4),
                        "discount": discount,
                        "price": product["price"],
                        "cost_price": product.get("cost_price", 0),
                        "user": user,
                        "source": "discount",
                        "anomaly_type": "alert_discount",
                        "comment": f"Rabat przekracza 45% ({discount}%)"
                    }
                    try:
                        r = requests.post("http://localhost:5000/anomalies/live", json=payload)
                        print(f"[DISCOUNT] Wysłano anomalię: {payload['title']} (rabat: {discount}%)")
                    except Exception as e:
                        print(f"[DISCOUNT] Błąd wysyłania: {e}")
