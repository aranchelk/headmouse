#!/usr/bin/env python
#coding=utf8
'''
Headmouse OpenCV wrapper module.

TODO: move face/eye/dot tracking into *functions*, not generators, and have a generic 
      state-tracking/"chase-cam" generator which utilizes the various tracking strategy
      functions.
'''

import logging
import sys
import contextlib
import itertools

import cv2

import util

#Todo: Separate camera setup for algorithm setup.

EYE_CASCADE_FILE = 'casacades/haarcascade_eye.xml'
EYE_CASCADE_FILE = 'cascades/frontalEyes35x16.xml'
EYE_CASCADE_FILE = 'casacades/oneEye.xml'
EYE_CASCADE_FILE = 'casacades/reye.xml'
EYE_CASCADE_FILE = 'cascades/haarcascade_lefteye_2splits.xml'

FACE_CASCADE_FILE = 'cascades/haarcascade_frontalface_default.xml'

visualize = False

THRESHOLD = 230
DEFAULT_RESOLUTION = (640, 480)
DEFAULT_FPS = 30
DEFAULT_CAMERA = 0
DEFAULT_FORMAT = 0
DEFAULT_TRACKER = None

def dumbAverage(numList):
    return (max(numList) + min(numList))/2

@contextlib.contextmanager
def camera(
        camera_id=DEFAULT_CAMERA,
        tracker_name=DEFAULT_TRACKER,
        resolution=DEFAULT_RESOLUTION,
        fps=DEFAULT_FPS,
        format_=DEFAULT_FORMAT
    ):
    # Sets up camera

    cap = cv2.VideoCapture(camera_id)
    width, height = resolution

    cap.set(3, width)
    cap.set(4, height)
    cap.set(5, fps)
    cap.set(8, format_)

    def camera_frames():
        while True:
            return_code, image = cap.read()
            yield image

    # TODO: restrict loadable generaton functions for security
    tracker = sys.modules[__name__].__dict__[tracker_name](camera_frames)

    yield tracker

    cap.release()
    cv2.destroyAllWindows()

def face_tracker(camera_frames, face_cascade_file=FACE_CASCADE_FILE):
    face_cascade = cv2.CascadeClassifier(face_cascade_file)
    for frame in camera_frames():
        raise NotImplemented()

