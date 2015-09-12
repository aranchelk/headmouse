#!/usr/bin/env python

# This module only handles camera setup and exports for visual analysis

import cv2
import cv2.cv as cv
import uuid
import time

# from: http://stackoverflow.com/questions/7322939/how-to-count-cameras-in-opencv-2-3
def count_cameras():
    # Not sure how to implement this
    pass


def simple_fps(calc_interval):
    last_time = float(time.time())
    fps = None
    frames = 0

    while True:
        yield fps
        frames += 1
        current_time = float(time.time())
        interval = current_time - last_time

        if (interval > calc_interval):

            #calculate fps
            fps = frames / interval

            #reset start values
            last_time = current_time
            frames = 0

        else:
            fps = None


fps = simple_fps(1)



class Camera(object):
    # Recommended camera
    # http://www.elpcctv.com/wide-angle-full-hd-usb-camera-module-1080p-usb20-ov2710-color-sensor-mjpeg-with-21mm-lens-p-204.html
    # 320X240  QVGA  MJPEG @120fps/  352X288 CIF  MJPEG @120fps
    # 640X480  VGA  MJPEG@120fps/   800X600 SVGA  MJPEG@60fps
    # 1024X768  XGA  MJPEG@30fps/  1280X720  HD   MJPEG@60fps
    # 1280X1024  SXGA MJPEG@30fps/  1920X1080 FHD  MJPEG@30fps

    def __init__(self, **kwargs):
        self.window_id = str(uuid.uuid4())
        print '__init__()'

        #cap = cv2.VideoCapture(kwargs['device_id'])
        cap = cv2.VideoCapture(0)

        # cap.set(3, kwargs['width'])
        # cap.set(4, kwargs['height'])
        # cap.set(cv2.cv.CV_CAP_PROP_FPS, 30.0)

        #cap.set(8, kwargs['format_'])
        #cap.set(cv2.cv.CV_CAP_PROP_FOURCC ,cv2.cv.CV_FOURCC('M', 'J', 'P', 'G'))
        #cap.set(cv2.cv.CV_CAP_PROP_FOURCC ,cv2.cv.CV_FOURCC('M', 'P', 'E', 'G'))
        #cap.set(5, 60)
        time.sleep(2)

        cap.set(3, 640)
        cap.set(4, 480)
        cap.set(5, 30)
        cap.set(8, 0)

        time.sleep(2)

        self.cap = cap

    def __enter__(self):
        print '__enter__()'
        return self

    def show_window(self):
        ret, frame = cam.cap.read()
        cv2.imshow(self.window_id, frame)

    def get_image(self):
        return_code, image = self.cap.read()
        self.show_window()
        #print self.cap.get(cv2.cv.CV_CAP_PROP_FPS)
        #return image

    def __exit__(self, exc_type, exc_val, exc_tb):
        print 'Bye.'
        self.cap.release()
        cv2.destroyWindow(self.window_id)



if __name__ == "__main__":
    camera_config = {
        'device_id':1,
        'width':320,
        'height':200,
        'fps':60,
        'format_':1
    }


    with Camera(**camera_config) as cam:
        #print dir(cam)
        #ret, frame = cam.cap.read()
        #cv2.imshow('frame', frame)

        cam.show_window()

        try:
            while True:
                cam.get_image()
                cam.show_window()

                fps_stat = fps.next()
                if fps_stat is not None:
                    print fps_stat

        except KeyboardInterrupt:
          # do nothing here
          pass


