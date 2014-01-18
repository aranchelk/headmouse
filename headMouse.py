#!/usr/bin/env python
#coding=utf8
'''
Headmouse!
'''

import logging
import time
import threading
import sys
import os
import ConfigParser

try:
    import pymouse
except ImportError:
    logging.warn("Unable to load PyMouse. Install PyUserinput for direct mouse control.")

import cv2

import hmCam
import hmFilterData as filter

try:
    import arduinoSerial
except ImportError:
    pass

CONFIG_FILE = os.path.expanduser('~/.headmouse')

ACCELERATION_EXPONENT = 2
OUTLIER_VELOCITY_THRESHOLD = 20

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
def arduino_output(config=None):
    '''Write mouse coordinates out to Arduino via serial'''
    arduino = arduinoSerial.get_serial_link(config['arduino_port'], config['arduino_baud'], timeout=1, async=True, slices=3)
    while True:
        x, y = yield
        arduino.move_mouse(x, y)

@consumer
def print_output(config=None):
    '''Write mouse coordinate changes out to stdout'''
    while True:
        x, y = yield
        print("{:d}, {:d}".format(x, y))

@consumer
def pymouse_output(config=None):
    '''Write mouse coordinates out to pymouse'''
    mouse = pymouse.PyMouse()
    while True:
        dx, dy = yield
        x, y = mouse.position()
        mouse.move(x + dx, y + dy)

def get_config(config_file=CONFIG_FILE):
    config = {
        'output': 'arduino_output',
        'arduino_baud': 115200,
        'arduino_port': 'COM7',

        'input': 'camera',
        'input_tracker': 'dot_tracker',
        'input_camera': 0,
        'input_resolution': (640, 480),
        'input_fps': 30,
        'input_visualize': True,

        'acceleration': 2.3,
        'sensitivity': 2.0,
        'smoothing': 0.90,
    }
    if os.path.exists(config_file):
        config_parser = ConfigParser.SafeConfigParser()
        config_parser.read([config_file])
        from_file = dict(config_parser.items('headmouse'))
        config.update(from_file)

    # type hacks... 
    # TODO: something better
    if isinstance(config['input_resolution'], basestring):
        config['input_resolution'] = [int(x) for x in config['input_resolution'].split(',')]
    for field in ('input_camera', 'input_fps', 'arduino_baud'):
        config[field] = int(config[field])
    for field in ('acceleration', 'sensitivity', 'smoothing'):
        config[field] = float(config[field])

    # TODO: argparse overrides
    return config

def main():
    '''Headmouse main loop'''
    config = get_config()

    # output driver setup
    output_driver = sys.modules[__name__].__dict__[config['output']](config=config)

    # input driver setup
    def input_source():
        hmCam.displayWindow = config['input_visualize']
        # todo: passthrough configs
        hmCam.bind(tracker_name=config['input_tracker'])
        while True:
            yield hmCam.popAndAnalyze()

    # signal proc chain setup
    velocity_gen = filter.relative_movement()
    sub_pix_gen = filter.sub_pix_trunc()
    stateful_smooth_gen = filter.stateful_smoother()
    input_smoother_gen = filter.ema_smoother(config['smoothing'])
    #slow_smoother_gen = filter.slow_smoother(.6)
    acceleration_gen = filter.accelerate_exp(
        p=ACCELERATION_EXPONENT,
        accel=config['acceleration'], 
        sensitivity=config['sensitivity']
        )

    # main loop setup
    startTime = time.time()
    timeC = 0
    loops = 0

    # main loop
    for coords in input_source():
        loops += 1
        timeC += time.time() - startTime
        if loops == 10:
            loops = 0
            logging.info("fps is around: {}".format(10. / timeC))
            timeC = 0
        #print "time took:", time.time() - startTime
        startTime = time.time()
        # Capture frame-by-frame

        ### Filter Section ###
        #Take absolute position return relative position
        v = velocity_gen.send(coords)
        v = filter.killOutliers(v, OUTLIER_VELOCITY_THRESHOLD)


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

        output_driver.send((x,y))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # input driver cleanup
    # When everything done, release the capture
    hmCam.cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(main())

