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
    img = annotate_image(img, dot_map=dot_map, coords=coords)
    cv2.imshow('frame', cv2.flip(img, flipCode=1))


def annotate_image(img, dot_map=None, coords=None):
    if dot_map is not None:
        mask = cv2.bitwise_not(dot_map)

        y_dim, x_dim = img.shape
        all_red = np.zeros((y_dim, x_dim, 3), np.uint8)
        all_red[:] = (0, 0, 255)

        all_red = cv2.bitwise_and(all_red, all_red, mask=dot_map)

        c_gray = cv2.cvtColor(img, cv2.cv.CV_GRAY2RGB)
        masked_gray = cv2.bitwise_and(c_gray, c_gray, mask = mask)

        img = cv2.add(masked_gray, all_red)

    if coords is not None and None not in coords:
        x, y, z = coords
        cv2.circle(img, (int(x), int(y)), int(40/z), (255, 0, 0), 3)

    return img


def process(img, conf=None):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, dots = cv2.threshold(gray, conf['dot_threshold'],255,cv2.THRESH_BINARY)

    indexed_dots = np.argwhere(dots) # 75 to 80 without, 66-67 with
    xs, ys = np.rot90(indexed_dots) # no obvious difference

    try:
        x = (np.ndarray.max(xs) + np.ndarray.min(xs))/2
        y = (np.ndarray.max(ys) + np.ndarray.min(ys))/2
    except ValueError:
        # This is indicative of an image with no dots, this is okay.
        x = 0
        y = 0

         # TODO: real distance, or measured fixed distance value
    z = 10

    return ((gray, dots), (x,y,z))


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def display_image(self):
        display(img=self.frame, coords=(self.x, self.y, self.z), dot_map=self.dots)
        pass

    def process(self):
        (x,y,z) = (0,0,0)
        if self.frame is not None:
        #     gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        #     ret, thresh3 = cv2.threshold(gray,self.config['dot_threshold'],255,cv2.THRESH_BINARY)
        #
        #     indexed_dots = np.argwhere(thresh3) # 75 to 80 without, 66-67 with
        #     xs, ys = np.rot90(indexed_dots) # no obvious difference
        #
        #     try:
        #         self.x = (np.ndarray.max(xs) + np.ndarray.min(xs))/2
        #         self.y = (np.ndarray.max(ys) + np.ndarray.min(ys))/2
        #     except ValueError:
        #         # This is indicative of an image with no dots, this is okay.
        #         self.x = 0
        #         self.y = 0
        #         pass
        #
        #     # TODO: real distance, or measured fixed distance value
        #     self.z = 10
        #
        #     self.dots = thresh3
        #     self.frame = gray
        #
        #     return self.x, self.y, self.z
            ((self.frame, self.dots),(x,y,z)) = process(self.frame, self.config)

        return x, y, z


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