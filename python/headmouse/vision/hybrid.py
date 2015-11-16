#!/usr/bin/env python

from __future__ import print_function

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import cv2
import util
import _vision
import numpy as np

import pkg_resources
import tempfile


cascade_file = tempfile.NamedTemporaryFile()
try:
    cascade_file.write(pkg_resources.resource_stream(
        __name__,
        '../data/cascades/haarcascade_frontalface_alt.xml'
        #'data/cascades/Nariz.xml'
    ).read())
except:
    with open('haarcascade_frontalface_alt.xml', 'rb') as f:
        cascade_file.write(f.read())
finally:
    cascade_file.flush()

EYE_CASCADE_FILE = cascade_file.name
eye_cascade_file=EYE_CASCADE_FILE
eye_cascade = cv2.CascadeClassifier(eye_cascade_file)


def midrange(numList):
    return (max(numList) + min(numList))/2


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def display_image(self):
        for (x,y,w,h) in self.faces:
            cv2.rectangle(self.frame,(x,y),(x+w,y+h),(255,0,0),2)

        cv2.imshow('frame', cv2.flip(self.frame, flipCode=1))

    def process(self):
        if self.frame is not None:
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            self.faces = eye_cascade.detectMultiScale(gray)

            self.frame = gray
        return 0, 0, 0


if __name__ == "__main__":
    from cameras import v4l2_loopback_camera as camera

    f = 180.0

    fps = util.simple_fps()
    print_fps = util.Every_n(f, lambda: print("fps: " + str( fps.next() * f)))

    camera_config = {
        'device_id':1,
        'width':1920,
        'height':1080,
        'format_':1,
        'display':True,
        'gray_scale':False,
        'dot_threshold': 240,
        'camera_gain': 0,
        'camera_brightness': 0
    }

    try:
        with camera.Camera(camera_config) as cam:
            vision_config = camera_config.copy()

            with Vision(cam, vision_config) as viz:
                display_frame = util.Every_n(1, viz.display_image)

                while True:
                    viz.get_image()
                    viz.process()

                    display_frame.next()
                    print_fps.next()

    except KeyboardInterrupt:
        print("Program exiting.")