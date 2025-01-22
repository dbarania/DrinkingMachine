import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO 
import time
import math
import threading
import queue

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
pump_1_pin = 23
pump_2_pin = 24
dist_1_trigger_pin = 5
dist_2_trigger_pin = 21
dist_1_echo_pin = 6
dist_2_echo_pin = 18
led_1_pin = 17 # led for indicating that container 1 needs refilling (turns on with less than a liter left)
led_2_pin = 27 # led for indicating that container 2 needs refilling (turns on with less than a liter left)

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

def container_levels_threaded(client, return_value = 0):
    result_queue = queue.Queue()
    threading.Thread(target=drink_container_levels, args=(client, return_value, result_queue)).start()

def calibrate_dist_sensors_threaded(client, sensor_1 = 1, sensor_2 = 2, return_dist = 0, result_queue = None):
    threading.Thread(target = calibrate_dist_sensors, args=(client, sensor_1, sensor_2, return_dist)).start()

def drink_container_levels(client, return_value = 0, result_queue = None):
    # distance from sensor 1

    error_1 = 0
    error_2 = 0
    calibrate_dist_sensors_threaded(client, 1, 1, 1, result_queue)
    distance_1, distance_2 = result_queue.get()
    print(f"{distance_1}, {distance_2}")
    if distance_1 < 0 or distance_1 > dist_to_sensor_1:
        volume_1 = 0
        error_1 = 1
    else:
        # calculate volume
        height_1 = dist_to_sensor_1 - distance_1 # height of liquid from bottom of container
        r2_1 = r_bottom + (r_top-r_bottom)*(height_1/h_bucket) # radius (cm) at the liquid level in container 1
        volume_1 = ((math.pi*height_1)/3)*(r_bottom**2+r_bottom*r2_1+r2_1**2)/1000 # remaining liquid in container 1 (liters)    

    if distance_2 < 0 or distance_2 > dist_to_sensor_2:
        volume_2 = 0
        error_2 = 1

    else:
        # calculate volume
        height_2 = dist_to_sensor_2 - distance_2 # height of liquid from bottom of container
        r2_2 = r_bottom + (r_top-r_bottom)*(height_2/h_bucket) # radius (cm) at the liquid level in container 2
        volume_2 = ((math.pi*height_2)/3)*(r_bottom**2+r_bottom*r2_2+r2_2**2)/1000 # remaining liquid in container 2 (liters)
    
    if error_1 == 1 and error_2 == 0:
        client.publish("drink_machine/messages", f"Invalid reading from distance sensor 1 ({round(distance_1, 1)} cm).")
        client.loop()
    if error_2 == 1 and error_1 == 0:
        client.publish("drink_machine/messages", f"Invalid reading from distance sensor 2 ({round(distance_2, 1)} cm).")
        client.loop()
    if error_1 == 1 and error_2 == 1:
        client.publish("drink_machine/messages", f"Invalid readings from distance sensors 1 and 2: {round(distance_1, 1)} cm, {round(distance_2, 1)} cm.")
        client.loop()

    # publish how much is left in each container
    client.publish("drink_machine/container/1/volume", str(volume_1))
    client.loop()
    client.publish("drink_machine/container/2/volume", str(volume_2)) 
    client.loop()    

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

def calibrate_dist_sensors(client, sensor_1 = 1, sensor_2 = 1, return_dist = 0, result_queue = None):
    global dist_to_sensor_1
    global dist_to_sensor_2
    if sensor_1 == 1:
        # distance from sensor 1
        GPIO.output(dist_1_trigger_pin, True)
        time.sleep(0.00001)
        GPIO.output(dist_1_trigger_pin, False)
        StartTime = time.time()
        StopTime = time.time()
        start_time = time.time()

        while GPIO.input(dist_1_echo_pin) == 0:
            StartTime = time.time()
            if time.time() - start_time > 2:
                print("timeout sensor 1")
                break
        while GPIO.input(dist_1_echo_pin) == 1:
            StopTime = time.time()
            if time.time() - start_time > 2:
                break
        TimeElapsed = StopTime - StartTime
        distance_1 = (TimeElapsed*34300)/2 # cm from sensor 1
        if return_dist == 0:
            dist_to_sensor_1 = distance_1
            if sensor_2 == 0:
                client.publish("drink_machine/messages", f"Sensor 1 distance updated to: {round(distance_1, 1)} cm.")   
                client.loop()
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
        if return_dist == 0:
            dist_to_sensor_2 = distance_2      
            if sensor_1 == 0:
                client.publish("drink_machine/messages", f"Sensor 2 distance updated to: {round(distance_2, 1)} cm.")  
                client.loop()            
    if sensor_1 == 1 and sensor_2 == 1 and return_dist == 0:
        client.publish("drink_machine/messages", f"Distance to sensor 1 and 2 updated: {round(distance_1, 1)} cm, {round(distance_2, 1)} cm.")
        client.loop()

    if return_dist == 1:
        return distance_1, distance_2
    
    if result_queue is not None:
        result_queue.put((distance_1, distance_2))

