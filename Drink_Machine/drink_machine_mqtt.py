import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO 
import time
import math

# Configuration
broker = "192.168.0.197"  # Replace with your broker's address
port = 1883  # Default MQTT port 
topics = ["car/drink", "control"]  # Topics to subscribe to

#response_topics = # topics for responses
# ["drink_machine/messages", # for error messages and so on 
# "drink_machine/container/1/volume", 
# "drink_machine/container/2/volume", 
# "drink_machine/pump/1", # on or off
# "drink_machine/pump/2",  # on or off
# "drink_machine/status"] # current machine status
client_id = "drink_machine"  # Unique client ID
RUNNING = True  # Global variable to control the loop

flow_rate_pump_1 = 1 # liters per minute
flow_rate_pump_2 = 1 # liters per minute
drink_size = 0.2 # liters
dist_to_sensor_1 = 20 # distance from bottom of bucket to sensor 1 (cm)
dist_to_sensor_2 = 20 # distance from bottom of bucket to sensor 2 (cm)

# bucket details (for estimating liters of liquid left)
r_bottom = 11.4 # radius at bottom of the bucket (cm)
r_top = 14.3 # radius at 10 liter mark (cm)
h_bucket = 19.1 # height of the bucket (cm)

# pins
pump_1_pin = 18
pump_2_pin = 19
dist_1_trigger_pin = 20
dist_2_trigger_pin = 21
dist_1_echo_pin = 22
dist_2_echo_pin = 23
led_1_pin = 24 # led for indicating that container 1 needs refilling (turns on with less than a liter left)
led_2_pin = 25 # led for indicating that container 2 needs refilling (turns on with less than a liter left)

















# configure pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(pump_1_pin, GPIO.OUT)
GPIO.setup(pump_2_pin, GPIO.OUT)
GPIO.setup(dist_1_trigger_pin, GPIO.OUT)
GPIO.setup(dist_2_trigger_pin, GPIO.OUT)
GPIO.setup(dist_1_echo_pin, GPIO.IN)
GPIO.setup(dist_2_echo_pin, GPIO.IN)
GPIO.setup(led_1_pin, GPIO.OUT)
GPIO.setup(led_2_pin, GPIO.OUT)

