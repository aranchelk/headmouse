#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import threading
import time

import util
import conf
import filters

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


def watch_config():
    # Todo: remove global declaration, since dicts are mutable, should work.
    global config
    while not needs_shutdown:
        time.sleep(1)
        config.update_all(conf.render())


t = threading.Thread(target=watch_config)
t.start()


if __name__ == '__main__':
    # Set up filters
    xy_delta_gen = filters.relative_movement()

    # Application restart involves multiple processes and can be triggered from multiple places.
    def restart():
        #p.terminate()
        python = sys.executable
        os.execl(python, python, * sys.argv)

    fps = util.simple_fps()
    freq = 60.0
    send_fps = util.Every_n(freq, lambda: print(str( float("{0:.2f}".format(fps.next() * freq)))))
    fps.next()

    # Todo: Need a fire all callbacks method on observable dict
    config.register_callback('output', lambda k, v: set_output_driver(v))
    set_output_driver(config['output'])

    config.register_callback('algorithm', lambda k, v: set_vision_driver(v))
    set_vision_driver(config['algorithm'])

    config.register_callback('camera', lambda k, v: set_camera_driver(v))
    set_camera_driver(config['camera'])

    config.register_callback('smoothing', lambda k, v: set_smoother(v))
    set_smoother(config['smoothing'])

    # Todo: Don't reinitialize camera for algorithm change
    while not (needs_shutdown or needs_restart):
        with camera_driver.Camera(config) as cam:
            with vision_driver.Vision(cam, config) as viz:
                display_frame = util.Every_n(3, viz.display_image)

                needs_reinitialization = False

                while not (needs_reinitialization or needs_shutdown or needs_restart):
                    try:
                        # Frame processing
                        viz.get_image()
                        coords = viz.process()

                        # if coords is None or None in coords:
                        #     continue
                        #
                        # coords = filters.mirror(coords)
                        # abs_pos_x, abs_pos_y, abs_pos_z = coords
                        #
                        # xy = xy_delta_gen.send((abs_pos_x, abs_pos_y))
                        #
                        # # Todo: add outliers here.
                        #
                        # xy = smoother.send(xy)
                        # xy = filters.accelerate(xy, current_config)
                        #
                        #
                        # output_driver.send_xy(xy)
                        #
                        # display_frame.next()
                        # send_fps.next()

                        if coords is not None and None not in coords:
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

    needs_shutdown = True
    sys.exit()

