#!/usr/bin/env python
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
### be sure /ami/sw/lib/python is in your PYTHONPATH
import Numeric
import mosaic
import Mrc
import math
from Tkinter import *
#import ImageViewer

## read the gonpos file
fp = open('02jun18a.pre.gonpos')
filelines = fp.readlines()
fp.close()

#target,source,gxoff,gyoff,theta,sclx,scly,thresh,gxmin,gxmax,gymin,gymax
vlmsize = 4096
gonlim = 1.5e-3
target = Numeric.zeros((vlmsize,vlmsize),Numeric.Float32)
theta = 2.310 + 1.0 * math.pi / 2.0
sclx = 3.56127239707e-07
scly = 3.56127239707e-07
thresh = 0.5
gxmin = -gonlim
gxmax = gonlim
gymin = -gonlim
gymax = gonlim

for line in filelines:
	fields = line.split()
	filename = fields[0]
	gxoff = float(fields[1])
	gyoff = float(fields[2])

	print 'reading ', filename
	source = Mrc.mrc_to_numeric(filename)
	source = source.astype(Numeric.Float32)

	print 'adding piece'
	mosaic.add_piece(target, source, gxoff, gyoff, theta, sclx, scly, thresh, gxmin, gxmax, gymin, gymax)


print 'saving vlm.mrc' 
Mrc.numeric_to_mrc(target, 'vlm.mrc')

if 0:
	root = Tk()
	iv = ImageViewer(root)
	iv.pack()
	iv.import_numeric(target)
	root.mainloop()
