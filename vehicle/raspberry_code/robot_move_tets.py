from time import sleep

import pigpio
from motor import Motor
from robot2 import Robot

r = Robot(False, False)
r.move_forward()
print("Driving forward for 3s")
sleep(3)

r.move_backward()
print("Driving backward for 3s")
sleep(3)

r.stop()
print("Stop for 3s")
sleep(3)

for i in range(0, 5):
    r.move_mode(i)
    print(f"Moving mode {i} for 3s")
    sleep(3)

print("Stop for 1s")
r.stop()
sleep(1)

print("Rotate in place left for 3s")
r.rotate_in_place(1)
sleep(3)

print("Rotate in place right for 3s")
r.rotate_in_place(-1)
sleep(3)

r.stop_connection()
