#!/usr/bin/env python

from __future__ import print_function

from Tkinter import *
import conf
import pprint
import os
import sys
import threading
import time

pp = pprint.PrettyPrinter(indent=4)
conn = None

root=Tk()
conf.initialize()
#pp.pprint(conf.current_config)

def stopProg(e):
    root.destroy()

def set_conf_parameter(name, value):
    conf.current_config[name] = value
    conf.apply_changes()

    send_config()

def add_slider(root, name=None, scale_data=None, initial=None):
    w = Scale(root, from_=scale_data[0], to=scale_data[1], resolution=scale_data[2], label=name)
    w.set(initial)
    w.bind("<ButtonRelease-1>", lambda event: set_conf_parameter(name, event.widget.get()))
    w.pack(padx=2, pady=5, side=LEFT)


def config_root(root):
    # Todo: make button definition declarative
    quit_button=Button(root, text="Quit")
    quit_button.pack()
    quit_button.bind('<Button-1>',stopProg)

    save_button=Button(root, text="Save")
    save_button.pack()
    save_button.bind('<Button-1>',lambda x: conf.save_changes())

    w = 800 # width for the Tk root
    h = 200 # height for the Tk root

    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen

    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    # set the dimensions of the screen
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    root.title("Headmouse")
    root.lift ()

def send_config():
    if conn is not None:
        conn.send(conf.current_config)

def check_parent_process():
    # http://stackoverflow.com/questions/28597692/python-multiprocessing-how-do-you-get-the-status-of-the-parent-from-the-child
    while True:
        if os.getppid() == 1:
            sys.exit("***Parent terminated, terminating GUI child process")
        else:
            print("***aokay")
            time.sleep(.5)


def intialize(io_pipe=None):
    global conn
    conn = io_pipe

    send_config()

    # Setup empty tkinter window
    config_root(root)

    # Create sliders for numerical parameters from conf
    for name, scale in conf.scale_data.iteritems():
        print("name:%s, scale:%s" % (name, scale))
        add_slider(root, **{'name':name, 'scale_data':scale, 'initial':conf.current_config[name]})

    # if __name__ != '__main__':
    #     t = threading.Thread(target=check_parent_process)
    #     t.start()

    root.mainloop()

if __name__ == '__main__':
    intialize()





