#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import gui_menu
from multiprocessing import Process, Pipe
import util
import conf
from naive_dots_vision import Vision
from cameras import v4l2_loopback_camera as camera

current_config = conf.render()


def f(conn):
    gui_menu.initialize(conn)


def restart():
    python = sys.executable
    os.execl(python, python, * sys.argv)


if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()

    def restart():
        p.terminate()
        python = sys.executable
        os.execl(python, python, * sys.argv)

    fps = util.simple_fps()
    f = 180.0
    print_fps = util.Every_n(f, lambda: print("fps: " + str( fps.next() * f)))

    conf_from_gui = parent_conn.recv()['config']
    print(conf_from_gui)
    current_config.update_all(conf_from_gui)
    current_config.register_callback('smoothing', lambda x, y: print("lambda print:", x, y))
    print(current_config.callbacks)

    with camera.Camera(current_config) as cam:
        with Vision(cam, current_config) as viz:
            display_frame = util.Every_n(3, viz.display_image)

            while True:
                try:
                    if parent_conn.poll(.001):
                        pipe_data = parent_conn.recv()

                        if 'config' in pipe_data:
                            current_config.update_all(pipe_data['config'])
                            # print(conf.current_config)
                        elif 'control' in pipe_data:
                            control_message = pipe_data['control']

                            if control_message == 'restart':
                                print('restart')
                                restart()
                            else:
                                print(control_message)
                    else:
                        if not p.is_alive():
                            sys.exit("GUI component has terminated.")

                    viz.get_image()
                    viz.process()

                    display_frame.next()
                    print_fps.next()


                except KeyboardInterrupt:
                    p.terminate()
                    #p.join()
                    sys.exit()



