#!/usr/bin/env python

# Intended to be run with v4l2 loopback camera

# Todos:
# * unhardcode everything

import cv2
import time
import uuid
# Todo: frame id should come from uuid
import os
import subprocess
import shlex # Todo: replace shlexes with cam_util.run()
import cam_util
import sys


class Camera():
    def __init__(self, current_config):
        # Todo: Add a function to decide whether or not image is displayed
        # Todo: if gray_scale is true, setup loopback camera ffmpeg stream in black and white
        #print('from camera')

        self.conf = current_config
        loopback_path = self.setup_loopback_camera()

        self.set_gain(current_config['camera_gain'])
        self.set_brightness(current_config['camera_brightness'])

        try:
            self.conf.register_callback('camera_gain', lambda k, v: self.set_gain(v))
            self.conf.register_callback('camera_brightness', lambda k, v: self.set_brightness(v))
        except AttributeError:
            print 'Running in static config mode, values won\'t update.'

        #print("loopback ocv:", cam_util.path_to_ocv_id(loopback_path))
        self.window_id = 'frame'
        self.cap = cv2.VideoCapture(cam_util.path_to_ocv_id(loopback_path))

        self.gray_scale = self.conf['gray_scale'] if 'gray_scale' in self.conf else True
        self.frame = None


    def setup_loopback_camera(self):
        # Check to see if a loopback camera already exists: # v4l2-ctl --list-devices (parse result
        _, cam_types = zip(*cam_util.get_devices())

        if 'loopback' in cam_types:
                loopback = [x for x,y in cam_util.list_linux_devices() if y == 'loopback'][0]

                time.sleep(2)
                conflicting_process, _ = cam_util.run("lsof | grep %s | grep -v %s | grep ffmpeg | head -n 1 | awk '{print $2'}" % (loopback, os.getpid()))

                if conflicting_process:
                    cam_util.run("kill -9 %s" % conflicting_process)
                    # Todo: implement syncrhonous kill method.
                    time.sleep(3)

        else:
            cam_util.run('sudo modprobe v4l2loopback')

        #print("Initialize loopback module")


        loopback_path = [x for x,y in cam_util.list_linux_devices() if y == 'loopback'][0]

        #print(loopback_path)

        loopback_data = {
            'dimensions': "%dx%d" % self.conf['camera_dimensions'],
            'source_cam': cam_util.ocv_id_to_path(self.conf['camera_device_id']),
            'loopback': loopback_path
        }

        ffmpeg_cmd = "ffmpeg -f video4linux2 -input_format mjpeg -s %(dimensions)s -i %(source_cam)s -vcodec rawvideo -pix_fmt gray -threads 0 -f v4l2 %(loopback)s" % loopback_data
        #print ffmpeg_cmd

        self.stream_transcoder_process = subprocess.Popen(shlex.split(ffmpeg_cmd), stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT) # something long running

        time.sleep(2)
        return loopback_path

    def teardown_loopback_camera(self):
        print("Killing ffmpeg process...")
        self.stream_transcoder_process.terminate()
        subprocess.call(shlex.split("sudo modprobe -r v4l2loopback"))
        #time.sleep(2)
        print("Done trying to kill process.")

    def reset_loopback_camera(self):
        self.teardown_loopback_camera()
        self.setup_loopback_camera()

    def __enter__(self):
        #print '__enter__()'
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print 'Camera cleaning up...'
        self.cap.release()
        cv2.destroyWindow(self.window_id)
        time.sleep(2)
        self.teardown_loopback_camera()

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

    def process(self):
        # Not implemented
        pass

    def set_gain(self, gain):
        cam_util.run("v4l2-ctl -d %s --set-ctrl gain=%s" % (self.conf['camera_device_id'], str(gain)))


    def set_brightness(self, gain):
        cam_util.run("v4l2-ctl -d %s --set-ctrl brightness=%s" % (self.conf['camera_device_id'], str(gain)))


if __name__ == "__main__":
    conf = {
        'camera_device_id':1,
        'width':640,
        'height':480,
        'format_':1,
        'gray_scale':False,
        'camera_gain':0,
        'camera_brightness':0,
        'camera_dimensions': (640, 480)
    }

    c = Camera(conf)

    try:
        with Camera(conf) as cam:
            while True:
                cam.get_image()
                cam.display_image()
                pass
    #
    #         while True:
    #             frame =
    #             display_frame.next()
    except KeyboardInterrupt:
        print "bye"
