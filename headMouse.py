import numpy as np
import cv2
import serial
import io
import time
import os

arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

cap = cv2.VideoCapture(1)
'''
cap.set(3, 320)
cap.set(4, 200)
cap.set(5, 30)
cap.set(8, 1)
'''
os.system('echo test')
os.system('sudo v4l2-ctl -d /dev/video1 --set-fmt-video=width=640,height=480,pixelformat=0')


orb = cv2.ORB()

currentX = 0
currentY = 0
oldX = 0
oldY = 0
diffX = 0
diffY = 0

startTime = time.time()
timeC = 0
loops = 0

def btrAvg(numList):
    return (max(numList) + min(numList))/2    

while(True):
    loops += 1
    timeC += time.time() - startTime
    if loops == 100:
        loops = 0
        print "fps is", 100. / timeC 
        timeC = 0
    #print "time took:", time.time() - startTime
    startTime = time.time()
    # Capture frame-by-frame
    ret, img = cap.read()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret,thresh3 = cv2.threshold(img,230,255,cv2.THRESH_BINARY)
    kp = orb.detect(thresh3,None)

    if kp:
	xList = []
	yList = []
        for k in kp:
            xList.append(k.pt[0])
	    yList.append(k.pt[1])
        

        currentX = btrAvg(xList) 
        currentY = btrAvg(yList) 

        diffX = (currentX - oldX) * 2
        diffY = (currentY - oldY) * 2

        oldX = currentX
        oldY = currentY


        #print "x and y diffs are %s, %s" % (diffX, diffY)

        if( diffX != 0 and diffY != 0):
            arduino.write("32100\n" + str(int(-(diffX))) + "\n" + str(int(diffY)) + "\n")

        cv2.circle(img, (int(currentX), int(currentY)) , 5, (255,0,0))
        #cv2.rectangle(img, ( btrAvg(xList), btrAvg(yList) ), ( 20,20), (255, 0, 0), 2)
    	img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)

    # Display the resulting frame
    cv2.imshow('frame',img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
