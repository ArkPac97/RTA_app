from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'products',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

def is_anomaly(product):
    # przykałd zbyt niska cena dla elektroniki
    if product['category'] == 'electronics' and product['price'] < 50:
        return True
    return False

print("Nasłuchiwanie...")
for message in consumer:
    product = message.value
    if is_anomaly(product):
        print(f"ANOMALIA: {product['title']} ({product['category']}) – {product['price']} zł")
