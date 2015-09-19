#!/usr/bin/env python
from __future__ import print_function
import os
import ConfigParser

USER_CONFIG_FILE = os.path.expanduser("~/.headmouse")
TEMP_FILE = os.path.expanduser("~/.headmouse.scratch")
config_parser = ConfigParser.SafeConfigParser()
current_config = None

base_config = {
        'output': 'arduino_output',
        'arduino_baud': 115200,
        # 'arduino_port': '/dev/tty.usbmodemfa13131',
        'device_id':2,

        'width':640,
        'height':480,
        'format_':1,
        'display':True,
        'gray_scale':False,

        'algorithm':'naive_dots_vision',
        'camera':'v4l2_looback_camera',

        'input':'camera',
        'input_tracker':'dot_tracker',
        'input_visualize': True,
        'input_realtime_search_timeout': 2.0,
        'input_slow_search_delay': 2.0,

        'input_camera_name': 0,
        # Todo: change wxh to this format 'input_camera_resolution': (1280, 720),
        'input_camera_fps': 30,

        'acceleration': 2.3,
        'sensitivity': 2.0,
        'smoothing': 0.90,
        'output_smoothing': 0.90,
        'distance_scaling': True,
        'dot_threshold': 245,
        'camera_gain': 0,

        'verbosity': 0,
        }
option_menu_data = {
    'algorithm': ['naive_dots_vision', 'eye_haar_vision'],
    'camera': ['v4l2_looback_camera', 'simple_camera']
}

scale_data = {
    # tuple(min, max, grad)
    'acceleration': (0, 3, .1),
    'sensitivity': (0, 2, .1),
    'smoothing': (0, 1, .05),
    'dot_threshold': (200, 254, 1),
    'camera_gain': (0, 50, 5),
}


def config_from_file(config_file):
    try:
        config_parser.read([config_file])
        return dict(config_parser.items('headmouse'))
    except:
        # Todo: don't except any exception
        config_parser.add_section('headmouse')
        return {}


def render_config():
    # Applies default base config to user_config_file
    full_conf = base_config.copy()
    full_conf.update(config_from_file(USER_CONFIG_FILE))

    # Cast values from config parser to match default as parser always returns dict of strings
    for k,v in base_config.iteritems():
        full_conf[k] = type(v)(full_conf[k])

    return full_conf


def write_to_file(file_name):
    for k, v in current_config.iteritems():
        config_parser.set('headmouse', k, str(v))

    with open(file_name, 'w+') as f:
        config_parser.write(f)


def save_changes():
    write_to_file(USER_CONFIG_FILE)


def initialize():
    global current_config
    current_config = render_config()


if __name__ == "__main__":
    initialize()
    print(current_config)

