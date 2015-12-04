#!/usr/bin/env python
#coding=utf8

import logging
logger = logging.getLogger(__name__)
import sys
import contextlib
import itertools
import time
import math
import pkg_resources
import tempfile

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")

import cv2
import psutil

import util
import _vision


cascade_file = tempfile.NamedTemporaryFile()
try:
    cascade_file.write(pkg_resources.resource_stream(
        __name__,
        '../data/cascades/haarcascade_lefteye_2splits.xml'
        #'data/cascades/Nariz.xml'
    ).read())
except:
    with open('haarcascade_lefteye_2splits.xml', 'rb') as f:
        cascade_file.write(f.read())
finally:
    cascade_file.flush()

EYE_CASCADE_FILE = cascade_file.name

visualize = False

THRESHOLD = 200
DEFAULT_RESOLUTION = (640, 480)
DEFAULT_FPS = 30
DEFAULT_CAMERA = 1
DEFAULT_FORMAT = 0
DEFAULT_TRACKER = None

# TODO: change slow search behavior to target FPS in various search modes
DEFAULT_REALTIME_SEARCH_TIMEOUT = 2.0
DEFAULT_SLOW_SEARCH_DELAY = 2.0

TARGET_SEARCH_KILOPIXELS = 10
MAX_SEARCH_KILOPIXELS = 100

    # tracker = sys.modules[__name__].__dict__[tracker_name](
    #         camera_frames,
    #         realtime_search_timeout=realtime_search_timeout,
    #         slow_search_delay=slow_search_delay
    #     )


# def middle_quarter_crop(frame, objects=None):
#     # static crop
#     height, width = frame.shape
#     (w_x0, w_y0), (w_x1, w_y1) = ((1./4) * width, (1./4) * height), ((3./4) * width, (3./4) * height)
#     return ((w_x0, w_y0), (w_x1, w_y1)), frame[ w_y0:w_y1, w_x0:w_x1 ]
#
#
# def unity_crop(frame, objects=None):
#     height, width = frame.shape
#     return ((0,0), (width, height)), frame


def chase_crop(frame, objects):
    '''
    "Chase camera" cropper

    Crop the image to be processed based upon previously detected objects. Since we're tracking facial
    movements in a video stream, we can presume that the new objects to be detected will be somewhat
    near any objects previously detects (i.e. there's a limit to how fast the user can move his head).

    We can reduce the image processing workload by searching only this nearby interesting area, defaulting
    back to searching the entire frame if the search object is lost.
    '''
    height, width = frame.shape

    if objects is None or len(objects) == 0:
        return ((0, 0), (0,0)), frame
    else:
        # determine bounding box around interesting points
        interesting_points = list(itertools.chain(*[[(x, y), (x + w, y + h)] for x, y, w, h in objects]))
        interesting_x, interesting_y = zip(*interesting_points)
        box = (min(interesting_x), min(interesting_y)), (max(interesting_x), max(interesting_y))
        (b_x0, b_y0), (b_x1, b_y1) = box
        box_width, box_height = (b_x1 - b_x0), (b_y1 - b_y0)
        center_x, center_y = ((b_x0 + b_x1) / 2.), ((b_y0 + b_y1) / 2.)

        # calculate a window some % larger than that bounding box
        window_width, window_height = (box_width * 2.0), (box_height * 2.0)
        window = (center_x - window_width / 2., center_y - window_height / 2.),\
                 (center_x + window_width / 2., center_y + window_height / 2.)

        # ensure the window fits in the frame
        window = (int(max(0,     window[0][0])), int(max(0,      window[0][1]))),\
                 (int(min(width, window[1][0])), int(min(height, window[1][1])))
        (w_x0, w_y0), (w_x1, w_y1) = window

        '''
        logger.debug("Cropping to {}x{}, actual {}x{}, bounding box ({},{}), ({},{})".format(
            window_width, window_height,
            w_x1 - w_x0, w_y1 - w_y0,
            w_x0, w_y0, w_x1, w_y1
            ))
        '''

        # crop the frame to the "interesting + x%" window
        return ((w_x0, w_y0), (w_x1, w_y1)), frame[w_y0:w_y1, w_x0:w_x1]


def slow_empty_search(realtime_search_timeout, slow_search_delay):
    # track how long it's been since we've found an object
    missing_since = None
    delay_until = None
    while True:
        object_count = yield delay_until is None or time.time() >= delay_until
        if object_count is not None:
            if object_count  > 0:
                # if we found objects, make sure the timeout counters are cleared
                missing_since = None
                delay_until = None
            else:
                logger.debug("No target objects found!")
                if missing_since is None:
                    # if no objects, found, ensure the missing_since timer is set
                    missing_since = time.time()
                else:
                    # if we haven't seen an object in a while, search less often
                    if time.time() - missing_since > realtime_search_timeout:
                        delay_until = time.time() + slow_search_delay
                        logger.info("Missed object for {} s, delaying until {} ({} s)".format(
                                realtime_search_timeout,
                                delay_until,
                                slow_search_delay
                            ))


