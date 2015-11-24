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
import math

from better_dots import process as bd_process
from better_dots import annotate_image as bd_annotate

from naive_dots import process as nd_process
from naive_dots import annotate_image as nd_annotate

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
    x = int(x)
    y = int(y)
    rad = int(rad)

    cv2.rectangle(img,(x - rad, y - rad), (x + rad, y + rad), color, 2)
    cv2.circle(img, (x,y), 2, color, 3)


def cropped_roi(img, dimensions):
    # Note, opencv coordinate system, 0,0 is upper right
    y1, y2, x1, x2 = dimensions

    return {'image':img[y1:y2, x1:x2], 'offset':(x1, y1)}

def normalize_detected(results):
    #Opencv alternates between returning an ndarray or empty tuple depending, none, or greater results.
    if results == ():
        return []
    else:
        return results.tolist()


def search_area_to_roi(x, y, x_rad, y_rad):
    for v in [x,y, x_rad, y_rad]:
        assert isinstance(v, int)

    x1 = x - x_rad
    x2 = x + x_rad
    y1 = y - y_rad
    y2 = y + y_rad

    return y1, y2, x1, x2

# def expand_roi((y1, y2, x1, x2), factor):
#     w = x2 - x1
#     h = y2 - y1
#
#     x_padding = int(w * factor / 2)
#     y_padding = int(h * factor / 2)
#
#     return y1 - y_padding, y2 + y_padding, x1 - x_padding, x2 + x_padding


def expand_rectangle((x,y,w,h), factor):
    h_delta = h * factor
    w_delta = w * factor

    x = int(round(x - w_delta / 2))
    y = int(round(y - h_delta / 2))

    h = int(round(h + h_delta))
    w = int(round(w + w_delta))

    return x, y, w, h


def rectangle_from_point(center, w, h):
    x, y = center

    x = x - w / 2
    y = y - h / 2

    return x, y, w, h


def rectangle_to_roi(x, y, w, h):
    y1 = y
    y2 = y + h
    x1 = x
    x2 = x + w

    return y1, y2, x1, x2


# def rectangle_morph_face_to_glasses((x, y, w, h)):
#     x_delta = int(w * 0.2)
#     y_delta = int(h * -0.1)
#
#     x -= x_delta
#     w += 2 * x_delta
#
#     y -= y_delta
#     h += 2 * y_delta
#
#     return x, y, w, h


def face_to_left_dot((x, y, w, h)):
    x += int(w * 0.7)
    y += int(h * 0.14)

    size = int(w * 0.4)
    w = size
    h = size

    return x, y, w, h


def darken(x):
    x -= 80
    if x < 0:
        x = 0
    return np.uint8(x)

darken_vec = np.vectorize(darken)


