import pigpio
from gpio_module import GpioModule


class Motor(GpioModule):
    MAX_DUTY_CYCLE = 255
    FREQUENCY = 1000

    def __init__(self, pi: pigpio.pi, control_pin: int, direction_pins: tuple[int, int]):
        super().__init__(pi)
        self.pi = pi

        self.control_pin = control_pin
        self.direction_pin0 = direction_pins[0]
        self.direction_pin1 = direction_pins[1]

        self.pi.set_mode(self.direction_pin0, pigpio.OUTPUT)
        self.pi.set_mode(self.direction_pin1, pigpio.OUTPUT)

        self.pi.set_mode(self.control_pin, pigpio.OUTPUT)

        self.pi.set_PWM_range(self.control_pin, self.MAX_DUTY_CYCLE)
        self.pi.set_PWM_frequency(self.control_pin, self.FREQUENCY)

    def update_speed(self, speed: float):
        quantized_speed = int(round(abs(speed) * self.MAX_DUTY_CYCLE))
        status = self.pi.set_PWM_dutycycle(self.control_pin, quantized_speed)
        direction = int(speed > 0)
        self.pi.write(self.direction_pin0, direction)
        self.pi.write(self.direction_pin1, 1 - direction)
