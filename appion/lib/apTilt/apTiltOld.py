#Part of the new pyappion

import sys,os,re
import time
import random
import math
import apImage
import apParticle
import apDatabase
import apDisplay
import apCorrelate
import apParam
#import libCV
import apLoop
import numarray
import numarray.nd_image as nd_image
import numarray.linear_algebra as linear_algebra
import numarray.random_array as random_array
from scipy import optimize

try:
	import pyami.correlator as correlator
	import pyami.peakfinder as peakfinder
	import pyami.imagefun as imagefun
except:
	import correlator
	import peakfinder
	import imagefun

	apDisplay.printError("Could not find pyami")
	


def process(img1,img2,params):

	jpgdir = os.path.join(params['rundir'],"jpgs")
	apParam.createDirectory(jpgdir, warning=False)

	shortname = apDisplay.shortenImageName(img1['filename'])
	name = os.path.join(jpgdir,shortname)
	tilt1 = apDatabase.getTiltAngle(img1,params)
	tilt2 = apDatabase.getTiltAngle(img2,params)
	dtilt = abs(tilt1 - tilt2)
	print "total tilt angle=",round(dtilt,4)

	doG1 = _doG(img1, params)
	halos1, particles = _createParticleHalos(img1,params)
	halodoG1 = 0.75*apImage.normStdev(doG1) + apImage.normStdev(halos1)
	#apImage.arrayToJpeg(doG1,name+"-doG1.jpg")

	doG2 = _doG(img2, params)
	halos2, particles = _createParticleHalos(img2,params)
	halodoG2 = 0.75*apImage.normStdev(doG2) + apImage.normStdev(halos2)
	#apImage.arrayToJpeg(doG2,name+"-doG2.jpg")

	shift0, prob1 = getTiltedShift(doG1,tilt1,doG2,tilt2,name,params)
	print "*** corrct shift prob(1)=",apDisplay.colorProb(prob1)

	trans = _rotMatrixDeg(dtilt)
	print "TRANS=\n",numarray.around(trans,3)
	print "SHIFT=",numarray.around(shift0,3)
	#print "*** separa libcv prob(1)=",apDisplay.colorProb(prob1)
	#print "*** good libcv r prob(8)=",apDisplay.colorProb(prob8)
	#tilt,twist,scale,prob2 = _matrixToEulers(trans)

	tilt,twist1,twist2,scale,shift,prob2 = _optimizeTiltByCorrCoeff(halodoG1,halodoG2,dtilt,shift0)
	perdiff = abs(abs(tilt)-dtilt)/dtilt
	prob5 = math.exp(-1.0*perdiff)
	prob6 = math.exp(-1.0*(abs(twist1)+abs(twist2)))
	prob7 = math.exp(-1.0*abs(scale-1.0))

	matrix  = _rotMatrixDeg(tilt,twist1,scale)
	print "tilt=",round(tilt,2),"("+\
		str(round(dtilt,1))+") twist=",round(twist1,6),"twist2=",round(twist2,6)," scale=",round(scale,6)
	print "shift=",numarray.around(shift,3)
	print "*** correct tilt prob(5)=",apDisplay.colorProb(prob5)
	print "*** corrct twist prob(6)=",apDisplay.colorProb(prob6)
	print "*** optimization prob(2)=",apDisplay.colorProb(prob2)
	#prob3,prob4 = _makeOutput(doG1,doG2,tilt,twist,scale,shift,name+"doG")
	#prob3,prob4 = _makeOutput(halos1,halos2,tilt,twist,scale,shift,name+"halo")
	prob3,prob4 = _makeOutput(halodoG1,halodoG2,tilt,twist1,twist2,scale,shift,dtilt,shift0,name+"halodoG")
	print "*** better align prob(3)=",apDisplay.colorProb(prob3)
	print "*** good overlap prob(4)=",apDisplay.colorProb(prob4)

	totprob = float(prob1*prob2*prob3*prob4*prob5*prob6*prob7)
	totprob = math.sqrt(totprob)
	print "\nTOTAL PROB = ",apDisplay.colorProb(totprob)

	#time.sleep(r)
	outfile=os.path.join(params['rundir'],params['runid']+".dat")
	f = open(outfile,"a")
	f.write(shortname+" \t"+str(round(totprob,4)))
	for p in prob1,prob3,prob4,prob5,prob6,prob7:
		f.write("\t"+str(round(p,4)))
	f.write("\ttilt="+str(round(tilt,4)))
	f.write("\ttwist1="+str(round(twist1,4)))
	f.write("\ttwist2="+str(round(twist2,4)))
	f.write("\tscale="+str(round(scale,4)))
	f.write("\tshift="+str(numarray.around(shift,4)))
	f.write("\n")
	f.close()


	#sys.exit(1)



