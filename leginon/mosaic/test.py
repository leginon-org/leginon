#!/usr/bin/env python

### be sure /ami/sw/lib/python is in your PYTHONPATH
import Numeric
import mosaic
from mrc.Mrc import *
import math
from Tkinter import *
from viewer.ImageViewer import ImageViewer

## read the gonpos file
fp = open('02jun18a.pre.gonpos')
filelines = fp.readlines()
fp.close()

#target,source,gxoff,gyoff,theta,sclx,scly,thresh,gxmin,gxmax,gymin,gymax
vlmsize = 4096
gonlim = 1.5e-3
target = Numeric.zeros((vlmsize,vlmsize),Numeric.Float)
theta = 2.310 + 1.0 * math.pi / 2.0
sclx = 3.56127239707e-07
scly = 3.56127239707e-07
thresh = 0.2
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
	source = mrc_to_numeric(filename)

	print 'adding piece'
	mosaic.add_piece(target, source, gxoff, gyoff, theta, sclx, scly, thresh, gxmin, gxmax, gymin, gymax)


print 'saving vlm.mrc' 
numeric_to_mrc(target, 'vlm.mrc')

if 0:
	root = Tk()
	iv = ImageViewer(root)
	iv.pack()
	iv.import_numeric(target)
	root.mainloop()
