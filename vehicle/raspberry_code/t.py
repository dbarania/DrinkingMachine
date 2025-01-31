import vision_module
import cv2
import time

v = vision_module.VisionModule(2)

while True:
    v.new_frame()
    cv2.imshow("name", v._frame)
    v.identify_surroundings()

    if cv2.waitKey(30) == 'q':
        break
