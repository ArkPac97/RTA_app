from kafka import KafkaConsumer
import json
import os
import requests
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARTS_PATH = os.path.join(BASE_DIR, 'data', 'carts.json')
USERS_PATH = os.path.join(BASE_DIR, 'data', 'users.json')
CSV_PATH = os.path.join(BASE_DIR, 'data', 'anomalies_discount.csv')

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

def append_to_csv(file_path, data, header):
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

print("[DISCOUNT] Nasłuchiwanie anomalii rabatowych...")

header = [
    "cartId", "productId", "title", "margin", "discount", "price", "cost_price",
    "userId", "userName", "anomaly_type", "comment"
]

for message in consumer:
    product = message.value
    carts = load_carts()
    discount = product.get("discount", 0)
    price = product.get("price", 0)
    cost = product.get("cost_price", 0)
    margin = round((price - cost) / price, 4) if price > 0 else -1

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
                    
                    row = {
                    "cartId": cart["id"],
                    "productId": product["id"],
                    "title": product["title"],
                    "margin": margin,
                    "discount": discount,
                    "price": price,
                    "cost_price": cost,
                    "userId": user.get("id", ""),
                    "userName": user.get("name", ""),
                    "anomaly_type": "alert_discount",
                    "comment": f"Rabat przekracza 45% ({discount}%)"
                    }

                    append_to_csv(CSV_PATH, row, header)
                    
                    try:
                        r = requests.post("http://localhost:5000/anomalies/live", json=payload)
                        print(f"[DISCOUNT] Wysłano anomalię: {payload['title']} (rabat: {discount}%)")
                    except Exception as e:
                        print(f"[DISCOUNT] Błąd wysyłania: {e}")
