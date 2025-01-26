import paho.mqtt.client as mqtt

broker = "192.168.0.197"  # Replace with your broker's address
port = 1883  # Default MQTT port 
topics = ["car/drink", "control"]  # Topics to subscribe to

class CommunicationModule:
    CLIENT_ID = "Vehicle_bartender"

    def __init__(self):
        """Initialize the MQTT client and set up event handlers."""
        self.client = mqtt.Client(client_id=self.CLIENT_ID)
        
        # Assign event handlers
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Connect to the broker asynchronously (non-blocking)
        self.client.connect_async(broker, port, 60)
        self.client.loop_start()  # Start non-blocking loop

    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to the broker."""
        if rc == 0:
            print("Connected to MQTT broker.")
            # Subscribe to all topics upon successful connection
            for topic in topics:
                self.client.subscribe(topic)
                print(f"Subscribed to topic: {topic}")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        print(f"Received message on topic '{msg.topic}': {msg.payload.decode()}")

    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from the broker."""
        print("Disconnected from MQTT broker.")

    def publish(self, topic, message):
        """Publish a message to a given topic."""
        result = self.client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Message '{message}' sent to topic '{topic}'")
        else:
            print(f"Failed to publish message to {topic}")

    def stop(self):
        """Stop the MQTT client loop and disconnect."""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped.")