def create_gray_img(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def create_color_img(img):
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def create_threshold_image(gray_img, threshold_value):
    _, dots = cv2.threshold(gray_img, threshold_value,255,cv2.THRESH_BINARY)
    return dots

def np_median_or_zero(xs):
    med = np.median(xs)

    if math.isnan(med):
        return 0

    return med


def process_dots(threshold_img, offset=(0,0)):
    indexed_dots = np.argwhere(threshold_img) # 75 to 80 without, 66-67 with

    # Todo: test for 0 values here

    xs, ys = np.rot90(indexed_dots) # no obvious difference

    try:
        x = np_median_or_zero(xs)
        y = np_median_or_zero(ys)

    except ValueError:
        # This is indicative of an image with no dots, this is okay.
        x = 0
        y = 0

         # TODO: real distance, or measured fixed distance value
    z = 10

    x = (np.ndarray.max(xs) + np.ndarray.min(xs))/2
    y = (np.ndarray.max(ys) + np.ndarray.min(ys))/2

    x += offset[0]
    y += offset[1]

    return {'coords': (x,y,z),
            'count': len(indexed_dots),
            'x_min': np.ndarray.min(xs) + offset[0],
            'x_max': np.ndarray.max(xs) + offset[0],
            'y_min': np.ndarray.min(ys) + offset[1],
            'y_max': np.ndarray.max(ys) + offset[1]
            }


def annotate_with_rectangle(img, (x, y, w, h), color=(255,0,0)):
    cv2.rectangle(img, (x,y),(x+w,y+h),color,2)

#
# def annotate_with_roi(img, (y1, y2, x1, x2), color=(200,200,50)):
#     cv2.rectangle(img, (x1,y1),(x2,y2),color,2)


def annotate_with_coordinates(img, coords, color=(255,0,0)):
    x, y, z = coords
    cv2.circle(img, (int(x), int(y)), int(5), color, 2)


def annotate_with_dots(color_img, dot_map, color=(0,255,0)):
    mask = cv2.bitwise_not(dot_map)

    # Unknown length of shape depending on color or grayscale image
    y_dim, x_dim = color_img.shape[0], color_img.shape[1]

    all_red = np.zeros((y_dim, x_dim, 3), np.uint8)
    all_red[:] = (0, 0, 255)

    all_red = cv2.bitwise_and(all_red, all_red, mask=dot_map)
    masked_gray = cv2.bitwise_and(color_img, color_img, mask = mask)

    return cv2.add(masked_gray, all_red)


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def __init__(self, *args, **kwargs):
        self.other_faces = None
        self.face = None
        self.process_count = 0
        self.process_max_iterations = 50
        self.dot_tracker = None
        self.left_dot_boundry = None

        super(Vision, self).__init__(*args, **kwargs)

    def display_image(self):
        gray = self.frame
        color = cv2.cvtColor(self.frame, cv2.COLOR_GRAY2BGR)

        if self.coords:
            annotate_with_coordinates(color, self.coords, color=(0,255,255))

        # if self.dot_tracker:
        #     annotate_with_rectangle(color, self.dot_tracker)

        if self.face:
            annotate_with_rectangle(color, self.face)
            annotate_with_rectangle(color, self.left_dot_boundry, color=(255,255,0))
            #annotate_with_rectangle(color, expand_rectangle(self.left_dot_boundry, 1.2), color=(255,255,0))

            #color[y1:y2, x1:x2] = annotate_with_dots(color[y1:y2, x1:x2], dots)


            cv2.imshow('roi', cv2.flip(color, flipCode=1))
            pass



        #cv2.imshow('frame', cv2.flip(self.frame, flipCode=1))

    def process(self):
        self.coords = (0,0,0) # Todo: this should be None, and everything should accept None
        # Todo:
        # * Update ROI based on reflector location
        # * If reflector location is empty, scan
        # ROI example http://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection.html#gsc.tab=0
        if self.frame is not None:
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # Only find face every n times
            if self.process_count == 0:
                # Find face
                faces = normalize_detected(eye_cascade.detectMultiScale(self.frame))

                if faces:
                    if len(faces) > 1:
                        # Tallest face is most likely the operator
                        faces = [sorted(faces, key=lambda (x,y,w,h): h, reverse=True)[0]]
                        self.other_faces = faces.pop(0)
                    else:
                        other_faces = None

                    self.face = faces[0]

                    self.left_dot_boundry = face_to_left_dot(self.face)

                    self.process_count += 1
                else:
                    # If no faces were detected, try again on next pass.
                    self.process_count = 0

            elif self.process_count > self.process_max_iterations:
                self.process_count = 0
            else:
                self.process_count += 1


        if self.face:
            y1, y2, x1, x2 = rectangle_to_roi(*self.left_dot_boundry)
            dots = create_threshold_image(self.frame[y1:y2, x1:x2], self.config['dot_threshold'])
            dot_info = process_dots(dots, offset=(x1, y1))
            self.coords = dot_info['coords']
            dot_count = dot_info['count']

            if dot_count > 0:
                # Update the roi
                new_width = dot_info['x_max'] - dot_info['x_min']
                new_height = dot_info['y_max'] - dot_info['y_min']

                self.left_dot_boundry = expand_rectangle(
                    rectangle_from_point((self.coords[0], self.coords[1]), new_height, new_width),
                    2
                )

        return self.coords


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