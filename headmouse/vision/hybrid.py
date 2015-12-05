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

def normalize_detected(raw):
    if raw == ():
        return []

    return raw.tolist()


def search_area_to_roi(x, y, x_rad, y_rad):
    for v in [x,y, x_rad, y_rad]:
        assert isinstance(v, int)

    x1 = x - x_rad
    x2 = x + x_rad
    y1 = y - y_rad
    y2 = y + y_rad

    return y1, y2, x1, x2


def expand_rectangle_from_center((x,y,w,h), factor):
    h_delta = h * factor
    w_delta = w * factor

    x = int(round(x - w_delta / 2))
    y = int(round(y - h_delta / 2))

    h = int(round(h + h_delta))
    w = int(round(w + w_delta))

    return x, y, w, h


def expand_rectangle_from_corner((x,y,w,h), factor):
    return int(factor * x), int(factor * y), int(factor * w), int(factor * h)


def rectangle_from_point(center, w, h):
    x, y = center

    x = x - w / 2
    y = y - h / 2

    return x, y, w, h


def rectangle_from_dot_info(dot_info):
    return rectangle_from_point((dot_info['coords'][0], dot_info['coords'][1]),
                                dot_info['footprint'][0], dot_info['footprint'][1])


def rectangle_to_roi(x, y, w, h):
    y1 = y
    y2 = y + h
    x1 = x
    x2 = x + w

    return y1, y2, x1, x2


def face_to_dot_boundary(xywh, xywh_factors):
    x, y, w, h = xywh
    fx, fy, fw, fh = xywh_factors

    rx = x + int(w * fx)
    ry = y + int(h * fy)

    # Todo: use both fw and fh
    size = int(w * fw)
    rw = size
    rh = size

    return rx, ry, rw, rh


def face_to_left_dot(x, y, w, h):
    x += int(w * 0.7)
    y += int(h * 0.14)

    size = int(w * 0.4)
    w = size
    h = size

    return x, y, w, h

def face_to_right_dot(x, y, w, h):
    x -= int(w * 0.1)
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

    if len(indexed_dots) == 0:
        return {'coords': None, 'count': 0, 'footprint': None}

    xs, ys = np.rot90(indexed_dots) # no obvious difference

    try:
        x = np_median_or_zero(xs)
        y = np_median_or_zero(ys)

    except ValueError:
        # This is indicative of an image with no dots, this is okay.
        x = 0
        y = 0

        print(indexed_dots)

         # TODO: real distance, or measured fixed distance value
    z = 10

    x = (np.ndarray.max(xs) + np.ndarray.min(xs))/2
    y = (np.ndarray.max(ys) + np.ndarray.min(ys))/2

    x += offset[0]
    y += offset[1]

    x_min = np.ndarray.min(xs) + offset[0]
    x_max = np.ndarray.max(xs) + offset[0]
    y_min = np.ndarray.min(ys) + offset[1]
    y_max = np.ndarray.max(ys) + offset[1]

    footprint = (x_max - x_min + 1, y_max - y_min + 1)

    return {'coords': (x,y,z),
            'count': len(indexed_dots),
            'footprint': footprint
            }


def annotate_with_rectangle(img, (x, y, w, h), color=(255,0,0)):
    cv2.rectangle(img, (x,y),(x+w,y+h),color,1)

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


def validate_dot_boundary(dot_info, camera_dimensions):
    if dot_info == None:
        return False

    if dot_info['coords'] is None:
        return False

    if dot_info['count'] == 0:
        return False

    ratio = float(min(dot_info['footprint']))/float(max(dot_info['footprint']))

    if ratio < 0.6:
        return False

    # Todo: Add proper boundary validation
    # Validate based on size relative to frame
    # Validate on shape, i.e. squareness
    # Validate on how many dots are present
    # Validate on dots vs size

    # Todo: make this a configuration, max relative dot size.
    if dot_info['footprint'][0] > camera_dimensions[0] * 0.14:
        return False

    if dot_info['footprint'][1] > camera_dimensions[1] * 0.14:
        return False

    return True


def shrink_to_width(img, width):
    factor = float(width) / img.shape[1]
    height = int(img.shape[0] * factor)
    return cv2.resize(img, (width,height), interpolation=cv2.INTER_AREA), factor


