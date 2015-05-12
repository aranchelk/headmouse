#!/usr/bin/env python
#coding=utf8
import logging
logger = logging.getLogger(__name__)

import random
import operator
import itertools

# need non-mp Queue for the Queue.Full exception
import time

def child_process_event_handler(queue, fps, slices, port, baud, timeout=1):
    def interpolated_deltas():
        '''
        Pull mouse coords of the Queue shared with the parent process,
        then split them up into interpolated segments and yield the 
        segments one at a time
        '''
        while True:
            x, y = queue.get()
            for d_x, d_y in delta_slice_x_y(x, y, slices):
                yield d_x, d_y

    logger.debug('In serial child handler')

    serial_handle = serial.Serial(port, baud, timeout=timeout)
    interval = 1. / (fps * slices)

    for d_x, d_y in interpolated_deltas():
        move_mouse(d_x, d_y, serial_handle)
        time.sleep(interval)

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
    return zip(delta_slice(int(x), slice_quantity), delta_slice(int(y), slice_quantity))

class AsyncArduino:
    def __init__(self, port, baud, timeout=1, fps=30, slices=3):
        #self.connection = serial.Serial(port, baud, timeout=timeout)
        self.fps = fps
        self.interp_slices = slices
        self.port = port
        self.baud = baud

        self.queue = multiprocessing.Queue(SERIAL_COMMAND_BUFFER_LENGTH)
        p = multiprocessing.Process(
            target=child_process_event_handler, 
            args=(self.queue, fps, slices, port, baud)
        )
        p.start()
        self.__child_process = p

    def __del__(self):
        self.__child_process.join()
        self.__child_process.terminate()
        pass

    def move_mouse(self, x, y):
        # non-blocking; better to drop frames if the HW driver isn't keeping up
        try:
            self.queue.put_nowait((x, y))
        except Queue.Full:
            logger.debug("Dropping data, serial handler not keeping up")
            pass

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
