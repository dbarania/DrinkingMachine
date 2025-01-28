from time import sleep

from robot2 import Robot

r = Robot()
sleep(10)
print("Publishing a message")
r.publish("car/satus", "IDLE")
sleep(60)
r.stop_connection()
