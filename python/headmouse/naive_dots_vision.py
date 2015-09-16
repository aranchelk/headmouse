#!/usr/bin/env python

from __future__ import print_function
import cv2
import util


def midrange(numList):
    return (max(numList) + min(numList))/2


class DotPoints:
    # Given a list of keypoints returned by opencv feature detect algo, present usable data
    def cursor_position(self):
        if len(self.kp) > 0:
            if self.x_range > 100:
                r = int((1 / self.x_range**2) * 650000)
            else:
                r = 10
            return midrange(self.x_list), midrange(self.y_list), r
        else:
            return 0, 0, self.distance

    def set_block_area(self, percent_x, percent_y, offset_x, offset_y):
        if self.kp is not None:
            self.block_area = [( ( min(self.x_list), min(self.y_list) ) , ( max(self.x_list), max(self.y_list) ) )]

    def __init__(self, kp):
        self.kp = kp

        self.x_list = []
        self.y_list = []

        self.block_area = None
        self.distance = 10.0

        if len(kp) > 0:
            for k in kp:
                self.x_list.append(k.pt[0])
                self.y_list.append(k.pt[1])

                self.x_range = max(self.x_list) - min(self.x_list)





def display(faces=None, objects=None, kp=None, coords=(None, None), boxes=None, img=None):
    if coords:
        x, y, distance = coords
    if img is not None:
        if boxes is not None:
            for (x0,y0), (x1, y1) in boxes:
                cv2.rectangle(img, (int(x0),int(y0)), (int(x1),int(y1)), (0, 0, 255))
        if faces:
            for xt, yt, w, h in faces:
                cv2.rectangle(img, (xt, yt), (xt + h, yt + h), (0, 255, 0))
        if objects is not None:
            for xt, yt, w, h in objects:
                cv2.rectangle(img, (xt, yt), (xt + h, yt + h), (0, 255, 0))
        if kp:
            img = cv2.drawKeypoints(img,kp,color=(0,255,0), flags=0)
        if x is not None and y is not None:
            cv2.circle(img, (int(x), int(y)), int(40/distance), (255, 255, 255), 3)

    cv2.imshow('frame', cv2.flip(img, flipCode=1))


class Vision:
    def __init__(self, camera, config):
        self.config = config
        self.camera = camera
        self.frame = None
        self.x = None
        self.y = None
        self.z = None

    def __enter__(self):
        self.camera.__enter__()
        return self

    def __exit__(self, *args):
        self.camera.__exit__(*args)

    def get_image(self):
        self.frame = self.camera.get_image()
        return self.frame

    def display_image(self):
        #cv2.imshow('frame', cv2.flip(self.frame,flipCode=1))
        display(img=self.frame, kp=self.kp, coords=(self.x, self.y, self.z))
        pass

    def process(self):
        if self.frame is not None:
            # TODO: real distance, or measured fixed distance value
            detector = cv2.ORB()

            x, y = None, None
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            #print(self.config['dot_threshold'])
            ret, thresh3 = cv2.threshold(gray,self.config['dot_threshold'],255,cv2.THRESH_BINARY)

            self.kp = detector.detect(thresh3)
            dp = DotPoints(self.kp)

            self.x, self.y, self.z = dp.cursor_position()

            return self.x, self.y, self.z


if __name__ == "__main__":
    from cameras import v4l2_loopback_camera as camera

    f = 180.0

    fps = util.simple_fps()
    print_fps = util.Every_n(f, lambda: print("fps: " + str( fps.next() * f)))

    camera_config = {
        'device_id':2,
        'width':640,
        'height':480,
        'format_':1,
        'display':True,
        'gray_scale':False
    }

    try:
        with Vision(camera.Camera(camera_config), camera_config) as cam:
            display_frame = util.Every_n(3, cam.display_image)

            while True:
                cam.get_image()
                cam.process()

                display_frame.next()
                print_fps.next()


    except KeyboardInterrupt:
        print("Program exiting.")