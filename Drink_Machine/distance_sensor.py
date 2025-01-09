#Libraries
import RPi.GPIO as GPIO
import time
 
#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

#set GPIO Pins container with water
GPIO_TRIGGER_W = 18
GPIO_ECHO_W = 24

#set GPIO Pins container with beer
GPIO_TRIGGER_B = 17
GPIO_ECHO_B = 22
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER_W, GPIO.OUT)
GPIO.setup(GPIO_ECHO_W, GPIO.IN)
 
def distance_water():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER_W, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER_W, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO_W) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO_W) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance_water = (TimeElapsed * 34300) / 2

     
    return distance_water
 
def distance_beer():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER_B, True)
 
    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER_B, False)
 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while GPIO.input(GPIO_ECHO_B)== 0:
        StartTime = time.time()
 
    # save time of arrival
    while GPIO.input(GPIO_ECHO_B)== 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance_beer = (TimeElapsed * 34300) / 2
     
    return distance_beer



if __name__ == '__main__':
    try:
        while True:
            dist_w = distance_water()
            print ("Measured Distance Water = %.1f cm" % dist_w)
            dist_b = distance_beer()
            print ("Measured Distance Beer  = %.1f cm" % dist_b)
            time.sleep(3)
 
        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()