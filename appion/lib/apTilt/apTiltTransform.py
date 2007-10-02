import math
import numpy
import apImage
import apDisplay
import ImageDraw
from scipy import optimize, ndimage

##
##
## Fit All Least Squares Routine
##
##


def willsq(a1, a2, \
		 theta0, gamma0=0.0, phi0=0.0, scale0=1.0, shiftx0=0.0, shifty0=0.0,\
		 xscale=numpy.ones((6), dtype=numpy.float32)):
	"""
	given two sets of particles; find the tilt, and twist of them
	"""	
	#x0 initial values
	fit = {}
	initx = numpy.array((
		theta0 * math.pi/180.0,
		gamma0 * math.pi/180.0,
		phi0   * math.pi/180.0,
		scale0,
		shiftx0,
		shifty0,
	), dtype=numpy.float32)

	#x1 delta values
	x0 = numpy.zeros(6, dtype=numpy.float32)
	#xscale scaling values
	#xscale = numpy.ones(5, dtype=numpy.float32)
	#xscale = numpy.array((1,1,1,1,1), dtype=numpy.float32)

	#print "optimizing angles and shift..."
	#print "initial rmsd:",_diffParticles(x0, initx, xscale, a1, a2)
	a1f = numpy.asarray(a1, dtype=numpy.float32)
	a2f = numpy.asarray(a2, dtype=numpy.float32)
	solved = optimize.fmin(_diffParticles, x0, args=(initx, xscale, a1f, a2f), 
		xtol=1e-4, ftol=1e-4, maxiter=500, maxfun=500, disp=0, full_output=1)
	x1 = solved[0]
	fit['rmsd'] = float(solved[1]) #_diffParticles(x1, initx, xscale, a1, a2)
	fit['iter'] = int(solved[3])
	#print "final rmsd: "+str(fit['rmsd'])+" in "+str(fit['iter'])+" iterations"

	#x3 final values
	x3 = x1 * xscale + initx
	fit['theta']  = x3[0]*180.0/math.pi
	fit['gamma']  = x3[1]*180.0/math.pi
	fit['phi']    = x3[2]*180.0/math.pi
	fit['scale']  = x3[3]
	fit['shiftx'] = x3[4]
	fit['shifty'] = x3[5]
	fit['point1'], fit['point2'] = getPointsFromArrays(a1, a2, fit['shiftx'], fit['shifty'])
	#print "Final=",fit['point1'],"\t", fit['point2']
	fit['prob'] = math.exp(-1.0*math.sqrt(abs(fit['rmsd'])))**2
	return fit

def _diffParticles(x1, initx, xscale, a1, a2):
	x2 = x1 * xscale + initx
	theta  = x2[0]
	gamma  = x2[1]
	phi    = x2[2]
	scale  = x2[3]
	shiftx = x2[4]
	shifty = x2[5]
	point1, point2 = getPointsFromArrays(a1, a2, shiftx, shifty)
	#print point1,"\t",point2
	a2b = a2Toa1(a2, theta, gamma, phi, scale, point1, point2)
	#maxpix = float(len(a2b))
	diffmat = (a1 - a2b)
	xrmsd = ndimage.mean(diffmat[:,0]**2)
	yrmsd = ndimage.mean(diffmat[:,1]**2)
	rmsd = math.sqrt(xrmsd + yrmsd)/float(len(a2b))
	#print (x2*57.29).round(decimals=3),round(rmsd,6)
	return rmsd

def getPointsFromArrays(a1, a2, shiftx, shifty):
	if len(a1) == 0 or len(a2) == 0:
		return None,None
	point1 = numpy.asarray(a1[0,:], dtype=numpy.float32)
	point2 = numpy.asarray(a2[0,:], dtype=numpy.float32) + numpy.array([shiftx,shifty], dtype=numpy.float32)
	return (point1, point2)

def setPointsFromArrays(a1, a2, data):
	if len(a1) > 0 and len(a2) > 0:
		data['point1'] = numpy.asarray(a1[0,:], dtype=numpy.float32)
		data['point2'] = numpy.asarray(a2[0,:], dtype=numpy.float32) + numpy.array([data['shiftx'], data['shifty']], dtype=numpy.float32)
		data['point2b'] = numpy.asarray(a2[0,:], dtype=numpy.float32) - numpy.array([data['shiftx'], data['shifty']], dtype=numpy.float32)
	return

