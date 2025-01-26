import pigpio
from enum import Enum
from motor import Motor
from vision_module import VisionModule
from lcd_controller import LcdController
from communication_module import CommunicationModule

LEFT_MOTOR_PWM_GPIO = 18
LEFT_MOTOR_DIRECTION_GPIOS = (23, 24)
RIGHT_MOTOR_PWM_GPIO = 13
RIGHT_MOTOR_DIRECTION_GPIOS = (5, 6)

I2C_DATA_GPIO = 2
I2C_CLK_GPIO = 2

CAMERA_ID = 0

T = 0.1


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
        self.pi_daemon = pigpio.pi()
        self.communication = CommunicationModule()
        self.vision = VisionModule(CAMERA_ID)
        self.left_motor = Motor(self.pi_daemon, LEFT_MOTOR_PWM_GPIO, LEFT_MOTOR_DIRECTION_GPIOS)
        self.right_motor = Motor(self.pi_daemon, RIGHT_MOTOR_PWM_GPIO, RIGHT_MOTOR_DIRECTION_GPIOS)

    def mainloop(self):
        while True:
            match self.state:
                case State.IDLE