#####################################################
# Get shift
#####################################################

def getTiltedShift(img1,tilt1,img2,tilt2,name,params):
	apix = params['apix']
	diam = params['diam']
	bin = params['bin']

	### untilt images
	dtilt = (tilt1 - tilt2)/2.0
	untilt1 = _tiltImg1ToImg2(img1,dtilt)
	untilt2 = _tiltImg2ToImg1(img2,dtilt)
	### shrink by 10%
	untilt1 = apImage.cutEdges(untilt1,0.1)
	untilt2 = apImage.cutEdges(untilt2,0.1)
	footy = numarray.array(([0,0,0,],[1,1,1,],[0,0,0,]))

	### cross-correlate
	cc = correlator.cross_correlate(untilt1,untilt2)
	cc = nd_image.median_filter(cc,size=3,mode='constant',footprint=footy)
	cc = apImage.lowPassFilter(cc,bin=1,radius=3.0,apix=1.0)
	shiftcc = getBigPeak(cc)
	#apImage.arrayToJpegPlusPeak(cc, name+"-cc.jpg", shiftcc)

	### phase-correlate
	pc = correlator.phase_correlate(untilt1,untilt2,zero=True)
	pc = nd_image.median_filter(pc,size=3,mode='constant',footprint=footy)
	pc = apImage.lowPassFilter(pc,bin=1,radius=3.0,apix=1.0)
	shiftpc = getBigPeak(pc)
	#apImage.arrayToJpegPlusPeak(pc, name+"-pc.jpg", shiftpc)

	### merge-correlate
	cc = apImage.normStdev(cc)
	m1 = numarray.where(cc > 2.0, pc, 0.0)
	pc = apImage.normStdev(pc)
	m2 = numarray.where(pc > 2.0, cc, 0.0)
	mm = m1*m2
	shiftmm = getBigPeak(mm)
	#apImage.arrayToJpegPlusPeak(mm, name+"-mm.jpg", shiftmm)

	shift, shiftprob = getBestShift(shiftcc,shiftpc,shiftmm)
	if shiftprob < 0.1:
		apImage.arrayToJpegPlusPeak(cc, name+"-cc.jpg", shiftcc)
		apImage.arrayToJpegPlusPeak(pc, name+"-pc.jpg", shiftpc)
		apImage.arrayToJpegPlusPeak(mm, name+"-mm.jpg", shiftmm)
		apImage.arrayToJpegPlusPeak(untilt1, name+"-untilt1.jpg", shiftmm)
		apImage.arrayToJpegPlusPeak(untilt2, name+"-untilt2.jpg", shiftmm)
		#apDisplay.printError("not ready for this yet, all points are different")

	fixtilt2 = _tiltImg2ToImg1(img2,dtilt,shift=shift)
	apImage.arrayToJpeg(img1, name+"-fixorig1.jpg")
	apImage.arrayToJpeg(fixtilt2, name+"-fixtilt2.jpg")

	#apImage.arrayToJpegPlusPeak(mm, name+"-mult.jpg", -1.0*shift.copy())
	hshape = numarray.array((mm.shape[0]/2, mm.shape[1]/2))
	mmshift = nd_image.shift(mm, hshape, mode='wrap')
	apImage.arrayToJpegPlusPeak(mmshift, name+"-mult.jpg", -1.0*(hshape+shift.copy()))
	return shift, shiftprob

