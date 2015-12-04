#!/usr/bin/env python

import math

radius = 1

def consumer(func):
            def wrapper(*args,**kw):
                gen = func(*args, **kw)
                gen.next()
                return gen
            wrapper.__name__ = func.__name__
            wrapper.__dict__ = func.__dict__
            wrapper.__doc__  = func.__doc__
            return wrapper


def circle_pos():
    for rad in [x * .1 for x in range(20)]:
        radians = math.pi * rad 
    
        y = math.cos(radians) * radius
        x = math.sin(radians) * radius
    
        yield (x, y)

def move_delta():
    last_x = 0
    last_y = 0

    for x_pos, y_pos in circle_pos():

        yield (x_pos - last_x, y_pos - last_y)
        #yield (x_pos, y_pos)

        last_x = x_pos
        last_y = y_pos
 
while True:
    for x, y in move_delta():
        print "c1,%s,%s" % (radius * x, radius * y)

