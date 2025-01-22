from gpio_module import GpioModule


class CameraModule(GpioModule):
    def __init__(self, camera_id):
        super().__init__()
        self.camera = camera_id
        self.h = hash(camera_id )