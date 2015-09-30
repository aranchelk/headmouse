#!/usr/bin/env python
from __future__ import print_function
import os
import ConfigParser

USER_CONFIG_FILE = os.path.expanduser("~/.headmouse")
TEMP_FILE = os.path.expanduser("~/.headmouse.scratch")
config_parser = ConfigParser.SafeConfigParser()


class ObservableDict(dict):
    def __init__(self, *args, **kwargs):
        self.callbacks = {}
        super(ObservableDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        # We don't set the same key to the value twice to avoid triggering callbacks unnecessarily
        if self[key] != value:
            if key in self.callbacks:
                for f in self.callbacks[key]:
                    f(key, value)
                    # was debugging multiple instances of module print(id(self))
        super(ObservableDict, self).__setitem__(key, value)

    def register_callback(self, conf_key, function):
        if conf_key in self.callbacks:
            self.callbacks[conf_key].append(function)
        else:
            self.callbacks[conf_key] = [function]

    def update_all(self, new_val_dict):
        for k, v in new_val_dict.iteritems():
            self[k] = new_val_dict[k]

# Contains default values and establishes types for values parsed from ini files
template_config = {
        'output': 'arduino_output',
        'arduino_baud': 115200,
        # 'arduino_port': '/dev/tty.usbmodemfa13131',
        'device_id':2,

        'width': 640,
        'height': 480,
        'format_': 1,
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

# Template config Metadata, currently used for settings GUI rendering, could also be used for validation.
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


def from_file(file_path, template):
    try:
        config_parser.read([file_path])
        conf = dict(config_parser.items('headmouse'))

        if template is not None:
            # Cast values from config parser to match default as parser always returns dict of strings
            for k,v in template.iteritems():
                conf[k] = type(v)(conf[k])
        return conf

    except ConfigParser.NoSectionError:
        print("No config available!")
        config_parser.add_section('headmouse')
        return {}


def render_config():
    # Apply default base config to user_config_file
    full_conf = template_config.copy()
    full_conf.update(from_file(USER_CONFIG_FILE, full_conf))
    return ObservableDict(full_conf)


def save(conf, path=USER_CONFIG_FILE):
    for k, v in conf.iteritems():
        config_parser.set('headmouse', k, str(v))

    with open(path, 'w+') as f:
        config_parser.write(f)


if __name__ == "__main__":
    c = render_config()
    print(c)
    c.register_callback('smoothing', lambda x, y: print(x, y))
    c['smoothing'] = .2
    c['smoothing'] = .2

    #save(c)


