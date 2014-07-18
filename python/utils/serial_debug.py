#!/usr/bin/env python
# coding=utf8

# http://stackoverflow.com/a/15095449/706819

import os
import pty

def print_serial():
	master, slave = pty.openpty()
	tty_name = os.ttyname(slave)

	print("Write serial data to {}\nCtrl-C to exit\n\n".format(tty_name))

	while True:
		print(os.read(master, 1024))

if __name__ == '__main__':
	print_serial()
