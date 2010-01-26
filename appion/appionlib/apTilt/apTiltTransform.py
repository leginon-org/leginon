import math
import sys
#PIL
import ImageDraw
#scipy
import numpy
from scipy import optimize, ndimage
#appion
import apImage
import apDisplay
import apDog
#pyami
from pyami import peakfinder
from pyami import correlator


#================================
#================================
def repairPicks(a1, a2, rmsd):
	"""
	Attempts to repair lists a1 and a2 that have become shifted
	out of frame with minimal damage
	"""
	maxdev = ndimage.mean(rmsd[:5])
	avgdev = 3*ndimage.mean(rmsd)
	x0 = [ maxdev, avgdev, 0.25*len(rmsd), 0.75*len(rmsd) ]
	print x0
	solved = optimize.fmin(_rsmdStep, x0, args=([rmsd]), 
		xtol=1e-4, ftol=1e-4, maxiter=500, maxfun=500, disp=0, full_output=1)
	upstep = int(math.floor(solved[0][2]))
	print solved

	a1b = numpyPop2d(a1, upstep)
	a2b = numpyPop2d(a2, upstep)

	return a1b, a2b

#================================
#================================			
def _rsmdStep(x1, rmsd):
	mean1  = x1[0]
	mean2  = x1[1]
	upstep = int(x1[2])
	dnstep = int(x1[3])
	fit = numpy.ones((len(rmsd)))*mean1
	fit[upstep:dnstep] += mean2
	error = ndimage.mean((rmsd-fit)**2/fit)

	return error


##
##
## Fit All Least Squares Routine
##
##


#================================
#================================
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
	fit['gamma']  = x3[1]*180.0/math.pi % 180.0
	fit['phi']    = x3[2]*180.0/math.pi % 180.0
	if fit['gamma'] > 90:
		fit['gamma'] -= 180.0
	if fit['phi'] > 90:
		fit['phi'] -= 180.0
	fit['scale']  = x3[3]
	fit['shiftx'] = x3[4]
	fit['shifty'] = x3[5]
	fit['point1'], fit['point2'] = getPointsFromArrays(a1, a2, fit['shiftx'], fit['shifty'])
	#print "Final=",fit['point1'],"\t", fit['point2']
	fit['prob'] = math.exp(-1.0*math.sqrt(abs(fit['rmsd'])))**2
	return fit

#================================
#================================
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
	#xmed = numpy.median(diffmat[:,0]**2)
	#ymed = numpy.median(diffmat[:,1]**2)
	rmsd = math.sqrt((xrmsd + yrmsd)/float(len(a2b)))
	#rmed = math.sqrt((xmed + ymed)/float(len(a2b)))
	#print (x2*57.29).round(decimals=3),round(rmsd,6)
	return rmsd

#================================
#================================
def getPointsFromArrays(a1, a2, shiftx, shifty):
	if len(a1) == 0 or len(a2) == 0:
		return None,None
	point1 = numpy.asarray(a1[0,:], dtype=numpy.float32)
	point2 = numpy.asarray(a2[0,:], dtype=numpy.float32) + numpy.array([shiftx,shifty], dtype=numpy.float32)
	return (point1, point2)

#================================
#================================
def setPointsFromArrays(a1, a2, data):
	if len(a1) > 0 and len(a2) > 0:
		data['point1'] = numpy.asarray(a1[0,:], dtype=numpy.float32)
		data['point2'] = ( numpy.asarray(a2[0,:], dtype=numpy.float32) 
			+ numpy.array([data['shiftx'], data['shifty']], dtype=numpy.float32) )
		data['point2b'] = ( numpy.asarray(a2[0,:], dtype=numpy.float32) 
			- numpy.array([data['shiftx'], data['shifty']], dtype=numpy.float32) )
	else:
		print a1, a2
		print "FAILED"
	return

#================================
#================================
def a1Toa2Data(a1, data):
	thetarad = data['theta']*math.pi/180.0
	gammarad = data['gamma']*math.pi/180.0
	phirad   = data['phi']*math.pi/180.0

	if not 'point2b' in data:
		data['point2b'] = data['point2'] - 2 * numpy.array([data['shiftx'], data['shifty']], dtype=numpy.float32)

	return a2Toa1(a1, -1.0*thetarad, 1.0*phirad, 1.0*gammarad, 
		1.0/data['scale'], data['point2'], data['point1'])

#================================
#================================
def a2Toa1Data(a2, data):
	"""
	flips the values and runs a2Toa1
	"""
	thetarad = data['theta']*math.pi/180.0
	gammarad = data['gamma']*math.pi/180.0
	phirad   = data['phi']*math.pi/180.0
	return a2Toa1(a2, thetarad, gammarad, phirad, 
		data['scale'], data['point1'], data['point2'])

