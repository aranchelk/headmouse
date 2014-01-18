#!/usr/bin/env python
#coding=utf8
'''
Headmouse OpenCV wrapper module.
'''

import cv2

#Todo: Separate camera setup for algorithm setup.

cap = None
orb = None
displayWindow = False
THRESHOLD = 230
setup = {'width':640, 'height':480, 'fps':30, 'format':0}

def dumbAverage(numList):
    return (max(numList) + min(numList))/2

def bind(cameraId):
    #Sets up camera
    global cap, orb
    cap = cv2.VideoCapture(cameraId)
    cap.set(3, setup['width'])
    cap.set(4, setup['height'])
    cap.set(5, setup['fps'])
    cap.set(8, setup['format'])
    orb = cv2.ORB()


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

def popAndAnalyze():
    x = None
    y = None
    ret, img = cap.read()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret,thresh3 = cv2.threshold(gray,THRESHOLD,255,cv2.THRESH_BINARY)
    kp = orb.detect(thresh3,None)

    if kp:
        x, y = kp_to_xy(kp)

    # Display the resulting frame
    if displayWindow is True:
        if x is not None and y is not None:
            cv2.circle(img, (int(x), int(y)) , 5, (255,0,0))
        img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)
        cv2.imshow('frame',img)

    return [x, y]

def cleanup():
    cap.release()
    cv2.destroyAllWindows()
