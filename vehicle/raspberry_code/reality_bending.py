import robot2
import curses
import paho.mqtt.client as mqtt
from lcd_controller import LcdController

#
#
# def main(stdscr):
#     curses.cbreak()  # Reacts instantly to keypresses
#     stdscr.keypad(True)  # Enables arrow key detection
#     stdscr.clear()
#     stdscr.refresh()
#
#     while True:
#         key = stdscr.getch()
#         stdscr.clear()  # Clear the screen before printing
#         stdscr.addstr("Press WASD keys to move. Press Q to quit.\n")
#
#
#         if key == ord('q'):
#             break
#         elif key == ord('w'):
#             stdscr.addstr("Moving Up\n")
#         elif key == ord('a'):
#             stdscr.addstr("Moving Left\n")
#         elif key == ord('s'):
#             stdscr.addstr("Moving Down\n")
#         elif key == ord('d'):
#             stdscr.addstr("Moving Right\n")
#
#         stdscr.refresh()
#
#
# curses.wrapper(main)
drinks = ["Gin & Tonic", "Gin", "Tonic", ' ']
i = 0


class RealityBendingApplication:
    def __init__(self):
        self.robot = robot2.Robot(connection=False)
        self.last_pressed = None

    def main(self, stdscr):
        curses.cbreak()  # Reacts instantly to keypresses
        stdscr.keypad(True)  # Enables arrow key detection
        stdscr.clear()
        stdscr.refresh()

        while True:
            key = stdscr.getch()
            stdscr.clear()  # Clear the screen before printing
            stdscr.addstr("Press WASD keys to move. Press Q to quit.\n")
            if key == self.last_pressed:
                continue
            else:
                self.last_pressed = key
            if key == 27:
                break
            elif key == ord('w'):
                self.robot.motors_controller.move_straight()
            elif key == ord('s'):
                self.robot.motors_controller.move_straight(-1)
            elif key == ord('a'):
                self.robot.motors_controller.move_slight_left()
            elif key == ord('d'):
                self.robot.motors_controller.move_slight_right()
            elif key == ord('q'):
                self.robot.motors_controller.turn_in_place(1)

            elif key == ord('e'):
                self.robot.motors_controller.turn_in_place(-1)

            elif key == ord(' '):
                self.robot.motors_controller.stop()
            elif ord('1') <= key <= ord('3'):
                drink = drinks[int(chr(key)) - 1]
                self.robot.lcd_controller.write_new_line(drink)
            stdscr.refresh()
        self.robot.motors_controller.stop()
        self.robot.vision.release()


app = RealityBendingApplication()
curses.wrapper(app.main)
