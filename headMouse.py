#!/usr/bin/env python
#coding=utf8
'''
Headmouse!
'''

import cv2
import serial
import time
import threading

import hmCam
import hmFilterData as filter
import arduinoSerial

CAMERA_ID = 0
ARDUINO_PORT = 'COM7'
hmCam.displayWindow = True

if __name__ == "__main__":

    arduino = arduinoSerial.get_sync_arduino(ARDUINO_PORT, 115200, timeout=1)

    hmCam.bind(CAMERA_ID)

    velocity_gen = filter.relative_movement()
    sub_pix_gen = filter.sub_pix_trunc()
    stateful_smooth_gen = filter.stateful_smoother()
    input_smoother_gen = filter.em1 a_smoother(.85)
    slow_smoother_gen = filter.slow_smoother(.6)
    acceleration_gen = filter.accelerate_exp(p=2, accel=1.4, sensitivity=6.5)

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
        v = velocity_gen.send(coords)
        v = filter.killOutliers(v, 20)


        v = slow_smoother_gen.send((v, 6))
        v = input_smoother_gen.send(v)
        v = acceleration_gen.send(v)
        #v = filter.accelerate(v)

        v = sub_pix_gen.send(v)

        #Mirror image on x-axis
        x = -v[0]
        y = v[1]

        #Duplicate in Arduino
        #print "coords are:" + x + ", " + y

        arduino.move_mouse(x,y)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    hmCam.cleanup()