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
import filters

current_config = conf.render()
output_driver = None

# Todo: replace this with a generic method for all drivers
# Todo: consider renaming vision and camera dirs with _drivers
def set_output_driver(driver_name):
    global output_driver
    output_driver = __import__('output_drivers.' + driver_name).__dict__[driver_name]
    #print(dir(output_driver))

# Todo:
# To this add lambdas to output, camera, and algorithm to dynamically load the modules
# Add "Save and restart" button to GUI
# Move algorithms to subdir


def f(conn):
    gui_menu.initialize(conn)


if __name__ == '__main__':
    # Set up filters
    xy_delta_gen = filters.relative_movement()

    # GUI process setup
    # Todo: give variables more descriptive names.
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()

    # Application restart involves multiple processes and can be triggered from multiple places.
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

    current_config.register_callback('output', lambda k, v: set_output_driver(v))
    set_output_driver(current_config['output'])

    with camera.Camera(current_config) as cam:
        with Vision(cam, current_config) as viz:
            display_frame = util.Every_n(3, viz.display_image)

            # Todo: when conf run all registered_callbacks method is in place, run it here.

            while True:
                try:
                    # Handle messages from GUI component
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

                    # Frame processing
                    viz.get_image()
                    coords = viz.process()

                    coords = filters.mirror(coords)
                    abs_pos_x, abs_pos_y, abs_pos_z = coords

                    xy = xy_delta_gen.send((abs_pos_x, abs_pos_y))

                    output_driver.send_xy(xy)

                    display_frame.next()
                    send_fps.next()


                except KeyboardInterrupt:
                    p.terminate()
                    sys.exit()