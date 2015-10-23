from __future__ import print_function
import sys

def send_xy(xy):
    x, y = xy
    sys.stdout.write("%s, %s\n" % (str("{0:.2f}".format(x)), str("{0:.2f}".format(y))))
    sys.stdout.flush()