#!/usr/bin/env python

import tifffile
import sys
from pyami import numpil
from pyami import mrc

infile = sys.argv[1]
outfile = sys.argv[2]

tif = tifffile.TIFFfile(infile)
a = tif.asarray()
print('MINMAX', a.min(), a.max())

mrc.write(a, outfile)
