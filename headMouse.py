#!/usr/bin/env python
#coding=utf8
'''
Headmouse!
'''

import serial
import time
import threading
import sys

import cv2

import hmCam
import hmFilterData as filter
import arduinoSerial

CAMERA_ID = 0
ARDUINO_PORT = 'COM7'
INPUT_VISUALIZER = True

def main():
    # output driver setup
    arduino = arduinoSerial.get_serial_link(ARDUINO_PORT, 115200, timeout=1, async=False, slices=8)

    # input driver setup
    hmCam.displayWindow = INPUT_VISUALIZER
    hmCam.bind(CAMERA_ID)
    
    def input_source():
    	while True:
    		yield hmCam.popAndAnalyze()

    # signal proc chain setup
    velocity_gen = filter.relative_movement()
    sub_pix_gen = filter.sub_pix_trunc()
    stateful_smooth_gen = filter.stateful_smoother()
    input_smoother_gen = filter.ema_smoother(.90)
    #slow_smoother_gen = filter.slow_smoother(.6)
    acceleration_gen = filter.accelerate_exp(p=2, accel=2.3, sensitivity=2)

    # main loop setup
    startTime = time.time()
    timeC = 0
    loops = 0

    # main loop
    for coords in input_source():
        loops += 1
        timeC += time.time() - startTime
        if loops == 100:
            loops = 0
            print "fps is around:", 100. / timeC
            timeC = 0
        #print "time took:", time.time() - startTime
        startTime = time.time()
        # Capture frame-by-frame

        ### Filter Section ###
        #Take absolute position return relative position
        v = velocity_gen.send(coords)
        v = filter.killOutliers(v, 20)


        #v = slow_smoother_gen.send((v, 6))
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

    # input driver cleanup
    # When everything done, release the capture
    hmCam.cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(main())

