#Part of the new pyappion

import sys,os,re
import time
import random
import math
import apImage,apParticle,apDatabase,apDisplay,apCorrelate,apParam
import libCV
import apLoop
import numarray
import numarray.nd_image as nd_image
import numarray.linear_algebra as linear_algebra
import numarray.random_array as random_array
import scipy.optimize as optimize
import correlator
import peakfinder

def process(img1,img2,params):

	jpgdir = os.path.join(params['rundir'],"jpgs")
	apParam.createDirectory(jpgdir)

	shortname = apDisplay.shortenImageName(img1['filename'])
	name = os.path.join(jpgdir,shortname)
	#name = re.sub("0[01]_000(?P<id>[0-9][0-9]en)_0[01]","\g<id>",name)
	#name = re.sub("_0+","_",name)
	#name = re.sub("_v0[0-9]","",name)
	tilt1 = apDatabase.getTiltAngle(img1,params)
	tilt2 = apDatabase.getTiltAngle(img2,params)
	dtilt = abs(tilt1 - tilt2)
	print "total tilt angle=",round(dtilt,4)

	doG1 = _doG(img1, params)
	halos1, particles = _createParticleHalos(img1,params)
	halodoG1 = apImage.normRange(doG1) + apImage.normRange(halos1)
	apImage.arrayToJpeg(doG1,name+"-doG1.jpg")

	doG2 = _doG(img2, params)
	halos2, particles = _createParticleHalos(img2,params)
	halodoG2 = apImage.normRange(doG2) + apImage.normRange(halos2)
	apImage.arrayToJpeg(doG2,name+"-doG2.jpg")

	shift = _getTiltedShift(doG1,tilt1,doG2,tilt2,name,params)
	trans = _rotMatrixDeg(dtilt)

	prob1 = 1.0
	prob8 = 1.0
	#trans,shift,prob1,prob8 = _compareImages(doG1,doG2,dtilt,params['binpixdiam'])
	print "TRANS=\n",numarray.around(trans,3)
	print "SHIFT=",numarray.around(shift,3)
	#print "*** separa libcv prob(1)=",apDisplay.colorProb(prob1)
	#print "*** good libcv r prob(8)=",apDisplay.colorProb(prob8)
	#tilt,twist,scale,prob2 = _matrixToEulers(trans)

	tilt,twist,scale,shift,prob2 = _optimizeTiltByCorrCoeff(halodoG1,halodoG2,dtilt,shift)
	perdiff = abs(abs(tilt)-dtilt)/dtilt
	prob5 = math.exp(-1.0*perdiff)
	prob6 = math.exp(-1.0*(twist/10.0)**2)

	matrix  = _rotMatrixDeg(tilt,twist,scale)
	print "tilt=",round(tilt,2),"("+\
		str(round(dtilt,1))+") twist=",round(twist,6)," scale=",round(scale,6)
	print "shift=",numarray.around(shift,3)
	print "*** correct tilt prob(5)=",apDisplay.colorProb(prob5)
	print "*** corrct twist prob(6)=",apDisplay.colorProb(prob6)
	print "*** matrix fit prob (2) =",apDisplay.colorProb(prob2)
	prob3,prob4 = _makeOutput(doG1,doG2,matrix,shift,name+"doG")
	prob3,prob4 = _makeOutput(halos1,halos2,matrix,shift,name+"halo")
	prob3,prob4 = _makeOutput(halos1+doG1,halos2+doG2,matrix,shift,name+"halodoG")
	print "*** better align prob(3)=",apDisplay.colorProb(prob3)
	print "*** good overlap prob(4)=",apDisplay.colorProb(prob4)

	prob7 = 1.0
	totprob = prob1*prob2*prob3*prob4*prob5*prob6*prob7*prob8
	totprob = math.sqrt(totprob)
	print "\nTOTAL PROB = ",apDisplay.colorProb(totprob)
	#time.sleep(r)
	outfile=os.path.join(params['rundir'],params['runid']+".dat")
	f = open(outfile,"a")
	f.write(shortname+" \t"+str(round(totprob,4)))
	for p in prob1,prob3,prob4,prob5:
		f.write("\t"+str(round(p,4)))
	f.write("\ttilt ="+str(round(tilt,4)))
	f.write("\ttwist="+str(round(twist,4)))
	f.write("\tscale="+str(round(scale,4)))
	f.write("\tshift="+str(numarray.around(shift,4)))
	f.write("\n")
	f.close()
	#sys.exit(1)

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	#this is a temporary fix while Jim fixes peakfinder
	pf=peakfinder.PeakFinder(lpf=lpf)
	pf.subpixelPeak(newimage=image, npix=npix, guess=guess, limit=limit)
	return pf.getResults()