def getBestShift(shift1,shift2,shift3,err=10.0):
	diff = numarray.zeros((4,4),typecode=numarray.Float64)
	shifts = numarray.array(([shift1,shift2,shift3,[0,0],]))
	good = numarray.zeros((4),typecode=numarray.Float64)

	for i in range(3):
		score = 0
		for j in range(3):
			if i != j:
				diff[i,j] = nd_image.sum((shifts[i]-shifts[j])**2)
				good[i] += 1.0/(diff[i,j] + 0.5)

	shift = numarray.zeros((2),typecode=numarray.Float64)
	count = 0.0

	#push slightly towards zero for low prob situations
	shifts[3] = numarray.array(([0,0]))
	good[3] = 1.0e-3
	for i in range(4):
		shift += shifts[i]*good[i]
		count += good[i]
		#print "shift",i,shift/count,shifts[i],good[i]
	shift = shift/count
	prob  = (count/12.0)**(0.20)+0.3
	if prob > 1: prob = 1.0
	#print shift, count, prob
	return shift, prob

def getBigPeak(img,stdev=2.5):
	#apImage.printImageInfo(img)
	img = apImage.normStdev(img)
	mask = img > stdev
	blob = findPeak(img,mask)
	if blob != None:
		subpixpeak = blob.stats['center']
		#peak = findSubpixelPeak(img, lpf=2) # this is a temp fix.  
		#subpixpeak = peak['subpixel peak']
		shift = correlator.wrap_coord(subpixpeak, img.shape)
		shiftar = -1.0*numarray.array((shift[0],shift[1]))
		#print numarray.around(shiftar,5)
		return shiftar
	return None

def findSubpixelPeak(image, npix=25, guess=None, limit=None, lpf=None):
	#this is a temporary fix while Jim fixes peakfinder
	pf = peakfinder.PeakFinder(lpf=lpf)
	pf.subpixelPeak(newimage=image, npix=npix, guess=guess, limit=limit)
	return pf.getResults()

def findPeak(image, mask, maxblobs=1, maxsize=5000, minsize=10):
	blobs = imagefun.find_blobs(image, mask, border=0, maxblobs=maxblobs, 
		maxblobsize=maxsize, minblobsize=minsize, method="biggest")
	#import pprint
	#for blob in blobs:
	#	pprint.pprint(blob.stats)
	if len(blobs) > 0:
		return blobs[0]
	return None

#####################################################
# Image manipulations
#####################################################

def _doG(imgdict,params):
	apix = params['apix']
	diam = params['diam']
	bin = params['bin']
	dogimg = apImage.preProcessImage(imgdict['image'], lowpass=diam/10.0, params=params)
	dogimg = apImage.diffOfGauss(dogimg,apix=apix,bin=bin,diam=diam,k=2.0)
	return dogimg

def _createParticleHalos(img,params):
	immult = 1.5
	noise = 0.0
	halos = numarray.zeros(img['image'].shape)
	particles,shift = apParticle.getParticles(img, params['selexonId'])
	numpart = len(particles)
	print "found",numpart,"particles for image",apDisplay.shortenImageName(img['filename'])
	if numpart == 0:
		halos = apImage.binImg(halos,4)
		return halos,[]
	for prtl in particles:
		x0=int(prtl['ycoord']+0.5)
		y0=int(prtl['xcoord']+0.5)
		halos[x0][y0] = 2.0*prtl['correlation']
	halos = apImage.preProcessImage(halos, bin=4, lowpass=params['diam'], apix=params['apix'])
	#halos += immult*apImage.preProcessImage(img['image'], bin=4, lowpass=40, apix=params['apix'])
	#if noise > 0:
	#	halos += random_array.uniform(0.0, noise, shape=halos.shape)
	return halos,particles


#####################################################
# Output some informational images
#####################################################

