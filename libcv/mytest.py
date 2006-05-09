#!/usr/bin/env python

import Mrc
import mser
import sys

im1 = Mrc.mrc_to_numeric(sys.argv[1])
im2 = Mrc.mrc_to_numeric(sys.argv[2])

result = mser.matchImages(im1, im2, 0.00004, 0.9, 0.03, 0.05 )

print '%s' % (result)
