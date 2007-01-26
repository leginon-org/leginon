'''
convenience functions for raster of points
'''
import numarray
import numarray.linear_algebra

def createRaster(shape, spacing, angle, indices=False, limit=None):
	'''
	raster across entire image
	'''
	co = spacing * numarray.cos(angle)
	si = spacing * numarray.sin(angle)
	E = numarray.array(((co,si),(-si,co)), numarray.Float32)
	Einv = numarray.linear_algebra.inverse(E)

	## define a range for the raster
	corners = []
	for p in ((0,shape[1]),(shape[0],0),shape):
		i,j = numarray.matrixmultiply(Einv, numarray.array(p, numarray.Float32))
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
			p = numarray.matrixmultiply(E, numarray.array((i,j), numarray.Float32))
			if (0 <= p[0] < shape[0]) and (0 <= p[1] < shape[1]):
				rasterpoints.append(tuple(p))
				ind.append((i,j))

	if indices:
		return ind
	else:
		return rasterpoints


def createIndices(shape):
	ind = numarray.indices(shape, numarray.Float32)
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
	co = spacing * numarray.cos(angle)
	si = spacing * numarray.sin(angle)
	E = numarray.array(((co,si),(-si,co)), numarray.Float32)
	Einv = numarray.linear_algebra.inverse(E)

	# create full raster over whole image
	rasterpoints = []

	shape = limit,limit

	ind = createIndices(shape)

	for i in ind:
		p = numarray.matrixmultiply(E, numarray.array(i, numarray.Float32))
		rasterpoints.append(tuple(p))

	return rasterpoints


