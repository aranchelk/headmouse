#!/usr/bin/env python
#coding=utf8
'''
Headmouse!
'''

import cv2
import serial
import time

import hmCam
import hmFilterData as filter

CAMERA_ID = 0
ARDUINO_PORT = 'COM7'

if __name__ == "__main__":

    arduino = serial.Serial(ARDUINO_PORT, 9600, timeout=1)

    hmCam.bind(CAMERA_ID)

    move_gen = filter.relative_movement()
    move_gen.send(None)
    sub_pix_gen = filter.sub_pix_trunc()
    sub_pix_gen.send(None)

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

        coords = hmCam.popAndAnalyze()

        ### Filter Section ###
        #Take absolute position return relative position
        coords = move_gen.send(coords)
        #Subpixel info
        coords = sub_pix_gen.send(coords)

        #Convert this to an acceleration filter
        x = coords[0] * 6
        y = coords[1] * 6

        x = -(x)


        #Duplicate in Arduino
        x = str(int(x))
        y = str(int(y))


        #print "coords are:" + x + ", " + y


        if( x != 0 or y != 0):
            arduino.write("32100\n" + x + "\n" + y + "\n")



        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    hmCam.cleanup()
