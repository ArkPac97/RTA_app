from kafka import KafkaProducer
import json
import time
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS_PATH = os.path.join(BASE_DIR, 'data', 'products.json')

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

with open(PRODUCTS_PATH, 'r', encoding='utf-8') as f:
    products = json.load(f)

for product in products:
    producer.send('products', product)
    print(f"Iteracja: title: {product['title']} / price: {product['price']} / cost_price: {product['cost_price']} / discount: {product['discount']}")
    time.sleep(4)

producer.flush()
print("Koniec listy")
