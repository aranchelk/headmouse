# coding=utf8

import logging
logger = logging.getLogger(__name__)
import math
import numpy

def consumer(func):
    '''
    Decorator taking care of initial next() call to "sending" generators

    From PEP-342
    http://www.python.org/dev/peps/pep-0342/
    '''
    def wrapper(*args,**kw):
        gen = func(*args, **kw)
        next(gen)
        return gen
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__  = func.__doc__
    return wrapper

@consumer
def relative_movement():
    old_coords = [0,0]
    new_coords = [0,0]
    diff_coords = [0,0]

    while True:
        x, y = yield diff_coords
        if x is None or y is None:
            x, y = 0, 0
        diff_coords[0] = x - old_coords[0]
        diff_coords[1] = y - old_coords[1]
        old_coords = x, y


def mirror(coords):
    l = list(coords)
    x = l.pop(0)
    x *= -1

    return tuple([x]+l)


def limiter(coords, max_abs_value):
    out_list = []

    for c in list(coords):
        if abs(c) > max_abs_value:
            c = max_abs_value * numpy.sign(c)

        out_list.append(c)

    return out_list


def get_int_and_remainder(num):
    return int(num), num - int(num)

@consumer
def sub_pix_trunc():
    '''
    Subpixel truncator

    This generator truncates values with decimals to integers
    It stores the remainder and adds it to the next value given on next pass
    In that way it simulates a greater internal resolution
    See Microsoft's paper on mouse ballistics, look for UoM Mickey
    '''

    remainders = [0,0]
    trunc_coords = [0,0]
    orig_coords = [0,0]
    aug_coords = [0,0]

    while True:
        #print "x orig: %s, aug: %s, trunc: %s, remainder: %s" % (orig_coords[0], aug_coords[0], trunc_coords[0], remainders[0])
        orig_coords = yield trunc_coords

        aug_coords[0] = orig_coords[0] + remainders[0]
        aug_coords[1] = orig_coords[1] + remainders[1]

        trunc_coords[0], remainders[0] = get_int_and_remainder(aug_coords[0])
        trunc_coords[1], remainders[1] = get_int_and_remainder(aug_coords[1])

@consumer
def ema(alpha):
    out = 0
    while True:
        in_ = yield out
        out = in_ * alpha + out * (1 - alpha)

@consumer
def ema_smoother(alpha=0.5):
    v_out = 0
    ema_x, ema_y = ema(alpha), ema(alpha)

    while True:
        x_in, y_in = yield v_out
        v_out = ema_x.send(x_in), ema_y.send(y_in)

@consumer
def slow_smoother(alpha=0.5):
    smoother = ema_smoother(alpha)
    v_out = (0,0)
    v = (0,0)

    while True:
        last_v = v
        v, max_smooth = yield v_out
        v_mag = (v[0] ** 2 + v[1] ** 2 ) ** 0.5
        #print v_mag
        v_smooth = smoother.send(v)

        if v_mag < max_smooth:
            v_out = v_smooth
        else:
            v_out = v
            #print "### Fast, no smoothing ###"



@consumer
def stateful_smoother():
    #Operates similar to sub_pix_trunc, except in never returns partial values, if activated, it stores the value and
    #and returns nothing
    threshold = [1.3, 1.3]
    stored_coords = [0,0]
    aug_coords = [0,0]

    while True:
        orig_coords = yield aug_coords

        for i in range(2):
            print i
            if math.fabs(orig_coords[i] + stored_coords[i]) > threshold[i]:
                aug_coords[i] = orig_coords[i]
                stored_coords[i] = 0
            else:
                stored_coords[i] += orig_coords[i]
                aug_coords[i] = 0


def accelerate(coords, conf):
    p = 2

    v_mag = numpy.linalg.norm(coords) # Get vector magnitude
    scale = v_mag ** (p - 1) * conf['acceleration'] + conf['sensitivity']

    return tuple(map(lambda x: scale * x, coords))


@consumer
def accelerate_exp(p=2, accel=6, sensitivity=0):
    v_out = 0,0

    while True:
        v_x, v_y = yield v_out
        v_mag = (v_x ** 2 + v_y ** 2 ) ** 0.5
        scale = v_mag ** (p - 1) * accel + sensitivity
        v_out = v_x * scale, v_y * scale


def killOutliers(coords, threshold=2000):
    if math.fabs(coords[0]) > threshold or math.fabs(coords[1]) > threshold:
        logger.info("*** Outlier ***")
        print 'outlier'
        return [0,0]
    else:
        return coords
