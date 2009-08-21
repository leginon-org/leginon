#!/usr/bin/env python

"""
function to calculate the surface area of thresholded 3d numpy array

from pyami import surfarea
pixarea = surfarea.surfaceArea(array)
area = pixarea * (apix**2)
"""

import os
import sys
import time
import numpy
import quietscipy
from scipy import ndimage

### these are the weight for the different types of surface voxels
Svalues = [0.00, 0.894, 1.3409, 1.5879, 4.00, 2.6667, 3.3333, 1.79, 2.68, 4.08]

### this footprint is used to assess the type of surface voxel
footprint = numpy.array([ [[0,0,0], [0,1,0], [0,0,0]], [[0,1,0], [1,1,1], [0,1,0]], [[0,0,0], [0,1,0], [0,0,0]], ])

### this array is used to convert footprints to a single integer
dotarray = numpy.array([1,2,4,0,8,16,32])

### when the footprint is convert to an integer, these are the appropriate weights
intWeights = [4.0800, 3.3333, 3.3333, 2.6667, 3.3333, 2.6667, 2.6667, 1.5879, 3.3333, 2.6667, 2.6667, 1.5879, 2.6800, 4.0000, 4.0000, 1.3409, 3.3333, 2.6667, 2.6800, 4.0000, 2.6667, 1.5879, 4.0000, 1.3409, 2.6667, 1.5879, 4.0000, 1.3409, 4.0000, 1.3409, 1.7900, 0.8940, 3.3333, 2.6800, 2.6667, 4.0000, 2.6667, 4.0000, 1.5879, 1.3409, 2.6667, 4.0000, 1.5879, 1.3409, 4.0000, 1.7900, 1.3409, 0.8940, 2.6667, 4.0000, 4.0000, 1.7900, 1.5879, 1.3409, 1.3409, 0.8940, 1.5879, 1.3409, 1.3409, 0.8940, 1.3409, 0.8940, 0.8940, 0.0000, ]

#======================
def findValues():
	"""
	This script was used to create the intWeights table
	"""
	for i in range(64):
		footprint = intToFootprint(i)
		weight = surfaceWeight(footprint)
		sys.stdout.write("%.4f, "%(weight))
		#i2 = footprintToInt(footprint)
		#print i, footprint, i2
	print "\n"

#======================
def footprintToInt(footprint):
	"""
	Takes a footprint and returns an integer
	"""
	#return int(footprint[0] + 2*footprint[1] + 4*footprint[2] + 8*footprint[4] + 16*footprint[5] + 32*footprint[6])
	return int(numpy.dot(footprint, dotarray))

#======================
def intToFootprint(n):
	"""
	Takes an integer (0->63) and returns the footprint
	"""
	footprint = []
	count = 0
	while count < 6:
		count += 1
		if count == 4:
			footprint.append(1)
		footprint.append(n % 2)
		n = n >> 1
	return numpy.array(footprint)

#======================
def surfaceWeightByIfs(footprint):
	"""
	Calculate the surface area weight for a given footprint	
	"""
	### conversion is the slowest step
	nfootprint = numpy.array(footprint, dtype=numpy.bool)

	### return empty voxels
	if nfootprint[3] == 0:
		return Svalues[0]

	### number of empty neighbors
	notneighbors = 7 - nfootprint.sum()

	### zero and one are zero and one
	if notneighbors <= 1:
		return Svalues[notneighbors]

	### two empty neighbors, usually S2 or sometimes S7
	### S7 always has an empty pair across from each other
	elif notneighbors == 2:
		if nfootprint[0] == 0:
			if nfootprint[6] == 0:
				return Svalues[7]
			return Svalues[2]
		elif nfootprint[1] == 0:
			if nfootprint[5] == 0:
				return Svalues[7]
			return Svalues[2]
		elif nfootprint[2] == 0:
			if nfootprint[4] == 0:
				return Svalues[7]
			return Svalues[2]
		return Svalues[2]

	### three empty neighbors, equally S3 or S4
	### S3 has at least one filled and one empty pair across from each other
	elif notneighbors == 3:
		if nfootprint[0] == 1 and nfootprint[6] == 1:
			return Svalues[4]
		elif nfootprint[1] == 1 and nfootprint[5] == 1:
			return Svalues[4]
		elif nfootprint[2] == 1 and nfootprint[4] == 1:
			return Svalues[4]
		return Svalues[3]

	### four empty neighbors, usually S5 or sometimes S8
	### S8 always has a filled pair across from each other
	elif notneighbors == 4:
		if nfootprint[0] == 1:
			if nfootprint[6] == 1:
				return Svalues[8]
			return Svalues[5]
		elif nfootprint[1] == 1:
			if nfootprint[5] == 1:
				return Svalues[8]
			return Svalues[5]
		elif nfootprint[2] == 1:
			if nfootprint[4] == 1:
				return Svalues[8]
			return Svalues[5]
		return Svalues[5]

	### remaining easy cases
	elif notneighbors == 5:
		return Svalues[6]
	elif notneighbors == 6:
		return Svalues[9]

	raise Exception, "Failed to categorize"

