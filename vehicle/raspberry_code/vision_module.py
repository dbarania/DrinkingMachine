import cv2
from gpio_module import GpioModule

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
FPS = 20


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

        # ArUco marker settings
        self._aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self._params = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(self._aruco_dict, cv2.aruco.DetectorParameters())

        # Video writer setup
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.frame_writer = cv2.VideoWriter("frame_output.avi", fourcc, FPS, (CAMERA_WIDTH, CAMERA_HEIGHT),
                                            isColor=True)
        self.threshold_writer = cv2.VideoWriter("threshold_output.avi", fourcc, FPS, (CAMERA_WIDTH, CAMERA_HEIGHT),
                                                isColor=False)

    def new_frame(self):
        if not self.cam.isOpened():
            print("Camera is not opened")
            return -1

        ret, self._frame = self.cam.read()
        if not ret:
            print("Failed to grab frame")
            return -1

        self._frame = cv2.cvtColor(self._frame, cv2.COLOR_BGR2GRAY)

        # Write the grayscale frame to video
        color_frame = cv2.cvtColor(self._frame, cv2.COLOR_GRAY2BGR)  # Convert back to BGR for saving
        self.frame_writer.write(color_frame)

    def line_analysis(self):
        result = None
        if self._frame is None:
            print("No frame available for analysis")
            return None

        height = self._frame.shape[0]
        bottom_half_frame = height // 2

        marker_in_bottom_half = False
        marker_in_top_half = False

        if self.last_corners is not None:
            marker_in_bottom_half = any(y > bottom_half_frame for _, y in self.last_corners)
            marker_in_top_half = any(y < bottom_half_frame for _, y in self.last_corners)

        if marker_in_top_half and marker_in_bottom_half:
            print("Marker found on both halves, frame dropped")
            return None
        elif marker_in_bottom_half and not marker_in_top_half:
            crop_end = int(height / 2)
            self._threshold_frame = self._frame[:crop_end, :]
            print("Taking top half of frame")
        else:
            crop_start = int(height * 0.5)
            self._threshold_frame = self._frame[crop_start:, :]
            print("Taking bottom half of frame")

        _, self._threshold_frame = cv2.threshold(self._threshold_frame, 90, 150, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(self._threshold_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                result = (cx, cy)

        # Convert threshold frame to 3 channels so it can be saved in video
        threshold_bgr = cv2.cvtColor(self._threshold_frame, cv2.COLOR_GRAY2BGR)
        self.threshold_writer.write(threshold_bgr)

        return result

    def identify_surroundings(self):
        if self._frame is None:
            return None

        corners, ids, _ = self._detector.detectMarkers(self._frame)
        self.last_corners = corners[0][0] if corners else None

        return ids[0] if ids is not None else None

    def release(self):
        """Release the video writers and camera"""
        self.cam.release()
        self.frame_writer.release()
        self.threshold_writer.release()
        print("Resources released successfully.")
