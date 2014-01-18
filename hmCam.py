#!/usr/bin/env python
#coding=utf8
'''
Headmouse OpenCV wrapper module.

TODO: move face/eye/dot tracking into *functions*, not generators, and have a generic 
      state-tracking/"chase-cam" generator which utilizes the various tracking strategy
      functions.
'''

import cv2

#Todo: Separate camera setup for algorithm setup.

EYE_CASCADE_FILE = 'casacades/haarcascade_eye.xml'
EYE_CASCADE_FILE = 'cascades/frontalEyes35x16.xml'
EYE_CASCADE_FILE = 'casacades/oneEye.xml'
EYE_CASCADE_FILE = 'casacades/reye.xml'
EYE_CASCADE_FILE = 'cascades/haarcascade_lefteye_2splits.xml'

FACE_CASCADE_FILE = 'cascades/haarcascade_frontalface_default.xml'

cap = None
displayWindow = False
THRESHOLD = 230
X_MAX, Y_MAX = 320, 240
setup = {'width': X_MAX, 'height': Y_MAX, 'fps':30, 'format':0}

def dumbAverage(numList):
    return (max(numList) + min(numList))/2

def bind(cameraId):
    #Sets up camera
    global cap, tracker
    cap = cv2.VideoCapture(cameraId)
    cap.set(3, setup['width'])
    cap.set(4, setup['height'])
    cap.set(5, setup['fps'])
    cap.set(8, setup['format'])

    tracker = eye_tracker()

def popAndAnalyze():
    return next(tracker)

def cleanup():
    cap.release()
    cv2.destroyAllWindows()

def camera_frames():
    while True:
        return_code, image = cap.read()
        yield image

def face_tracker(face_cascade_file=FACE_CASCADE_FILE):
    face_cascade = cv2.CascadeClassifier(face_cascade_file)
    for frame in camera_frames():
        raise NotImplemented()

def eye_tracker(eye_cascade_file=EYE_CASCADE_FILE):
    eye_cascade = cv2.CascadeClassifier(eye_cascade_file)
    for frame in camera_frames():
        x, y = None, None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)[Y_MAX / 4. : 3 * Y_MAX / 4., X_MAX / 4. : 3 * X_MAX / 4.]

        faces, eyes, objects = None, None, None

        #faces = face_cascade.detectMultiScale(gray)
        objects = eye_cascade.detectMultiScale(gray)
        #objects = face_cascade.detectMultiScale(gray)

    #    objects = []
    #    for (x,y,w,h) in faces:
    #        roi_gray = gray[y:y+h, x:x+w]
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
        if displayWindow is True:
            display(faces=faces, objects=objects, coords=(x,y), img=gray)

        yield x, y

def dot_tracker():
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
            if displayWindow is True:
                display(kp=kp, coords=(x,y), img=gray)

            yield x, y

def display(faces=None, objects=None, kp=None, coords=(None, None), img=None):
    x, y = coords
    if img is not None:
        if faces:
            for xt, yt, w, h in faces:
                cv2.circle(img, (int(xt + w / 2.), int(yt + h / 2.)), int((w + h) / 2.), (0,0,255))
        for xt, yt, w, h in objects:
            cv2.circle(img, (int(xt + w / 2.), int(yt + h / 2.)), int((w + h) / 2.), (0,255,0))
        if kp:
            img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)
        if x is not None and y is not None:
            cv2.circle(img, (int(x), int(y)) , 5, (255,0,0))
        cv2.imshow('frame', img)

