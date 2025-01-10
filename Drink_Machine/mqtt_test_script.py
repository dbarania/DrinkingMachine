import paho.mqtt.client as mqtt

# MQTT Broker Details
BROKER = "192.168.0.197"  # Replace with the broker's IP if not running locally
PORT = 1883           # Default MQTT port
TOPIC = "test/messages"    # Replace with your desired topic

# Callback for when the client receives a connection acknowledgment from the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to the topic after connecting
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

# Callback for when a message is received
def on_message(client, userdata, msg):
    print(f"Received message on topic '{msg.topic}': {msg.payload.decode()}")
    
    try:
        # Attempt to strip quotes and convert to an integer
        payload = int(msg.payload.decode().strip('"'))
        if payload == 1:
            print(f'This will perform some action because the message was {payload}')
        else:
            print(f"Received an integer that is not 1: {payload}")
    except ValueError:
        # Handle non-integer messages
        print(f"Received a non-integer message: {msg.payload.decode()}")


# Initialize MQTT Client
client = mqtt.Client()

# Attach callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(BROKER, PORT, 60)

# Start the network loop in a non-blocking way
client.loop_start()

# Publish messages in a loop
try:
    while True:
        message = input("Enter message to send (or 'exit' to quit): ")
        if message.lower() == "exit":
            break
        # Publish the message to the same topic
        client.publish(TOPIC, message)
        print(f"Message sent: {message}")

except KeyboardInterrupt:
    print("\nExiting...")

# Stop the loop and disconnect
client.loop_stop()
client.disconnect()
