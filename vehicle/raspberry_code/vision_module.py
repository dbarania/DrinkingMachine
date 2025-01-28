from gpio_module import GpioModule
import cv2

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
FPS = 10
n = 50


class VisionModule(GpioModule):
    def __init__(self, camera_id):
        super().__init__()
        self.cam = cv2.VideoCapture(camera_id)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cam.set(cv2.CAP_PROP_FPS, FPS)
        self._frame = None
        self._threshold_frame = None
        self.last_corners = None
        self._aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self._params = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(self._aruco_dict, cv2.aruco.DetectorParameters())

    def new_frame(self):
        if not self.cam.isOpened():
            print("Camera is not opened")
            return -1
        ret, self._frame = self.cam.read()
        self._frame = cv2.cvtColor(self._frame, cv2.COLOR_BGR2GRAY)

    # def line_analysis(self):
    #     result = None
    #     _, self._threshold_frame = cv2.threshold(self._frame, 90, 150, cv2.THRESH_BINARY_INV)
    #     height = self._threshold_frame.shape[0]
    #     crop_start = int(height * (1 - n / 100))
    #     self._threshold_frame = self._threshold_frame[crop_start:, :]
    #
    #     # Convert to BGR so colors can be drawn
    #     self._threshold_frame = cv2.cvtColor(self._threshold_frame, cv2.COLOR_GRAY2BGR)
    #
    #     contours, hierarchy = cv2.findContours(self._threshold_frame[:, :, 0], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #     bottom_half_threshold = self._frame.shape[0] // 2
    #     if self.last_corners is not None:
    #         for corner in self.last_corners:
    #             x, y = corner
    #             if y > bottom_half_threshold:
    #                 print("marker found, frame dropped")
    #                 return None
    #
    #     if len(contours) > 0:
    #         c = max(contours, key=cv2.contourArea)
    #         M = cv2.moments(c)
    #         if M["m00"] != 0:
    #             cx = int(M['m10'] / M['m00'])
    #             cy = int(M['m01'] / M['m00'])
    #             result = (cx, cy)
    #             # Draw a red dot (BGR: (0, 0, 255))
    #             cv2.circle(self._threshold_frame, (cx, cy), 5, (0, 0, 255), -1)
    #
    #     cv2.drawContours(self._threshold_frame, contours, -1, (0, 255, 0), 3)
    #
    #     return result

    def line_analysis(self):
        result = None
        height = self._frame.shape[0]
        bottom_half_frame = height // 2

        marker_in_bottom_half = False
        marker_in_top_half = False

        if self.last_corners is not None:
            marker_in_bottom_half = any([y > bottom_half_frame for _, y in self.last_corners])
            marker_in_top_half = any([y < bottom_half_frame for _, y in self.last_corners])

        if marker_in_top_half and marker_in_bottom_half:
            print("marker found on both halves, frame dropped")
            return None
        elif marker_in_bottom_half and not marker_in_top_half:
            crop_end = int(height / 2)
            self._threshold_frame = self._frame[:crop_end, :]
            print("Taking top half of frame")
        else:
            crop_start = int(height * (1 - n / 100))
            self._threshold_frame = self._frame[crop_start:, :]
            print("Taking bottom half of frame")

        _, self._threshold_frame = cv2.threshold(self._threshold_frame, 90, 150, cv2.THRESH_BINARY_INV)
        contours, hierarchy = cv2.findContours(self._threshold_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                result = (cx, cy)
                # Draw a red dot (BGR: (0, 0, 255))
                cv2.circle(self._threshold_frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.drawContours(self._threshold_frame, contours, -1, (0, 255, 0), 3)

        return result

    def identify_surroundings(self):
        corners, ids, _ = self._detector.detectMarkers(self._frame)
        self.last_corners = corners[0][0] if corners else None
        print(self.last_corners)

        if ids is None:
            return None
        else:
            return ids[0]
