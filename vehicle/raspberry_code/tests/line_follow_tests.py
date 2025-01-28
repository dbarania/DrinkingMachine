from robot2 import Robot
import time

r = Robot()

tstart = time.time()

while time.time() < tstart + 100:
    r.move()