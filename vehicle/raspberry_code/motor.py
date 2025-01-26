import pigpio
from gpio_module import GpioModule


class Motor(GpioModule):
    MAX_DUTY_CYCLE = 255
    FREQUENCY = 1000

    def __init__(self, pi: pigpio.pi, direction_pin: int, control_pins: tuple[int, int]):
        self.pi = pi
        self.direction_pin = direction_pin
        self.control_pin0 = control_pins[0]
        self.control_pin1 = control_pins[1]
        self.pi.set_PWM_range(self.control_pin, self.MAX_DUTY_CYCLE)
        self.pi.set_PWM_frequency(self.control_pin, self.FREQUENCY)

    def update_speed(self, speed: float):
        quantized_speed = int(round(abs(speed) * self.MAX_DUTY_CYCLE))
        status = self.pi.set_PWM_dutycycle(self.control_pin, quantized_speed)
        direction = int(speed > 0)
        self.pi.write(self.control_pin0, direction)
        self.pi.write(self.control_pin1, 1 - direction)
