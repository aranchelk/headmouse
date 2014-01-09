import math

def relative_movement():
    old_coords = [0,0]
    new_coords = [0,0]
    diff_coords = [0,0]

    while True:
        new_coords = yield diff_coords
        diff_coords[0] = new_coords[0] - old_coords[0]
        diff_coords[1] = new_coords[1] - old_coords[1]
        old_coords = new_coords

def get_int_and_remainder(num):
    neg = False

    if num < 0:
        neg = True
        num = -(num)

    integer_component = int(num)

    decimal_component = num
    while decimal_component > 1:
        decimal_component -= 1

    if neg is True:
        integer_component = -(integer_component)
        decimal_component = -(decimal_component)

    return integer_component, decimal_component


def sub_pix_trunc():
    #This generator truncates values with decimals to integers
    #It stores the remainder and adds it to the next value given on next pass
    #In that way it simulates a greater internal resolution
    #See Microsoft's paper on mouse ballistics, look for UoM Mickey

    remainders = [0,0]
    trunc_coords = [0,0]
    orig_coords = [0,0]
    aug_coords = [0,0]

    while True:
        #print "x orig: %s, aug: %s, trunc: %s, remainder: %s" % (orig_coords[0], aug_coords[0], trunc_coords[0], remainders[0])
        orig_coords = yield trunc_coords

        aug_coords[0] = orig_coords[0] + remainders[0]
        aug_coords[1] = orig_coords[1] + remainders[1]

        trunc_coords[0], remainders[0] = get_int_and_remainder(orig_coords[0])
        trunc_coords[1], remainders[1] = get_int_and_remainder(orig_coords[1])