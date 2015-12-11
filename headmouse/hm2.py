#!/usr/bin/env python

# Todo: Record and print total stats at end of run, write out to file, maybe csv.
# Todo: Option to record video and xyz
# Todo: Turn display on and off.
# Todo: conf binary options
# Todo: conf write in number option
# Todo: Think of ways to make needs_ vars more elegant, maybe a service.
# Todo: consider renaming vision and camera dirs with _drivers
# Todo: resolution selection in GUI
# Todo: camera device selection in GUI
# Todo: callbacks on resolution and camera device selection to restart camera
# Todo: save profiles
# Todo: auto-config
# Todo: when on os-x attempt to open scratch file before main config file
# Todo: graceful handling of Arduino wait

# Todo: don't throw away good dots in hybrid mode if face-find fails

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

# OSX has an error when launching GUI subprocesses
# If use_config_gui is false, the program will just watch ~/.headmouse
use_config_gui = sys.platform != 'darwin'

config = conf.render()
output_driver = None
vision_driver = None
camera_driver = None
smoother = None
needs_camera_reinit = False
needs_vision_reinit = False
needs_shutdown = False
needs_restart = False


def update_component(c_name, c_value):
    global smoother, camera_driver, vision_driver, output_driver, needs_camera_reinit, needs_vision_reinit

    if c_name == 'camera':
        camera_driver = __import__('cameras.' + c_value).__dict__[c_value]
        needs_camera_reinit = True
    elif c_name == 'algorithm':
        vision_driver = __import__('vision.' + c_value).__dict__[c_value]
        needs_vision_reinit = True
    elif c_name == 'output':
        output_driver = __import__('output_drivers.' + c_value).__dict__[c_value]
    elif c_name == 'smoothing':
        smoother = filters.ema_smoother(c_value)
    elif c_name == 'camera_dimensions':
        needs_camera_reinit = True
    elif c_name == 'camera_device_id':
        needs_camera_reinit = True


def handle_gui_process_messages(parent_conn, gui_child_process, polling_wait=.001):
    global needs_restart, needs_shutdown

    if parent_conn.poll(polling_wait):
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


def watch_config():
    # Todo: remove global declaration, since dicts are mutable, should work.
    global config
    while not needs_shutdown:
        time.sleep(1)
        config.update_all(conf.render())


if __name__ == '__main__':
    if use_config_gui:
        # GUI process setup
        parent_conn, child_conn = Pipe()
        gui_child_process = Process(target=gui_menu.initialize, args=(child_conn,))
        gui_child_process.start()
        handle_gui_process_messages(parent_conn, gui_child_process, polling_wait=1)

        gui_watcher_thread = threading.Thread(target=watch_gui_process, args=(parent_conn, gui_child_process))
        gui_watcher_thread.start()
    else:
        print("Gui menu can't be launched directly on OS X, you can launch gui_menu.py in a separete process.")
        config_file_watcher = threading.Thread(target=watch_config)
        config_file_watcher.start()

    # Application restart involves multiple processes and can be triggered from multiple places.
    def restart():
        if use_config_gui:
            gui_child_process.terminate()
        python = sys.executable
        os.execl(python, python, * sys.argv)


    xy_delta_gen = filters.relative_movement()

    fps = util.simple_fps()

    freq = 60
    if use_config_gui:
        send_fps = util.Every_n(freq, lambda: parent_conn.send(str( float("{0:.2f}".format(fps.next() * freq)))))
    else:
        send_fps = util.Every_n(freq, lambda: print(str( float("{0:.2f}".format(fps.next() * freq)))))

    config.register_callback('output', update_component)
    config.register_callback('algorithm', update_component)
    config.register_callback('camera', update_component)
    config.register_callback('smoothing', update_component)
    config.register_callback('camera_dimensions', update_component)
    config.register_callback('camera_device_id', update_component)

    config.execute_all_callbacks()

    # Todo: See if there's a cleaner way to structure the nested whiles, approval of 3136 would have been nice.
    while not (needs_shutdown or needs_restart):
        with camera_driver.Camera(config) as cam:
            needs_camera_reinit = False
            while not (needs_camera_reinit or needs_shutdown or needs_restart):
                with vision_driver.Vision(cam, config) as viz:
                    needs_vision_reinit = False

                    display_frame = util.Every_n(4, viz.display_image)

                    while not (needs_vision_reinit or needs_camera_reinit or needs_shutdown or needs_restart):

                        try:
                            # Frame processing
                            viz.get_image()
                            coords = viz.process()

                            if coords is not None and None not in coords:
                                coords = filters.mirror(coords)
                                abs_pos_x, abs_pos_y, abs_pos_z = coords
                                xy = xy_delta_gen.send((abs_pos_x, abs_pos_y))

                                if not filters.detect_outliers(xy, config['max_input_distance']):
                                    xy = smoother.send(xy)
                                    xy = filters.accelerate(xy, config)

                                    output_driver.send_xy(xy)

                            if config['display']:
                                display_frame.next()
                            send_fps.next()

                        except KeyboardInterrupt:
                            needs_restart = False
                            needs_shutdown = True

    if needs_restart:
        restart()

    if use_config_gui:
        gui_child_process.terminate()
    sys.exit()
