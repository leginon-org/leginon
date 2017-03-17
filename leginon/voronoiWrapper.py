#!/usr/bin/env python

"""
This wrapper is created to avoid complications with older versions of scipy

The Voronoi function requires scipy version 0.12 or newer
"""

try:
	from scipy.spatial import Voronoi
	#print "libcv found"
except ImportError:
	#print "libcv not found"
	def Voronoi(points):
		raise NotImplementedError("This function requires scipy version 0.12 or newer")

def pointsToVoronoiPoints(points):
	vor = Voronoi(points)
	return vor.points

if __name__ == '__main__':
	import numpy
	points = numpy.array([[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [1.8, 1.8]])
	vpoints = pointsToVoronoiPoints(points)
	vor = Voronoi(points)
	from matplotlib import pyplot
	from scipy.spatial import voronoi_plot_2d
	voronoi_plot_2d(vor)
	pyplot.show()