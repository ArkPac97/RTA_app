from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

with open('data/products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

for product in products:
    producer.send('products', product)
    print(f"Sent: {product['title']} - {product['price']} zł")
    time.sleep(0.2)  # symulacja strumienia

producer.flush()
print("Wysłano wszystkie produkty.")
