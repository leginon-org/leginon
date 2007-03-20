#Part of the new pyappion

import sys
import time
import random
import math
import apImage,apParticle
import libCV
import numarray
import numarray.nd_image as nd_image
import numarray.linear_algebra as linear_algebra
import scipy.optimize as optimize

def process(img1,img2,params):
	r = random.uniform(0,0.5)
	apix = params['apix']
	print "sleeping ",r
	time.sleep(r)
	box=128


	blank1 = numarray.zeros(img1['image'].shape)
	particles,shift = apParticle.getParticles(img1,params)
	print "found",len(particles),"particles for image1"
	for prtl in particles:
		x0=int(prtl['xcoord']-(box/2)-shift['shiftx']+0.5)
		y0=int(prtl['ycoord']-(box/2)-shift['shifty']+0.5)
		blank1[x0][y0] = 1
	blank1 = apImage.preProcessImage(blank1,bin=4,lowpass=400,apix=apix)
	apImage.arrayToJpeg(blank1,"blank1.jpg")

	blank2 = numarray.zeros(img2['image'].shape)
	particles,shift = apParticle.getParticles(img2,params)
	print "found",len(particles),"particles for image2"
	for prtl in particles:
		x0=int(prtl['xcoord']-(box/2)-shift['shiftx']+0.5)
		y0=int(prtl['ycoord']-(box/2)-shift['shifty']+0.5)
		blank2[x0][y0] = 1
	blank2 = apImage.preProcessImage(blank2,bin=4,lowpass=400,apix=apix)
	apImage.arrayToJpeg(blank2,"blank2.jpg")


	#blank1 = apImage.lowPassFilter(blank1,apix=1.0,bin=1,radius=10.0)


	#imgdata1 = apImage.preProcessImage(blank1['image'],bin=4,lowpass=10,apix=apix)
	#imgdata2 = apImage.preProcessImage(img2['image'],bin=4,lowpass=10,apix=apix)
	trans,shift,prob1 = _compareImages(blank1,blank2)
	print trans
	print shift
	print "prob1=",round(prob1,6)
	tilt,twist,prob2 = _matrixToEulers(trans)
	matrix  = _rotMatrixDeg(tilt,twist)
	print "tilt=",round(tilt,2),"twist=",round(twist,6),"\nprob2=",round(prob2,6)
	prob3 = _makeOutput(blank1,blank2,trans,matrix,shift)
	print "prob3=",round(prob3,6)
	time.sleep(r)
	sys.exit(1)

def _makeOutput(img1,img2,trans,matrix,shift):
	invtrans  = linear_algebra.inverse(trans)
	invmatrix = linear_algebra.inverse(matrix)
	output1   = nd_image.affine_transform(img2, trans,    offset= shift, mode='constant', cval=0.0)
	output2   = nd_image.affine_transform(img1, invtrans, offset=-shift, mode='constant', cval=0.0)
	model1    = nd_image.affine_transform(img2, matrix,   offset= shift, mode='constant',cval=0.0)
	model2    = nd_image.affine_transform(img1, invmatrix,offset=-shift, mode='constant', cval=0.0)
	mask1   = output1 != 0.0
	mask2   = output2 != 0.0
	mmask1   = model1 != 0.0
	mmask2   = model2 != 0.0
	overlap1 = float(nd_image.sum(mmask1))/float(mmask1.shape[0]*mmask1.shape[1])
	overlap2 = float(nd_image.sum(mmask2))/float(mmask2.shape[0]*mmask2.shape[1])
	print "overlap1=",overlap1*100.0
	print "overlap2=",overlap2*100.0
	rho0    = apImage.correlationCoefficient(img1,img2)
	rhoOut1 = apImage.correlationCoefficient(img1,output1,mask1)
	rhoOut2 = apImage.correlationCoefficient(img2,output2,mask2)
	rhoMod1 = apImage.correlationCoefficient(img1,model1,mmask1)
	rhoMod2 = apImage.correlationCoefficient(img2,model2,mmask2)
	print "rho0    =",rho0
	print "rhoOut1 =",rhoOut1
	print "rhoOut2 =",rhoOut2
	print "rhoMod1 =",rhoMod1
	print "rhoMod2 =",rhoMod2
	apImage.arrayToJpeg(img1*mask1,"1imgdata1.jpg")
	apImage.arrayToJpeg(img2*mask2,"2imgdata2.jpg")
	#apImage.arrayToJpeg((imgdata1-output1)*mask1,"1diff1.jpg")
	#apImage.arrayToJpeg((imgdata2-output2)*mask2,"2diff2.jpg")
	#apImage.arrayToJpeg(mask,"mask.jpg")
	apImage.arrayToJpeg(output1*mask1,"1output1.jpg")
	apImage.arrayToJpeg(output2*mask2,"2output2.jpg")
	apImage.arrayToJpeg(model1*mmask1,"1model1.jpg")
	apImage.arrayToJpeg(model2*mmask2,"2model2.jpg")
	rhoDiff = (rhoMod1 + rhoMod2)/2.0 - rho0
	return rhoDiff**(0.1)

