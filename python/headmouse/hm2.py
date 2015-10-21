#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import gui_menu
from multiprocessing import Process, Pipe
import util
import conf
from vision.naive_dots import Vision
from cameras import v4l2_loopback_camera as camera

current_config = conf.render()

# Todo:
# Need a dymanic module importer function
# Need a dict of pointers to the dynamically imported functions
# To this add lambdas to output, camera, and algorithm to dynamically load the modules
# Add "Save and restart" button to GUI
# Move algorithms to subdir


def f(conn):
    gui_menu.initialize(conn)


if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()

    def restart():
        p.terminate()
        python = sys.executable
        os.execl(python, python, * sys.argv)

    fps = util.simple_fps()
    freq = 60.0
    send_fps = util.Every_n(freq, lambda: parent_conn.send(str( float("{0:.2f}".format(fps.next() * freq)))))
    fps.next()

    conf_from_gui = parent_conn.recv()['config']
    current_config.update_all(conf_from_gui)

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
                                restart()
                            else:
                                #print(control_message)
                                pass
                    else:
                        if not p.is_alive():
                            sys.exit("GUI component has terminated.")

                    viz.get_image()
                    viz.process()

                    display_frame.next()
                    send_fps.next()


                except KeyboardInterrupt:
                    p.terminate()
                    sys.exit()