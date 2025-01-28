import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO 
import time
import math
import threading

# Configuration
broker = "192.168.0.197"  # Replace with your broker's address
port = 1883  # Default MQTT port 
topics = ["customer/1", "car/status", "customer/1", "customer/2", "drink", "control"]  # Topics to subscribe to

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
dist_2_trigger_pin = 17
dist_1_echo_pin = 6
dist_2_echo_pin = 27
led_1_pin = 22 # led for indicating that container 1 needs refilling (turns on with less than a liter left)
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

drinks = ("Gin & tonic", "Gin", "Tonic")
order_queue = []
menu_index = 0 # Index of drink currently shown on the ordering screen
cancel_flag = 0
car_status = "Idle" # Idle or Busy

class customer:
    def __init__(self, number):
        self.number = number
        self.status = "Idle" # Idle, In queue, Ordering, Waiting for drink
        self.shake_count = 0 # cancel order if coaster is shaken 3 times in a row

customer1 = customer(1)
customer2 = customer(2)

def update_car(client, message):
    global customer1
    global customer2
    global menu_index
    global drinks
    global order_queue, car_status
    if message == "IDLE" and len(order_queue) > 0: # if car is idle send to customer
        client.publish("car/command", f"{order_queue[0]}")
        client.loop()
        car_status = "Busy"
    elif message == "ORDERING":
        if order_queue[0] == 1:
            customer1.status = "Ordering"
            client.publish("car/screen", f"{drinks[menu_index]}")
            client.loop()
            client.publish("customer/1/order", "start")
            client.loop()
        elif order_queue[0] == 2:
            customer2.status = "Ordering"
            client.publish("car/screen", f"{drinks[menu_index]}")
            client.loop()
            client.publish("customer/2/order", "start")
            client.loop()
    elif message == "WAITING_DRINK":
        drink = drinks[menu_index]
        mix_drink(client, drink)
        menu_index = 0
        order_queue.pop(0)
        client.publish("ordering_queue", f"{order_queue}")
        client.loop()


def customer_status(client, topic, message):
    global customer1
    global customer2    
    customer = int(topic.split("/")[-1])
    if customer == 1:
        if customer1.status == "In queue" and message == "shake":
            customer1.shake_count += 1
            if customer1.shake_count >= 3:
                queue(client, topic, 0)
                customer1.shake_count = 0
        elif customer1.status == "Idle" and message != "shake":
            queue(client, topic)
        elif customer1.status == "Ordering":
            ordering(client, message, topic)
    elif customer == 2:
        if customer2.status == "In queue" and message == "shake":
            customer2.shake_count += 1
            if customer2.shake_count >= 3:
                queue(client, topic, 0)
        elif customer2.status == "Idle" and message != "shake":
            queue(client, topic)
        elif customer2.status == "Ordering":
            ordering(client, message, topic)

def queue(client, topic, add=1):
    global customer1
    global customer2    
    # add: 1 for add to queue, 0 for remove from queue
    # customer: customer number (position, 1 or 2)
    global order_queue, car_status
    customer = int(topic.split("/")[-1])
    if add == 1 and customer not in order_queue:
        order_queue.append(customer)
        if car_status == "Idle":
            client.publish("car/command", f"{order_queue[0]}")
            client.publish()
            car_status = "Busy"
        if customer == 1:
            customer1.status = "In queue"
        elif customer == 2:
            customer2.status = "In queue"        
    elif add == 0:
        order_queue.remove(customer)
        if customer == 1:
            customer1.status = "Idle"
        elif customer == 2:
            customer2.status = "Idle"
    client.publish("ordering_queue", f"{order_queue}")
    client.loop()

