from gpio_module import GpioModule
import pigpio


# This code is almost entirely copied from pigpio i2c lcd example

class LcdController(GpioModule):
    def __init__(self, pi: pigpio, i2c_bus, address, width=16, backlight_on=True,
                 RS=0, RW=1, E=2, BL=3, B4=4):
        self.pi = pi
        super().__init__(pi)
        self.width = width
        self.backlight_on = backlight_on

        self.RS = (1 << RS)
        self.E = (1 << E)
        self.BL = (1 << BL)
        self.B4 = B4

        self._h = pi.i2c_open(i2c_bus, address)

        self._init()
        print("Initialized LCD")

    def backlight(self, on):
        """
        Switch backlight on (True) or off (False).
        """
        self.backlight_on = on

    def _init(self):
        self._inst(0x33)  # Initialise 1
        self._inst(0x32)  # Initialise 2
        self._inst(0x06)  # Cursor increment
        self._inst(0x0C)  # Display on,move_to off, blink off
        self._inst(0x28)  # 4-bits, 1 line, 5x8 font
        self._inst(0x01)  # Clear display

    def _byte(self, MSb, LSb):
        if self.backlight_on:
            MSb |= self.BL
            LSb |= self.BL

        self.pi.i2c_write_device(self._h,
                                 [MSb | self.E, MSb & ~self.E, LSb | self.E, LSb & ~self.E])

    def _inst(self, bits):
        MSN = (bits >> 4) & 0x0F
        LSN = bits & 0x0F

        MSb = MSN << self.B4
        LSb = LSN << self.B4

        self._byte(MSb, LSb)

    def _data(self, bits):
        MSN = (bits >> 4) & 0x0F
        LSN = bits & 0x0F

        MSb = (MSN << self.B4) | self.RS
        LSb = (LSN << self.B4) | self.RS

        self._byte(MSb, LSb)

    def move_to(self, row, column):
        """
        Position cursor at row and column (0 based).
        """
        self._inst(self._LCD_ROW[row] + column)

    def put_inst(self, byte):
        """
        Write an instruction byte.
        """
        self._inst(byte)

    def put_symbol(self, index):
        """
        Write the symbol with index at the current cursor postion
        and increment the cursor.
        """
        self._data(index)

    def put_chr(self, char):
        """
        Write a character at the current cursor postion and
        increment the cursor.
        """
        self._data(ord(char))

    def put_str(self, text):
        """
        Write a string at the current cursor postion.  The cursor will
        end up at the character after the end of the string.
        """
        for i in text:
            self.put_chr(i)

    def put_line(self, row, text):
        """
        Replace a row (0 based) of the LCD with a new string.
        """
        text = text.ljust(self.width)[:self.width]

        self.move_to(row, 0)

        self.put_str(text)

    def close(self):
        """
        Close the LCD (clearing the screen) and release used resources.
        """
        self._inst(0x01)

        self.pi.i2c_close(self._h)

    def clear_screen(self):
        self.put_inst(0x01)
        self.put_inst(0x02)

    def write_new_line(self, text: str):
        self.clear_screen()
        self.put_str(text)
