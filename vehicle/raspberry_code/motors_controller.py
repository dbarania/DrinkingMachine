import pigpio
from motor import Motor
from time import sleep

LEFT_MOTOR_PWM_GPIO = 18
LEFT_MOTOR_DIRECTION_GPIOS = (23, 24)
RIGHT_MOTOR_PWM_GPIO = 13
RIGHT_MOTOR_DIRECTION_GPIOS = (5, 6)

LEFT = 1
RIGHT = -1
FORWARD = 1
BACKWARD = -1

DEFAULT_SPEED = 0.75


class MotorsController:
    def __init__(self, pi: pigpio):
        self.pi_daemon = pi
        self.left_motor = Motor(self.pi_daemon, LEFT_MOTOR_PWM_GPIO, LEFT_MOTOR_DIRECTION_GPIOS)
        self.right_motor = Motor(self.pi_daemon, RIGHT_MOTOR_PWM_GPIO, RIGHT_MOTOR_DIRECTION_GPIOS)

    def turn_in_place(self, direction: int):
        speed_left = -DEFAULT_SPEED * direction
        speed_right = DEFAULT_SPEED * direction
        self.right_motor.update_speed(speed_right)
        self.left_motor.update_speed(speed_left)

    def stop(self):
        self.right_motor.update_speed(0)
        self.left_motor.update_speed(0)

    def move_straight(self, direction: int = FORWARD, speed=DEFAULT_SPEED):
        self.left_motor.update_speed(direction * speed)
        self.right_motor.update_speed(direction * speed)

    def move_slight_left(self):
        self.right_motor.update_speed(DEFAULT_SPEED * 1.2)  # 0.88
        self.left_motor.update_speed(DEFAULT_SPEED * 0.75)  # 0.68

    def move_slight_right(self):
        self.right_motor.update_speed(DEFAULT_SPEED * 0.75)  # 0.64
        self.left_motor.update_speed(DEFAULT_SPEED * 1.2)  # 0.88

    def turning_left(self):
        turn_time = 0.3
        self.turn_in_place(LEFT)
        sleep(turn_time)
        self.move_straight(FORWARD)
        sleep(turn_time)