def ordering(client ,message, topic):
    global customer1
    global customer2    
    # cycle through the menu and publish to screen
    # commands: left, right, cancel, confirm
    global order_queue
    global menu_index
    global drinks
    global cancel_flag
    customer = int(topic.split("/")[-1])
    if message == "left":
        menu_index -= 1
        if menu_index == -1:
            menu_index = len(drinks) - 1
        client.publish("car/screen", f"{drinks[menu_index]}")
        client.loop()
    elif message == "right":
        menu_index += 1
        if menu_index == len(drinks):
            menu_index = 0
        client.publish("car/screen", f"{drinks[menu_index]}")
        client.loop()
    elif message == "cancel" or message == "timeout":
        if cancel_flag == 1 or message == "timeout":
            menu_index = 0
            client.publish("car/command", "cancel")
            client.loop()
            if len(order_queue) > 0:
                client.publish("car/command", f"{order_queue[menu_index]}")
                client.loop()
            if customer == 1:
                customer1.status = "Idle"
                client.publish("customer/1/order", "stop")
                client.loop()
            elif customer == 2:
                customer2.status = "Idle"   
                client.publish("customer/2/order", "stop") 
                client.loop()  
            cancel_flag = 0
        else:
            cancel_flag = 1
            client.publish("car/screen", "Shake again to cancel")
            client.loop()
    elif message == "confirm":
        client.publish("car/command", "confirm")
        client.loop()
        if customer == 1:
            customer1.status = "Waiting for drink"
        elif customer == 2:
            customer2.status = "Waiting for drink"


def drink_container_levels(client, return_value = 0):
    # distance from sensor 1
    error_1 = 0
    error_2 = 0
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
        error_1 = 1
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

def calibrate_dist_sensors(client, sensor_1 = 1, sensor_2 = 1):
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
        dist_to_sensor_2 = distance_2      
        if sensor_1 == 0:
            client.publish("drink_machine/messages", f"Sensor 2 distance updated to: {round(distance_2, 1)} cm.")  
            client.loop()            
    if sensor_1 == 1 and sensor_2 == 1:
        client.publish("drink_machine/messages", f"Distance to sensor 1 and 2 updated: {round(distance_1, 1)} cm, {round(distance_2, 1)} cm.")
        client.loop()

def mix_drink(client, drink):
    # container 1 has gin, container 2 has tonic
    global drink_size
    gin_ratio = 0.5
    tonic_ratio = 1 - gin_ratio
    volume_1, volume_2 = drink_container_levels(client, 1)
    if drink == "Gin & tonic":
        if volume_1 > drink_size * gin_ratio and volume_2 > drink_size * tonic_ratio:
            client.publish("drink_machine/drink_status", "0")
            client.loop()
            time_1 = gin_ratio * float(drink_size/(flow_rate_pump_1/60)) # how long to run the gin pump
            time_2 = tonic_ratio * float(drink_size/(flow_rate_pump_2/60)) # how long to run the tonic pump
            # pour gin
            client.publish("drink_machine/status", "Pouring gin...")
            client.loop()
            client.publish("drink_machine/pump/1", "On")
            client.loop()
            GPIO.output(pump_1_pin, GPIO.HIGH)
            start_time = time.monotonic()
            while time.monotonic() - start_time < time_1:
                client.loop(timeout=0.1)
            GPIO.output(pump_1_pin, GPIO.LOW)
            client.publish("drink_machine/pump/1", "Off")
            # pour tonic
            client.publish("drink_machine/status", "Pouring tonic...")
            client.loop()
            client.publish("drink_machine/pump/2", "On")
            client.loop()
            GPIO.output(pump_2_pin, GPIO.HIGH)
            start_time = time.monotonic()
            while time.monotonic() - start_time < time_2:
                client.loop(timeout=0.1)
            GPIO.output(pump_2_pin, GPIO.LOW)
            client.publish("drink_machine/pump/2", "Off")
            client.loop()
            # update drink machine status
            client.publish("drink_machine/status", "Idle")
            client.loop()
            # send ready signal to the car
            client.publish("drink_machine/drink_status", "1")
            client.loop()
            # update container levels
            drink_container_levels(client)            
        elif volume_1 < drink_size * gin_ratio:
            client.publish("drink_machine/messages", "Container 1 needs to be refilled before system can continue.")
            client.loop()
        elif volume_2 < drink_size * tonic_ratio:
            client.publish("drink_machine/messages", "Container 2 needs to be refilled before system can continue.")
            client.loop()
    # add elsif for each drink
    elif drink == "Gin":
        if volume_1 > drink_size:
            client.publish("drink_machine/drink_status", "0")
            client.loop()
            time_1 = gin_ratio * float(drink_size/(flow_rate_pump_1/60)) # how long to run the gin pump
            # pour gin
            client.publish("drink_machine/status", "Pouring gin...")
            client.loop()
            client.publish("drink_machine/pump/1", "On")
            client.loop()
            GPIO.output(pump_1_pin, GPIO.HIGH)
            start_time = time.monotonic()
            while time.monotonic() - start_time < time_1:
                client.loop(timeout=0.1)
            GPIO.output(pump_1_pin, GPIO.LOW)
            client.publish("drink_machine/pump/1", "Off")
            client.loop()
            client.publish("drink_machine/status", "Idle")
            client.loop()  
            # send ready signal to the car
            client.publish("drink_machine/drink_status", "1")
            client.loop()         
            # update container levels
            drink_container_levels(client)            
        else:
            client.publish("drink_machine/messages", "Container 1 needs to be refilled before system can continue.")
            client.loop()
    elif drink == "Tonic":
        if volume_2 > drink_size * tonic_ratio:
            client.publish("drink_machine/drink_status", "0")
            client.loop()
            time_2 = tonic_ratio * float(drink_size/(flow_rate_pump_2/60)) # how long to run the tonic pump
            # pour tonic
            client.publish("drink_machine/status", "Pouring tonic...")
            client.loop()
            client.publish("drink_machine/pump/2", "On")
            client.loop()
            GPIO.output(pump_2_pin, GPIO.HIGH)
            start_time = time.monotonic()
            while time.monotonic() - start_time < time_2:
                client.loop(timeout=0.1)
            GPIO.output(pump_2_pin, GPIO.LOW)
            client.publish("drink_machine/pump/2", "Off")
            client.loop()
            # update drink machine status
            client.publish("drink_machine/status", "Idle")
            client.loop()
            # send ready signal to the car
            client.publish("drink_machine/drink_status", "1")
            client.loop()            
            # update container levels
            drink_container_levels(client)
        else:
            client.publish("drink_machine/messages", "Container 2 needs to be refilled before system can continue.")
            client.loop()            
    else:
        client.publish("drink_machine/messages", "Recieved unknown drink.")
        client.loop()
        client.publish("drink_machine/drink_status", "0")
        client.loop()

