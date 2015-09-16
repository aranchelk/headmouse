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
    def __init__(self, passed_config):
        # Todo: Add a function to decide whether or not image is displayed
        # Todo: if gray_scale is true, setup loopback camera ffmpeg stream in black and white
        self.conf = passed_config
        self.setup_loopback_camera(self.conf['width'], self.conf['height'], self.conf['gray_scale'])

        self.window_id = str('frame')
        print '__init__()'
        self.cap = cv2.VideoCapture(self.conf['device_id'])
        self.gray_scale = self.conf['gray_scale'] if 'gray_scale' in self.conf else True
        self.frame = None

    def setup_loopback_camera(self, width, height, is_gray_scale):
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
        'device_id':2,
        'width':640,
        'height':480,
        'format_':1,
        'gray_scale':False
    }

    try:
        with Camera(**camera_config) as cam:
            display_frame = every_n(4, cam.display_image)

            while True:
                frame = cam.get_image()
                display_frame.next()
    except KeyboardInterrupt:
        print "bye"