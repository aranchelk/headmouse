#!/usr/bin/env python

from __future__ import print_function
import sys
import gui_menu
from multiprocessing import Process, Pipe
import util
from naive_dots_vision import Vision
from cameras import v4l2_loopback_camera as camera


def f(conn):
    gui_menu.initialize(conn)


if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()

    fps = util.simple_fps()
    f = 180.0
    print_fps = util.Every_n(f, lambda: print("fps: " + str( fps.next() * f)))

    # camera_config = {
    #     'device_id':2,
    #     'width':640,
    #     'height':480,
    #     'format_':1,
    #     'display':True,
    #     'gray_scale':False
    # }

    camera_config = parent_conn.recv()

    with Vision(camera.Camera(camera_config), camera_config) as cam:
        display_frame = util.Every_n(3, cam.display_image)

        while True:
            try:
                if parent_conn.poll(.001):
                    camera_config.update(parent_conn.recv())
                else:
                    if not p.is_alive():
                        sys.exit("GUI component has terminated.")

                cam.get_image()
                cam.process()

                display_frame.next()
                print_fps.next()


            except KeyboardInterrupt:
                p.terminate()
                #p.join()
                sys.exit()



