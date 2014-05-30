#!/usr/bin/env python
#coding=utf8
'''
Write to stdin to serial
'''

import logging
logger = logging.getLogger(__name__)
import random
import operator
import threading
import itertools

from multiprocessing import Process, Pipe

try:
    import serial
except ImportError:
    logger.warn("Unable to load PySerial. No Arduino output available.")
    raise

class SyncArduino:
    def __init__(self, port='COM7', baud=115200, timeout=1):
        self.connection = serial.Serial(port, baud, timeout=timeout)

    def move_mouse(self, x, y):
        move_mouse(int(x), int(y), self.connection)


def get_serial_link(port, baud, timeout=1, fps=30, slices=3, async=False):
    if async is False:
        return SyncArduino(port, baud, timeout)
    else:
        return AsyncArduino(port, baud, timeout, fps, slices)


def child_process_event_loop(conn, fps, slices, port, baud, timeout=1):
    serial_handle = serial.Serial(port, baud, timeout=timeout)
    while conn.poll(3):
        try:
            x, y, port, baud = conn.recv()
            move_mouse_interp(x,y, fps, slices, serial_handle)
        except Exception as e:
            h = open('./templog', 'a')
            h.write(e)


def move_mouse(x, y, handle):
    try:
        command = "32100\n%d\n%d\n" % (int(x),int(y))
        handle.write(command)
        f = '/Users/carl/sandbox/headmouse/python/headmouse/templog'
        s = "move %s,%s\n\n" % (x, y)
        h = open(f, 'a')
        h.write(s)
    except Exception as e:
        h = open(f, 'a')
        h.write('e')

def delta_slice(delta, slice_quantity):

    delta_min_slice_val = int(delta / slice_quantity)
    delta_remainder = delta - delta_min_slice_val * slice_quantity

    delta_min_slice_list = [delta_min_slice_val] * slice_quantity

    delta_remainder_slice_list = [1] * delta_remainder
    delta_remainder_slice_list += [0]*(slice_quantity - len(delta_remainder_slice_list))

    multi_add = lambda a,b: map(operator.add, a,b)

    #http://stackoverflow.com/questions/17595590/correct-style-for-element-wise-operations-on-lists-without-numpy-python
    out_list = multi_add(delta_min_slice_list, delta_remainder_slice_list)

    random.shuffle(out_list)

    return out_list


def delta_slice_x_y(x, y, slice_quantity):
    return zip(delta_slice(x, slice_quantity), delta_slice(y, slice_quantity))


def move_mouse_interp(x, y, fps, interp_slices, serial_handle):
    #Split x,y delta into the a series of commands and schedule them to run
    print 'starting mmi'

    i = 0
    inc = 1.0 / (fps * interp_slices)
    for x, y in delta_slice_x_y(x, y, interp_slices):
        threading.Timer(inc * i, move_mouse, [x,y, serial_handle]).start()
        i += 1


class AsyncArduino:
    def __init__(self, port, baud, timeout=1, fps=30, slices=3):
        #self.connection = serial.Serial(port, baud, timeout=timeout)
        self.fps = fps
        self.interp_slices = slices
        self.port = port
        self.baud = baud

        parent_conn, child_conn = Pipe()
        p = Process(target=child_process_event_loop, args=(child_conn, fps, slices, port, baud))
        p.start()
        self.__child_process = p
        self.__child_process_connection = parent_conn

    def __del__(self):
        self.__child_process.join()
        self.__child_process.terminate()
        pass

    def move_mouse(self, x, y):
        self.__child_process_connection.send((x, y, self.port, self.baud))


if __name__ == '__main__':
    #ard = AsyncArduino('/dev/tty.usbmodemfa13131', 9600, 1, slices=10, fps=10)
    #ard.move_mouse_interp(100,90)

    #ard.move_mouse(50,60)
    port = '/dev/tty.usbmodemfa13131'
    baud = 115200
    timeout = 1
    x = 5
    y = 5
    fps = 30
    slices = 3

    sh = serial.Serial(port, baud, timeout=timeout)


    for i in range(1, 100):
        #move_mouse(x,y, sh)
        move_mouse_interp(x, y, fps, slices, sh)
