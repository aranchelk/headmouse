#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import gui_menu
from multiprocessing import Process, Pipe
import util
import conf
import filters
import threading
import time

config = conf.render()
output_driver = None
vision_driver = None
camera_driver = None
smoother = None
needs_reinitialization = False
needs_shutdown = False
needs_restart = False

# Todo: replace this with a generic method for all drivers
# Todo: consider renaming vision and camera dirs with _drivers
def set_output_driver(driver_name):
    global output_driver
    output_driver = __import__('output_drivers.' + driver_name).__dict__[driver_name]


def set_vision_driver(driver_name):
    global vision_driver, needs_reinitialization
    vision_driver = __import__('vision.' + driver_name).__dict__[driver_name]
    needs_reinitialization=True


def set_camera_driver(driver_name):
    global camera_driver, needs_reinitialization
    camera_driver = __import__('cameras.' + driver_name).__dict__[driver_name]
    needs_reinitialization=True


def set_smoother(smoothing_amount):
    global smoother
    smoothing_amount = 1 - smoothing_amount
    smoother = filters.ema_smoother(smoothing_amount)


def handle_gui_process_messages(parent_conn, gui_child_process):
    global needs_restart, needs_shutdown

    if parent_conn.poll(.001):
        pipe_data = parent_conn.recv()

        if 'config' in pipe_data:
            config.update_all(pipe_data['config'])
        elif 'control' in pipe_data:
            control_message = pipe_data['control']
            if control_message == 'restart':
                needs_restart = True
            else:
                print("Unhandled control message", control_message)
    else:
        if not gui_child_process.is_alive():
            print("GUI component has terminated.")
            needs_shutdown = True


def watch_gui_process(parent_conn, gui_child_process):
    while not needs_shutdown:
        time.sleep(.03)
        handle_gui_process_messages(parent_conn, gui_child_process)


if __name__ == '__main__':
    # GUI process setup
    parent_conn, child_conn = Pipe()
    gui_child_process = Process(target=gui_menu.initialize, args=(child_conn,))
    gui_child_process.start()

    t = threading.Thread(target=watch_gui_process, args=(parent_conn, gui_child_process))
    t.start()

    # Application restart involves multiple processes and can be triggered from multiple places.
    def restart():
        gui_child_process.terminate()
        python = sys.executable
        os.execl(python, python, * sys.argv)


    xy_delta_gen = filters.relative_movement()

    fps = util.simple_fps()
    send_fps = util.Every_n(60, lambda: parent_conn.send(str( float("{0:.2f}".format(fps.next() * 60)))))

    handle_gui_process_messages(parent_conn, gui_child_process)

    config.register_callback('output', lambda k, v: set_output_driver(v))
    config.register_callback('algorithm', lambda k, v: set_vision_driver(v))
    config.register_callback('camera', lambda k, v: set_camera_driver(v))
    config.register_callback('smoothing', lambda k, v: set_smoother(v))

    config.execute_all_callbacks()

    # Todo: Don't reinitialize camera for algorithm change
    while not (needs_shutdown or needs_restart):
        with camera_driver.Camera(config) as cam:
            with vision_driver.Vision(cam, config) as viz:
                display_frame = util.Every_n(4, viz.display_image)

                needs_reinitialization = False

                while not (needs_reinitialization or needs_shutdown or needs_restart):
                    try:
                        # Frame processing
                        viz.get_image()
                        coords = viz.process()

                        if None not in coords:
                            coords = filters.mirror(coords)
                            abs_pos_x, abs_pos_y, abs_pos_z = coords
                            xy = xy_delta_gen.send((abs_pos_x, abs_pos_y))

                            if not filters.detect_outliers(xy, config['max_input_distance']):
                                xy = smoother.send(xy)
                                xy = filters.accelerate(xy, config)

                                output_driver.send_xy(xy)

                        display_frame.next()
                        send_fps.next()

                    except KeyboardInterrupt:
                        needs_restart = False
                        needs_shutdown = True

    if needs_restart:
        restart()

    gui_child_process.terminate()
    sys.exit()