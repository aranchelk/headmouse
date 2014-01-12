#!/usr/bin/env python
#coding=utf8
'''
Write to stdin to serial
'''

import serial
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


class AsyncArduino:
    def __init__(self, port='COM7', baud=115200, timeout=1):
        #self.connection = serial.Serial(port, baud, timeout=timeout)
        pass

    #def move_mouse(self, x, y):
        #self.connection.write("32100\n%d\n%d\n" % (int(x),int(y)))

    def move_mouse_interp(self, x, y):
        #Split commands into the a series of commands and schedule them to run
        interp_slices = 4
        interp_data = []

        x_interp_trunc = int(x/interp_slices)
        x_interp_remainder = x - x_interp_trunc * (interp_slices - 1)

        y_interp_trunc = int(y/interp_slices)
        y_interp_remainder = y - y_interp_trunc * (interp_slices - 1)

        interp_data.append((x_interp_remainder, y_interp_remainder))

        for i in range(interp_slices - 1):
            interp_data.append((x_interp_trunc, y_interp_trunc))

        for xy in interp_data:
            print xy


def get_async_arduino(port, baud, timeout):
    return AsyncArduino(port, baud, timeout)

'''            data = re.split('\,', message)

            control_code = int(message_data.pop(0))

            if control_code == 32100 and interp_slices > 1:
                interp_data = []

'''

if __name__ == '__main__':
    ard = get_async_arduino(5, 9600, 1)
    ard.move_mouse_interp(10,9)

