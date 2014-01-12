#!/usr/bin/env python
from multiprocessing import Process, Pipe
import re

def async_serial_writer(conn, fps=30, interp_slices=2):
    #Open serial connection

    while conn.poll(2):
        try:
            message = conn.recv()






            #Divide by 4, convert to int, on last go, subtract from original to prevent losing 1 in decimals
            #serial write to arduino
            #threading.Timer
            #automatically calculate wait times input fps and shutter_blade_count

            #In final version, no send needed
            conn.send('child:' + str(message))
        except:
            continue

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=async_serial_writer, args=(child_conn,))
    p.start()
    for i in range(10):
        parent_conn.send('test' + str(i) + "\n")
        print i

    while parent_conn.poll(1):
        print parent_conn.recv()

    p.join()
    p.terminate()

    #Parent has 4 methods for child: start, send, stop, read