# Define actions based on messages
def perform_action(topic, message):
#    print(f"Action triggered by message '{message}' on topic '{topic}'")
    # Example: Publish a response
    if topic == "car/drink":
        mix_drink(message)
    elif topic == "control":
        if message == "container_levels":
            drink_container_levels()
        elif message == "calibrate dist sensors":
            calibrate_dist_sensors()
        elif message == "calibrate dist sensor 1":
            calibrate_dist_sensors(1, 0)
        elif message == "calibrate dist sensor 2":
            calibrate_dist_sensors(0, 1)
        elif message.startswith("pump_1 run"):
            # Extract the runtime from the message
            try:
                _, seconds_str = message.split()
                runtime = int(seconds_str)  # Convert to an integer
                if runtime > 10:  # Cap the runtime at 10 seconds
                    runtime = 10
                
                GPIO.output(pump_1_pin, GPIO.HIGH)
                client.publish("drink_machine/status", f"Running pump 1 for {runtime} seconds")
                client.publish("drink_machine/pump/1", "On")
                time.sleep(runtime)  # Run the pump for the specified time
                GPIO.output(pump_1_pin, GPIO.LOW)
                client.publish("drink_machine/pump/1", "Off")                
                client.publish("drink_machine/status", "Idle")
            except ValueError:
                # If message doesn't contain a valid number, handle the error
                client.publish("drink_machine/messages", "Invalid runtime specified for pump 1. Must be below 10 seconds.")

        elif message.startswith("pump_2 run"):
            # Extract the runtime from the message
            try:
                _, seconds_str = message.split()
                runtime = int(seconds_str)  # Convert to an integer
                if runtime > 10:  # Cap the runtime at 10 seconds
                    runtime = 10
                
                GPIO.output(pump_2_pin, GPIO.HIGH)
                client.publish("drink_machine/pump/2", "On")
                client.publish("drink_machine/status", f"Running pump 2 for {runtime} seconds")
                time.sleep(runtime)  # Run the pump for the specified time
                GPIO.output(pump_2_pin, GPIO.LOW)
                client.publish("drink_machine/pump/2", "Off")
                client.publish("drink_machine/status", "Idle")
            except ValueError:
                # If message doesn't contain a valid number, handle the error
                client.publish("drink_machine/messages", "Invalid runtime specified for pump 2. Must be below 10 seconds.")

        elif message.startswith("pump_1 pour"):
            container_1_volume, container_2_volume = drink_container_levels(1)
            # Extract the runtime from the message
            try:
                _, liters_str = message.split()
                liters = int(liters_str)  # Convert to an integer
                if liters > 1:  # Cap the volume at 10 seconds
                    liters = 1
                runtime = liters/(flow_rate_pump_1/60) # how long to run the pump
                if liters <= container_1_volume:
                    GPIO.output(pump_1_pin, GPIO.HIGH)
                    client.publish("drink_machine/pump/1", "On")
                    client.publish("drink_machine/status", f"Pouring {liters} liters from container 1")
                    time.sleep(runtime)  # Run the pump for the specified time
                    GPIO.output(pump_1_pin, GPIO.LOW)
                    client.publish("drink_machine/pump/1", "Off")
                    client.publish("drink_machine/status", "Idle")
                else:
                    client.publish("drink_machine/messages", f"Only {liters} liters left in container 1.")
            except ValueError:
                # If message doesn't contain a valid number, handle the error
                client.publish("drink_machine/messages", "Invalid runtime specified for pump 1.")

        elif message.startswith("pump_2 pour"):
            # Extract the runtime from the message
            try:
                _, liters_str = message.split()
                liters = int(liters_str)  # Convert to an integer
                if liters > 1:  # Cap the volume at 1 liter
                    liters = 1
                runtime = liters/(flow_rate_pump_2/60) # how long to run the pump
                if liters <= container_2_volume:
                    GPIO.output(pump_2_pin, GPIO.HIGH)
                    client.publish("drink_machine/status", f"Pouring {liters} liters from container 2")
                    time.sleep(runtime)  # Run the pump for the specified time
                    GPIO.output(pump_2_pin, GPIO.LOW)
                    client.publish("drink_machine/status", "Idle")
                else:
                    client.publish("drink_machine/messages", f"Only {liters} liters left in container 2.")
            except ValueError:
                # If message doesn't contain a valid number, handle the error
                client.publish("drink_machine/messages", "Invalid runtime specified for pump 1.")

        else:
            client.publish("drink_machine/messages", "Recieved unknown control command.")
    
        



def mix_drink(drink):
    if drink == "soda":
        time_1 = drink_size/(flow_rate_pump_1/60) # how long to run the pump
        # update drink machine status
        client.publish("drink_machine/status", "Pouring soda...")
        GPIO.output(pump_1_pin, GPIO.HIGH)
        time.sleep(time_1) # run pump
        GPIO.output(pump_1_pin, GPIO.LOW)
        # update drink machine status
        client.publish("drink_machine/status", "Idle")
        # update container levels
        drink_container_levels()

    # add elsif for each drink

    else:
        client.publish("drink_machine/messages", "Recieved unknown drink.")