def pump_pour(client, message, pump_number):
    container_1_volume, container_2_volume = drink_container_levels(client, return_value=1)
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
    volume_1, volume_2 = drink_container_levels(client, 1)
    if pump_number == 1:
        if volume_1 < 1:
            client.publish("drink_machine/messages", "The container needs at least 1 liter before calibration can start.")
            client.loop()
        else:
            try:
                if runtime < 10 or runtime > 20:
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
                    new_volume_1, new_volume_2 = drink_container_levels(client, 1)
                    pumped_volume = volume_1 - new_volume_1
                    flow_rate_pump_1 = pumped_volume * (runtime / 60)
                    client.publish("drink_machine/messages", f"Pumped {pumped_volume} liters.\nFlow rate for pump 1 updated to {flow_rate_pump_1} liters/min.")
                    client.loop()
                else:
                    client.publish("drink_machine/messages", "Pump 1 calibration cancelled.")

            except ValueError:
                client.publish("drink_machine/messages", "Calibration time needs to be between 10 and 20 seconds.")
                client.loop()

    elif pump_number == 2:
        if volume_2 < 1:
            client.publish("drink_machine/messages", "The container needs at least 1 liter before calibration can start.")
            client.loop()
        else:
            try:
                if runtime < 10 or runtime > 20:
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
                    new_volume_1, new_volume_2 = drink_container_levels(client, 1)
                    pumped_volume = volume_2 - new_volume_2
                    flow_rate_pump_2 = pumped_volume * (runtime / 60)
                    client.publish("drink_machine/messages", f"Pumped {pumped_volume} liters.\nFlow rate for pump 2 updated to {flow_rate_pump_2} liters/min.")
                    client.loop()
                else:
                    client.publish("drink_machine/messages", "Pump 2 calibration cancelled.")

            except ValueError:
                client.publish("drink_machine/messages", "Calibration time needs to be between 10 and 20 seconds.")
                client.loop()

def commands(client):
    message = """topic: drink
    1: Gin
    2: Tonic
    3: Gin & tonic
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

def perform_action(client, topic, message):
    if topic == "drink":
        mix_drink_threaded(client, message)
    elif topic == "control":
        if message == "container_levels":
            drink_container_levels(client)
        elif message == "calibrate dist sensors":
            calibrate_dist_sensors(client)
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
    elif topic == "customer/1" or topic == "customer/2":
        customer_status(client, topic, message)
    elif topic == "car/status":
        update_car(client, message)

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