def a1Toa2Data(a1, data):
	thetarad = data['theta']*math.pi/180.0
	gammarad = data['gamma']*math.pi/180.0
	phirad   = data['phi']*math.pi/180.0
	if not 'point2b' in data:
		data['point2b'] = data['point2'] - 2*numpy.array([data['shiftx'], data['shifty']], dtype=numpy.float32)
	return a2Toa1(a1, -1.0*thetarad, -1.0*phirad, -1.0*gammarad, 
		1.0/data['scale'], data['point2b'], data['point1'])

def a2Toa1Data(a1, data):
	"""
	flips the values and runs a2Toa1
	"""
	thetarad = data['theta']*math.pi/180.0
	gammarad = data['gamma']*math.pi/180.0
	phirad   = data['phi']*math.pi/180.0
	return a2Toa1(a1, thetarad, gammarad, phirad, 
		data['scale'], data['point1'], data['point2'])

def a1Toa2(a1, theta, gamma, phi, scale, point1, point2):
	"""
	flips the values and runs a2Toa1
	"""
	raise NotImplementedError
	a1b = a2Toa1(a1, -1.0*theta, -1.0*phi, -1.0*gamma, 1.0/scale, point1, point2)
	return a1b

def a2Toa1(a2, theta, gamma, phi, scale, point1, point2):
	"""
	transforms second list of points one into same affine space as first list

	a1     -> first numpy list
	a2     -> second numpy list
	theta  -> tilt angle
	gamma  -> image 1 rotation
	phi    -> image 2 rotation
	point1 -> numpy coordinates for a particle in image 1
	point2 -> numpy coordinates for a particle in image 2
	"""
	#gamma rotation
	cosgamma = math.cos(gamma)
	singamma = math.sin(gamma)
	gammamat = numpy.array([[ cosgamma, -singamma ], [ singamma, cosgamma ]], dtype=numpy.float32)
	#theta compression
	if theta < 0:
		thetamat  = numpy.array([[ math.cos(theta), 0.0 ], [ 0.0,  1.0]], dtype=numpy.float32)
	else:
		thetamat  = numpy.array([[ 1.0/math.cos(theta), 0.0 ], [ 0.0, 1.0]], dtype=numpy.float32)
	#phi rotation
	cosphi = math.cos(phi)
	sinphi = math.sin(phi)
	phimat = numpy.array([[ cosphi, -sinphi ], [ sinphi, cosphi ]], dtype=numpy.float32)
	#scale factor
	scalemat =  numpy.array([[ scale, 0.0 ], [ 0.0, scale ]], dtype=numpy.float32)
	#merge together
	if scale > 1.0:
		trans = numpy.dot(numpy.dot(numpy.dot(scalemat,phimat),thetamat),gammamat)
	else:
		trans = numpy.dot(numpy.dot(numpy.dot(phimat,thetamat),gammamat),scalemat)
	#convert a2 -> a1
	a2b = numpy.zeros(a2.shape, dtype=numpy.float32)
	for i in range((a2.shape)[0]):
		a2c = numpy.dot(trans, a2[i,:] - point2) + point1
		a2b[i,0] = a2c[0]
		a2b[i,1] = a2c[1]
	return a2b

