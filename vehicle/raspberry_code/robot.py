import time
import cv2
import pigpio
import paho.mqtt.client as mqtt
from enum import Enum

from pigpio import INPUT

from motor import Motor
from vision_module import VisionModule
from lcd_controller import LcdController

LEFT_MOTOR_PWM_GPIO = 18
LEFT_MOTOR_DIRECTION_GPIOS = (23, 24)
RIGHT_MOTOR_PWM_GPIO = 13
RIGHT_MOTOR_DIRECTION_GPIOS = (5, 6)
PHOTODIODE_GPIO = 10

I2C_BUS = 1
I2C_ADDRESS = 0x27

CAMERA_ID = 0

T = 0.1

BROKER = "192.168.0.197"  # Replace with your broker's address
PORT = 1883  # Default MQTT port
TOPICS = ["car/drink", "control"]  # Topics to subscribe to
ORDER_PICKED = 10
ORDER_CANCELED = 11
BASE = 0


class State(Enum):
    IDLE = 1
    FOLLOWING_LINE_MAIN = 2
    FOLLOWING_LINE_TO_CUSTOMER = 3
    ORDERING = 4
    WAITING_FOR_CUP = 5
    RETURNING_TO_MAIN_LINE = 6
    GOING_TO_DRINK_MACHINE = 7


class Robot:
    def __init__(self):
        self.state = State.IDLE
        self.customer = None
        self.target_marker = None
        self.order_finished = False

        self.pi_daemon = pigpio.pi()
        self.vision = VisionModule(CAMERA_ID)
        self.left_motor = Motor(self.pi_daemon, LEFT_MOTOR_PWM_GPIO, LEFT_MOTOR_DIRECTION_GPIOS)
        self.right_motor = Motor(self.pi_daemon, RIGHT_MOTOR_PWM_GPIO, RIGHT_MOTOR_DIRECTION_GPIOS)
        self.lcd_controller = LcdController(self.pi_daemon, I2C_BUS, I2C_ADDRESS)
        self.pi_daemon.set_mode(PHOTODIODE_GPIO, INPUT)
        self.client = mqtt.Client("robot")
        # Assign event handlers
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # Connect to the broker asynchronously (non-blocking)
        self.client.connect_async(BROKER, PORT, 60)
        self.client.loop_start()  # Start non-blocking loop

    def main_loop(self):
        while True:
            match self.state:
                case State.IDLE:
                    time.sleep(T)
                    continue
                case State.FOLLOWING_LINE_MAIN:
                    self.target_marker = self.customer
                    self.line_following_loop()
                case State.FOLLOWING_LINE_TO_CUSTOMER:
                    self.target_marker = 10
                    self._left_turn_maneuver()

                    self.line_following_loop()

                case State.ORDERING:
                    self.right_motor.update_speed(0)
                    self.left_motor.update_speed(0)

                case State.WAITING_FOR_CUP:
                    self.cup_waiting_loop()
                case State.RETURNING_TO_MAIN_LINE:
                    self.target_marker = self.customer
                    self._left_turn_maneuver()
                    self._left_turn_maneuver()

                    self.line_following_loop()
                case State.GOING_TO_DRINK_MACHINE:
                    self._left_turn_maneuver()
                    self.target_marker = BASE

                    self.line_following_loop()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            # Subscribe to all topics upon successful connection
            for topic in TOPICS:
                self.client.subscribe(topic)
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        data = msg.payload.decode("utf-8")
        if topic == "car/customer_ready":
            self.state = State.FOLLOWING_LINE_MAIN
            self.customer = int(data)
        elif topic == "car/customer_order":
            if data.isdigit():

                if int(data) == ORDER_PICKED:
                    self.state = State.WAITING_FOR_CUP
                    self.lcd_controller.write_new_line("Put a cup in a  cupholder")
                    self.order_finished = True
                elif int(data) == ORDER_CANCELED:
                    self.state = State.RETURNING_TO_MAIN_LINE
                    self.order_finished = True
            else:
                self.lcd_controller.write_new_line(data)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        print("Disconnected from MQTT broker.")

    def publish(self, topic, message):
        result = self.client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Message '{message}' sent to topic '{topic}'")
        else:
            print(f"Failed to publish message to {topic}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped.")

    def line_following_loop(self):
        while True:
            t1 = time.time()
            self.vision.new_frame()
            result = self.vision.identify_surroundings()
            if result:
                self.publish('car/status', result[0])
                if result[0] == self.target_marker:
                    match self.state:
                        case State.FOLLOWING_LINE_MAIN:
                            self.state = State.FOLLOWING_LINE_TO_CUSTOMER
                            break
                        case State.FOLLOWING_LINE_TO_CUSTOMER:
                            self.state = State.ORDERING
                            break
                        case State.RETURNING_TO_MAIN_LINE:
                            self.state = State.GOING_TO_DRINK_MACHINE
                            break
                        case State.GOING_TO_DRINK_MACHINE:
                            break
            result = self.vision.line_analysis()

            if result is None:
                print("I am lost, pls help")
                break
            bucket = self._analyse_line_results(result[0])
            match bucket:
                case 0:
                    self.right_motor.update_speed(0.9)
                    self.left_motor.update_speed(0.5)
                case 1:
                    self.right_motor.update_speed(0.95)
                    self.left_motor.update_speed(0.8)
                case 2:
                    self.right_motor.update_speed(1)
                    self.left_motor.update_speed(1)
                case 3:
                    self.right_motor.update_speed(0.8)
                    self.left_motor.update_speed(0.95)
                case 4:
                    self.right_motor.update_speed(0.5)
                    self.left_motor.update_speed(0.9)
            print(f"{time.time() - t1} finished loop")
            time.sleep(T)

    def _analyse_line_results(self, cx, cy=0):
        width = self.vision.cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        bucket_size = width + 1 // 5
        bucket = cx // bucket_size
        return bucket

    def _left_turn_maneuver(self):
        self.right_motor.update_speed(1)
        self.left_motor.update_speed(-1)
        # TODO magic number
        time.sleep(0.3)

    def ordering_loop(self):
        while not self.order_finished:
            time.sleep(T)

    def cup_waiting_loop(self):
        status = True
        while status:
            status = not self.pi_daemon.read(PHOTODIODE_GPIO)
        self.publish('car/status', "Cup picked up")
        self.state = State.RETURNING_TO_MAIN_LINE

    def kill_all(self):
        self.left_motor.kill_self()
        self.right_motor.kill_self()
        self.vision.kill_self()
        self.lcd_controller.clear_screen()
        self.lcd_controller.close()
