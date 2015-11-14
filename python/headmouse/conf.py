#!/usr/bin/env python
from __future__ import print_function
import os
import ConfigParser
import pkgutil
from ast import literal_eval as make_tuple

USER_CONFIG_FILE = os.path.expanduser("~/.headmouse")
config_parser = ConfigParser.SafeConfigParser()


def get_modules_in_dir(dir_name):
    return [name for _, name, _ in pkgutil.iter_modules([dir_name]) if name[0] != '_' ]


class ObservableDict(dict):
    # Extending Python dict with callback registration
    def __init__(self, *args, **kwargs):
        self.callbacks = {}
        super(ObservableDict, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        # We only fire the callback if the value has actually changed.
        if self.__getitem__(key) != value:
            if key in self.callbacks:
                for f in self.callbacks[key]:
                    f(key, value)
        super(ObservableDict, self).__setitem__(key, value)

    def register_callback(self, conf_key, function):
        if conf_key not in self.callbacks:
            self.callbacks[conf_key] = [function]
        else:
            self.callbacks[conf_key].append(function)

    def execute_all_callbacks(self):
        for key, func_list in self.callbacks.iteritems():
            dict_val = self.__getitem__(key)
            for f in func_list:
                f(key, dict_val)


    def update_all(self, new_val_dict):
        for k, v in new_val_dict.iteritems():
            self[k] = new_val_dict[k]

# Contains default values and establishes types for values parsed from ini files
template_config = {
        'output': 'null', # output driver

        'camera':'simple_camera', # Camera driver
        'camera_device_id':1,
        'camera_dimensions': (640, 480),
        'display':True,

        'algorithm':'better_dots',
        'input_realtime_search_timeout': 2.0,
        'input_slow_search_delay': 2.0,

        'acceleration': 2.3,
        'sensitivity': 2.0,
        'smoothing': 0.90,
        'max_input_distance': 70,

        'distance_scaling': True,
        'dot_threshold': 245,
        'camera_gain': 0,
        'camera_brightness': 0,

        'verbosity': 0,
        }

# Template config Metadata, currently used for settings GUI rendering, could also be used for validation.
option_menu_data = {
    # List of valid options
    'algorithm': get_modules_in_dir('vision'),
    'camera': get_modules_in_dir('cameras'),
    'output': get_modules_in_dir('output_drivers')
}

scale_data = {
    # tuple(min, max, grad)
    'acceleration': (0, 3, .1),
    'sensitivity': (0, 2, .1),
    'smoothing': (0, 1, .05),
    'dot_threshold': (200, 254, 1),
    'camera_gain': (0, 100, 5),
    'camera_brightness': (-100, 100, 5),
}


def cast_by_template(coll, template):
    for template_key,template_val in template.iteritems():
        if template_key in coll:
            if isinstance(template_val, tuple): # This should be more flexible
                coll[template_key] = tuple_cast_by_template(coll[template_key], template[template_key])
            else:
                coll[template_key] = type(template_val)(coll[template_key])

    return coll


def tuple_cast_by_template(coll, template):
    coll = make_tuple(coll)

    if len(coll) != len(template):
        raise ValueError("Lenghts don't match between collection and template.")
    ret = []

    for ind, val in enumerate(template):
        ret.append( type(template[ind])(coll[ind]))

    return tuple(ret)


def from_file(file_path, template):
    try:
        config_parser.read([file_path])
        conf = dict(config_parser.items('headmouse'))

        if template is not None:
            return cast_by_template(conf, template)

    except ConfigParser.NoSectionError:
        print("No config available!")
        config_parser.add_section('headmouse')
        return {}


def render():
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
    c = render()
    print(c)
    c.register_callback('smoothing', lambda x, y: print(x, y))
    c['smoothing'] = .2
    c['smoothing'] = .2
    c.update_all(template_config)

    #save(c)


