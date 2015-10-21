#!/usr/bin/env python
from __future__ import print_function

from Tkinter import *
import conf
import pprint
import os
import sys
import threading
import time

# Todo: set up a thread to watch for ctrl+c and exit promptly.

pp = pprint.PrettyPrinter(indent=4)
conn = None

root=Tk()
current_config = conf.render()

fps_status = StringVar()
fps_status.set("fps: ...")

temp_fp = 1

status_message=StringVar()


def set_status_message(message):
    status_message.set(time.strftime("%H:%M:%S") + ": %s" % message)


def stop_program(*args):
    root.destroy()


def restart_program(*args):
    if conn is not None:
        conn.send({'control': 'restart'})


def save_config(*args):
    conf.save(current_config)
    set_status_message("Config saved.")


def set_conf_parameter(name, value):
    current_config[name] = value
    #conf.apply_changes()
    send_config()
    set_status_message("Set %s to %s" %(name, str(value)))


def add_slider(root, name=None, scale_data=None, initial=None):
    w = Scale(root, from_=scale_data[0], to=scale_data[1], resolution=scale_data[2], label=name)
    w.set(initial)
    w.bind("<ButtonRelease-1>", lambda event: set_conf_parameter(name, event.widget.get()))
    w.pack(padx=2, pady=5, side=LEFT)


def config_root(root):
    # Todo: make button definition declarative
    label_title = Label(root, text="Headmouse",  fg="black", font="Helvetica 16 bold")
    label_title.pack()

    status = Label(root, textvariable=status_message, bd=1, relief=SUNKEN, anchor=W)
    status.pack(side=BOTTOM, fill=X)

    separator = Frame(root, bd=1, relief=SUNKEN)
    separator.pack(side=BOTTOM)

    quit_button=Button(separator, text="Quit")
    quit_button.pack(side=LEFT)
    quit_button.bind('<Button-1>', stop_program)

    reset_button=Button(separator, text="Restart")
    reset_button.pack(side=LEFT)
    reset_button.bind('<Button-1>', restart_program)

    save_button=Button(separator, text="Save")
    save_button.pack(side=LEFT)
    save_button.bind('<Button-1>', save_config)

    label_fps = Label(root, textvariable=fps_status)
    label_fps.pack(side=BOTTOM)

    def update_status_info():
        if conn is not None:
            if conn.poll(.001):
                pipe_data = conn.recv()
                fps_status.set("fps: " + str(pipe_data))
        label_fps.after(100, update_status_info)

    update_status_info()



    #w = 1200 # width for the Tk root
    #h = 200 # height for the Tk root

    # get screen width and height
    #ws = root.winfo_screenwidth() # width of the screen
    #hs = root.winfo_screenheight() # height of the screen

    #x = (ws/2) - (w/2)
    #y = (hs/2) - (h/2)

    # set the dimensions of the screen
    # and where it is placed
    #root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    root.title("Headmouse")
    root.lift ()


def send_config():
    c = {}
    c.update(current_config)
    if conn is not None:
        conn.send({'config':c})

def check_parent_process():
    # http://stackoverflow.com/questions/28597692/python-multiprocessing-how-do-you-get-the-status-of-the-parent-from-the-child
    while True:
        if os.getppid() == 1:
            sys.exit("***Parent terminated, terminating GUI child process")
        else:
            print("***aokay")
            time.sleep(.5)


def add_option_menu(root, name=None, options=None, initial=None):
    str_v =  StringVar(root)
    str_v.set(initial) # default value

    def callback(*args):
        set_conf_parameter(name, str_v.get())

    str_v.trace('w', callback)

    option_frame = Frame(root)
    w = OptionMenu(option_frame, str_v, *options)

    option_label = Label(option_frame)
    option_label["text"] = name
    option_label.pack(side=LEFT)

    w.pack(side=LEFT)

    option_frame.pack()


def initialize(io_pipe=None):
    global conn
    conn = io_pipe

    send_config()

    # Setup empty tkinter window
    config_root(root)

    slider_frame = Frame(root, relief=SUNKEN, bd=1)
    slider_frame.pack(side=LEFT)
    # Create sliders for numerical parameters from conf
    for name, scale in conf.scale_data.iteritems():
        add_slider(slider_frame, **{'name':name, 'scale_data':scale, 'initial':current_config[name]})

    menu_frame = Frame(root, relief=SUNKEN, bd=1)
    menu_frame.pack(side=LEFT)
    for name, options in conf.option_menu_data.iteritems():
        add_option_menu(menu_frame, name=name, options=options, initial=current_config[name])


    root.mainloop()

if __name__ == '__main__':
    # Overriding remote restart message, with actual restart
    def restart_program(*args):
        python = sys.executable
        os.execl(python, python, * sys.argv)


    initialize()





