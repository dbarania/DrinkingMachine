from time import sleep

import pigpio
from motor import Motor

LEFT_MOTOR_PWM_GPIO = 18
LEFT_MOTOR_DIRECTION_GPIOS = (23, 24)

print("test begin")

pid = pigpio.pi()
motor = Motor(pid, LEFT_MOTOR_PWM_GPIO, LEFT_MOTOR_DIRECTION_GPIOS)
print("motor initialized")
print("Speed 1 for 3s")
motor.update_speed(1)
sleep(3)
print("Speed -1 for 3s")
motor.update_speed(-1)
sleep(3)
print("motor stop")
motor.update_speed(0)

for s in range(5, 10):
    print(f"Motor speed {s / 10} for 2 s")
    motor.update_speed(s / 10)
    sleep(2)

