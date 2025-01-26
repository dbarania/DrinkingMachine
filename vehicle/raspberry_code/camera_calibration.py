import cv2
import numpy as np
cam = cv2.VideoCapture(0)
# frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
# frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
# print([frame_height, frame_width])
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
# print(cam.get(cv2.CAP_PROP_))
focus = cam.get(cv2.CAP_PROP_FOCUS)

n = 40

def frame_changes(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow("gray", gray)

    _, threshold = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY_INV)    
    cv2.imshow("Threshold", threshold)

    n = 50  # For example, analyze the lower 30% of the image
    height = threshold.shape[0]
    crop_start = int(height * (1 - n / 100))

    # Crop the lower n% of the image
    lower_part = threshold[crop_start:, :]

    contours, hierarchy = cv2.findContours(lower_part, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] !=0 :
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            print("CX : "+str(cx)+"  CY : "+str(cy))
            cv2.circle(lower_part, (cx,cy), 3, (255,0,0), -1)

    cv2.drawContours(lower_part, contours, -1, (0,255,0),3)

    cv2.imshow("name", lower_part)

    # low_b = np.uint8([5,5,5])
    # high_b = np.uint8([0,0,0])
    # mask = cv2.inRange(lower_part, high_b, low_b)
    # contours, hierarchy = cv2.findContours(mask, 1, cv2.CHAIN_APPROX_NONE)
    # if len(contours) > 0:
    #     c = max(contours, key=cv2.contourArea)
    #     M = cv2.moments(c)
    #     if M["m00"] !=0 :
    #         cx = int(M['m10']/M['m00'])
    #         cy = int(M['m01']/M['m00'])
    #         print("CX : "+str(cx)+"  CY : "+str(cy))
    #         cv2.circle(lower_part, (cx,cy), 5, (255,255,255), -1)

    #     cv2.drawContours(lower_part, c, -1, (0,255,0), 1)
    # cv2.imshow("Frame",lower_part)        


while True:
    ret, frame = cam.read()
    # cv2.imshow("Frame", frame)
    frame_changes(frame)
    if cv2.waitKey(1) == ord('q'):
        break

