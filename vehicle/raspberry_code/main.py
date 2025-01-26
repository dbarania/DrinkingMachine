import pigpio
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


def main():
    pi_daemon = pigpio.pi()
    communication = CommunicationModule()
    vision = VisionModule(CAMERA_ID)
    left_motor = Motor(pi_daemon, LEFT_MOTOR_PWM_GPIO, LEFT_MOTOR_DIRECTION_GPIOS)
    right_motor = Motor(pi_daemon, RIGHT_MOTOR_PWM_GPIO, RIGHT_MOTOR_DIRECTION_GPIOS)
