#!/usr/bin/env python

from __future__ import print_function
import shlex
import sys
from subprocess import Popen, PIPE
import re

if sys.platform == 'darwin':
    print("Not implemented for osx")
elif sys.platform != 'linux2':
    print("Not implemented on non-linux platforms.")


def run(command_string, verbose=False):
    if verbose:
        print("Running: %s" % command_string)
    p = Popen(command_string, stdout=PIPE, stderr=PIPE, shell=True, close_fds=True)
    out, err = p.communicate()

    if p.returncode != 0:
        print(out, err)
        raise ValueError

    return out, err


def ocv_id_to_path(ocv_id):
    paths, _ = zip(*list_linux_devices())
    return paths[ocv_id]


def path_to_ocv_id(path):
    return [(x,y) for x,(y,_) in enumerate(list_linux_devices()) if y == path][0][0]


def extract_card_type(v4l2_string):
    p = re.compile('Dummy video device.*')
    card = v4l2_string.split("\n")[2].split(': ')[1]

    if p.match(card):
        return "loopback"
    elif card == 'Integrated Camera':
        return "internal"
    elif card == 'USB 2.0 Camera':
        return "external"
    else:
        return card


def get_linux_device_string(path):
    return run("v4l2-ctl --info -d %s" % path)[0]


def list_linux_devices():
    cmd = 'ls -1 /dev/video*'
    out, err = run(cmd)

    if out:
        cameras = filter(lambda x: x != '', out.split("\n"))

        cam_path_type = map(lambda c: (c, extract_card_type(get_linux_device_string(c))), cameras)

        return cam_path_type
    else:
        raise ValueError

def get_devices():
    if sys.platform == 'darwin':
        return [(0, 'unknown'), (1, 'unknown')]
    elif sys.platform == 'linux2':
        paths, cam_types = zip(*list_linux_devices())
        return list(enumerate(cam_types))