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
	z0 = (maxz + minz) / 2.0
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
	h = 6.6e-34
	m = 9.1e-31
	charge = 1.6e-19
	wavelength = h / math.sqrt( 2 * m * charge * ht)
	return (Cs*wavelength**3*s**4/2+1.0)/(wavelength * s**2)

def calculateFirstNode(ht,z,Cs=2.0e-3):
	# length unit is meters, and ht in Volts
	'''This works for defocus larger than about 110 nm underfocus at 120kV'''
	wavelength = 3.7e-12 * 1e5 / ht
	a = Cs*(wavelength**3)/4.0
	b = z*wavelength/2
	c = 0.5
	if b**2 >= 4*a*c:
		s2m = b/(2*a) - 1*math.sqrt(b**2-4*a*c)/(2*a)
		s = math.sqrt(s2m)
		return s

def find_ast_ellipse(grad,thr,dmean,drange):
	mrc.write(grad,'grad.mrc')
	mrc.write(thr,'thr.mrc')
	maxsize=4*(drange)*(drange)
	blobs = imagefun.find_blobs(grad,thr,maxblobsize=maxsize,minblobsize=0)
	points = []
	goods = []
	# find isolated blobs in the range
	for blob in blobs:
		if blob.stats['size']==0:
			points.append(blob.stats['center'])
		else:
			points.append(blob.stats['maximum_position'])
	shape = grad.shape
	center = map((lambda x: x / 2), shape)
	for point in points:
		d = math.hypot(point[0]-center[0],point[1]-center[1])
		if d > dmean-drange and d < dmean+drange:
			goods.append(point)
	# divide the continuous blob into wedges and find centers of each
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
				d = math.hypot(newposition[0]-center[0],newposition[1]-center[1])
				distances.append(d)
				if d > dmean-drange:
					gooddistances.append(d)
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

def fitFirstCTFNode(pow, rpixelsize, defocus, ht):
	filter = ndimage.gaussian_filter(pow,3)
	grad = ndimage.gaussian_gradient_magnitude(filter,3)
	thr = imagefun.threshold(grad,grad.mean()+3*grad.std())
	if defocus:
		z = abs(defocus)
		s = calculateFirstNode(ht,z)
		dmean = max(0.8*s/rpixelsize, 30)
	else:
		shape = pow.shape
		r = 20
		center = ( shape[0] / 2, shape[1] / 2 ) 
		grad[center[0]-r: center[0]+r, center[1]-r: center[1]+r] = 0
		peak = ndimage.maximum_position(grad)
		dmean = math.hypot(peak[0] - center[0], peak[1] - center[1])
	drange = max(dmean / 4, 10)
	eparams = find_ast_ellipse(grad,thr,dmean,drange)
	if eparams:
		z0, zast, ast_ratio, alpha = getAstigmaticDefocii(eparams,rpixelsize, ht)
		return z0,zast,ast_ratio, alpha, eparams

