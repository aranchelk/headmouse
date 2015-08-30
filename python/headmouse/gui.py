#!/usr/bin/env python

from Tkinter import *

root=Tk()


def stopProg(e):
    root.destroy()

def callback(test):
    print "hi"
    print dir(test.widget)
    print (test.widget.get())

def add_slider(master):
    w = Scale(master, from_=0, to=100, resolution=0.1, label="test")
    w.bind("<ButtonRelease-1>", callback)
    w.pack(padx=5, pady=10, side=LEFT)


button1=Button(root,
      text="Hello World click to close")

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

root.title("app")

add_slider(root)
add_slider(root)

root.lift ()

root.mainloop()



