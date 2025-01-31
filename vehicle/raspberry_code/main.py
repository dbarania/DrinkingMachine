import signal
import sys

import robot
robot_global = None


def signal_handler(sig, frame):
    if isinstance(robot_global, robot.Robot):
        robot_global.kill_all()

    sys.exit(0)


# Register signal handler for Ctrl + C
signal.signal(signal.SIGINT, signal_handler)


def main():
    global robot_global
    robot_global = robot.Robot()
    robot_global.main_loop()


if __name__ == '__main__':
    main()