def mix_drink(client, drink):
    global drink_size
    if drink == "soda":
        volume_1, volume_2 = container_levels_threaded(client, 1)
        if volume_1 > drink_size:
            time_1 = float(drink_size/(flow_rate_pump_1/60)) # how long to run the pump
            # update drink machine status
            client.publish("drink_machine/status", "Pouring soda...")
            client.loop()
            client.publish("drink_machine/pump/1", "On")
            client.loop()
            GPIO.output(pump_1_pin, GPIO.HIGH)
            start_time = time.monotonic()
            while time.monotonic() - start_time < time_1:
                client.loop(timeout=0.1)
            GPIO.output(pump_1_pin, GPIO.LOW)
            client.publish("drink_machine/pump/1", "Off")
            # update drink machine status
            client.publish("drink_machine/status", "Idle")
            client.loop()
            # update container levels
            container_levels_threaded(client)
        else:
            client.publish("drink_machine/messages", "Container 1 needs to be refilled before system can continue.")
    # add elsif for each drink

    else:
        client.publish("drink_machine/messages", "Recieved unknown drink.")
        client.loop()

def pump_pour(client, message, pump_number):
    container_1_volume, container_2_volume = container_levels_threaded(client, return_value=1)
    if pump_number == 1:
        # Extract liters from the message
        try:
            _, liters_str = message.split("pour")
            liters = float(liters_str)  # Convert to an integer
            if liters > 1:  # Cap the volume at 10 seconds
                liters = 1
            runtime = liters/(flow_rate_pump_1/60) # how long to run the pump
            if liters <= container_1_volume:
                GPIO.output(pump_1_pin, GPIO.HIGH)
                client.publish("drink_machine/pump/1", "On")
                client.loop()
                client.publish("drink_machine/status", f"Pouring {liters} liters from container 1")
                client.loop()
                start_time = time.monotonic()
                while time.monotonic() - start_time < runtime:
                    client.loop(timeout=0.1)                
                GPIO.output(pump_1_pin, GPIO.LOW)
                client.publish("drink_machine/pump/1", "Off")
                client.loop()
                client.publish("drink_machine/status", "Idle")
                client.loop()
            else:
                client.publish("drink_machine/messages", f"Only {container_1_volume} liters left in container 1.")
                client.loop()
        except ValueError:
            # If message doesn't contain a valid number, handle the error
            client.publish("drink_machine/messages", "Invalid runtime specified for pump 1.")
            client.loop()
    else:
        # Extract liters from the message
        try:
            _, liters_str = message.split("pour")
            liters = float(liters_str)  # Convert to an integer
            if liters > 1:  # Cap the volume at 1 liter
                liters = 1
            runtime = liters/(flow_rate_pump_2/60) # how long to run the pump
            if liters <= container_2_volume:
                GPIO.output(pump_2_pin, GPIO.HIGH)
                client.publish("drink_machine/status", f"Pouring {liters} liters from container 2")
                client.loop()
                start_time = time.monotonic()
                while time.monotonic() - start_time < runtime:
                    client.loop(timeout=0.1)    
                GPIO.output(pump_2_pin, GPIO.LOW)
                client.publish("drink_machine/status", "Idle")
                client.loop()
            else:
                client.publish("drink_machine/messages", f"Only {container_2_volume} liters left in container 2.")
                client.loop()
        except ValueError:
            # If message doesn't contain a valid number, handle the error
            client.publish("drink_machine/messages", "Invalid runtime specified for pump 2.")
            client.loop()


