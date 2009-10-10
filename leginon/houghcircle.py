#!/usr/bin/env python

import numpy
import scipy.ndimage as ndimage
import scipy.signal

sqrtof2 = numpy.sqrt(2.0)

def rasterCircle(x0, y0, radius):
	f = 1 - radius
	ddF_x = 1
	ddF_y = -2 * radius
	x = 0
	y = radius
	points = []
	points.append((x0, y0 + radius))
	points.append((x0, y0 - radius))
	points.append((x0 + radius, y0))
	points.append((x0 - radius, y0))

	while x < y:
		if f >= 0:
			y -= 1
			ddF_y += 2
			f += ddF_y
		x += 1
		ddF_x += 2
		f += ddF_x
		points.append((x0 + x, y0 + y))
		points.append((x0 - x, y0 + y))
		points.append((x0 + x, y0 - y))
		points.append((x0 - x, y0 - y))
		points.append((x0 + y, y0 + x))
		points.append((x0 - y, y0 + x))
		points.append((x0 + y, y0 - x))
		points.append((x0 - y, y0 - x))
	return points

def rasterCircle00(radius):
	f = 1 - radius
	ddF_x = 1
	ddF_y = -2 * radius
	x = 0
	y = radius
	points = {}
	points[(0, radius)] = None
	points[(0, -radius)] = None
	points[(radius, 0)] = None
	points[(-radius, 0)] = None

	while x < y:
		if f >= 0:
			y -= 1
			ddF_y += 2
			f += ddF_y
		x += 1
		ddF_x += 2
		f += ddF_x
		points[( x,  y)] = None
		points[(-x,  y)] = None
		points[( x, -y)] = None
		points[(-x, -y)] = None
		points[( y,  x)] = None
		points[(-y,  x)] = None
		points[( y, -x)] = None
		points[(-y, -x)] = None
	return points.keys()

def circleKernel(radius):
	shape = 2*radius+1
	shape = shape,shape
	kernel = numpy.zeros(shape)
	points = rasterCircle(radius,radius,radius)
	rows,cols = numpy.array(points).transpose()
	kernel[rows,cols] = 1
	return kernel

def transform(image, radii):
	maxradius = max(radii)
	inputshape = image.shape
	resultshape = len(radii), inputshape[0]+2*maxradius, inputshape[1]+2*maxradius
	result = numpy.zeros(resultshape, image.dtype)
	for r,radius in enumerate(radii):
		circlepoints = rasterCircle00(radius)
		for circlepoint in circlepoints:
			row0 = maxradius - circlepoint[0]
			row1 = row0 + inputshape[0]
			col0 = maxradius - circlepoint[1]
			col1 = col0 + inputshape[1]
			result[r][row0:row1, col0:col1] += image
	return result

def transform2(image, radii, limit=None):
	# limit = (rowstart, rowend, colstart, colend)
	maxradius = max(radii)
	inputshape = image.shape
	resultshape = len(radii), limit[1]-limit[0], limit[3]-limit[2]
	result = numpy.zeros(resultshape, image.dtype)
	paddedshape = inputshape[0]+2*maxradius, inputshape[1]+2*maxradius
	paddedimage = numpy.zeros(paddedshape, image.dtype)
	paddedimage[maxradius:maxradius+inputshape[0], maxradius:maxradius+inputshape[1]] = image
	for r,radius in enumerate(radii):
		circlepoints = rasterCircle00(radius)
		for circlepoint in circlepoints:

			row0 = maxradius + circlepoint[0] + limit[0]
			row1 = maxradius + circlepoint[0] + limit[1]
			col0 = maxradius + circlepoint[1] + limit[2]
			col1 = maxradius + circlepoint[1] + limit[3]

			result[r] += paddedimage[row0:row1, col0:col1]

	return result