def _compareImages(img1,img2):
	minsize  = 50
	maxsize  = 250000
	blur     = 0
	sharp    = 0
	whtonblk = True
	blkonwht = True

	bigtrans1  = libCV.MatchImages(img1, img2, minsize, maxsize,\
		blur, sharp, whtonblk, blkonwht)
	bigtrans2 = libCV.MatchImages(img1, img2, 100, maxsize,\
		blur, sharp, whtonblk, blkonwht)

	bigtrans = (bigtrans1 + bigtrans2) / 2.0
	errmat   = (bigtrans1[:3,:2] - bigtrans2[:3,:2])/(abs(bigtrans[:3,:2])+5e-2)
	err      = nd_image.mean(errmat)
	prob     = math.exp(-1.0*abs(err))**2
	trans    = bigtrans[:2,:2]
	shift    = bigtrans[2,:2]
	return trans,shift,prob

def _diffMatrix(x,t0,t1):
	trans = numarray.array( [ [t0[0], t0[1]], [t1[0], t1[1]] ] )
	matrix = _rotMatrixRad(x[0],x[1])
	return nd_image.mean((matrix-trans)**2)
	
def _rotMatrixRad(tilt,twist):
	costwist = math.cos(twist)
	sintwist = math.sin(twist)
	tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, math.cos(tilt) ]])
	twistmat = numarray.array([[ costwist, -sintwist ], [ sintwist, costwist ]])
	#return numarray.matrixmultiply(tiltmat,twistmat)
	return numarray.matrixmultiply(twistmat,tiltmat)

def _rotMatrixDeg(tilt,twist):
	tilt2 = tilt/180.0*math.pi
	twist2 = twist/180.0*math.pi
	costwist = math.cos(twist2)
	sintwist = math.sin(twist2)
	tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, math.cos(tilt2) ]])
	twistmat = numarray.array([[ costwist, -sintwist ], [ sintwist, costwist ]])
	#return numarray.matrixmultiply(tiltmat,twistmat)
	return numarray.matrixmultiply(twistmat,tiltmat)

def _matrixToEulers(trans, tilt0=15.0, twist0=0.0):
	x0 = numarray.array([tilt0,twist0])*math.pi/180.0
	#trans = array([[1.00297072, -7.02714670e-03],[-9.42688432e-04, 0.966770461]])
	x1 = optimize.fmin(_diffMatrix,x0,args=(trans),xtol=0.001,ftol=0.1,maxiter=1000)
	tilt  = x1[0]*180.0/math.pi
	twist = x1[1]*180.0/math.pi
	err = _diffMatrix(x1,trans[0],trans[1])
	prob = math.exp(-1.0*math.sqrt(abs(err)))**2
	return tilt,twist,prob
	
