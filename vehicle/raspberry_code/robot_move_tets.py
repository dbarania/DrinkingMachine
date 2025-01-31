from time import sleep
import sys
import motors_controller
import pigpio

mode = None

if len(sys.argv) > 1:
    mode = int(sys.argv[1])

pid = pigpio.pi()
controller = motors_controller.MotorsController(pid)
print("Controller initialized")
if mode == 1 or mode is None:
    print("Moving forward for 3s")
    controller.move_straight()
    sleep(3)
    controller.stop()
    sleep(1)

if mode == 2 or mode is None:
    print("Moving backward for 3s")
    controller.move_straight(motors_controller.BACKWARD)
    sleep(3)
    controller.stop()
    sleep(1)

if mode == 3 or mode is None:
    for i in range(10, 21):
        controller.move_straight(speed=i / 20)
        print(f"Speed {i / 20} 2s")
        sleep(2)

    controller.stop()
    sleep(1)

if mode == 4 or mode is None:
    print("slight left")
    controller.move_slight_left()
    sleep(2)
if mode == 5 or mode is None:
    print("slight right")
    controller.move_slight_right()
    sleep(2)

controller.stop()
