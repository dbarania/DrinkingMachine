import cv2
import time
from vision_module import VisionModule


def main():
    camera_id = 0  # Change if needed (e.g., 1 for external cameras)
    vision = VisionModule(camera_id)

    while True:
        vision.new_frame()

        line_pos = vision.line_analysis()
        marker_id = vision.identify_surroundings()
        print(line_pos)
        print(marker_id)

        # Display the current frame for visual debugging
        cv2.imshow("Processed Frame", vision._frame)
        cv2.imshow("Threshold Frame", vision._threshold_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
            break

        time.sleep(0.1)  # Add delay to avoid high CPU usage

    vision.cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
