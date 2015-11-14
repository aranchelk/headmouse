#!/usr/bin/env python

from __future__ import print_function
import sys
import os
import threading
import time

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


def watch_config():
    # Todo: remove global declaration, since dicts are mutable, should work.
    global current_config
    while not needs_shutdown:
        time.sleep(1)
        current_config.update_all(conf.render())


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
                display_frame = util.Every_n(3, viz.display_image)
                #config_reloader = util.Every_n(60, reload_config)

                # Todo: when conf run all registered_callbacks method is in place, run it here.
                needs_reinitialization = False

                while not (needs_reinitialization or needs_shutdown or needs_restart):
                    try:

                        # Frame processing
                        viz.get_image()
                        coords = viz.process()

                        if None in coords:
                            continue

                        coords = filters.mirror(coords)
                        abs_pos_x, abs_pos_y, abs_pos_z = coords

                        xy = xy_delta_gen.send((abs_pos_x, abs_pos_y))

                        # Todo: add outliers here.

                        xy = smoother.send(xy)
                        xy = filters.accelerate(xy, current_config)


                        output_driver.send_xy(xy)

                        display_frame.next()
                        #config_reloader.next()
                        send_fps.next()

                    except KeyboardInterrupt:
                        needs_restart = False
                        needs_shutdown = True

    if needs_restart:
        restart()

    needs_shutdown = True
    sys.exit()

