'''
convenience functions for raster of points
'''
import numarray
import numarray.linear_algebra

def createRaster(shape, spacing, angle):
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
	print 'min', mini, minj, 'max', maxi, maxj

	# create full raster over whole image
	rasterpoints = []
	for i in range(mini,maxi+1):
		for j in range(minj,maxj+1):
			p = numarray.matrixmultiply(E, numarray.array((i,j), numarray.Float32))
			if (0 <= p[0] < shape[0]) and (0 <= p[1] < shape[1]):
				rasterpoints.append(tuple(p))

	return rasterpoints
