#!/usr/bin/env python

"""
This wrapper is created to avoid complications with older versions of scipy

The Voronoi function requires scipy version 0.12 or newer
"""

import numpy

try:
	from scipy.spatial import Voronoi
	#print "scipy voronoi found"
except ImportError:
	#print "scipy voronoi not found"
	def Voronoi(points):
		raise NotImplementedError("This function requires scipy version 0.12 or newer")

def pointsToVoronoiPoints(points, filter=False):
	vor = Voronoi(points)
	if filter is True:
		vertices = filterPoints(points, vor.vertices)
	else:
		vertices = vor.vertices
	return vertices

def filterVoronoiPoints(points, voronoi_points):
	"""
	removes Voronoi points outside range of initial points
	"""
	numpypoints = numpy.array(points)
	xmin = (numpypoints[:,0]).min()
	xmax = (numpypoints[:,0]).max()
	ymin = (numpypoints[:,1]).min()
	ymax = (numpypoints[:,1]).max()
	filteredPoints = []
	for vp in voronoi_points:
		x = vp[0]
		y = vp[1]
		if xmin < x < xmax  and ymin < y < ymax:
			filteredPoints.append(vp)
	return filteredPoints

def centralPoint(points):
	numpypoints = numpy.array(points)
	xavg = (numpypoints[:,0]).mean()
	yavg = (numpypoints[:,1]).mean()
	a = numpy.array((xavg, yavg))
	mindist = 1e10
	for p in points:
		dist = numpy.power(a - p, 2).mean()
		if dist < mindist:
			minpoint = p
			mindist = dist
	return minpoint

def centralPoints(points, count=3):
	if count > len(points):
		plist = []
		for p in points:
			plist.append(p)
		return plist
	numpypoints = numpy.array(points)
	xavg = (numpypoints[:,0]).mean()
	yavg = (numpypoints[:,1]).mean()
	a = numpy.array((xavg, yavg))
	minpoints = []
	mindistlist = []
	for i in range(count):
		mindistlist.append(1e10)
		minpoints.append((0,0))
	mindistlist = numpy.array(mindistlist)
	for p in points:
		maxmindist = mindistlist.max()
		argmax = numpy.argmax(mindistlist)
		dist = numpy.power(a - p, 2).mean()
		if dist < maxmindist:
			minpoints[argmax] = p
			mindistlist[argmax] = dist
	return minpoints

if __name__ == '__main__':
	import numpy
	points = numpy.array([[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [2, 0], [2, 1], [2, 2]])
	print len(points), points[0]
	vpoints = pointsToVoronoiPoints(points)
	print vpoints
	print len(vpoints), vpoints[0]
	print centralPoints(vpoints)
	vor = Voronoi(points)
	from matplotlib import pyplot
	from scipy.spatial import voronoi_plot_2d
	voronoi_plot_2d(vor)
	pyplot.show()