def _makeOutput(img1,img2,tilt,twist1,twist2,scale,shift,tilt0,shift0,name):
	"""
	create JPEG output for two images (img1, img2) and trnasformation matrices
	"""
	model1 = _tiltImg1ToImg2(img1,tilt/2.0,twist2)
	model2 = _tiltImg2ToImg1(img2,tilt/2.0,twist1,scale,shift)
	shift2 = _tiltImg2ToImg1(img2,tilt0/2.0,0.0,1.0,shift0)
	mask   = (model1 != 0.0) * (model2 != 0.0)
	overlap = float(nd_image.sum(mask))/float(mask.shape[0]*mask.shape[1])
	prob4 = math.sqrt(overlap)
	
	rho0   = apImage.correlationCoefficient(model1,shift2,mask)
	rhoMod = apImage.correlationCoefficient(model1,model2,mask)
	apImage.arrayToJpeg(shift2*mask,name+"-mashift2.jpg")
	apImage.arrayToJpeg(model1*mask,name+"-model1.jpg")
	apImage.arrayToJpeg(model2*mask,name+"-model2.jpg")
	rhoDiff = rhoMod - rho0 + 0.25
	if rhoDiff <= 0:
		return 0.0,prob4
	return math.sqrt(rhoDiff),prob4

#####################################################
# Old libCV technique
#####################################################

def _compareImages(img1,img2,tiltangle,binpixdiam):
	"""
	takes two images (img1, img2) and finds trnasformation matrix
	"""
	if binpixdiam != None:
		minsize = binpixdiam**2/4.0
	else:
		minsize = 5
	maxsize  = 100000
	blur     = 0
	sharp    = 0
	whtonblk = True
	blkonwht = True

	goodMat = _rotMatrixDeg(tiltangle,0.0)

	img1b = 1000.0*apImage.normStdev(img1)
	img2b = 1000.0*apImage.normStdev(img2)

	bigtrans1  = libCV.MatchImages(img1b, img2b, minsize, maxsize,\
		blur, sharp, whtonblk, blkonwht) #, tiltangle)

	tprob1 = math.exp(-1.0*nd_image.sum(abs(bigtrans1[:2,:2]-goodMat))**2)
	print numarray.around(bigtrans1,5)
	print "*** good libcvr prob(8a)=",apDisplay.colorProb(tprob1)

	bigtrans2 = libCV.MatchImages(2.0*img1b, 2.0*img2b, 2*minsize, maxsize,\
		blur, sharp, whtonblk, blkonwht) #, tiltangle)

	tprob2 = math.exp(-1.0*nd_image.sum(abs(bigtrans2[:2,:2]-goodMat))**2)
	print numarray.around(bigtrans2,5)
	print "*** good libcvr prob(8b)=",apDisplay.colorProb(tprob2)

	if tprob1 > tprob2 + 0.3 or tprob2 < 1e-4:
		print "1>2:",tprob1," > ",tprob2
		bigtrans = bigtrans1
		fprob = tprob1
	elif tprob2 > tprob1 + 0.3 or tprob1 < 1e-4:
		print "2>1:",tprob2," > ",tprob1
		bigtrans = bigtrans2
		fprob = tprob2
	else:
		bigtrans = (bigtrans1 + bigtrans2) / 2.0
		fprob = math.sqrt(tprob1*tprob2)

	errmat   = (bigtrans1[:3,:2] - bigtrans2[:3,:2])/(abs(bigtrans[:3,:2])+5e-2)
	err      = nd_image.mean(errmat)
	prob     = 0.5*math.exp(-1.0*abs(err))**2+0.5
	trans    = bigtrans[:2,:2]
	shift    = bigtrans[2,:2]
	return trans,shift,prob,fprob

#####################################################
# Image rotations and tilts
#####################################################

def _tiltImageFromTo(img,starttilt,endtilt,rot=0.0,scale=1.0,shift=numarray.array((0,0))):
	return

def _tiltImg2ToImg1(img,tilt,twist=0.0,scale=1.0, shift=numarray.zeros(2)):
	#compressing image
	tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, math.cos(tilt/180.0*math.pi) ]])
	#twisting clockwise
	costwist = math.cos(twist/180.0*math.pi)
	sintwist = math.sin(twist/180.0*math.pi)
	twistmat = numarray.array([[ costwist, -sintwist ], [ sintwist, costwist ]])
	#up-scaling image
	scalemat = numarray.array([[ scale, 0.0 ], [ 0.0, scale ]])
	trans = numarray.matrixmultiply(numarray.matrixmultiply(twistmat,tiltmat),scalemat)
	imgrot = nd_image.affine_transform(img, trans, offset=shift, mode='constant', cval=0.0)
	return imgrot