#================================
#================================
def a1Toa2(a1, theta, gamma, phi, scale, point1, point2):
	"""
	flips the values and runs a2Toa1
	"""
	#raise NotImplementedError
	a1b = a2Toa1(a1, -1.0*theta, 1.0*phi, 1.0*gamma, 1.0/scale, point2, point1)
	return a1b

#================================
#================================
def a2Toa1(a2, theta, gamma, phi, scale, point1, point2):
	"""
	transforms second list of points one into same affine space as first list

	a1     -> first numpy list of x,y coordinates 
	a2     -> second numpy list of x,y coordinates
	theta  -> tilt angle
	gamma  -> image 1 rotation
	phi    -> image 2 rotation
	point1 -> numpy coordinates for a particle in image 1
	point2 -> numpy coordinates for a particle in image 2
	"""
	#gamma rotation, negative for inverse rotation
	cosgamma = math.cos(1.0*phi)
	singamma = math.sin(1.0*phi)
	gammamat = numpy.array([[ cosgamma, -singamma ], [ singamma, cosgamma ]], dtype=numpy.float32)
	#theta compression
	if theta < 0:
		thetamat  = numpy.array([[ math.cos(theta), 0.0 ], [ 0.0,  1.0]], dtype=numpy.float32)
	else:
		thetamat  = numpy.array([[ 1.0/math.cos(theta), 0.0 ], [ 0.0, 1.0]], dtype=numpy.float32)
	#phi rotation
	cosphi = math.cos(-1.0*gamma)
	sinphi = math.sin(-1.0*gamma)
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

#================================
#================================
def maskOverlapRegion(image1, image2, data):
	#image1 = ndimage.median_filter(image1, size=2)
	#image2 = ndimage.median_filter(image2, size=2)

	#SET IMAGE LIMITS
	####################################
	gap = int(image1.shape[0]/256.0)
	xm = image1.shape[1]+gap
	ym = image1.shape[0]+gap
	a1 = numpy.array([ data['point1'], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])
	xm = image2.shape[1]+gap
	ym = image2.shape[0]+gap
	a2 = numpy.array([ data['point2'], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])

	#CALCULATE TRANSFORM LIMITS
	####################################
	a2mask = a1Toa2Data(a1, data)
	a1mask = a2Toa1Data(a2, data)
	#print "a1=",a1
	#print "a1mask=",a1mask
	#print "a2=",a2
	#print "a2mask=",a2mask

	#CONVERT NUMPY TO POLYGON LIST
	####################################
	#maskimg2 = polygon.filledPolygon(img.shape, vert2)
	a1masklist = []
	a2masklist = []
	for j in range(4):
		for i in range(2):
			item = int(a1mask[j+1,i])
			a1masklist.append(item)
			item = int(a2mask[j+1,i])
			a2masklist.append(item)

	#CREATE POLYGON MASK FROM THE LIMITS 1 -> IMAGE 2
	####################################
	#print "a2mask=",numpy.asarray(a2mask, dtype=numpy.int32)
	#print "a2masklist=",a2masklist
	mask2 = numpy.zeros(shape=image2.shape, dtype=numpy.bool_)
	mask2b = apImage.arrayToImage(mask2, normalize=False)
	mask2b = mask2b.convert("L")
	draw2 = ImageDraw.Draw(mask2b)
	draw2.polygon(a2masklist, fill="white")
	mask2 = apImage.imageToArray(mask2b, dtype=numpy.float32)

	#DRAW POLYGON ONTO IMAGE 2
	####################################
	mean2 = ndimage.mean(image2)
	std2 = ndimage.standard_deviation(image2)
	immin2 = mean2 - 2.0*std2
	#med2 = numpy.median(image2.flatten())
	#print "MAX=",ndimage.maximum(image2), med2, mean2, std2
	#immin2 = ndimage.minimum(image2)+1.0
	image2 = (image2-immin2)*mask2/255.0
	#mean2 = ndimage.mean(image2)
	#std2 = ndimage.standard_deviation(image2)
	#med2 = numpy.median(image2.flatten())
	immax2 = min(ndimage.maximum(image2), 8.0*std2)
	#print "MAX=",ndimage.maximum(image2), med2, mean2, std2
	#immax2 = mean2 + 3.0 * std2
	image2 = numpy.where(image2==0, immax2, image2)

	#CREATE POLYGON MASK FROM THE LIMITS 2 -> IMAGE 1
	####################################
	#print "a1mask=",numpy.asarray(a1mask, dtype=numpy.int32)
	#print "a1masklist=",a1masklist
	mask1 = numpy.zeros(shape=image1.shape, dtype=numpy.bool_)
	mask1b = apImage.arrayToImage(mask1, normalize=False)
	mask1b = mask1b.convert("L")
	draw1 = ImageDraw.Draw(mask1b)
	draw1.polygon(a1masklist, fill="white")
	mask1 = apImage.imageToArray(mask1b, dtype=numpy.float32)

	#DRAW POLYGON ONTO IMAGE 1
	####################################
	mean1 = ndimage.mean(image1)
	std1 = ndimage.standard_deviation(image1)
	#med1 = numpy.median(image1.flatten())
	immin1 = mean1 - 2.0 * std1
	#immin1 = ndimage.minimum(image1)+1.0
	#print "MAX=",ndimage.maximum(image1), med1, mean1, std1
	image1 = (image1-immin1)*mask1/255.0
	#mean1 = ndimage.mean(image1)
	#std1 = ndimage.standard_deviation(image1)
	#med1 = numpy.median(image1.flatten())
	immax1 = min(ndimage.maximum(image1), 8.0*std1)
	#print "MAX=",ndimage.maximum(image1), med1, mean1, std1
	#immax1 = mean1 + 3.0 * std1
	image1 = numpy.where(image1==0, immax1, image1)

	return (image1, image2)

