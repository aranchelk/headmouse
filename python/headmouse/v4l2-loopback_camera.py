#!/usr/bin/env python

# Intended to be run with v4l2 loopback camera
# v4l2-ctl --list-devices
# sudo modprobe v4l2loopback
# ffmpeg -f video4linux2 -input_format mjpeg -s 640x480 -i /dev/video1 -vcodec rawvideo -pix_fmt gray -threads 0 -f v4l2 /dev/video2

import cv2
import time
import uuid

def simple_fps(calc_interval):
    last_time = float(time.time())
    fps = None
    frames = 0

    while True:
        yield fps
        frames += 1
        current_time = float(time.time())
        interval = current_time - last_time

        if (interval > calc_interval):

            #calculate fps
            fps = frames / interval

            #reset start values
            last_time = current_time
            frames = 0

        else:
            fps = None


def print_unless_none(value):
    if value is not None:
        print value


class Camera():
    def __init__(self, **kwargs):
        # Todo: Add a function to decide whether or not image is displayed
        # Todo: Add setup of virtual loopback camera
        # Todo: if gray_scale is true, setup loopback camera ffmpeg stream in black and white
        # Todo: Consider dropping root permissions after setting up loopback camera
        self.window_id = str('frame')
        print '__init__()'
        self.cap = cv2.VideoCapture(kwargs['device_id'])
        self.display = kwargs['display'] if 'display' in kwargs else False
        self.gray_scale = kwargs['gray_scale'] if 'gray_scale' in kwargs else True

        if 'stats_function' in kwargs:
            self.stats_function = kwargs['stats_function']
        else:
            self.stats_function = None

    def __enter__(self):
        print '__enter__()'
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print 'Bye.'
        self.cap.release()
        cv2.destroyWindow(self.window_id)
        # Todo: add a function to destroy loopback camera

    def get_image(self):
        #self.display = not self.display
        ret, frame = self.cap.read()

        if self.display:
            cv2.imshow('frame', frame)

        if self.stats_function:
            self.stats_function()

        if cv2.waitKey(1) & 0xFF == ord('q'):
             raise Exception('Quit issued from cv2 process')

        return frame

if __name__ == "__main__":

    fps = simple_fps(1)

    camera_config = {
        'device_id':2,
        'width':320,
        'height':200,
        'fps':60,
        'format_':1,
        'display':True,
        'gray_scale':False,
        'stats_function': lambda:print_unless_none(fps.next())
    }
    with Camera(**camera_config) as cam:
        while True:
            frame = cam.get_image()