def pump_run(client, message, pump_number):
    if pump_number == 1:
        # Extract the runtime from the message
        try:
            _, number = message.split("run")
            runtime = int(number)  # Convert to an integer
            n = runtime
            if runtime > 10:  # Cap the runtime at 10 seconds
                runtime = 10
            
            GPIO.output(pump_1_pin, GPIO.HIGH)
            client.publish("drink_machine/pump/1", "On")
            client.loop()
            start_time = time.monotonic()
            last_updated_time = start_time
            client.publish("drink_machine/status", f"Running pump 1 for {n} seconds...")
            client.loop()
            n -= 1
            while time.monotonic() - start_time < runtime:
                if GPIO.input(pump_1_pin) == GPIO.HIGH:
                    current_time = time.monotonic()
                    if current_time - last_updated_time >= 1:
                        client.publish("drink_machine/status", f"Running pump 1 for {n} seconds...")
                        n -= 1
                        last_updated_time = current_time
                    client.loop(timeout=0.1)   
                else:
                    break
            GPIO.output(pump_1_pin, GPIO.LOW)
            client.publish("drink_machine/pump/1", "Off")     
            client.loop()           
            client.publish("drink_machine/status", "Idle")
            client.loop()
        except ValueError:
            # If message doesn't contain a valid number, handle the error
            client.publish("drink_machine/messages", "Invalid runtime specified for pump 1. Can be max 10 seconds.")
            client.loop()
    else:
        # Extract the runtime from the message
        try:
            _, number = message.split("run")
            runtime = int(number)  # Convert to an integer
            n = runtime
            if runtime > 10:  # Cap the runtime at 10 seconds
                runtime = 10
            GPIO.output(pump_2_pin, GPIO.HIGH)
            client.publish("drink_machine/pump/2", "On")
            client.loop()
            start_time = time.monotonic()
            last_updated_time = start_time
            client.publish("drink_machine/status", f"Running pump 2 for {n} seconds...")
            client.loop()
            n -= 1
            while time.monotonic() - start_time < runtime:
                if GPIO.input(pump_2_pin) == GPIO.HIGH:
                    current_time = time.monotonic()
                    if current_time - last_updated_time >= 1:
                        client.publish("drink_machine/status", f"Running pump 2 for {n} seconds...")
                        n -= 1
                        last_updated_time = current_time
                    client.loop(timeout=0.1)   
                else:
                    break 
            GPIO.output(pump_2_pin, GPIO.LOW)
            client.publish("drink_machine/pump/2", "Off")
            client.loop()
            client.publish("drink_machine/status", "Idle")
            client.loop()
        except ValueError:
            # If message doesn't contain a valid number, handle the error
            client.publish("drink_machine/messages", "Invalid runtime specified for pump 2. Must be below 10 seconds.")
            client.loop()

def stop_pumps(client):
    GPIO.output(pump_1_pin, GPIO.LOW)
    GPIO.output(pump_2_pin, GPIO.LOW)
    client.publish("drink_machine/pump/1", "Off")
    client.loop()
    client.publish("drink_machine/pump/2", "Off")
    client.loop()
    client.publish("drink_machine/status", "Idle")
    client.loop()
    client.publish("drink_machine/messages", "Pumps stopped.")
    client.loop()

def calibrate_pump(client, message, pump_number):
    global flow_rate_pump_1
    global flow_rate_pump_2
    _, number = message.split("calibrate")
    runtime = int(number)
    n = runtime
    completed = True
    volume_1, volume_2 = container_levels_threaded(client, 1)
    if pump_number == 1:
        if volume_1 < 1:
            client.publish("drink_machine/messages", "The container needs at least 1 liter before calibration can start.")
            client.loop()
        else:
            try:
                if runtime < 5 or runtime > 10:
                    raise ValueError("Not valid number")
                GPIO.output(pump_1_pin, GPIO.HIGH)
                client.publish("drink_machine/pump/1", "On")
                client.loop()
                start_time = time.monotonic()
                last_updated_time = start_time
                client.publish("drink_machine/status", f"Calibrating pump 1 for {n} seconds...")
                client.loop()
                n -= 1
                while time.monotonic() - start_time < runtime:
                    if GPIO.input(pump_1_pin) == GPIO.HIGH:
                        current_time = time.monotonic()
                        if current_time - last_updated_time >= 1:
                            client.publish("drink_machine/status", f"Calibrating pump 1 for {n} seconds...")
                            n -= 1
                            last_updated_time = current_time
                        client.loop(timeout=0.1)   
                    else:
                        completed = False
                        break  
                if completed == True:
                    GPIO.output(pump_1_pin, GPIO.LOW)
                    client.publish("drink_machine/pump/1", "Off")
                    client.loop()
                    client.publish("drink_machine/status", "Idle")
                    client.loop()
                    new_volume_1, new_volume_2 = container_levels_threaded(client)
                    pumped_volume = volume_1 - new_volume_1
                    flow_rate_pump_1 = pumped_volume * (runtime / 60)
                    client.publish("drink_machine/messages", f"Pumped {pumped_volume} liters.\nFlow rate for pump 1 updated to {flow_rate_pump_1} liters/min.")
                    client.loop()
                else:
                    client.publish("drink_machine/messages", "Pump 1 calibration cancelled.")

            except ValueError:
                client.publish("drink_machine/messages", "Calibration time needs to be between 5 and 10 seconds.")
                client.loop()

    elif pump_number == 2:
        if volume_2 < 1:
            client.publish("drink_machine/messages", "The container needs at least 1 liter before calibration can start.")
            client.loop()
        else:
            try:
                if runtime < 5 or runtime > 10:
                    raise ValueError("Not valid number")
                GPIO.output(pump_2_pin, GPIO.HIGH)
                client.publish("drink_machine/pump/2", "On")
                client.loop()
                start_time = time.monotonic()
                last_updated_time = start_time
                client.publish("drink_machine/status", f"Calibrating pump 2 for {n} seconds...")
                client.loop()
                n -= 1
                while time.monotonic() - start_time < runtime:
                    if GPIO.input(pump_2_pin) == GPIO.HIGH:
                        current_time = time.monotonic()
                        if current_time - last_updated_time >= 1:
                            client.publish("drink_machine/status", f"Calibrating pump 2 for {n} seconds...")
                            n -= 1
                            last_updated_time = current_time
                        client.loop(timeout=0.1)   
                    else:
                        completed = False
                        break  
                if completed == True:
                    GPIO.output(pump_2_pin, GPIO.LOW)
                    client.publish("drink_machine/pump/2", "Off")
                    client.loop()
                    client.publish("drink_machine/status", "Idle")
                    client.loop()
                    new_volume_1, new_volume_2 = container_levels_threaded(client)
                    pumped_volume = volume_2 - new_volume_2
                    flow_rate_pump_2 = pumped_volume * (runtime / 60)
                    client.publish("drink_machine/messages", f"Pumped {pumped_volume} liters.\nFlow rate for pump 2 updated to {flow_rate_pump_2} liters/min.")
                    client.loop()
                else:
                    client.publish("drink_machine/messages", "Pump 2 calibration cancelled.")

            except ValueError:
                client.publish("drink_machine/messages", "Calibration time needs to be between 5 and 10 seconds.")
                client.loop()