def drink_container_levels(return_value = 0):
    # distance from sensor 1
    GPIO.output(dist_1_trigger_pin, True)
    time.sleep(0.00001)
    GPIO.output(dist_1_trigger_pin, False)
    StartTime = time.time()
    StopTime = time.time()

    while GPIO.input(dist_1_echo_pin) == 0:
        StartTime = time.time()
    while GPIO.input(dist_1_echo_pin) == 1:
        StopTime = time.time()
    TimeElapsed = StopTime - StartTime
    distance_1 = (TimeElapsed*34300)/2 # cm from sensor 1
    if distance_1 < 0 or distance_1 > dist_to_sensor_1:
        volume_1 = 0
        client.publish("drink_machine/messages", f"Invalid reading from distance sensor 1 ({distance_1} cm).")
    else:
        # calculate volume
        height_1 = dist_to_sensor_1 - distance_1 # height of liquid from bottom of container
        r2_1 = r_bottom + (r_top-r_bottom)*(height_1/h_bucket) # radius (cm) at the liquid level in container 1
        volume_1 = ((math.pi*height_1)/3)*(r_bottom**2+r_bottom*r2_1+r2_1**2)/1000 # remaining liquid in container 1 (liters)    

    # distance from sensor 2
    GPIO.output(dist_2_trigger_pin, True)
    time.sleep(0.00001)
    GPIO.output(dist_2_trigger_pin, False)
    StartTime = time.time()
    StopTime = time.time()

    while GPIO.input(dist_2_echo_pin) == 0:
        StartTime = time.time()
    while GPIO.input(dist_2_echo_pin) == 1:
        StopTime = time.time()
    TimeElapsed = StopTime - StartTime
    distance_2 = (TimeElapsed*34300)/2 # cm from sensor 1
    if distance_2 < 0 or distance_2 > dist_to_sensor_2:
        volume_2 = 0
        client.publish("drink_machine/messages", f"Invalid reading from distance sensor 2 ({distance_2} cm).")


    else:
        # calculate volume
        height_2 = dist_to_sensor_2 - distance_2 # height of liquid from bottom of container
        r2_2 = r_bottom + (r_top-r_bottom)*(height_2/h_bucket) # radius (cm) at the liquid level in container 2
        volume_2 = ((math.pi*height_2)/3)*(r_bottom**2+r_bottom*r2_2+r2_2**2)/1000 # remaining liquid in container 2 (liters)
    
    # publish how much is left in each container
    client.publish("drink_machine/container/1/volume", str(volume_1))
    client.publish("drink_machine/container/2/volume", str(volume_2))     

    if volume_1 < 1:
        GPIO.output(led_1_pin, GPIO.HIGH)
    else:
        GPIO.output(led_1_pin, GPIO.LOW)
    if volume_2 < 1:
        GPIO.output(led_2_pin, GPIO.HIGH)
    else:
        GPIO.output(led_2_pin, GPIO.LOW)

    if return_value == 1:
        return volume_1, volume_2

def calibrate_dist_sensors(sensor_1 = 1, sensor_2 = 1):
    global dist_to_sensor_1
    global dist_to_sensor_2
    if sensor_1 == 1:
        # distance from sensor 1
        GPIO.output(dist_1_trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(dist_1_trigger_pin, False)
        StartTime = time.time()
        StopTime = time.time()

        while GPIO.input(dist_1_echo_pin) == 0:
            StartTime = time.time()
        while GPIO.input(dist_1_echo_pin) == 1:
            StopTime = time.time()
        TimeElapsed = StopTime - StartTime
        distance_1 = (TimeElapsed*34300)/2 # cm from sensor 1
        client.publish("drink_machine/messages", f"Sensor 1 distance updated to: {distance_1} cm.")   
        dist_to_sensor_1 = distance_1
    if sensor_2 == 1:
        # distance from sensor 2
        GPIO.output(dist_2_trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(dist_2_trigger_pin, False)
        StartTime = time.time()
        StopTime = time.time()

        while GPIO.input(dist_2_echo_pin) == 0:
            StartTime = time.time()
        while GPIO.input(dist_2_echo_pin) == 1:
            StopTime = time.time()
        TimeElapsed = StopTime - StartTime
        distance_2 = (TimeElapsed*34300)/2 # cm from sensor 2
        client.publish("drink_machine/messages", f"Sensor 2 distance updated to: {distance_2} cm.")  
        dist_to_sensor_2 = distance_2       


# Callback for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to topics
        for topic in topics:
            client.subscribe(topic)
    else:
        print(f"Failed to connect, return code {rc}")

# Callback for when a message is received
def on_message(client, userdata, msg):
    global RUNNING
    topic = msg.topic
    message = msg.payload.decode()
#    print(f"Received message '{message}' on topic '{topic}'")
    
    if topic == "control" and message == "stop":
        client.publish("drink_machine/status", "Received stop command. Shutting down...")
        RUNNING = False
    else:
        perform_action(topic, message)

# Create MQTT client instance
client = mqtt.Client(client_id)
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker
print("Connecting to broker...")
client.connect(broker, port, 60)

# Run the client loop
client.loop_start()  # Start loop in a background thread
try:
    while RUNNING:
        pass  # Keep the script running
except KeyboardInterrupt:
    print("Interrupted by user")
finally:
    client.loop_stop()  # Stop the loop
    client.disconnect()  # Disconnect cleanly
    GPIO.cleanup() # reset GPIO settings
    print("MQTT client disconnected and GPIO cleaned up")
