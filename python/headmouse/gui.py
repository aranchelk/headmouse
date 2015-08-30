#!/usr/bin/env python

from Tkinter import *
import conf
import pprint
pp = pprint.PrettyPrinter(indent=4)

root=Tk()
conf.initialize()
pp.pprint(conf.current_config)

def stopProg(e):
    root.destroy()

def set_conf_parameter(name, value):
    conf.current_config[name] = value
    conf.apply_changes()

def add_slider(root, name=None, scale_data=None, initial=None):
    w = Scale(root, from_=scale_data[0], to=scale_data[1], resolution=scale_data[2], label=name)
    w.set(initial)
    w.bind("<ButtonRelease-1>", lambda event: set_conf_parameter(name, event.widget.get()))
    w.pack(padx=5, pady=10, side=LEFT)

def config_root(root):
    button1=Button(root,
          text="Quit")

    button1.pack()
    button1.bind('<Button-1>',stopProg)

    w = 800 # width for the Tk root
    h = 650 # height for the Tk root

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

config_root(root)

for name, scale in conf.scale_data.iteritems():
    print "name:%s, scale:%s" % (name, scale)
    add_slider(root, **{'name':name, 'scale_data':scale, 'initial':0})

root.mainloop()



