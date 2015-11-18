#!/usr/bin/env python

from __future__ import print_function

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import cv2
import util
import _vision


def midrange(numList):
    return (max(numList) + min(numList))/2


class DotPoints:
    # Given a list of keypoints returned by opencv feature detect algo, present usable data
    def cursor_position(self):
        if len(self.kp) > 0:
            if self.x_range > 100:
                r = int((1 / self.x_range**2) * 650000)
            else:
                r = 10
            return midrange(self.x_list), midrange(self.y_list), r
        else:
            return 0, 0, self.distance

    def set_block_area(self, percent_x, percent_y, offset_x, offset_y):
        if self.kp is not None:
            self.block_area = [( ( min(self.x_list), min(self.y_list) ) , ( max(self.x_list), max(self.y_list) ) )]

    def __init__(self, kp):
        self.kp = kp

        self.x_list = []
        self.y_list = []

        self.block_area = None
        self.distance = 10.0

        if len(kp) > 0:
            for k in kp:
                self.x_list.append(k.pt[0])
                self.y_list.append(k.pt[1])

                self.x_range = max(self.x_list) - min(self.x_list)


def process(img, conf=None):
    # TODO: real distance, or measured fixed distance value
    detector = cv2.ORB()

    x, y = None, None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh3 = cv2.threshold(gray, conf['dot_threshold'],255,cv2.THRESH_BINARY)

    kp = detector.detect(thresh3)
    dp = DotPoints(kp)

    x, y, z = dp.cursor_position()

    return (gray, kp), (x,y,z)


def annotate_image(img, kp=None, coords=None):
    if coords is not None and None not in coords:
        x, y, z = coords
        cv2.circle(img, (int(x), int(y)), int(40/z), (255, 0, 0), 3)
    if kp:
        img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)
    return img


def display(img=None, kp=None, coords=(None, None)):
    img = annotate_image(img, kp, coords)
    cv2.imshow('frame', cv2.flip(img, flipCode=1))


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def display_image(self):
        #cv2.imshow('frame', cv2.flip(self.frame,flipCode=1))
        display(img=self.frame, kp=self.kp, coords=(self.x, self.y, self.z))
        pass

    def process(self):
        if self.frame is not None:
            (self.frame, self.kp), (self.x, self.y, self.z) = process(self.frame, self.config)
            # TODO: real distance, or measured fixed distance value

            return self.x, self.y, self.z


if __name__ == "__main__":
    from cameras import v4l2_loopback_camera as camera

    f = 180.0

    fps = util.simple_fps()
    print_fps = util.Every_n(f, lambda: print("fps: " + str( fps.next() * f)))

    camera_config = {
        'device_id':1,
        'width':640,
        'height':480,
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
                display_frame = util.Every_n(3, viz.display_image)

                while True:
                    viz.get_image()
                    viz.process()

                    display_frame.next()
                    print_fps.next()

    except KeyboardInterrupt:
        print("Program exiting.")