#======================
def surfaceWeightByInts(footprint):
	#nfootprint = numpy.array(footprint, dtype=numpy.bool)
	if footprint[3] < 0.1:
		return Svalues[0]
	n = footprintToInt(footprint)
	return intToWeight(n)

#======================
def intToWeight(n):
	return intWeights[n]

#======================
#======================
#======================
def surfaceArea(volume):
	### ints is faster because of the conversion
	return surfaceAreaByInts(volume)

#======================
def surfaceAreaByIfs(volume):
	surf = ndimage.generic_filter(volume, surfaceWeightByIfs, footprint=footprint)
	surfarea = surf.sum()

	"""
	#testing
	Scounts = []
	for i in Svalues:
		Smatrix = numpy.where(abs(surf-i) < 0.01, 1.0, 0.0)
		Scounts.append(Smatrix.sum())
	Sarray = numpy.array(Scounts)
	#total = Sarray[1:].sum()
	#print Sarray/total
	print numpy.array(Sarray, dtype=numpy.int16)
	"""

	return  surfarea

#======================
def surfaceAreaByInts(volume):
	surf = ndimage.generic_filter(volume, surfaceWeightByInts, footprint=footprint)
	surfarea = surf.sum()

	"""
	#testing
	Scounts = []
	for i in Svalues:
		Smatrix = numpy.where(abs(surf-i) < 0.01, 1.0, 0.0)
		Scounts.append(Smatrix.sum())
	Sarray = numpy.array(Scounts)
	#total = Sarray[1:].sum()
	#print Sarray/total
	print numpy.array(Sarray, dtype=numpy.int16)
	"""

	return  surfarea

#======================
#======================
#======================
def randomSurface():
	### create a random array
	import random
	shape = []
	for i in range(3):
		dim = int(random.random()*50+1)*4
		shape.append(dim)
	#print "Shape of array: ", shape
	rand = numpy.random.random(shape)
	### zero the edges
	rand[0,:,:] = 0.0
	rand[:,0,:] = 0.0
	rand[:,:,0] = 0.0
	rand[shape[0]-1,:,:] = 0.0
	rand[:,shape[1]-1,:] = 0.0
	rand[:,:,shape[2]-1] = 0.0
	### reduce the randomness
	rand = ndimage.median_filter(rand, size=2)
	rand = ndimage.median_filter(rand, size=3)
	rand = ndimage.median_filter(rand, size=4)
	### make it boolean
	array = numpy.where(rand > 0.2, 1.0, 0.0)
	return array

#======================
def readMrc():
	if len(sys.argv) <= 1:
		return False
	mrcfile = sys.argv[1]
	if not os.path.isfile(mrcfile):
		return False
	import mrc
	voldata = mrc.read(mrcfile)
	array = numpy.where(voldata > 0.5, 1.0, 0.0)
	return array

#======================
def testSurface():
	array = readMrc()
	if not array:
		array = randomSurface()
	print "Shape of array: ", array.shape

	tifs = time.time()
	surfareabyifs = surfaceAreaByIfs(array)
	print "Surface area by ifs = %.3f pixels"%(surfareabyifs)
	fifs = time.time()

	tints = time.time()
	surfareabyints = surfaceAreaByInts(array)
	print "Surface area by ints = %.3f pixels"%(surfareabyints)
	fints = time.time()

	import apDisplay
	size = float(array.shape[0]*array.shape[1]*array.shape[2])
	print ""
	print "*** Surface area by ifs = %.3f pixels"%(surfareabyifs)
	print apDisplay.timeString((fifs-tifs)), "total time"
	print apDisplay.timeString((fifs-tifs)/size), "per voxel"
	print ""
	print "*** Surface area by ints = %.3f pixels"%(surfareabyints)
	print apDisplay.timeString((fints-tints)), "total time"
	print apDisplay.timeString((fints-tints)/size), "per voxel"	
	print ""

#======================
#======================

if __name__ == "__main__":
	#findValues()
	testSurface()