def maskOverlapRegion(image1, image2, data):
		image1 = ndimage.median_filter(image1, size=2)
		image2 = ndimage.median_filter(image2, size=2)
		#SET IMAGE LIMITS
		gap = int(image1.shape[0]/256.0)
		xm = image1.shape[0]+gap
		ym = image1.shape[1]+gap
		a1 = numpy.array([ data['point1'], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])
		xm = image2.shape[0]+gap
		ym = image2.shape[1]+gap
		a2 = numpy.array([ data['point2'], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])
		#CALCULATE TRANSFORM LIMITS
		a2mask = a1Toa2Data(a1, data)
		a1mask = a2Toa1Data(a2, data)
		#print "a1=",a1
		#print "a1mask=",a1mask
		#print "a2=",a2
		#print "a2mask=",a2mask

		#CONVERT NUMPY TO LIST
		a1masklist = []
		a2masklist = []
		for j in range(4):
			for i in range(2):
				item = int(a1mask[j+1,i])
				a1masklist.append(item)
				item = int(a2mask[j+1,i])
				a2masklist.append(item)
		#DRAW A POLYGON FROM THE LIMITS 1->2
		#print "a2mask=",numpy.asarray(a2mask, dtype=numpy.int32)
		#print "a2masklist=",a2masklist
		mask2 = numpy.zeros(shape=image2.shape, dtype=numpy.bool_)
		mask2b = apImage.arrayToImage(mask2, normalize=False)
		mask2b = mask2b.convert("L")
		draw2 = ImageDraw.Draw(mask2b)
		draw2.polygon(a2masklist, fill="white")
		mask2 = apImage.imageToArray(mask2b, dtype=numpy.float32)
		immin2 = ndimage.minimum(image2)+1.0
		image2 = (image2+immin2)*mask2
		immax2 = ndimage.maximum(image2)
		image2 = numpy.where(image2==0,immax2,image2)
		#DRAW A POLYGON FROM THE LIMITS 2->1
		#print "a1mask=",numpy.asarray(a1mask, dtype=numpy.int32)
		#print "a1masklist=",a1masklist
		mask1 = numpy.zeros(shape=image1.shape, dtype=numpy.bool_)
		mask1b = apImage.arrayToImage(mask1, normalize=False)
		mask1b = mask1b.convert("L")
		draw1 = ImageDraw.Draw(mask1b)
		draw1.polygon(a1masklist, fill="white")
		mask1 = apImage.imageToArray(mask1b, dtype=numpy.float32)
		immin1 = ndimage.minimum(image1)+1.0
		image1 = (image1+immin1)*mask1
		immax1 = ndimage.maximum(image1)
		image1 = numpy.where(image1==0,immax1,image1)

		return (image1, image2)

def mergePicks(picks1, picks2, limit=15.0):
	good = []
	#newa1 = numpy.vstack((a1, list1))
	for p2 in picks2:
		p1, dist = findClosestPick(p2,picks1)
		if dist > limit:
			good.append(p2)
	apDisplay.printMsg("Kept "+str(len(good))+" of "+str(len(picks2))+" overlapping peaks")
	if len(good) == 0:
		return picks1
	goodarray = numpy.asarray(good)
	newarray = numpy.vstack((picks1, goodarray))
	return newarray

def alignPicks(picks1, picks2, data, limit=5.0):
	list1 = []
	alignlist2 = []
	#transform picks2
	alignpicks2 = a2Toa1Data(picks2, data)
	#find closest pick and insert into lists
	filled = {}
	for pick in picks1:
		closepick,dist = findClosestPick(pick, alignpicks2)
		if dist < limit: 
			key = str(closepick)
			if not key in filled:
				list1.append(pick)
				alignlist2.append(closepick)
				filled[key] = True
	limit *= 2.0
	for pick in picks1:
		closepick,dist = findClosestPick(pick, alignpicks2)
		if dist < limit: 
			key = str(closepick)
			if not key in filled:
				list1.append(pick)
				alignlist2.append(closepick)
				filled[key] = True
	limit *= 2.0
	for pick in picks1:
		closepick,dist = findClosestPick(pick, alignpicks2)
		if dist < limit: 
			key = str(closepick)
			if not key in filled:
				list1.append(pick)
				alignlist2.append(closepick)
				filled[key] = True
	#convert lists
	nlist1 = numpy.array(list1, dtype=numpy.int32)
	nalignlist2 = numpy.array(alignlist2, dtype=numpy.int32)
	#transform back
	nlist2 = a1Toa2Data(nalignlist2, data)
	apDisplay.printMsg("Aligned "+str(len(nlist1))+" of "+str(len(picks1))+\
		" particles to "+str(len(nlist2))+" of "+str(len(picks2)))
	return nlist1, nlist2

def findClosestPick(origpick, picks):
	picked = None
	bestdist = 512.0
	for newpick in picks:
		dist = pickDist(origpick, newpick)
		if dist < bestdist:
			picked = newpick
			bestdist = dist
	return picked,bestdist

def pickDist(pick1, pick2):
	dist = math.hypot(pick1[0]-pick2[0], pick1[1]-pick2[1])
	return dist









