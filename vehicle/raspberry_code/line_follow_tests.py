from robot2 import Robot
import time

r = Robot(False, True, False)

tstart = time.time()

while time.time() < tstart + 5:
    r.move()

r.stop()
