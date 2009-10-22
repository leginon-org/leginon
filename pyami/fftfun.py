'''
convenience functions for displayed power spectrum
'''
import math
from pyami import imagefun, ellipse, mrc
from scipy import ndimage

def getAstigmaticDefocii(params,rpixelsize, ht):
	minr = rpixelsize * min(params['a'],params['b'])
	maxz = calculateDefocus(ht,minr)
	maxr = rpixelsize * max(params['a'],params['b'])
	minz = calculateDefocus(ht,maxr)
	z0 = (maxz + minz) / 2
	zast = maxz - z0
	ast_ratio = zast / z0
	alpha = params['alpha']
	if maxr == rpixelsize * params['b']:
		alpha = alpha + math.pi / 2
	while alpha >= math.pi / 2:
		alpha = alpha - math.pi
	while alpha < -math.pi / 2:
		alpha = alpha + math.pi

	return z0, zast, ast_ratio, alpha

def calculateDefocus(ht, s, Cs=2.0e-3):
		# unit is meters
	Cs = 2.0e-3
	wavelength = 3.7e-12 * 1e5 / ht
	return (Cs*wavelength**3*s**4/2+1)/(wavelength * s**2)

def find_ast_ellipse(grad,thr,dmean,drange):
	mrc.write(grad,'grad.mrc')
	mrc.write(thr,'thr.mrc')
	maxsize=4*(drange)*(drange)
	blobs = imagefun.find_blobs(grad,thr,maxblobsize=maxsize,minblobsize=0)
	points = []
	for blob in blobs:
		if blob.stats['size']==0:
			points.append(blob.stats['center'])
		else:
			points.append(blob.stats['maximum_position'])
	goods = []
	shape = grad.shape
	center = map((lambda x: x / 2), shape)
	for point in points:
		d = math.hypot(point[0]-center[0],point[1]-center[1])
		if d > dmean-drange and d < dmean+drange:
			goods.append(point)
	#print len(goods),dmean,drange
	offsets = []
	angles = []
	division = 32
	for i in range(0,division):
		angles.append(i * math.pi / division)
	while angles:
		angle = angles.pop()
		extra = 0
		blobs = []
		while len(blobs)==0 and extra < dmean:
			# move out until a blob is found
			offset = ((dmean+extra)*math.cos(angle)-(drange+extra)+center[0],(dmean+extra)*math.sin(angle)-(drange+extra)+center[1])
			dim = (drange+extra,drange+extra)
			gsample = grad[offset[0]:offset[0]+2*dim[0], offset[1]:offset[1]+2*dim[1]]
			sample = imagefun.threshold(gsample,grad.mean()+3*grad.std())
			# pad the edge to 0 so that blobs including the edge can be found
			sample[0:1,:]=0
			sample[-1:,:]=0
			sample[:,0:1]=0
			sample[:,-1:]=0
			#mrc.write(sample,os.path.join('sample%d.mrc'%(division-len(angles))))
			maxblobsize = dim[0]*dim[1]
			blobs = imagefun.find_blobs(gsample,sample,maxblobsize=maxsize,border=5+extra)
			distances = []
			gooddistances = []
			for blob in blobs:
				position = blob.stats['maximum_position']
				newposition = (position[0]+offset[0],position[1]+offset[1])
				#print 'blob position',position,newposition
				d = math.hypot(newposition[0]-center[0],newposition[1]-center[1])
				distances.append(d)
				if d > dmean-drange:
					gooddistances.append(d)
			#print distances
			if len(gooddistances) > 0:
				for i,blob in enumerate(blobs):
					position = blob.stats['maximum_position']
					newposition = (position[0]+offset[0],position[1]+offset[1])
					if distances[i] == min(gooddistances):
						#print division - len(angles),distances[i],position
						symposition = (center[0]*2-newposition[0],center[1]*2-newposition[1])
						goods.append(newposition)
						goods.append(symposition)
						break
			extra += drange / 2
	if len(goods) > 6:
		eparams =  ellipse.solveEllipseB2AC(goods)
		return eparams
	else:
		return None

def fitFirstCTFNode(pow, rpixelsize, ht, dmean=40, drange=10):
	filter = ndimage.gaussian_filter(pow,3)
	grad = ndimage.gaussian_gradient_magnitude(filter,3)
	thr = imagefun.threshold(grad,grad.mean()+3*grad.std())
	eparams = find_ast_ellipse(grad,thr,dmean,drange)
	if eparams:
		z0, zast, ast_ratio, alpha = getAstigmaticDefocii(eparams,rpixelsize, ht)
		return z0,zast,ast_ratio, alpha

