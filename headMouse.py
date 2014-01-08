#!/usr/bin/env python
#coding=utf8
'''
Headmouse!
'''

import cv2
import serial
import time

import hmCam

CAMERA_ID = 0
ARDUINO_PORT = 'COM7'

if __name__ == "__main__":

    arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)

    hmCam.bind(CAMERA_ID)

    currentX = 0
    currentY = 0
    oldX = 0
    oldY = 0
    diffX = 0
    diffY = 0

    startTime = time.time()
    timeC = 0
    loops = 0

    while(True):
        loops += 1
        timeC += time.time() - startTime
        if loops == 100:
            loops = 0
            print "fps is around:", 100. / timeC
            timeC = 0
        #print "time took:", time.time() - startTime
        startTime = time.time()
        # Capture frame-by-frame

        currentX, currentY = hmCam.popAndAnalyze()

        diffX = (currentX - oldX) * 2
        diffY = (currentY - oldY) * 2

        oldX = currentX
        oldY = currentY

        #print "x and y diffs are %s, %s" % (diffX, diffY)

        if( diffX != 0 and diffY != 0):
            arduino.write("32100\n" + str(int(-(diffX * 3))) + "\n" + str(int(diffY * 3)) + "\n")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    hmCam.cleanup()
