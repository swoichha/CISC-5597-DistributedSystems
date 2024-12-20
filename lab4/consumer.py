from kafka import KafkaConsumer

consumer = KafkaConsumer('test-topic', bootstrap_servers='localhost:9092', group_id='my-consumer-group',auto_offset_reset='earliest')

for message in consumer:
    print(f"Received: {message.value.decode('utf-8')}")