#####################################################
# Get shift
#####################################################

def _getTiltedShift(img1,tilt1,img2,tilt2,name,params):
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
	apImage.arrayToJpeg(untilt1, name+"-untilt1.jpg")
	apImage.arrayToJpeg(untilt2, name+"-untilt2.jpg")

	### cross-correlate
	cc = correlator.cross_correlate(untilt1,untilt2)
	cc = apImage.preProcessImage(cc,bin=1,lowpass=diam/10.0,apix=apix*bin)
	cc = apImage.normStdev(cc)
	#apImage.printImageInfo(cc)
	cc = numarray.where(cc<2.0,2.09,cc)
	#apImage.arrayToJpeg(cc, name+"-cc.jpg")
	peakcc=findSubpixelPeak(cc, lpf=5) # this is a temp fix.
	subpixpeakcc=peakcc['subpixel peak']
	shiftcc=correlator.wrap_coord(subpixpeakcc,cc.shape)
	print shiftcc

	### phase-correlate
	pc = correlator.phase_correlate(untilt1,untilt2,zero=True)
	#pc = apCorrelate.phaseCorrelate(untilt1,untilt2)
	pc = nd_image.median_filter(pc,size=3,mode='constant')
	pc = apImage.preProcessImage(pc,bin=1,lowpass=3.0,apix=1.0)
	pc = apImage.normStdev(pc)
	#apImage.printImageInfo(pc)
	pc = numarray.where(pc<2.0,2.09,pc)
	#apImage.arrayToJpeg(pc, name+"-pc.jpg")
	peakpc=findSubpixelPeak(pc, lpf=2) # this is a temp fix.  
	subpixpeakpc=peakpc['subpixel peak']
	shiftpc=correlator.wrap_coord(subpixpeakpc,pc.shape)
	print shiftpc

	### merge-correlate
	m1 = numarray.where(cc > 2.1,pc,0.0)
	m2 = numarray.where(pc > 2.1,cc,0.0)
	mm = numarray.where(m1*m2 > 2.1,m1*m2,5)
	#apImage.arrayToJpeg(mm, name+"-mult.jpg",)
	peakmm=findSubpixelPeak(mm, lpf=2) # this is a temp fix.  
	subpixpeakmm=peakmm['subpixel peak']
	shiftmm=correlator.wrap_coord(subpixpeakmm,mm.shape)
	print shiftmm

	shift = -1.0*numarray.array((shiftcc[0],shiftcc[1]))
	fixtilt1 = _tiltImg1ToImg2(img1,dtilt,shift=shift)
	fixtilt2 = _tiltImg2ToImg1(img2,dtilt,shift=shift)
	apImage.arrayToJpeg(fixtilt1, name+"-fixtilt1.jpg")
	apImage.arrayToJpeg(fixtilt2, name+"-fixtilt2.jpg")

	#shift = -1.0*numarray.array((shiftmm[0],shiftmm[1]))
	#apImage.arrayToJpegPlusPeak(mm, name+"-mult.jpg", -1.0*shift.copy())
	hshape = numarray.array((mm.shape[0]/2, mm.shape[1]/2))
	mmshift = nd_image.shift(mm, hshape, mode='wrap')
	apImage.arrayToJpegPlusPeak(mmshift, name+"-mult.jpg", hshape+shift.copy())
	return shift

#####################################################
# Image manipulations
#####################################################

def _doG(img,params):
	apix = params['apix']
	diam = params['diam']
	bin = params['bin']
	dogimg = apImage.preProcessImage(img['image'],bin=bin,lowpass=diam/10.0,apix=apix)
	dogimg = apImage.diffOfGauss(dogimg,apix=apix,bin=bin,diam=diam,k=2.0)
	return dogimg

