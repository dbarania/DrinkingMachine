import cv2
import threading
import time
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

        # Threading setup
        self.stop_event = threading.Event()
        self.writer_thread = threading.Thread(target=self._write_frames_thread, daemon=True)
        self.writer_thread.start()

    def new_frame(self):
        """Capture a new frame from the camera"""
        if not self.cam.isOpened():
            print("Camera is not opened")
            return -1

        ret, self._frame = self.cam.read()
        if not ret:
            print("Failed to grab frame")
            return -1

        self._frame = cv2.cvtColor(self._frame, cv2.COLOR_BGR2GRAY)

    def line_analysis(self):
        """Process the frame for line detection"""
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

        return result

    def identify_surroundings(self):
        """Detect ArUco markers in the frame"""
        if self._frame is None:
            return None

        corners, ids, _ = self._detector.detectMarkers(self._frame)
        self.last_corners = corners[0][0] if corners else None

        return ids[0] if ids is not None else None

    def _write_frames_thread(self):
        """Thread function to write frames to video files periodically (every 50ms)"""
        while not self.stop_event.is_set():
            self.new_frame()
            if self._frame is not None:
                color_frame = cv2.cvtColor(self._frame, cv2.COLOR_GRAY2BGR)  # Convert grayscale to BGR
                self.frame_writer.write(color_frame)

            if self._threshold_frame is not None:
                threshold_bgr = cv2.cvtColor(self._threshold_frame, cv2.COLOR_GRAY2BGR)
                self.threshold_writer.write(threshold_bgr)

            time.sleep(0.05)  # Sleep for 50ms

    def release(self):
        """Release the video writers, camera, and stop the thread"""
        self.stop_event.set()
        self.writer_thread.join()
        self.cam.release()
        self.frame_writer.release()
        self.threshold_writer.release()
        print("Resources released successfully.")
