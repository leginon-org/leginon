#!/usr/bin/env python
import numpy

def getDistanceArray(centers):
	'''
	using array math to get a square of distance matrix between all pairs of centers.
	'''
	s = len(centers)
	#create repeating 2D array
	x = numpy.repeat(centers[:,0],s).reshape((s,s))
	y = numpy.repeat(centers[:,1],s).reshape((s,s))
	# use transposed array to calculate square of distance.
	a = (x-x.T)**2+(y-y.T)**2
	return a

def withinDistance(center, centers, d):
	'''
	Return centers indices array that is within d distance from center.
	center: 1d numpy array as [x,y]
	centers: 2d numpy array [[x1,y1], [x2,y2]] 
	'''
	s = len(centers)
	x = numpy.repeat(center,s).reshape((2,s)).T
	dist_sq = numpy.sum((x-centers)*(x-centers), axis=1)
	indices_in_range = numpy.less_equal(dist_sq, d*d).nonzero()
	#indices_in_range is a one item tuple of 1D-array of integer.
	# count of indices_in_range is indices_in_range[0].shape[0]
	return indices_in_range[0]

if __name__=='__main__':
	centers = numpy.array(range(16), dtype=numpy.float).reshape((8,2))
	print centers
	center = numpy.array((5,5))
	distance = 1.0
	r = withinDistance(center, centers, distance)
	print(r.shape)