def _tiltImg1ToImg2(img,tilt,twist=0.0,scale=1.0, shift=numarray.zeros(2)):
	#expanding image
	tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, 1.0/math.cos(tilt/180.0*math.pi) ]])
	#twisting counter-clockwise
	costwist = math.cos(-1.0*twist/180.0*math.pi)
	sintwist = math.sin(-1.0*twist/180.0*math.pi)
	twistmat = numarray.array([[ costwist, -sintwist ], [ sintwist, costwist ]])
	#down-scaling image
	scalemat = numarray.array([[ 1.0/scale, 0.0 ], [ 0.0, 1.0/scale ]])
	trans = numarray.matrixmultiply(numarray.matrixmultiply(twistmat,tiltmat),scalemat)
	imgrot = nd_image.affine_transform(img, trans, offset=-1.0*shift, mode='constant', cval=0.0)
	return imgrot

def _compressImage(img,tilt,rot=0.0,scale=1.0,shift=numarray.zeros(2)):
	return

def _stretchImage(img,tilt,rot=0.0,scale=1.0,shift=numarray.zeros(2)):
	return

def _rotMatrixRad(tilt,twist=0.0,scale=1.0):
	"""
	creates the tilt rotation matrix with radians
	"""
	costwist = math.cos(twist)
	sintwist = math.sin(twist)

	if tilt < 0:
		tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, 1.0/math.cos(tilt) ]])
		#print "expanding image"
	else:
		tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, math.cos(tilt) ]])
		"""print "compressing image" """
	twistmat = numarray.array([[ costwist, -sintwist ], [ sintwist, costwist ]])
	scalemat = numarray.array([[ scale, 0.0 ], [ 0.0, scale ]])
	#return numarray.matrixmultiply(tiltmat,twistmat)
	result = numarray.matrixmultiply(numarray.matrixmultiply(twistmat,tiltmat),scalemat)
	return result

def _rotMatrixDeg(tilt,twist=0.0,scale=1.0):
	"""
	creates the tilt rotation matrix with degrees
	"""
	tilt2 = tilt/180.0*math.pi
	twist2 = twist/180.0*math.pi
	return _rotMatrixRad(tilt2,twist2,scale)

#####################################################
# Refinement algorithms
#####################################################

def _optimizeTiltByCorrCoeff(img1, img2, tilt0, shift0):
	"""
	given two images; find the tilt, twist, and scale of that matrix
	"""
	#initial guesses all zero
	x0 = numarray.zeros(6,typecode=numarray.Float64)

### FIRST PASS
	"""
	smimg1 = apImage.binImg(img1,4)
	smimg1 = apImage.cutEdges(smimg1,0.1)
	smimg2 = apImage.binImg(img2,4)
	smimg2 = apImage.cutEdges(smimg2,0.1)
	print "optimizing angles and shift..."
	x1 = optimize.fmin(_corrImages, x0, args=(tilt0, shift0, smimg1, smimg2), 
	 xtol=0.1, ftol=0.000001, maxiter=2500, disp=1)
	tilt,twist1,twist2,scale,shift = _x1ToParams(x1,tilt0,shift0)
	print tilt,twist,scale,shift
	"""

