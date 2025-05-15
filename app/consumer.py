from kafka import KafkaConsumer
import json

try:
    consumer = KafkaConsumer(
        'outbox.events.order',
        bootstrap_servers=['localhost:29092'],
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    print("Waiting for messages...")
    for message in consumer:
        print("\n=== New Order Event ===")
        print(f"Topic: {message.topic}")
        print(f"Partition: {message.partition}")
        print(f"Offset: {message.offset}")
        print(f"Key: {message.key}")
        print(f"Headers: {message.headers}")
        print(f"Value: {message.value}")

except Exception as e:
    print(f"An error occurred: {e}")