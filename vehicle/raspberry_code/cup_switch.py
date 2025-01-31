import pigpio
from gpio_module import GpioModule


class CupSwitch(GpioModule):
    def __init__(self, pi: pigpio.pi, diode_pin: int):
        super().__init__(pi)
        self.pi = pi

        self.pi.set_mode(diode_pin, pigpio.INPUT)
        self.diode_pin = diode_pin

    def read(self):
        return self.pi.read(self.diode_pin)
