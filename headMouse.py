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
ARDUINO_BAUD = 115200
INPUT_VISUALIZER = True

def consumer(func):
    '''
    Decorator taking care of initial next() call to "sending" generators

    From PEP-342
    http://www.python.org/dev/peps/pep-0342/
    '''
    def wrapper(*args,**kw):
        gen = func(*args, **kw)
        next(gen)
        return gen
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__  = func.__doc__
    return wrapper

## Output drivers

@consumer
def arduino_output(port=ARDUINO_PORT, baud=ARDUINO_BAUD):
    '''Write mouse coordinates out to Arduino via serial'''
    arduino = arduinoSerial.get_serial_link(port, baud, timeout=1, async=False, slices=8)
    while True:
        x,y = yield
        #arduino.move_mouse(x,y)
        print("{:d}, {:d}".format(x, y))

@consumer
def print_output():
    '''Write mouse coordinates out to stdout'''
    while True:
        x,y = yield
        print("{:d}, {:d}".format(x, y))

def main():
    '''Headmouse main loop'''
    # output driver setup
    output_driver = print_output()

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
    slow_smoother_gen = filter.slow_smoother(.6)
    acceleration_gen = filter.accelerate_exp(p=2, accel=1.4, sensitivity=6.5)

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

        output_driver.send((x,y))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # input driver cleanup
    # When everything done, release the capture
    hmCam.cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(main())

