#!/usr/bin/env python

import math
import time
import numpy
import random
from scipy import ndimage
#from appionlib.apImage import imagefile

"""
adapted from:
http://code.google.com/p/python-for-matlab-users/source/browse/Examples/scipy_canny.py
"""

#=======================
#=======================
def getRadialAndAngles(shape):
	## create a grid of distance from the center
	xhalfshape = shape[0]/2.0
	x = numpy.arange(-xhalfshape, xhalfshape, 1) + 0.5
	yhalfshape = shape[1]/2.0
	y = numpy.arange(-yhalfshape, yhalfshape, 1) + 0.5
	xx, yy = numpy.meshgrid(x, y)
	radialsq = xx**2 + yy**2 - 0.5
	angles = numpy.arctan2(yy,xx)
	return radialsq, angles

#=======================
#=======================
def non_maximal_edge_suppresion(mag, orient, minEdgeRadius=20, maxEdgeRadius=None):
	"""
	Non Maximal suppression of gradient magnitude and orientation.
	"""
	t0 = time.time()

	## bin orientations into 4 discrete directions
	abin = ((orient + math.pi) * 4 / math.pi + 0.5).astype('int') % 4

	radialsq, angles = getRadialAndAngles(mag.shape)
	
	### create circular mask
	if maxEdgeRadius is None:
		maxEdgeRadiusSq = radialsq[mag.shape[0]/2,mag.shape[0]/10]
	else:
		maxEdgeRadiusSq = maxEdgeRadius**2
	outermask = numpy.where(radialsq > maxEdgeRadiusSq, False, True)
	## probably a bad idea here
	innermask = numpy.where(radialsq < minEdgeRadius**2, False, True)

	### create directional filters to go with offsets
	horz = numpy.where(numpy.abs(angles) < 3*math.pi/4., numpy.abs(angles), 0)
	horz = numpy.where(horz > math.pi/4., True, False)
	vert = -horz
	upright = numpy.where(angles < math.pi/2, False, True)
	upleft = numpy.flipud(upright)
	upleft = numpy.fliplr(upleft)
	upright = numpy.logical_or(upright, upleft)
	upleft = -upright
	# for rotational edges
	filters = [horz, upleft, vert, upright]
	# for radial edges
	#filters = [vert, upright, horz, upleft]

	offsets = ((1,0), (1,1), (0,1), (-1,1))

	edge_map = numpy.zeros(mag.shape, dtype='bool')
	for a in range(4):
		di, dj = offsets[a]
		footprint = numpy.zeros((3,3), dtype="int")
		footprint[1,1] = 0
		footprint[1+di,1+dj] = 1
		footprint[1-di,1-dj] = 1
		## get adjacent maximums
		maxfilt = ndimage.maximum_filter(mag, footprint=footprint)
		## select points larger than adjacent maximums
		newedge_map = numpy.where(mag>maxfilt, True, False)
		## filter by edge orientation
		newedge_map = numpy.where(abin==a, newedge_map, False)
		## filter by location
		newedge_map = numpy.where(filters[a], newedge_map, False)
		## add to main map
		edge_map = numpy.where(newedge_map, True, edge_map)
	## remove corner edges
	edge_map = numpy.where(outermask, edge_map, False)
	edge_map = numpy.where(innermask, edge_map, False)

	#print time.time() - t0
	return edge_map

#=======================
#=======================
def canny_edges(image, minedges=5000, maxedges=15000, low_thresh=50, minEdgeRadius=20, maxEdgeRadius=None):
	"""
	Compute Canny edge detection on an image
	"""
	t0 = time.time()
	dx = ndimage.sobel(image,0)
	dy = ndimage.sobel(image,1)

	mag = numpy.hypot(dx, dy)
	mag = mag / mag.max()

	ort = numpy.arctan2(dy, dx)

	edge_map = non_maximal_edge_suppresion(mag, ort, minEdgeRadius, maxEdgeRadius)

	edge_map = numpy.logical_and(edge_map, mag > low_thresh)

	labels, numlabels = ndimage.measurements.label(edge_map, numpy.ones((3,3)))
	#print "labels", len(labels)

	#print maxs

	maxs = ndimage.measurements.maximum(mag, labels, range(1,numlabels+1))
	maxs = numpy.array(maxs, dtype=numpy.float64)
	high_thresh = maxs.mean()
	minThresh = maxs.min()

	#print time.time() - t0
	edge_count = edge_map.sum()
	count = 0
	while count < 25:
		t0 = time.time()
		count += 1
		maxs = ndimage.measurements.maximum(mag, labels, range(1,numlabels+1))
		maxs = numpy.array(maxs, dtype=numpy.float64)

		good_label = (maxs > high_thresh)
		good_label = numpy.append([False, ], good_label)
		numgood = good_label.sum()
		if numgood == numlabels and high_thresh > minThresh:
			print "ERROR"
			maxs.sort()
			print high_thresh
			print maxs[:3], maxs[-3:]
			print maxs[0], ">", high_thresh, "=", maxs[0] > high_thresh
			good_label = numpy.zeros((numlabels+1,), dtype=numpy.bool)
			good_label[1:] = maxs > high_thresh
			print good_label[:3], good_label[-3:]
			time.sleep(10)

		newedge_map = good_label[labels]
		#for i in range(len(maxs)):
		#	#if max(mag[labels==i]) < high_thresh:
		#	if maxs[i] < high_thresh:
		#		edge_map[labels==i] = False
		edge_count = newedge_map.sum()

		print "canny edges=%d, (thresh=%.3f) time=%.6f"%(edge_count, high_thresh, time.time() - t0)

		if edge_count > maxedges:
			rand = math.sqrt(random.random())
			new_thresh = high_thresh / rand
			# fix for too large values
			#print rand, new_thresh
			if new_thresh < 1.0:
				high_thresh = new_thresh
			else:
				high_thresh = math.sqrt(high_thresh)
		elif edge_count < minedges and high_thresh > minThresh:
			rand = math.sqrt(random.random())
			new_thresh = high_thresh * rand
			#print rand, new_thresh, minThresh
			high_thresh = new_thresh
		else:
			break

	#print time.time() - t0
	return newedge_map

#=======================
#=======================
#=======================
#=======================
if __name__ == "__main__":
	from scipy.misc import lena
	from matplotlib import pyplot
	lena = lena()
	image = ndimage.filters.gaussian_filter(lena, 6)

	edgeimage = canny_edges(image, minedges=2500, maxedges=15000, low_thresh=0.001, minEdgeRadius=20, maxEdgeRadius=None)

	pyplot.imshow(edgeimage)
	pyplot.gray()
	pyplot.show()



