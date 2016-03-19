#!/usr/bin/env python
from pyscope import tem,registry
from pyami import fftfun
import time

def getTEM():
	classes = registry.getClasses()
	for i in classes:
		name, c = i
		if issubclass(c, tem.TEM):
			t = c()
			break
	return t

t = getTEM()

print 'To estimate beam shift matrix, we will need to know the foot print of the camera on the main screen'
print '1. Set magnification to the magnification to be calibrated'
print '2. Spread the beam to cover approximately the size of the camera'

raw_input('hit enter when done')
print '---------------------------------------------------------------'
print 'Center the beam on the screen'
raw_input('hit enter when done. The beam shift will be recorded')
shift0 = t.getBeamShift()

print '--------'
print 'Shift beam along camera x axis to the right so that its left edge is at the center'
raw_input('hit enter when done. The beam shift will be recorded')
shiftcol = t.getBeamShift()

print '--------'
print 'Shift beam along camera y axis toward user so that its top edge is at the center'
raw_input('hit enter when done. The beam shift will be recorded')
shiftrow = t.getBeamShift()

print '--------'
camlength = int(raw_input('Enter average number of pixels of the camera: '))
print '---------------------------------------------------------------'
raw_input('hit enter when ready to continue')

t.setBeamShift(shift0)
# calculate beam shift matrix
pixelshift = camlength / 2.0

ydiff = [(shiftrow['y']-shift0['y'])/pixelshift, (shiftcol['y']-shift0['y'])/pixelshift]
xdiff = [(shiftrow['x']-shift0['x'])/pixelshift, (shiftcol['x']-shift0['x'])/pixelshift]

import numpy
matrix = numpy.array([xdiff,ydiff],numpy.float)
print '---------------------------------------------------------------'
print matrix
print '---------------------------------------------------------------'
print 'Write down the matrix and enter into Matrix Node Beam Shift Calibration ' 
print '---------------------------------------------------------------'

raw_input('hit enter or close window to finish.')
time.sleep(2)
print 'done'