def middle_quarter_crop(frame, objects=None):
    # static crop
    height, width = frame.shape
    (w_x0, w_y0), (w_x1, w_y1) = ((1./4) * width, (1./4) * height), ((3./4) * width, (3./4) * height)
    return ((w_x0, w_y0), (w_x1, w_y1)), frame[ w_y0:w_y1, w_x0:w_x1 ]
    
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
        logging.debug("Cropping to {}x{}, actual {}x{}, bounding box ({},{}), ({},{})".format(
            window_width, window_height,
            w_x1 - w_x0, w_y1 - w_y0,
            w_x0, w_y0, w_x1, w_y1
            ))
        '''

        # crop the frame to the "interesting + x%" window
        return ((w_x0, w_y0), (w_x1, w_y1)), frame[w_y0:w_y1, w_x0:w_x1]

def eye_tracker(camera_frames, eye_cascade_file=EYE_CASCADE_FILE):
    eye_cascade = cv2.CascadeClassifier(eye_cascade_file)
    objects = None
    
    #stats = util.Stats(Stats.average, "Average pixels processed: ~{} kpx")
    stats = util.Stats(Stats.quartiles, "Kilopixels processed: [{:.1f}, {:.1f}, {:.1f}, {:.1f}, {:.1f}]", interval = 30)
    for frame in camera_frames():
        x, y = None, None

        # most of the information is in value, so work with grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # TODO: if we lose the tracked object, zoom back out and try again
        # TODO: count the number of objects we want, try to limit tracking to only relevant objects
        # TODO: persist tracking info so we don't jump if we lose, e.g. one eye out of two (know which is left and right)
        # TODO: drop frames when we lose all tracking; maybe one per second after first one second of missing data?
        # TODO: pick a target area target kilopixel value and resize image patch to suit
        # TODO: classes for Box() and Window()
        # TODO: Track only one object per frame. This lowers search area pixel count for the next frame,
        #       encourages the seemingly more stable single eye tracking, and helps us eliminate crazy
        #       outlier objects (e.g. chins, second faces, etc.)
        # TODO: Favor eyes detected in approximately horizontal pairs. Prefer the most horizontal largest pair. 
        # TODO: Normalize search area size to about 10–15 kpx per single tracked eye (different if we found lots of objects)
        # get the image size, then crop to only the area we feel is relevant
        (upper_left, lower_right), cropped_gray = chase_crop(gray, objects)

        stats.push(cropped_gray.size / 1000.)

        faces, eyes, objects = None, None, None

        #faces = face_cascade.detectMultiScale(cropped_gray)
        objects_raw = eye_cascade.detectMultiScale(cropped_gray)
        #objects = face_cascade.detectMultiScale(cropped_gray)

        # normalize object coords to full frame
        objects = [ (x + upper_left[0], y + upper_left[1], w, h) for x, y, w, h in objects_raw ]

    #    objects = []
    #    for (x,y,w,h) in faces:
    #        roi_gray = cropped_gray[y:y+h, x:x+w]
    #        objects = [(ex + x, ey + y, ew, eh) for ex, ey, ew, eh in eye_cascade.detectMultiScale(roi_gray)]

        # todo: if >2 objects, eliminate all but the two to existing objects
        if len(objects) > 0:
            #x, y = [sum(l)/len(l) for l in zip(*[(x + w / 2.,y + h / 2.) for x,y,w,h in objects])]
            #print([(x + w/2., y+w/2.) for x, y, w, h in objects])
            #print(zip(*[(x + w/2., y + h/2.) for x, y, w, h in objects]))
            x, y = [(max(l) + min(l)) / 2. for l in zip(*[(x + w/2., y + h/2.) for x, y, w, h in objects])]
            #print((x, y))
        else:
            x, y = None, None

        # Display the resulting frame
        if visualize is True:
            display(faces=faces, 
                    objects=objects, 
                    coords=(x,y), 
                    boxes=[(upper_left, lower_right)],
                    img=frame)

        yield x, y

def dot_tracker(camera_frames):
    def kp_to_xy(kp):

        xList = []
        yList = []
        for k in kp:
            xList.append(k.pt[0])
            yList.append(k.pt[1])

        x = dumbAverage(xList)
        y = dumbAverage(yList)

        return x, y

    def kp_to_xy_new(kp):
        max_x = kp[0].pt[0]
        min_x = kp[0].pt[0]
        max_x_index = 0
        min_x_index = 0

        for i in range(len(kp)):
            if kp[i].pt[0] > max_x:
                max_x = kp[i].pt[0]
                max_x_index = i
            if kp[i].pt[0] < min_x:
                min_x = kp[i].pt[0]
                min_x_index = i

        x = (max_x + min_x) / 2

        x_thresh = .5
        y_list = []

        for k in kp:
            if max_x - k.pt[0] < x_thresh or k.pt[0] - min_x < x_thresh:
                y_list.append(k.pt[1])

        y = dumbAverage(y_list)

        return x, y

    orb = cv2.ORB()
    for frame in camera_frames():
        x, y = None, None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, thresh3 = cv2.threshold(gray,THRESHOLD,255,cv2.THRESH_BINARY)

        kp = orb.detect(thresh3,None)

        if kp:
            x, y = kp_to_xy(kp)

            # Display the resulting frame
            if visualize is True:
                display(kp=kp, coords=(x,y), img=gray)

            yield x, y

def display(faces=None, objects=None, kp=None, coords=(None, None), boxes=None, img=None):
    x, y = coords
    if img is not None:
        if boxes is not None:
            for (x0,y0), (x1, y1) in boxes:
                cv2.rectangle(img, (x0,y0), (x1,y1), (0, 0, 255))
        if faces:
            for xt, yt, w, h in faces:
                cv2.rectangle(img, (xt, yt), (xt + h, yt + h), (0, 255, 0))
        for xt, yt, w, h in objects:
            cv2.rectangle(img, (xt, yt), (xt + h, yt + h), (0, 255, 0))
        if kp:
            img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)
        if x is not None and y is not None:
            cv2.circle(img, (int(x), int(y)), 4, (255, 255, 255), 3)
        cv2.imshow('frame', cv2.flip(img, flipCode=1))