def commands(client):
    message = """topic: car/drink
    1: soda
topic: control
    1: container_levels (updates how many liters are left in all containers)
    2: calibrate dist sensors (run when both containers are empty)
    3: calibrate dist sensor 1 (run when container 1 is empty)
    4: calibrate dist sensor 2 (run when container 2 is empty)
    5: pump_1 calibrate x (calibrate pump 1. Turns on pump 1 for x seconds)
    6: pump_2 calibrate x (calibrate pump 2. Turns on pump 2 for x seconds)
    7: pump_1 run x (run pump 1 for x seconds. x is int <= 10)
    8: pump_2 run x (run pump 2 for x seconds. x is int <= 10)
    9: pump_1 pour x (pour x liters from container 1. x is float <= 1)
    10: pump_2 pour x (pour x liters from container 2. x is float <= 1)
    11: stop (stops any running pump)
    12: commands (show all commands)"""
    client.publish("drink_machine/messages", message)
    client.loop()

def calibrate_pump_threaded(client, message, pump_number):
    threading.Thread(target=calibrate_pump, args=(client, message, pump_number)).start()

def mix_drink_threaded(client, drink):
    threading.Thread(target=mix_drink, args=(client, drink)).start()

def pump_pour_threaded(client, message, pump_number):
    threading.Thread(target=pump_pour, args=(client, message, pump_number)).start()

def pump_run_threaded(client, message, pump_number):
    threading.Thread(target=pump_run, args=(client, message, pump_number)).start()

# Define actions based on messages
def perform_action(client, topic, message):
    # Example: Publish a response
    if topic == "car/drink":
        mix_drink_threaded(client, message)
    elif topic == "control":
        if message == "container_levels":
            container_levels_threaded(client)
        elif message == "calibrate dist sensors":
            calibrate_dist_sensors_threaded(client)
        elif message == "calibrate dist sensor 1":
            calibrate_dist_sensors(client, 1, 0)
        elif message == "calibrate dist sensor 2":
            calibrate_dist_sensors(client, 0, 1)
        elif message.startswith("pump_1 calibrate"):
            calibrate_pump_threaded(client, message, 1)
        elif message.startswith("pump_2 calibrate"):
            calibrate_pump_threaded(client, message, 2)
        elif message.startswith("pump_1 run"):
            pump_run_threaded(client, message, 1)
        elif message.startswith("pump_2 run"):
            pump_run_threaded(client, message, 2)
        elif message.startswith("pump_1 pour"):
            pump_pour_threaded(client, message, 1)
        elif message.startswith("pump_2 pour"):
            pump_pour_threaded(client, message, 2)
        elif message == "stop":
            stop_pumps(client)
        elif message == "commands":
            commands(client)
        else:
            client.publish("drink_machine/messages", "Recieved unknown control command.\nUse 'commands' to see all commands.")
            client.loop()
    
        




 


# Callback for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to topics
        for topic in topics:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
        client.publish("drink_machine/status", "Idle")
        client.publish("drink_machine/pump/1", "Off")
        client.publish("drink_machine/pump/2", "Off")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback for when a message is received
def on_message(client, userdata, msg):
    global RUNNING
    topic = msg.topic
    message = msg.payload.decode().strip()
    
    if topic == "control" and message == "exit":
        client.publish("drink_machine/status", "Received stop command. Shutting down...")
        RUNNING = False

    else:
        perform_action(client, topic, message)

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
