#!/usr/bin/env python

from __future__ import print_function

import cv2
import time
import uuid
import time
# Todo: frame id should come from uuid


class Camera():
    def __init__(self, current_config):
        # Todo: Add a function to decide whether or not image is displayed
        # Todo: if gray_scale is true, setup loopback camera ffmpeg stream in black and white

        self.conf = current_config
        self.window_id = str('frame') # Todo: change frame to UUID
        self.cap = cv2.VideoCapture(self.conf['camera_device_id'])

        self.cap.set(3, self.conf['camera_dimensions'][0])
        self.cap.set(4, self.conf['camera_dimensions'][1])

        self.gray_scale = self.conf['gray_scale'] if 'gray_scale' in self.conf else True
        self.frame = None

    def __enter__(self):
        #print '__enter__()'
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('Camera cleaning up...')
        self.cap.release()
        cv2.destroyWindow(self.window_id)
        time.sleep(2)

    def get_image(self):
        ret, frame = self.cap.read()
        self.frame = frame

        if cv2.waitKey(1) & 0xFF == ord('q'):
            raise Exception('Quit issued from cv2 process')

        return frame

    def display_image(self):
        if self.frame is not None:
            # Intuitive for user to see a mirror image.
            cv2.imshow('frame', cv2.flip(self.frame,flipCode=1))
        else:
            print("frame is none.")

    def process(self):
        # Not implemented
        pass


if __name__ == "__main__":
    def every_n(freq, func):
        counter = 0

        while True:
            if counter >= freq:
                yield func()
                counter = 0
            else:
                yield None

            counter += 1


    camera_config = {
        'device_id':1,
        'camera_dimensions': (640, 480),
        'format_':1,
        'gray_scale':False,
        'camera_gain':0,
        'camera_brightness':0
    }

    try:
        with Camera(camera_config) as cam:
            display_frame = every_n(4, cam.display_image)

            while True:
                frame = cam.get_image()
                display_frame.next()
    except KeyboardInterrupt:
        print("bye")