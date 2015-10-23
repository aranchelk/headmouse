#!/usr/bin/env python
#coding=utf8
'''
Write to stdin to serial
'''
from __future__ import print_function

import logging
import serial
import time

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import util
import filters

logger = logging.getLogger(__name__)
SERIAL_COMMAND_BUFFER_LENGTH = 4
serial_handle = None
mouse = None
maximum_move = 32000


@util.prep_gen
def move_mouse_gen(serial_handle):
    while True:
        x, y = yield
        serial_handle.write('c1,' + str(x) + ',' + str(y) + ';')

def set_mouse_max_move(serial_handle, maxMove):
    serial_handle.write('c2,' + str(maxMove))


def discover_serial_handle(glob_string = None):
    os_globs = {
        'linux2': '/dev/ttyACM*',
        'darwin': '/dev/tty.usb*'
    }

    if glob_string is None:
        glob_string = os_globs[sys.platform]

    import glob
    serial_interfaces = glob.glob(glob_string)

    max_attempts = 3
    wait_interval = 1 # in seconds
    version_data = None

    for i in range(max_attempts):
        print("Attempt: %s" % i)
        for port in serial_interfaces:
            print("Trying port %s" % port)
            baud = 57600
            timeout = 2

            try:
                sh = serial.Serial(port, baud, timeout=timeout)
                sh.write('c0')
                sh.flush()
                version_data = sh.readline().rstrip()
            except Exception: #todo: put the specific exception type
                pass

            if version_data == unicode("hm0.0.1"):
                print("Found serial on port:", port)
                return sh

        time.sleep(wait_interval)

    sys.exit("Could not find serial port for Arduino headmouse.")


def initialize():
    global serial_handle, mouse
    serial_handle = discover_serial_handle()
    mouse = move_mouse_gen(serial_handle)
    set_mouse_max_move(serial_handle, 50)


def send_xy(xy):
    x, y = xy
    # Todo: add a normailze ints function into filters or util and use that.
    x = int(round(float(x)))
    y = int(round(float(y)))

    xy = filters.limiter((x,y), maximum_move)

    mouse.send(xy)


if __name__ == '__main__':
    initialize()

    while True:
        try:
            line = sys.stdin.readline()
            formatted = line.rstrip()
            print(formatted)
            xy_list = formatted.split(', ')

            send_xy((xy_list[0], xy_list[1]))

        except Exception as e:
            print(e)
else:
    initialize()
