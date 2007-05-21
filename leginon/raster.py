'''
convenience functions for raster of points
'''
import numpy

def createRaster(shape, spacing, angle, indices=False, limit=None):
	'''
	raster across entire image
	'''
	co = spacing * numpy.cos(angle)
	si = spacing * numpy.sin(angle)
	E = numpy.array(((co,si),(-si,co)), numpy.float32)
	Einv = numpy.linalg.inv(E)

	## define a range for the raster
	corners = []
	for p in ((0,shape[1]),(shape[0],0),shape):
		i,j = numpy.dot(Einv, numpy.array(p, numpy.float32))
		i = int(i)
		j = int(j)
		corners.append((i,j))
	mini = maxi = minj = maxj = 0
	for corner in corners:
		if corner[0] > maxi:
			maxi = corner[0]
		if corner[0] < mini:
			mini = corner[0]
		if corner[1] > maxj:
			maxj = corner[1]
		if corner[1] < minj:
			minj = corner[1]

	# create full raster over whole image
	rasterpoints = []

	ind = []
	for i in range(mini,maxi+1):
		for j in range(minj,maxj+1):
			p = numpy.dot(E, numpy.array((i,j), numpy.float32))
			if (0 <= p[0] < shape[0]) and (0 <= p[1] < shape[1]):
				rasterpoints.append(tuple(p))
				ind.append((i,j))

	if indices:
		return ind
	else:
		return rasterpoints


def createIndices(shape):
	ind = numpy.indices(shape, numpy.float32)
	center0 = shape[0] / 2.0 - 0.5
	center1 = shape[1] / 2.0 - 0.5
	ind[0] = ind[0] - center0
	ind[1] = ind[1] - center1
	indices = zip(ind[0].flat, ind[1].flat)
	return indices

def createRaster2(spacing, angle, limit):
	'''
	raster across entire image
	'''
	co = spacing * numpy.cos(angle)
	si = spacing * numpy.sin(angle)
	E = numpy.array(((co,si),(-si,co)), numpy.float32)
	Einv = numpy.linalg.inv(E)

	# create full raster over whole image
	rasterpoints = []

	shape = limit,limit

	ind = createIndices(shape)

	for i in ind:
		p = numpy.dot(E, numpy.array(i, numpy.float32))
		rasterpoints.append(tuple(p))

	return rasterpoints


