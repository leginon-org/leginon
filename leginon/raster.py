'''
convenience functions for raster of points
'''
import numpy
import math

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
	'''
	square indices
	'''
	ind = numpy.indices(shape, numpy.float32)
	center0 = shape[0] / 2.0 - 0.5
	center1 = shape[1] / 2.0 - 0.5
	ind[0] = ind[0] - center0
	ind[1] = ind[1] - center1
	indices = zip(ind[0].flat, ind[1].flat)
	return indices

def createIndices2(a,b,angle,offset=False,odd=False,tiltoffset=(0,0)):
	'''
  indices enclosed by an ellipse
	'''
	offsetvalues = (0.5,0.25)
	cos = math.cos(angle)
	sin = math.sin(angle)
	maxab = math.ceil(max(a,b))
	if offset and not maxab % 2:
		# keep center offset pattern consistent
		maxab = maxab + 1
	maxind = 2 + 2 * maxab
	shape = maxind,maxind
	ind = numpy.indices(shape, numpy.float32)
	if offset:
		adds = numpy.ma.where(ind[0] % 2 == 0, numpy.zeros(shape),numpy.ones(shape)*0.5)
		ind = numpy.array((ind[0],ind[1]+adds.data))
		if odd:
			ind[0] = ind[0] + offsetvalues[0]
			ind[1] = ind[1] + offsetvalues[1]
		ind[0] = ind[0] + tiltoffset[0]
		ind[1] = ind[1] + tiltoffset[1]
	center0 = shape[0] / 2.0
	center1 = shape[1] / 2.0
	ind[0] = ind[0] - center0
	ind[1] = ind[1] - center1
	indices = zip(ind[0].flat, ind[1].flat)
	goodindices = []
	for index in indices:
		good = False
		row = abs(index[0]*cos-index[1]*sin)
		col = abs(index[0]*sin+index[1]*cos)
		testrange = (0.0,0.1,0.2,0.3,0.4,0.5)
		for deltarow in testrange:
			for deltacol in testrange:
				if row > deltarow:
					testrow = row - deltarow
				else:
					testrow = row
				if col > deltacol:
					testcol = col - deltacol
				else:
					testcol = col
				if (testcol/a)**2+(testrow/b)**2 <= 1:
					goodindices.append(index)
					good = True
					break
			if good:
					break
	return goodindices

def createRaster2(spacing, angle, limit):
	'''
	raster across image, limited by square defined by limit
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


def createRaster3(spacing, angle, limitindices):
	'''
	raster across entire image, limited by index list
	'''
	co = spacing * numpy.cos(angle)
	si = spacing * numpy.sin(angle)
	E = numpy.array(((co,si),(-si,co)), numpy.float32)
	Einv = numpy.linalg.inv(E)

	# create full raster over whole image
	rasterpoints = []

	for i in limitindices:
		p = numpy.dot(E, numpy.array(i, numpy.float32))
		rasterpoints.append(tuple(p))

	return rasterpoints