#================================
#================================
def getOverlapPercent(image1, image2, data):
	#SET IMAGE LIMITS
	gap = int(image1.shape[0]/256.0)
	xm = image1.shape[1]+gap
	ym = image1.shape[0]+gap
	a1 = numpy.array([ data['point1'], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])
	xm = image2.shape[1]+gap
	ym = image2.shape[0]+gap
	a2 = numpy.array([ data['point2'], [-gap,-gap], [-gap,ym], [xm,ym], [xm,-gap], ])

	#CALCULATE TRANSFORM LIMITS
	a2mask = a1Toa2Data(a1, data)
	a1mask = a2Toa1Data(a2, data)

	#CONVERT NUMPY TO POLYGON LIST
	a1masklist = []
	a2masklist = []
	for j in range(4):
		for i in range(2):
			item = int(a1mask[j+1,i])
			a1masklist.append(item)
			item = int(a2mask[j+1,i])
			a2masklist.append(item)

	#CREATE POLYGON MASK FROM THE LIMITS 1 -> IMAGE 2
	mask2 = numpy.zeros(shape=image2.shape, dtype=numpy.bool_)
	mask2b = apImage.arrayToImage(mask2, normalize=False)
	mask2b = mask2b.convert("L")
	draw2 = ImageDraw.Draw(mask2b)
	draw2.polygon(a2masklist, fill="white")
	mask2 = apImage.imageToArray(mask2b, dtype=numpy.float32)

	#CREATE POLYGON MASK FROM THE LIMITS 2 -> IMAGE 1
	mask1 = numpy.zeros(shape=image1.shape, dtype=numpy.bool_)
	mask1b = apImage.arrayToImage(mask1, normalize=False)
	mask1b = mask1b.convert("L")
	draw1 = ImageDraw.Draw(mask1b)
	draw1.polygon(a1masklist, fill="white")
	mask1 = apImage.imageToArray(mask1b, dtype=numpy.float32)

	percent1 = ndimage.sum(mask1) / (mask1.shape[0]*mask1.shape[1]) / ndimage.maximum(mask1)
	percent2 = ndimage.sum(mask2) / (mask2.shape[0]*mask2.shape[1]) / ndimage.maximum(mask2)

	return max(percent1,percent2), min(percent1,percent2)

#================================
#================================
def mergePicks(picks1, picks2, limit=25.0):
	good = []
	#newa1 = numpy.vstack((a1, list1))
	for p2 in picks2:
		p1, dist = findClosestPick(p2,picks1)
		if dist > limit:
			good.append(p2)
	#apDisplay.printMsg("Kept "+str(len(good))+" of "+str(len(picks2))+" overlapping peaks")
	if len(good) == 0:
		return picks1
	goodarray = numpy.asarray(good)
	newarray = numpy.vstack((picks1, goodarray))
	return newarray

