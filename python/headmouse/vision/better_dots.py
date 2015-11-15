#!/usr/bin/env python

from __future__ import print_function

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import cv2
import util
import _vision
import numpy as np


def midrange(numList):
    return (max(numList) + min(numList))/2


def display(faces=None, objects=None, kp=None, coords=(None, None, None), dot_map=None, boxes=None, img=None):
    if dot_map is not None:
        mask = cv2.bitwise_not(dot_map)

        y_dim, x_dim = img.shape
        all_red = np.zeros((y_dim, x_dim, 3), np.uint8)
        all_red[:] = (0, 0, 255)

        all_red = cv2.bitwise_and(all_red, all_red, mask=dot_map)

        c_gray = cv2.cvtColor(img, cv2.cv.CV_GRAY2RGB)
        masked_gray = cv2.bitwise_and(c_gray, c_gray, mask = mask)

        img = cv2.add(masked_gray, all_red)

    if coords:
        x, y, distance = coords
    if img is not None:
        if x is not None and y is not None:
            cv2.circle(img, (int(x), int(y)), int(40/distance), (255, 0, 0), 3)

    cv2.imshow('frame', cv2.flip(img, flipCode=1))


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def display_image(self):
        display(img=self.frame, coords=(self.x, self.y, self.z), dot_map=self.dots)
        pass

    def process(self):
        if self.frame is not None:
            # TODO: real distance, or measured fixed distance value
            detector = cv2.ORB()

            x, y = None, None
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            ret, thresh3 = cv2.threshold(gray,self.config['dot_threshold'],255,cv2.THRESH_BINARY)

            indexed_dots = np.argwhere(thresh3) # 75 to 80 without, 66-67 with
            xs, ys = np.rot90(indexed_dots) # no obvious difference

            try:
                self.x = (np.ndarray.max(xs) + np.ndarray.min(xs))/2
                self.y = (np.ndarray.max(ys) + np.ndarray.min(ys))/2
            except ValueError:
                # This is indicative of an image with no dots, this is okay.
                self.x = 0
                self.y = 0
                pass

            self.z = 10

            self.dots = thresh3
            self.frame = gray

            return self.x, self.y, self.z


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