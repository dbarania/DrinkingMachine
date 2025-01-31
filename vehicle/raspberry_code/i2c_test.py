from lcd_controller import LcdController
import pigpio
import time
pi = pigpio.pi()
lcd = LcdController(pi, 1, 0x27)
while True:
    lcd.clear_screen()
    time.sleep(1)
    lcd.write_new_line("LCD controller")
    time.sleep(2)
    lcd.clear_screen()
    time.sleep(1)
    lcd.write_new_line("Happy noises")
    time.sleep(2)