def image_to_dot_info(img, dot_boundary, threshold):
    y1, y2, x1, x2 = rectangle_to_roi(*dot_boundary)
    dots = create_threshold_image(img[y1:y2, x1:x2], threshold)

    dot_info = process_dots(dots, offset=(x1, y1))
    dot_info['dot_boundary'] = dot_boundary

    return dot_info


# Todo: Make this generic and place in a shared vision library
class Vision(_vision.Vision):

    def __init__(self, *args, **kwargs):
        self.other_faces = None
        self.face = None
        self.process_count = 0
        self.process_max_iterations = 2000
        self.dot_tracker = None
        self.dot_boundaries = None
        self.dots = None
        self.color = None
        self.coords = None

        super(Vision, self).__init__(*args, **kwargs)

    def display_image(self):
        color = self.color

        if self.other_faces and self.process_count < 100:
            for f in self.other_faces:
                annotate_with_rectangle(color, f, color=(50,20,0))

        if self.face and self.process_count < 100:
            annotate_with_rectangle(color, self.face)

        if self.dot_boundaries is not None and len(self.dot_boundaries) > 0:
            for db in self.dot_boundaries:
                annotate_with_rectangle(color, db, color=(255,255,0))
            #annotate_with_rectangle(color, expand_rectangle(self.left_dot_boundary, 1.2), color=(255,255,0))
        # Todo: fix this
        # if self.dots is not None and self.left_dot_boundary is not None:
        #     y1, y2, x1, x2 = rectangle_to_roi(*self.left_dot_boundary)
        #     color[y1:y2, x1:x2] = annotate_with_dots(color[y1:y2, x1:x2], self.dots)

        if self.coords:
            annotate_with_coordinates(color, self.coords, color=(0,0,255))

        cv2.imshow('frame', cv2.flip(color, flipCode=1))

    def process(self):
        # Todo: Change flow so face detection only activates if no dot is found.
        self.coords = None

        dot_descriptors = [(0.7, 0.14, 0.4, 0.4), (-0.1, 0.14, 0.4, 0.4)] # x,y,w,h

        if self.frame is not None:

            self.color = self.frame
            self.frame = create_gray_img(self.frame)

            # Only find face every n times
            if self.process_count == 0:
                self.face = None
                self.dot_boundaries = []
                # Find face
                # Shrinking image for faster face detection (about 30x faster).
                tiny_gray, factor = shrink_to_width(self.frame, 120)
                faces = normalize_detected(eye_cascade.detectMultiScale(tiny_gray))

                if faces:
                    if len(faces) > 1:
                        # Tallest face is most likely the operator
                        faces.sort(key=lambda x: x[3], reverse=True)

                    self.face = expand_rectangle_from_corner(faces[0], 1/factor)
                    self.other_faces = faces[1:]

                    self.dot_boundaries = map(lambda dd: face_to_dot_boundary(self.face, dd), dot_descriptors)

                    self.process_count += 1
                else:
                    # If no faces were detected, try again on next pass.
                    self.process_count = -1

            if self.process_count > 0 or self.face:
                dot_info_list = map(lambda db: image_to_dot_info(self.frame, db, self.config['dot_threshold']),
                               self.dot_boundaries)

                valid_di = filter(lambda di: validate_dot_boundary(di, self.config['camera_dimensions']), dot_info_list)

                if len(valid_di) == 0:
                    self.process_count = -1
                else:

                    if len(valid_di) != len(dot_descriptors):
                        # Some points are not being tracked, Try to reaquire soon.
                        iterations_until_retry = 10

                        if self.process_count + iterations_until_retry < self.process_max_iterations:
                            self.process_count = self.process_max_iterations - iterations_until_retry

                self.all_dot_coords = filter(lambda c: c is not None, map(lambda di: di['coords'], valid_di))

                if len(self.all_dot_coords) > 0:
                    x = np.mean(map(lambda (x,y,z): x, self.all_dot_coords))
                    y = np.mean(map(lambda (x,y,z): y, self.all_dot_coords))
                    z = np.mean(map(lambda (x,y,z): z, self.all_dot_coords))

                    self.coords = (x, y, z)

                    self.dot_boundaries = map(lambda di: expand_rectangle_from_center(rectangle_from_dot_info(di), 3),
                                          valid_di)
                else:
                    self.coords = None
                    self.process_count = -1

            else:
                # No dots detected. Search for face on next pass.
                self.process_count = -1

        if self.process_count > self.process_max_iterations:
            self.process_count = 0
        else:
            self.process_count += 1

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