def _createParticleHalos(img,params):
	immult = 1.5
	noise = 0.0
	halos = numarray.zeros(img['image'].shape)
	particles,shift = apParticle.getParticles(img,params)
	numpart = len(particles)
	if numpart == 0:
		return
	print "found",numpart,"particles for image",apDisplay.shortenImageName(img['filename'])
	for prtl in particles:
		x0=int(prtl['ycoord']+0.5)
		y0=int(prtl['xcoord']+0.5)
		halos[x0][y0] = 2.0*prtl['correlation']
	halos = apImage.preProcessImage(halos,bin=4,lowpass=params['diam'],apix=params['apix'])
	#halos += immult*apImage.preProcessImage(img['image'],bin=4,lowpass=40,apix=params['apix'])
	#if noise > 0:
	#	halos += random_array.uniform(0.0, noise, shape=halos.shape)
	return halos,particles

#####################################################
# Output some informational images
#####################################################

def _makeOutput(img1,img2,trans,shift,name):
	"""
	create JPEG output for two images (img1, img2) and trnasformation matrices
	"""
	invtrans  = linear_algebra.inverse(trans)
	model1   = nd_image.affine_transform(img2, trans,    offset= shift, mode='constant', cval=0.0)
	model2   = nd_image.affine_transform(img1, invtrans, offset=-shift, mode='constant', cval=0.0)
	mmask1   = model1 != 0.0
	mmask2   = model2 != 0.0
	overlap1 = float(nd_image.sum(mmask1))/float(mmask1.shape[0]*mmask1.shape[1])
	overlap2 = float(nd_image.sum(mmask2))/float(mmask2.shape[0]*mmask2.shape[1])
	if overlap1 > 0 and overlap2 > 0:
		prob4 = math.sqrt(overlap1*overlap2)
	else:
		prob4 = 0.0
	#print "overlap1=",overlap1*100.0
	#print "overlap2=",overlap2*100.0
	rho0    = apImage.correlationCoefficient(img1,img2)
	rhoMod1 = apImage.correlationCoefficient(img1,model1,mmask1)
	rhoMod2 = apImage.correlationCoefficient(img2,model2,mmask2)
	#print "rho0    =",rho0
	#print "rhoMod1 =",rhoMod1
	#print "rhoMod2 =",rhoMod2
	apImage.arrayToJpeg(img1*mmask1,name+"-1imgdata1.jpg")
	apImage.arrayToJpeg(img2*mmask2,name+"-2imgdata2.jpg")
	#apImage.arrayToJpeg(mask,"mask.jpg")
	apImage.arrayToJpeg(model1*mmask1,name+"-1model1.jpg")
	apImage.arrayToJpeg(model2*mmask2,name+"-2model2.jpg")
	rhoDiff = (rhoMod1 + rhoMod2)/2.0 - rho0 + 0.5
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
	imgrot = nd_image.affine_transform(img2, trans, offset=shift, mode='constant', cval=0.0)
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

def _stretchImage(img,tilt,rot=0.0,scale=1.0,shift=numarray.zeros(2))
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
	smimg1 = apImage.binImg(img1,4)
	smimg1 = apImage.cutEdges(smimg1,0.1)
	smimg2 = apImage.binImg(img2,4)
	smimg2 = apImage.cutEdges(smimg2,0.1)
	#initial guesses all zero
	x0 = numarray.zeros(5,typecode=numarray.Float64)
	print "optimizing angles and shift..."
	x1 = optimize.fmin(_diffImage,x0,args=(tilt0, shift0, smimg1, smimg2),xtol=0.001,ftol=0.001,maxiter=500)
	print x1
	tilt  = x[0] + tilt0
	twist = x[1]
	scale = x[2] + 1.0
	shift = numarray.array((x[3],x[4])) + shift0
	err = _diffImage(x1, tilt, shift, img1, img2)
	prob = math.exp(-1.0*math.sqrt(abs(err)))**2
	return tilt,twist,scale,shift,prob

def _diffImage(x,tilt0,shift0,img1,img2):
	tilt  = x[0] + tilt0
	twist = x[1]
	scale = x[2] + 1.0
	shift = numarray.array((x[3],x[4])) + shift0
	img2rot = _tiltImg2ToImg1(img2,tilt,twist,scale,shift)
	correlation = apImage.correlationCoefficient(img1,img2rot)
	#sys.stderr.write(str(round(correlation,4))+" ")
	return -1*correlation

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
	x1 = optimize.fmin(_diffMatrix,x0,args=(trans),xtol=0.001,ftol=0.1,maxiter=2000)
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
