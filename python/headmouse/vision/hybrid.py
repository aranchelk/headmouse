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


def search_area_to_roi(x, y, x_rad, y_rad):
    for v in [x,y, x_rad, y_rad]:
        assert isinstance(v, int)

    x1 = x - x_rad
    x2 = x + x_rad
    y1 = y - y_rad
    y2 = y + y_rad

    return y1, y2, x1, x2


def rectangle_to_roi(x, y, w, h):
    y1 = y
    y2 = y + h
    x1 = x
    x2 = x + w

    return y1, y2, x1, x2


def overlay_images(bottom_img, top_img, offset):
    gray_top = cv2.cvtColor(top_img, cv2.COLOR_BGR2GRAY)
    #padded_gray_top =
    gray_bottom = cv2.cvtColor(bottom_img, cv2.COLOR_BGR2GRAY)
    #print(gray_bottom)

    y_pad = int(bottom_img.shape[0] - top_img.shape[0])
    x_pad = int(bottom_img.shape[1] - top_img.shape[1])

    # There's probably a better way to do this.
    #center_mask = np.zeros((140,220))
    #center_mask.fill(1)

    # Todo: impement offset
    #np.lib.pad(a, [(y_before,y_after),(x_before,x_after)], 'constant', constant_values=(0,0))
    padded = np.lib.pad(gray_top, [(0,y_pad),(0, x_pad)], 'constant', constant_values=0)



    #print(bottom_img.shape, mask.shape)
    #print(mask)
    #mask = cv2.bitwise_not()

    #print(type(mask))

    # Unknown length of shape depending on color or grayscale image
    #y_dim, x_dim = img.shape[0], img.shape[1]

    #all_red = np.zeros((y_dim, x_dim, 3), np.uint8)
    #all_red[:] = (0, 0, 255)

    #all_red = cv2.bitwise_and(all_red, all_red, mask=dot_map)

    #c_gray = cv2.cvtColor(img, cv2.cv.CV_GRAY2RGB)
    #masked_bottom = cv2.bitwise_not(gray_bottom, mask)
    #print(gray_bottom.shape)
    #masked_bottom = cv2.bitwise_and(gray_bottom, gray_bottom, mask = mask)
    cv2.rectangle(gray_bottom,(0,0),(top_img.shape[1],top_img.shape[0]),(0,0,0),cv2.cv.CV_FILLED)

    return cv2.add(gray_bottom, padded)

    #return gray_bottom


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def __init__(self, *args, **kwargs):
        self.faces = None
        self.process_count = 0
        self.process_max_iterations = 50

        super(Vision, self).__init__(*args, **kwargs)


    def display_image(self):
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_GRAY2BGR)

        #cv2.circle(self.frame, (100,0), 2, (200,200,50), 3)

        if self.faces is not None and self.faces != ():
            face_list = self.faces.tolist()

            if len(face_list) > 1:
                face_list = [sorted(face_list, key=lambda (x,y,w,h): h, reverse=True)[0]]

            for (x,y,w,h) in self.faces:
                cv2.rectangle(self.frame,(x,y),(x+w,y+h),(255,0,0),2)

            # for (x,y,w,h) in face_list:
            #     cv2.rectangle(self.frame,(x,y),(x+w,y+h),(255,0,0),2)
            #
            #     rr_loc = (int(x + w/10), int(y + h * .3))
            #     lr_loc = (int(x + w* 9/10), int(y + h * .3))
            #
            #     r_rad = h/4
            #
            #     annotate_dot_search(self.frame, rr_loc, r_rad)
            #     #annotate_dot_search(self.frame, lr_loc, r_rad, color=(0,0,255))
            #
            #     #r_roi = self.frame[rr_loc[1] - r_rad:rr_loc[1] + r_rad, rr_loc[0] - r_rad: rr_loc + r_rad]
            #     r_roi = cropped_roi_square(self.frame, )
            #     #((r_gray, r_kp), (rx,ry,rz)) = nd_process(r_roi, conf=self.config)
            #     #self.frame = nd_annotate(self.frame, kp=r_kp, coords=(rx,ry,rz))
            #
            #     annotate_dot_search(self.frame, (rx, ry), 5, color=(255,255,0))

            if len(face_list) > 0:
                face = face_list[0]

                roi = cropped_roi(self.frame, rectangle_to_roi(*face))['image']

                overlay = overlay_images(self.frame, roi, (0,0))

                cv2.imshow('roi', cv2.flip(overlay, flipCode=1))
                pass





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