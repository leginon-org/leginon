#!/usr/bin/env python

import Mrc
import mser
import sys

im1 = Mrc.mrc_to_numeric(sys.argv[1])
im2 = Mrc.mrc_to_numeric(sys.argv[2])

result = mser.findclusters(im1, im2 )

print '%s' % (result)