### SECOND PASS
	localbin = 4
	smimg1 = apImage.binImg(img1,localbin)
	smimg1 = apImage.cutEdges(smimg1,0.05)
	smimg2 = apImage.binImg(img2,localbin)
	smimg2 = apImage.cutEdges(smimg2,0.05)
	print "optimizing angles and shift..."
	t0 = time.time()
	before = _rmsdImages(x0,tilt0,shift0,smimg1, smimg2, localbin)
	before2 = _corrImages(x0,tilt0,shift0,smimg1, smimg2, localbin)
	x1 = optimize.fmin(_rmsdImages, x0, args=(tilt0, shift0, smimg1, smimg2, localbin), 
	 xtol=0.01, ftol=0.00001, maxiter=500, disp=1)
	after = _rmsdImages(x1,tilt0,shift0,smimg1, smimg2, localbin)
	after2 = _corrImages(x1,tilt0,shift0,smimg1, smimg2, localbin)
	print "BEFORE=",before,before2
	print "AFTER=",after,after2
	if after < before:
		x0 = x1
	else:
		apDisplay.printWarning("optimization failed; rmsd got worse")
	tilt,twist1,twist2,scale,shift = _x1ToParams(x0,tilt0,shift0,1)
	print tilt,twist1,twist2,scale,shift,apDisplay.timeString(time.time()-t0)

### SUMMARIZE
	#err = _rmsdImages(x1, tilt, shift, img1, img2)
	prob = 1.0
	return tilt,twist1,twist2,scale,shift,prob

def _x1ToParams(x1,tilt0,shift0,bin):
	x2 = x1*1.0
	tilt  = x2[0] + tilt0
	twist1 = x2[1]
	twist2 = x2[2]
	#scale = x2[3]/10.0 + 1.0
	scale = 1.0
	shift = (numarray.array((x2[4]*10.0,x2[5])) + shift0)/float(bin)
	return tilt,twist1,twist2,scale,shift

def _corrImages(x1,tilt0,shift0,img1,img2,bin):
	tilt,twist1,twist2,scale,shift = _x1ToParams(x1,tilt0,shift0,bin)
	img1rot = _tiltImg1ToImg2(img1,tilt/2.0,twist2)
	img2rot = _tiltImg2ToImg1(img2,tilt/2.0,twist1,scale,shift)
	mask = (img2rot != 0.0)
	correlation = apImage.correlationCoefficient(img1,img2rot,mask)
	#print apDisplay.color(str(-1.0*correlation),"green")
	if correlation <= 0:
		return -1.0*correlation
	return -1.0*math.sqrt(correlation)

def _sumImageMult(x1,tilt0,shift0,img1,img2,bin):
	tilt,twist1,twist2,scale,shift = _x1ToParams(x1,tilt0,shift0,bin)
	img1rot = _tiltImg1ToImg2(img1,tilt/2.0,twist2)
	img2rot = _tiltImg2ToImg1(img2,tilt/2.0,twist1,scale,shift)
	mask = (img2rot != 0.0) * (img1rot != 0.0)
	-1.0*nd_image.mean(img1rot*img2rot*mask)

def _rmsdImages(x1,tilt0,shift0,img1,img2,bin):
	tilt,twist1,twist2,scale,shift = _x1ToParams(x1,tilt0,shift0,bin)
	img1rot = _tiltImg1ToImg2(img1,tilt/2.0,twist2)
	img2rot = _tiltImg2ToImg1(img2,tilt/2.0,twist1,scale,shift)
	mask = (img2rot != 0.0) * (img1rot != 0.0)
	msd = apImage.msd(img1rot,img2rot,mask)
	print apDisplay.color(str(msd),"red"),tilt,twist1,twist2,scale,shift
	#apImage.arrayToJpeg(img1rot,str(int(msd*100))+"smimg1.jpg")
	#apImage.arrayToJpeg(img2rot,str(int(msd*100))+"smimg2.jpg")
	#print msd,tilt,twist,scale,shift
	return msd

#####################################################

