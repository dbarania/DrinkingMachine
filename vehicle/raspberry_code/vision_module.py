from gpio_module import GpioModule
import cv2

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
n = 50


class VisionModule(GpioModule):
    def __init__(self, camera_id):
        super().__init__()
        self.cam = cv2.VideoCapture(camera_id)
        self._frame = None

    def newFrame(self):
        if not self.cam.isOpened():
            print("Camera is not opened")
            return -1
        ret, self._frame = self.cam.read()

    def line_analysis(self):
        image = cv2.cvtColor(self._frame, cv2.COLOR_BGR2GRAY)
        _, image = cv2.threshold(image, 130, 255, cv2.THRESH_BINARY_INV)
        height = image.shape[0]
        crop_start = int(height * (1 - n / 100))
        image = image[crop_start:, :]
        contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                return cx, cy
                # print("CX : " + str(cx) + "  CY : " + str(cy))
                # cv2.circle(image, (cx, cy), 3, (255, 0, 0), -1)
        # cv2.drawContours(image, contours, -1, (0, 255, 0), 3)

        # cv2.imshow("Frame", image)
        return None

    def identify_surroundings(self):
        pass
