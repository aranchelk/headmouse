#!/usr/bin/env python
#coding=utf8
'''
Write to stdin to serial
'''

import serial
import threading
from multiprocessing import Process, Pipe
import sys
import re
import time

class SyncArduino:
    def __init__(self, port='COM7', baud=115200, timeout=1):
        self.connection = serial.Serial(port, baud, timeout=timeout)

    def move_mouse(self, x, y):
        self.connection.write("32100\n%d\n%d\n" % (int(x),int(y)))


def get_sync_arduino(port, baud, timeout):
    return SyncArduino(port, baud, timeout)


def child_process_event_loop(conn, fps, slices):
    while conn.poll(3):
        try:
            x, y = conn.recv()
            move_mouse(x,y)
        except:
            continue

def move_mouse(x, y):
    #print "move %s,%s\n\n" % (x, y)
    h = open('./templog', 'a')
    h.write("move %s,%s\n" % (str(x), str(y)))

def move_mouse_interp(x, y, fps, interp_slices):
    #Split commands into the a series of commands and schedule them to run
    interp_data = []

    x_interp_trunc = int(x/interp_slices)
    x_interp_remainder = x - x_interp_trunc * (interp_slices - 1)

    y_interp_trunc = int(y/interp_slices)
    y_interp_remainder = y - y_interp_trunc * (interp_slices - 1)

    interp_data.append((x_interp_remainder, y_interp_remainder))

    for i in range(interp_slices - 1):
        interp_data.append((x_interp_trunc, y_interp_trunc))

    #Schedule mouse moves
    i = 0
    inc = 1.0 / (fps * interp_slices)
    for x, y in interp_data:
        threading.Timer(inc * i, move_mouse, [x,y]).start()
        i += 1


class AsyncArduino:
    def __init__(self, port='COM7', baud=115200, timeout=1, fps=30, slices=4):
        #self.connection = serial.Serial(port, baud, timeout=timeout)
        self.fps = fps
        self.interp_slices = slices

        parent_conn, child_conn = Pipe()
        p = Process(target=child_process_event_loop, args=(child_conn, fps, slices))
        p.start()
        self.__child_process = p
        self.__child_process_connection = parent_conn

    def __del__(self):
        self.__child_process.join()
        self.__child_process.terminate()
        pass

    def send_to_child(self, xy_delta):
        self.__child_process_connection.send(xy_delta)


def get_async_arduino(port, baud, timeout):
    return AsyncArduino(port, baud, timeout)

'''            data = re.split('\,', message)

            control_code = int(message_data.pop(0))

            if control_code == 32100 and interp_slices > 1:
                interp_data = []

'''

if __name__ == '__main__':
    ard = get_async_arduino(5, 9600, 1)
    #ard.move_mouse_interp(100,90)
    ard.send_to_child((50,60))

