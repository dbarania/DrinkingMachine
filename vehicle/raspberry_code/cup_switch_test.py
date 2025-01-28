from time import sleep

import pigpio
from cup_switch import CupSwitch

INPUT_GPIO = 17

pid = pigpio.pi()
temp = CupSwitch(pid, INPUT_GPIO)

for i in range(100):
    read = temp.read()
    print(f'{i}\t {read}')
    sleep(0.1)