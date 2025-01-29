import time

import cv2
import pigpio
import paho.mqtt.client as mqtt
from enum import Enum
import motors_controller
from vision_module import VisionModule
from lcd_controller import LcdController
from cup_switch import CupSwitch

SWITCH_GPIO = 10

I2C_BUS = 1
I2C_ADDRESS = 0x27

CAMERA_ID = 0

BROKER = "192.168.0.197"
PORT = 1883
TOPICS = ["customers/new", "control", "drink_machine/drink_status", "car/command", "car/screen"]

ORDER_PICKED = 10
ORDER_CANCELED = 11

BASE = 0
CUSTOMER_ENDPOINT = 10


class State(Enum):
    IDLE = 1
    MAIN_LINE = 2
    TURNING_TO_CUSTOMER = 3
    CUSTOMER_LINE = 4
    ORDERING = 5
    WAITING_CUP = 6
    ROTATING_180 = 7
    GO_BACK_LINE = 8
    TURNING_TO_MAIN = 9
    GOING_TO_MACHINE = 10
    WAITING_DRINK = 11


class Robot:

    def __init__(self, i2c=True, camera=True, connection=True):
        self._state = State.IDLE
        self.pi_daemon = pigpio.pi()
        if camera:
            self.vision = VisionModule(CAMERA_ID)
        self.motors_controller = motors_controller.MotorsController(self.pi_daemon)
        self.switch = CupSwitch(self.pi_daemon, SWITCH_GPIO)
        if i2c:
            self.lcd_controller = LcdController(self.pi_daemon, I2C_BUS, I2C_ADDRESS)
        self.customer = None
        self.target_marker = None
        if connection:
            self.client = mqtt.Client('Bartender')
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.connect_async(BROKER, PORT, 60)
            self.client.loop_start()  # Start non-blocking loop
        self.delivering = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: State):
        self._state = value
        self.publish_state()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            # Subscribe to all topics upon successful connection
            for topic in TOPICS:
                self.client.subscribe(topic)
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        print(f"Got a message from {msg.topic} with content: {msg.payload.decode().strip()}")
        topic = msg.topic
        data = msg.payload.decode("utf-8")
        data_int = int(data) if data.isdigit() else None
        match topic:
            case "customers/new":
                if data_int:
                    self.customer = self.customer[0]
                    self.target_marker = self.customer
                    self.state = State.MAIN_LINE
            case "car/screen":
                self.lcd_controller.write_new_line(data)
            case "car/command":
                if msg == "cancel":
                    self.state = State.ROTATING_180
                elif msg == "confirm":
                    self.state = State.WAITING_CUP
            case "drink_machine/drink_status":
                if data_int == 1:
                    self.state = State.MAIN_LINE
                    self.target_marker = self.customer
                    self.delivering = True

    def publish(self, topic, message):

        result = self.client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Message '{message}' sent to topic '{topic}'")
        else:
            print(f"Failed to publish message to {topic}")

    def stop_connection(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped.")

    def publish_state(self):
        self.publish("car/status", self.state.name)

    def main_loop(self):
        while True:
            match self.state:
                case State.IDLE:
                    continue
                case State.MAIN_LINE:
                    ret = self.move()
                    if ret:
                        self.state = State.TURNING_TO_CUSTOMER
                case State.TURNING_TO_CUSTOMER:
                    self.turning_left()
                    self.state = State.CUSTOMER_LINE
                    self.target_marker = CUSTOMER_ENDPOINT
                case State.CUSTOMER_LINE:
                    ret = self.move()
                    if ret:
                        self.stop()
                        self.state = State.ORDERING
                case State.ORDERING:
                    self.ordering_loop()
                case State.WAITING_CUP:
                    self.waiting_cup_loop(self.delivering)
                    self.state = State.ROTATING_180
                case State.ROTATING_180:
                    self.rotate_180()
                    self.state = State.GO_BACK_LINE
                case State.GO_BACK_LINE:
                    self.target_marker = self.customer
                    ret = self.move()
                    if ret:
                        self.stop()
                        self.state = State.TURNING_TO_MAIN
                case State.TURNING_TO_MAIN:
                    self.turning_left()
                    if self.delivering:
                        # TODO finish this logic
                        self.state = State.IDLE
                    else:
                        self.state = State.GOING_TO_MACHINE
                    self.target_marker = BASE
                case State.GOING_TO_MACHINE:
                    ret = self.move()
                    if ret:
                        self.state = State.WAITING_DRINK
                        self.stop()
                case State.WAITING_DRINK:
                    self.waiting_drink_loop()

    def _analyse_line_results(self, cx, cy=0):
        width = self.vision.cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        if cx <= 2 * width / 5:
            mode = 0
        elif 2 * width / 5 < cx <= 3 * width / 5:
            mode = 1
        else:
            mode = 2
        return mode

    def turning_left(self):
        self.motors_controller.turning_left()
        while True:
            self.vision.new_frame()
            ret = self.vision.line_analysis()
            if ret is not None:
                break

    def rotate_180(self):
        turn_time = 0.3
        self.motors_controller.turn_in_place(motors_controller.LEFT)
        time.sleep(turn_time)
        while True:
            self.vision.new_frame()
            ret = self.vision.line_analysis()
            if ret is not None:
                break

    def move(self):
        t1 = time.time()
        self.vision.new_frame()
        marker_id = self.vision.identify_surroundings()
        if marker_id is not None:
            self.publish("car/position", marker_id)
            if marker_id == self.target_marker:
                return True
        ret = self.vision.line_analysis()
        if ret is None:
            print("Don't see a line, going with last control")
        else:
            print(ret[0])
            mode = self._analyse_line_results(ret[0])
            print(mode)
            self.move_mode(mode)
        return False

    def stop(self):
        self.motors_controller.stop()

    def ordering_loop(self):
        while self.state == State.ORDERING:
            time.sleep(0.1)

    def waiting_cup_loop(self, target):
        status = None
        while status == target:
            status = self.switch.read()
        if target:
            print("delivery finished")
            self.publish('customer/status', "finished")

    def waiting_drink_loop(self):
        while self.state == State.WAITING_DRINK:
            time.sleep(0.1)

    def move_mode(self, mode):
        match mode:
            case 0:
                self.motors_controller.move_slight_left()
            case 1:
                self.motors_controller.move_straight(motors_controller.FORWARD)
            case 2:
                self.motors_controller.move_slight_left()
