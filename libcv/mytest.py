#!/usr/bin/env python

import Mrc
import mser

im1 = Mrc.mrc_to_numeric('05may26a_00016ma.mrc')
im2 = Mrc.mrc_to_numeric('05may26a_00024ma.mrc')

result = mser.findclusters(im1, im2 )

print '%s' % (result)
