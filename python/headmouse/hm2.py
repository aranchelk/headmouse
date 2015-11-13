#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import gui_menu
from multiprocessing import Process, Pipe
import util
import conf
import filters

current_config = conf.render()
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


if __name__ == '__main__':
    # Set up filters
    xy_delta_gen = filters.relative_movement()

    # GUI process setup
    # Todo: give variables more descriptive names.
    parent_conn, child_conn = Pipe()
    gui_child_process = Process(target=gui_menu.initialize, args=(child_conn,))
    gui_child_process.start()

    # Application restart involves multiple processes and can be triggered from multiple places.
    def restart():
        gui_child_process.terminate()
        python = sys.executable
        os.execl(python, python, * sys.argv)

    fps = util.simple_fps()
    freq = 60.0
    send_fps = util.Every_n(freq, lambda: parent_conn.send(str( float("{0:.2f}".format(fps.next() * freq)))))
    fps.next()

    conf_from_gui = parent_conn.recv()['config']
    current_config.update_all(conf_from_gui)

    # Todo: Need a fire all callbacks method on observable dict
    current_config.register_callback('output', lambda k, v: set_output_driver(v))
    set_output_driver(current_config['output'])

    current_config.register_callback('algorithm', lambda k, v: set_vision_driver(v))
    set_vision_driver(current_config['algorithm'])

    current_config.register_callback('camera', lambda k, v: set_camera_driver(v))
    set_camera_driver(current_config['camera'])

    current_config.register_callback('smoothing', lambda k, v: set_smoother(v))
    set_smoother(current_config['smoothing'])

    # Todo: Don't reinitialize camera for algorithm change
    while not (needs_shutdown or needs_restart):
        with camera_driver.Camera(current_config) as cam:
            with vision_driver.Vision(cam, current_config) as viz:
                display_frame = util.Every_n(4, viz.display_image)

                # Todo: when conf run all registered_callbacks method is in place, run it here.
                needs_reinitialization = False

                while not (needs_reinitialization or needs_shutdown or needs_restart):
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
                                    needs_restart = True
                                else:
                                    print("Unhandled control message", control_message)
                                    pass
                        else:
                            if not gui_child_process.is_alive():
                                sys.exit("GUI component has terminated.")

                        # Frame processing
                        viz.get_image()
                        coords = viz.process()

                        if None not in coords:
                            coords = filters.mirror(coords)
                            abs_pos_x, abs_pos_y, abs_pos_z = coords
                            xy = xy_delta_gen.send((abs_pos_x, abs_pos_y))

                            if not filters.detect_outliers(xy, current_config['max_input_distance']):
                                xy = smoother.send(xy)
                                xy = filters.accelerate(xy, current_config)

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