class Vision(_vision.Vision):

    def __init__(self, *args, **kwargs):
        eye_cascade_file=EYE_CASCADE_FILE
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_file)

        super(Vision, self).__init__(*args, **kwargs)

    def display_image(self):
        #def display(faces=None, objects=None, kp=None, coords=(None, None), boxes=None, img=None):

        vd = self.visualization_data.copy()

        #print("vd", self.visualization_data.coords)

        if vd['coords'] is not None:
            x, y, distance = vd['coords']

        if vd['boxes'] is not None:
            for (x0,y0), (x1, y1) in vd['boxes']:
                cv2.rectangle(self.frame, (int(x0),int(y0)), (int(x1),int(y1)), (0, 0, 255))
        # if faces:
        #     for xt, yt, w, h in faces:
        #         cv2.rectangle(img, (xt, yt), (xt + h, yt + h), (0, 255, 0))
        if vd['objects'] is not None:
            for xt, yt, w, h in vd['objects']:
                cv2.rectangle(self.frame, (xt, yt), (xt + h, yt + h), (0, 255, 0))
        # if vd['kp']:
        #     img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)
        if x is not None and y is not None:
            cv2.circle(self.frame, (int(x), int(y)), int(40/distance), (255, 255, 255), 3)

        cv2.imshow('frame', cv2.flip(self.frame, flipCode=1))
        #cv2.imshow('frame', cv2.flip(self.frame,flipCode=1))
        #display(img=self.frame, kp=self.kp, coords=(self.x, self.y, self.z))
        pass

    def process(self):
        if self.frame is not None:

            #realtime_search_timeout=DEFAULT_REALTIME_SEARCH_TIMEOUT,
            #slow_search_delay=DEFAULT_SLOW_SEARCH_DELAY,

            objects = []
            distance = 1

            # precompute values used for search area scaling computations
            target_search_height = math.sqrt(TARGET_SEARCH_KILOPIXELS * 1000.0)
            max_search_pixels = MAX_SEARCH_KILOPIXELS * 1000.0

            # periodic stats reporting loggers
            kpx_stats = util.Stats(util.Stats.quartiles, "Kilopixels processed: [{:.1f}, {:.1f}, {:.1f}, {:.1f}, {:.1f}]", interval = 30)
            scale_stats = util.Stats(util.Stats.quartiles, "Scale factors: [{:.2f}, {:.2f}, {:.2f}, {:.2f}, {:.2f}]", interval = 30)
            cpu_stats = util.Stats(util.Stats.average, "Average CPU usage {}%", interval = 30)
            distance_stats = util.Stats(util.Stats.quartiles, "Computed distances: [{:.1f}, {:.1f}, {:.1f}, {:.1f}, {:.1f}]", interval = 60)

            # drop frames based on active vs. no objects found tracking mode
            #frame_rate_manager = slow_empty_search(realtime_search_timeout, slow_search_delay)
            #for frame in camera_frames():
                #x, y = None, None
                #cpu_stats.push(psutil.cpu_percent(interval=0))

            # if frame rate manager tells us to drop a frame, stop processing
            #if next(frame_rate_manager):
            # most of the information is in value, so work with grayscale
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # TODO: if we lose the tracked object, zoom back out and try again
            # TODO: persist tracking info so we don't jump if we lose, e.g. one eye out of two (know which is left and right)
            # TODO: classes for Box() and Window()
            # TODO: Favor eyes detected in approximately horizontal pairs. Prefer the most horizontal largest pair.
            (upper_left, lower_right), cropped_gray = chase_crop(gray, objects)

            scale_factor = 1
            if len(objects) == 1 or len(objects) == 2:
                # if the search area is huge, resize it to 100 px high
                ch, cw = cropped_gray.shape
                scale_factor = target_search_height / ch
                if scale_factor >= 0.75:
                    scale_factor = 1
            elif len(objects) == 0:
                # if we're doing a whole frame search, ensure we don't search more than about 100 kpx
                square_scale_factor = max_search_pixels / cropped_gray.size
                if square_scale_factor < 0.5625: # 0.75 ** 2
                    scale_factor = math.sqrt(square_scale_factor)
                else:
                    scale_factor = 1

            if scale_factor < 0.75:
                cropped_gray = cv2.resize(cropped_gray, (0,0), fx=scale_factor, fy=scale_factor)

            kpx_stats.push(cropped_gray.size / 1000.)
            scale_stats.push(scale_factor)

            objects_raw = self.eye_cascade.detectMultiScale(gray)

            # normalize object coords to full frame
            objects = [(
                    int(x / scale_factor) + upper_left[0],
                    int(y / scale_factor) + upper_left[1],
                    int(w / scale_factor),
                    int(h / scale_factor))\
                for x, y, w, h in objects_raw]

            # eliminate all but one found object; we don't really want to track multiple eyes at once
            objects = objects[:1]

            if len(objects) > 0:
                # take the middle point between the extreme x and y coords as the usable center point
                x, y = [(max(l) + min(l)) / 2. for l in zip(*[(x + w/2., y + h/2.) for x, y, w, h in objects])]
                distance = float(gray.shape[0]) / objects[0][3]
            else:
                x, y = None, None

            self.visualization_data = {
                'objects':objects,
                'coords':(x, y, distance),
                'boxes':[(upper_left, lower_right)]
            }


            #frame_rate_manager.send(len(objects))

            distance_stats.push(distance)

            # now, scale the output by the inverse of the distance to the user, so
            # moving in close to the camera gives finer, not coarser, control
            return x, y, distance