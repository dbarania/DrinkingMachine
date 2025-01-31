import time
import asyncio
from bleak import BleakClient, BleakScanner
import paho.mqtt.client as mqtt

# Bluetooth and MQTT settings
RESULT_UUID = "13012F01-F8C3-4F4A-A8F4-15CD926DA146"
MQTT_BROKER = "192.168.0.197"  # Change to the IP address of your MQTT broker if needed
MQTT_PORT = 1883

mqtt_sub_topics = "customer/1/order"

# Timer settings
TIMER_LIMIT = 10  # Time in seconds before triggering alert
timer_running = False
timer_start = None

# Function to initialize the MQTT client
def setup_mqtt_client():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    return client

# Function to handle messages from MQTT
def on_message(client, userdata, message):
    global timer_running, timer_start
    payload = message.payload.decode('utf-8').strip()
    print(f"Received MQTT message: {payload} on topic: {message.topic}")
    
    if message.topic == "customer/1/order":
        if payload == "stop":
            print("Received stop message, stopping the timer.")
            timer_running = False  # Stop the timer if we receive the stop command
        elif payload == "start":
            print("Starting timer...")
            timer_running = True
            timer_start = time.time()  # Start a new timer

# Function to monitor the timer and publish if necessary
async def monitor_timer(client, mqtt_client):
    global timer_running, timer_start
    while True:
        if timer_running:
            elapsed_time = time.time() - timer_start
            if elapsed_time > TIMER_LIMIT:
                mqtt_client.publish("customer/1", "timeout")
                mqtt_client.loop()
                timer_running = False  # Stop the timer after sending the alert
        await asyncio.sleep(1)  # Check every second

# Main Bluetooth handling function
async def run(mqtt_client):
    global timer_start
    print('Raspberry Pi 5 Central Service')
    print('Looking for Arduino Nano 33 BLE Sense Peripheral Device...')

    found = False
    devices = await BleakScanner.discover()
    for d in devices:
        if 'Arduino Nano 33 BLE Sense' in d.name:
            print('Found Arduino Nano 33 BLE Sense Peripheral')
            found = True
            async with BleakClient(d.address) as client:
                print(f'Connected to Customer 1: {d.address}')

                while found:
                    try:
                        # Read data from Bluetooth
                        result = await client.read_gatt_char(RESULT_UUID)
                        res_convert = result.decode('utf-8')
                        if res_convert != "idle":
                            # Publish the data to the MQTT topic
                            mqtt_client.publish("customer/1", res_convert)
                            print(f"Published to MQTT: Movement detected - {res_convert}")
                            # Reset the timer if we receive a new Bluetooth message
                            if timer_running:
                                print("Resetting the timer...")
                                timer_start = time.time()

                    except Exception as e:
                        print(f"Error reading or publishing data: {e}")
                        await asyncio.sleep(5)

    if not found:
        print('Could not find Arduino Nano 33 BLE Sense Peripheral')

    print('Device found and connected, starting data reading...')

# Setup the MQTT client
mqtt_client = setup_mqtt_client()
mqtt_client.on_message = on_message
mqtt_client.subscribe(mqtt_sub_topics)
mqtt_client.loop_start()

print("Connected to MQTT broker.")

# Start the monitoring of the timer
loop = asyncio.get_event_loop()
loop.create_task(monitor_timer(mqtt_client))

try:
        loop.create_task(run(mqtt_client))
        loop.run_forever()
except KeyboardInterrupt:
        loop.stop()
        print('\nReceived Keyboard Interrupt')
except Exception as e:
    print(f"Error in Bluetooth loop: {e}")
finally:
    print('\nShutting down...')
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("Disconnected from MQTT broker.")

