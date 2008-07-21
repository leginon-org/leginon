#!/usr/bin/python -O

# this will save the particle stack number into the header of a stack.
# use this if you want to run cenalignint, and keep track of the particles.

import sys
from EMAN import *

if len(sys.argv) < 2:
    print "usage: renumber.py [filename]"
    sys.exit()

filename=sys.argv[1]

n=fileCount(filename)[0]
im=EMData()
for i in range(n):
    im.readImage(filename,i)
    im.setNImg(i)
    im.writeImage(filename,i)
    print i
