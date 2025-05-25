from kafka import KafkaConsumer
import json
import os
import requests

# Ścieżki do plików
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARTS_PATH = os.path.join(BASE_DIR, 'data', 'carts.json')
USERS_PATH = os.path.join(BASE_DIR, 'data', 'users.json')

# Wczytanie danych
def load_carts():
    with open(CARTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

with open(USERS_PATH, 'r', encoding='utf-8') as f:
    users = json.load(f)

user_map = {u["id"]: u for u in users}

# Konfiguracja konsumenta
consumer = KafkaConsumer(
    'products',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

print("[MARGIN] Nasłuchiwanie anomalii marżowych...")

# Pętla nasłuchująca
for message in consumer:
    product = message.value
    price = product.get("price", 0)
    cost = product.get("cost_price", 0)
    discount = product.get("discount", 0)
    margin = round((price - cost) / price, 4) if price > 0 else -1

    # Sprawdzenie progu marży
    if margin < 0.2:
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
                        "margin": margin,
                        "discount": discount,
                        "price": price,
                        "cost_price": cost,
                        "user": user,
                        "source": "margin",
                        "anomaly_type": "alert_margin",
                        "comment": f"Marża poniżej 20% ({margin * 100:.1f}%)"
                    }
                    try:
                        r = requests.post("http://localhost:5000/anomalies/live", json=payload)
                        print(f"[MARGIN] Wysłano anomalię: {payload['title']} (marża: {margin * 100:.1f}%)")
                    except Exception as e:
                        print(f"[MARGIN] Błąd wysyłania: {e}")
