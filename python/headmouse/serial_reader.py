#!/usr/bin/env python
#coding=utf8
'''
Write to stdin to serial
'''
import sys
import logging
import util
import serial
import thread
import time

logger = logging.getLogger(__name__)

SERIAL_COMMAND_BUFFER_LENGTH = 4



def send_mouse_command(x, y, serial_handle):
    try:
        #serial_string = "32100" + ard_num_string(x) + ard_num_string(y)
        serial_handle.write('m' + str(x)+ ',' + str(y) +'\n')
        # serial_handle.write( + '\r\n')
        # serial_handle.write(+ '\r\n')


    except Exception as e:
        logging.error("Error writing to serial output")
#        print e

@util.prep_gen
def move_mouse_gen(serial_handle):
    while True:
        x, y = yield
        serial_handle.write('c1,' + str(x) + ',' + str(y) + ';')

def set_mouse_max_move(serial_handle, maxMove):
    serial_handle.write('c2,' + str(maxMove))


def discover_serial_handle(glob_string = '/dev/tty.usb*'):
    import glob
    serial_interfaces = glob.glob(glob_string)

    for port in serial_interfaces:
        print "Trying port %s" % port
        baud = 57600
        timeout = 2

        try:
            sh = serial.Serial(port, baud, timeout=timeout)
            sh.write('c0')
            sh.flush()
            version_data = sh.readline().rstrip()
        except Exception:
            continue
    
        if version_data == unicode("hm0.0.1"):
            print "Found serial on port:", port
            return sh

    sys.exit("Could not find serial port for Arduino headmouse.")

if __name__ == '__main__':
    maxMag = 32000

    sh = discover_serial_handle()
    set_mouse_max_move(sh, 50)

    while True:
        try:
            print 'serial:', sh.readline().rstrip()
            sh.write('c3')

        except Exception as e:
            pass