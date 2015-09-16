import os
import ConfigParser


USER_CONFIG_FILE = os.path.expanduser("~/.headmouse")
TEMP_FILE = os.path.expanduser("~/.headmouse.scratch")
config_parser = ConfigParser.SafeConfigParser()
current_config = None



base_config = {
        'output': 'arduino_output',
        'arduino_baud': 115200,
        #'arduino_port': '/dev/tty.usbmodemfa13131',
        'device_id':2,

        'width':640,
        'height':480,
        'format_':1,
        'display':True,
        'gray_scale':False,

        'input': 'camera',
        'input_tracker': 'dot_tracker',
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

scale_data = {
    # Todo: Add default value as 4th param
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
        return {}


def render_config():
    # Applies default base config to user_config_file
    full_conf = base_config.copy()
    # Todo: wrap in try block, their may not be a user file
    full_conf.update(config_from_file(USER_CONFIG_FILE))
    return full_conf


def write_to_file(file_name):
    # Writes current config to scratch file
    # todo: test has_section and if needed add_section.

    for k, v in current_config.iteritems():
        config_parser.set('headmouse', k, str(v))

    with open(file_name, 'w+') as f:
        config_parser.write(f)


def apply_changes():
    #write_to_file(TEMP_FILE)
    pass


def save_changes():
    # Writes current config to user config file
    #write_to_file(USER_CONFIG_FILE)
    pass


def initialize(from_scratch=False):
    global current_config
    # When multiple instances run concurrently, all but first should intiialize from temp file.
    if not from_scratch:
        current_config = render_config()
    else:
        # Todo: this should be wrapped in some retries.
        current_config = config_from_file(TEMP_FILE)

if __name__ == "__main__":
    initialize(from_scratch=True)
    print current_config
    #apply_changes()