def betterMergePicks(picks1a, picks1b, picks2a, picks2b, limit=25.0, msg=True):
	picks1c = []
	picks2c = []
	origpart = picks1b.shape[0]
	#elimate peaks that overlap with already picked
	for i in range(picks1b.shape[0]):
		p1a, dist = findClosestPick(picks1b[i], picks1a)
		if dist > limit:
			#no nearby particle
			picks1c.append(picks1b[i])
			picks2c.append(picks2b[i])
			#picks1b = numpyPop2d(picks1b, i)
			#picks2b = numpyPop2d(picks2b, i)
	#apDisplay.printMsg("Kept "+str(len(picks1c))+" of "+str(len(picks1b)))
	#apDisplay.printMsg("Kept "+str(len(picks2c))+" of "+str(len(picks2b)))
	picks1d = []
	picks2d = []
	for i,p2c in enumerate(picks2c):
		p2a, dist = findClosestPick(p2c, picks2a)
		if dist > limit:
			#no nearby particle
			picks1d.append(picks1c[i])
			picks2d.append(picks2c[i])
	#apDisplay.printMsg("Kept "+str(len(picks1d))+" of "+str(len(picks1c)))
	#apDisplay.printMsg("Kept "+str(len(picks2d))+" of "+str(len(picks2c)))
	picks1e = numpy.asarray(picks1d, dtype=numpy.int32)
	picks2e = numpy.asarray(picks2d, dtype=numpy.int32)
	#merge pick sets
	if picks1e.shape[0] > 0 and picks2e.shape[0] > 0:
		newa1 = numpy.vstack((picks1a, picks1e))
		newa2 = numpy.vstack((picks2a, picks2e))
	else:
		newa1 = picks1a
		newa2 = picks2a
	if msg is True:
		newpart = len(newa1) - len(picks1a)
		#newpart1 = len(picks1b) - elim
		apDisplay.printMsg("Imported "+str(newpart)+" of "+str(origpart)
			+" & merged with existing " +str(len(picks1a))+" giving "+str(len(newa1))+" particles")

	return newa1,newa2

#================================
#================================
def numpyPop2d(a, i):
	return numpy.vstack((a[0:i,:],a[i+1:len(a),:]))

#================================
#================================
def alignPicks(picks1, picks2, data, limit=20.0):
	list1 = []
	alignlist2 = []
	#transform picks2
	alignpicks2 = a2Toa1Data(picks2, data)
	#find closest pick and insert into lists
	filled = {}
	for pick in picks1:
		closepick, dist = findClosestPick(pick, alignpicks2)
		if dist < limit: 
			key = str(closepick)
			if not key in filled:
				list1.append(pick)
				alignlist2.append(closepick)
				filled[key] = True
	"""
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
	"""
	#convert lists
	nlist1 = numpy.array(list1, dtype=numpy.int32)
	nalignlist2 = numpy.array(alignlist2, dtype=numpy.int32)
	#transform back
	nlist2 = a1Toa2Data(nalignlist2, data)
	apDisplay.printMsg("Aligned "+str(len(nlist1))+" of "+str(len(picks1))+\
		" particles to "+str(len(nlist2))+" of "+str(len(picks2)))
	return nlist1, nlist2



#================================
#================================
def findClosestPick(origpick, picks):
	picked = None
	bestdist = 512.0
	for newpick in picks:
		dist = pickDist(origpick, newpick)
		if dist < bestdist:
			picked = newpick
			bestdist = dist
	return picked,bestdist

#================================
#================================
def alignPicks2(picks1, picks2, data, limit=20.0, msg=True):
	### create distance dictionary
	alignpicks2 = a2Toa1Data(picks2, data)
	sortedDict2 = {}
	index = 0
	while index < len(alignpicks2):
		p2 = alignpicks2[index]
		key = "%d,%d"%(p2[0]/limit, p2[1]/limit,)
		if not key in sortedDict2:
			sortedDict2[key] = [index,]
		else:
			sortedDict2[key].append(index)
		index+=1

	### find matching picks
	filled = {}
	list1 = []
	alignlist2 = []
	for p1 in picks1:
		closepick, dist = findClosestPick2(p1, alignpicks2, sortedDict2, limit)
		if dist < limit: 
			key = str(closepick)
			if not key in filled:
				list1.append(p1)
				alignlist2.append(closepick)
				filled[key] = True
	#convert lists
	nlist1 = numpy.array(list1, dtype=numpy.int32)
	nalignlist2 = numpy.array(alignlist2, dtype=numpy.int32)
	#transform back
	nlist2 = a1Toa2Data(nalignlist2, data)
	if msg is True:
		apDisplay.printMsg("Aligned "+str(len(nlist1))+" of "+str(len(picks1))+\
			" particles to "+str(len(nlist2))+" of "+str(len(picks2)))
	return nlist1, nlist2


#================================
#================================
def findClosestPick2(origpick, picks, sdict, limit):
	picked = None
	bestdist = 512.0
	x = int(origpick[0]/limit)
	y = int(origpick[1]/limit)
	indpicks = []
	for i in range(x-1,x+2):
		for j in range(y-1,y+2):
			key = "%d,%d"%(i,j)
			if key in sdict:
				indpicks.extend(sdict[key])
	for index in indpicks:
		#print index, len(picks)
		newpick = picks[index]
		dist = pickDist(origpick, newpick)
		if dist < bestdist:
			picked = newpick
			bestdist = dist
	return picked, bestdist

#================================
#================================
def pickDist(pick1, pick2):
	dist = math.hypot(pick1[0]-pick2[0], pick1[1]-pick2[1])
	return dist









