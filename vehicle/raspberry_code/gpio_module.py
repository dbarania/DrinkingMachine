import pigpio


class GpioModule:
    def __init__(self, pi: pigpio.pi = None):
        if pi:
            self.pi = pi

    def kill_self(self):
        # filtered_values = [value for key, value in data.items() if keyword in key]
        # return filtered_values
        if hasattr(self, "pi"):
            pins = [value for key, value in self.__dict__ if "pin" in key]
            for pin in pins:
                self.pi.write(pin, 0)
