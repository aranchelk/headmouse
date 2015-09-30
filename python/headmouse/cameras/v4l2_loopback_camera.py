#!/usr/bin/env python

# Intended to be run with v4l2 loopback camera

import cv2
import time
import uuid
# Todo: frame id should come from uuid
import os
import subprocess
import shlex


class Camera():
    def __init__(self, current_config):
        # Todo: Add a function to decide whether or not image is displayed
        # Todo: if gray_scale is true, setup loopback camera ffmpeg stream in black and white
        print('from camera')

        self.conf = current_config

        self.set_gain(current_config['camera_gain'])
        self.set_brightness(current_config['camera_brightness'])

        self.conf.register_callback('camera_gain', lambda k, v: self.set_gain(v))
        self.conf.register_callback('camera_brightness', lambda k, v: self.set_brightness(v))

        self.setup_loopback_camera()
        self.window_id = str('frame')
        self.cap = cv2.VideoCapture(2)
        self.gray_scale = self.conf['gray_scale'] if 'gray_scale' in self.conf else True
        self.frame = None


    def setup_loopback_camera(self):
        # Check to see if a loopback camera already exists: # v4l2-ctl --list-devices (parse result
        subprocess.call(shlex.split("sudo modprobe v4l2loopback"))
        ffmpeg_cmd = "ffmpeg -f video4linux2 -input_format mjpeg -s %dx%d -i /dev/video1 -vcodec rawvideo -pix_fmt gray -threads 0 -f v4l2 /dev/video2" % (self.conf['width'], self.conf['height'])
        print ffmpeg_cmd

        self.stream_transcoder_process = subprocess.Popen(shlex.split(ffmpeg_cmd), stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT) # something long running
        time.sleep(1)
        pass

    def teardown_loopback_camera(self):
        subprocess.call(shlex.split("sudo modprobe -r v4l2loopback"))
        self.stream_transcoder_process.kill()

    def reset_loopback_camera(self):
        self.teardown_loopback_camera()
        self.setup_loopback_camera()

    def __enter__(self):
        print '__enter__()'
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print 'Camera cleaning up...'
        self.cap.release()
        cv2.destroyWindow(self.window_id)
        # Todo: add a function to destroy loopback camera

    def get_image(self):
        ret, frame = self.cap.read()
        self.frame = frame

        if cv2.waitKey(1) & 0xFF == ord('q'):
            raise Exception('Quit issued from cv2 process')

        return frame

    def display_image(self):
        if self.frame is not None:
            # More intuitive for user to see a mirror image.
            cv2.imshow('frame', cv2.flip(self.frame,flipCode=1))

    def get_camera_id(self):
        return 2

    def process(self):
        # Not implemented
        pass

    def set_gain(self, gain):
        subprocess.call(shlex.split("v4l2-ctl -d 1 --set-ctrl gain=" + str(gain)))

    def set_brightness(self, gain):
        subprocess.call(shlex.split("v4l2-ctl -d 1 --set-ctrl brightness=" + str(gain)))

if __name__ == "__main__":
    def every_n(freq, func):
        counter = 0

        while True:
            if counter >= freq:
                yield func()
                counter = 0
            else:
                yield None

            counter += 1


    camera_config = {
        'device_id':1,
        'width':640,
        'height':480,
        'format_':1,
        'gray_scale':False
    }

    try:
        with Camera(camera_config) as cam:
            display_frame = every_n(4, cam.display_image)

            while True:
                frame = cam.get_image()
                display_frame.next()
    except KeyboardInterrupt:
        print "bye"