def _optimizeTiltByTransMatrix(img1, img2, tilt0, shift0):
	"""
	given two images; find the tilt, twist, and scale of that matrix
	"""
	smimg1 = apImage.binImg(img1,4)
	smimg1 = apImage.cutEdges(smimg1,0.1)
	smimg2 = apImage.binImg(img2,4)
	smimg2 = apImage.cutEdges(smimg2,0.1)
	#initial guesses all zero
	x0 = numarray.zeros(6,typecode=numarray.Float64)
	print "optimizing angles and shift..."
	x1 = optimize.fmin(_diffImageMatrix, x0, args=(tilt0, shift0, smimg1, smimg2), 
	 xtol=0.0001, ftol=0.00001, maxiter=2500, disp=1)
	trans,shift = _x1ToParamsMartix(x1,tilt0,shift0)
	print trans,shift
	smimg1 = apImage.binImg(img1,2)
	smimg1 = apImage.cutEdges(smimg1,0.1)
	smimg2 = apImage.binImg(img2,2)
	smimg2 = apImage.cutEdges(smimg2,0.1)
	x1 = optimize.fmin(_diffImageMatrix, x0, args=(tilt0, shift0, smimg1, smimg2), 
	 xtol=0.001, ftol=0.00001, maxiter=250, disp=1)
	trans,shift = _x1ToParamsMartix(x1,tilt0,shift0)
	print trans,shift
	err = _diffImageMatrix(x1, tilt, shift, img1, img2)
	prob = 1.0
	return trans,shift,prob

def _x1ToParamsMatrix(x1,tilt0,shift0):
	x2 = x1*100
	costilt = math.cos(tilt0*math.pi/180.0)
	trans = numarray.array(([x2[0]+1.0,x2[1],],[x2[2]+costilt,x2[3],]))
	shift = numarray.array((x2[4],x2[5])) + shift0
	return trans,shift

def _diffImageMatrix(x1,tilt0,shift0,img1,img2):
	trans,shift = _x1ToParamsMatrix(x1,tilt0,shift0)
	img2rot = nd_image.affine_transform(img2, trans, offset=-1.0*shift, mode='constant', cval=0.0)
	correlation = apImage.correlationCoefficient(img1,img2rot)
	#sys.stderr.write(str(round(correlation,4))+" ")
	if correlation <= 0:
		return -1.0*correlation
	return -1.0*math.sqrt(correlation)

#####################################################

def _optimizeTiltByParticles(parts1, parts2, tilt0, shift0, twist0=0.0, scale0=1.0):
	"""
	given two sets of particles; find the tilt, twist, and scale of that matrix
	"""
	dtilt = tilt0*math.pi/180.0
	x0 = numarray.array([0.0,twist0*math.pi/180.0,scale0,shift0[0]/40.0,shift0[1]/40.0])
	#trans = array([[1.00297072, -7.02714670e-03],[-9.42688432e-04, 0.966770461]])
	print "optimizing angles and shift..."
	x1 = optimize.fmin(_diffImage,x0,args=(dtilt, parts1, parts2),xtol=0.01,ftol=0.01,maxiter=500)
	tilt  = -1.0*(x1[0]-dtilt)*180.0/math.pi
	twist = x1[1]*180.0/math.pi
	scale = x1[2]
	shift = numarray.array((x1[3],x1[4]))*40.0
	err = _diffImage(x1, dtilt, img1, img2)
	prob = math.exp(-1.0*math.sqrt(abs(err)))**2
	return tilt,twist,scale,shift,prob

def _diffParticles(x, dtilt, parts1, parts2):
	return

#####################################################

def _matrixToEulers(trans, tilt0=15.0, twist0=0.0, scale0=1.0):
	"""
	given a matrix (trans); find the tilt, twist, and scale of that matrix
	"""
	x0 = numarray.array([tilt0*math.pi/180.0,twist0*math.pi/180.0,scale0])
	#trans = array([[1.00297072, -7.02714670e-03],[-9.42688432e-04, 0.966770461]])
	x1 = optimize.fmin(_diffMatrix, x0, args=(trans), 
		xtol=0.001, ftol=0.1, maxiter=2000, disp=1)
	tilt  = x1[0]*180.0/math.pi
	twist = x1[1]*180.0/math.pi
	scale = x1[2]
	err = _diffMatrix(x1,trans[0],trans[1])
	prob = math.exp(-1.0*math.sqrt(abs(err)))**2
	return tilt,twist,scale,prob

def _diffMatrix(x,t0,t1):
	trans = numarray.array( [ [t0[0], t0[1]], [t1[0], t1[1]] ] )
	matrix = _rotMatrixRad(x[0],x[1],x[2])
	return nd_image.mean((matrix-trans)**2)
