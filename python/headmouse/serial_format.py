import sys

for line in sys.stdin:
    formatted = line.rstrip()
    xy_list = formatted.split(', ')
    x = int(round(float(xy_list[0])))
    y = int(round(float(xy_list[1])))


    print x,y
