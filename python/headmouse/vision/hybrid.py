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

#haar_file = 'haarcascade_frontalface_alt2.xml'
#haar_file = 'haarcascade_frontalface_alt_tree.xml'
haar_file = 'haarcascade_frontalface_alt.xml'
#haar_file = 'haarcascade_frontalface_default.xml'

cascade_file = tempfile.NamedTemporaryFile()
try:
    cascade_file.write(pkg_resources.resource_stream(
        __name__,
        '../data/cascades/' + haar_file
        #'data/cascades/Nariz.xml'
    ).read())
except:
    with open(haar_file, 'rb') as f:
        cascade_file.write(f.read())
finally:
    cascade_file.flush()

EYE_CASCADE_FILE = cascade_file.name
eye_cascade_file=EYE_CASCADE_FILE
eye_cascade = cv2.CascadeClassifier(eye_cascade_file)


def midrange(numList):
    return (max(numList) + min(numList))/2


def annotate_dot_search(img, (x,y), rad, color=(0,255,0)):
    cv2.rectangle(img,(x - rad, y - rad), (x + rad, y + rad), color, 2)
    cv2.circle(img, (x,y), 2, color, 3)


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def __init__(self, *args, **kwargs):
        self.faces = None
        self.process_count = 0
        self.process_max_iterations = 50

        super(Vision, self).__init__(*args, **kwargs)


    def display_image(self):
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_GRAY2BGR)
        if self.faces is not None and self.faces != ():
            face_list = self.faces.tolist()

            #print(face_list)

            if len(face_list) > 1:
                print("multiple faces detected.")
                face_list = [sorted(face_list, key=lambda (x,y,w,h): h, reverse=True)[0]]

            for (x,y,w,h) in self.faces:
                cv2.rectangle(self.frame,(x,y),(x+w,y+h),(255,0,0),2)

            for (x,y,w,h) in face_list:
                cv2.rectangle(self.frame,(x,y),(x+w,y+h),(255,0,0),2)

                rr_loc = (int(x + w/10), int(y + h * .3))
                lr_loc = (int(x + w* 9/10), int(y + h * .3))

                r_rad = h/4

                annotate_dot_search(self.frame, rr_loc, r_rad)
                annotate_dot_search(self.frame, lr_loc, r_rad, color=(0,0,255))

        cv2.imshow('frame', cv2.flip(self.frame, flipCode=1))

    def process(self):
        # Todo:
        # * Search only in reflector locations
        # * Update ROI based on reflector location
        # * If reflector location is empty, scan
        # ROI example http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
        if self.frame is not None:
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            if self.process_count == 0:
                # Find face
                self.faces = eye_cascade.detectMultiScale(self.frame)

            if self.faces == ():
                self.process_count = 0
            elif self.process_count > self.process_max_iterations:
                self.process_count = 0
            else:
                self.process_count += 1

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