import pigpio


class GpioModule:
    def __init__(self, pi: pigpio.pi = None):
        if pi:
            self.pi = pi

    def kill_self(self):
        if hasattr(self, "pi"):
            pins = [value for key, value in self.__dict__ if "pin" in key]
            for pin in pins:
                self.pi.write(pin, 0)
