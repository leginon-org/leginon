#!/usr/bin/env python
import sys

infilename=sys.argv[1]
outfilename=sys.argv[2]
binning = int(sys.argv[3])

from pyami import mrc
a=mrc.read(infilename)
if len(a.shape) > 2:
	a = a[0,:,:]
print(a.shape)
from pyami import imagefun
b=imagefun.bin(a,binning)
print('Binning %s by %d and save to %s' % (infilename, binning, outfilename))
mrc.write(b,outfilename)
