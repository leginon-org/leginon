#Part of the new pyappion

import sys,os,re
import time
import random
import math
import apImage,apParticle,apDatabase,apDisplay
import libCV
import apLoop
import numarray
import numarray.nd_image as nd_image
import numarray.linear_algebra as linear_algebra
import numarray.random_array as random_array
import scipy.optimize as optimize

def process(img1,img2,params):
	name =os.path.join("jpgs",os.path.basename(img1['filename']))
	name = re.sub("0[01]_000(?P<id>[0-9][0-9]en)_0[01]","\g<id>",name)
	name = re.sub("_0+","_",name)
	name = re.sub("_v0[0-9]","",name)
	tilt1 = apDatabase.getTiltAngle(img1,params)
	tilt2 = apDatabase.getTiltAngle(img2,params)
	dtilt = abs(tilt1 - tilt2)
	#print "TILT1=",tilt1
	#print "TILT2=",tilt2
	print "total tilt angle=",round(dtilt,4)
	r = random.uniform(0,0.5)
	apix = params['apix']
	#print "sleeping ",r
	#time.sleep(r)
	noise = 0.0
	immult = 1.5

	blank1 = numarray.zeros(img1['image'].shape)
	particles,shift = apParticle.getParticles(img1,params)
	numpart1 = len(particles)
	if numpart1 == 0:
		return
	print "found",numpart1,"particles for image1"
	for prtl in particles:
		x0=int(prtl['ycoord']+0.5)
		y0=int(prtl['xcoord']+0.5)
		blank1[x0][y0] = 2.0*prtl['correlation']
	blank1 = apImage.preProcessImage(blank1,bin=4,lowpass=params['diam'],apix=apix)
	#apImage.arrayToJpeg(blank1,name+"-realblank1.jpg")
	blank1 += immult*apImage.preProcessImage(img1['image'],bin=4,lowpass=40,apix=apix)
	blank1 += random_array.uniform(0.0, noise, shape=blank1.shape)
	apImage.arrayToJpeg(blank1,name+"-blank1.jpg")

	blank2 = numarray.zeros(img2['image'].shape)
	particles,shift = apParticle.getParticles(img2,params)
	numpart2 = len(particles)
	if numpart2 == 0:
		return
	print "found",numpart2,"particles for image2"
	for prtl in particles:
		x0=int(prtl['ycoord']+0.5)
		y0=int(prtl['xcoord']+0.5)
		blank2[x0][y0] = 2.0*prtl['correlation']
	blank2 = apImage.preProcessImage(blank2,bin=4,lowpass=params['diam'],apix=apix)
	blank2 += immult*apImage.preProcessImage(img2['image'],bin=4,lowpass=40,apix=apix)
	blank2 += random_array.uniform(0.0, noise, shape=blank2.shape)
	apImage.arrayToJpeg(blank2,name+"-blank2.jpg")

	prob7 = 1.0-(numpart1**-1.0 + numpart2**-1.0)*5.0
	if(prob7 < 0): prob7 = 0
	print "*** number particles (7)=",apDisplay.colorProb(prob7)

	#blank1 = apImage.lowPassFilter(blank1,apix=1.0,bin=1,radius=10.0)


	#imgdata1 = apImage.preProcessImage(blank1['image'],bin=4,lowpass=10,apix=apix)
	#imgdata2 = apImage.preProcessImage(img2['image'],bin=4,lowpass=10,apix=apix)
	trans,shift,prob1,prob8 = _compareImages(blank1,blank2,dtilt,params['binpixdiam'])
	print "TRANS=\n",numarray.around(trans,3)
	print "SHIFT=",numarray.around(shift,3)
	print "*** separa libcv prob(1)=",apDisplay.colorProb(prob1)
	print "*** good libcv r prob(8)=",apDisplay.colorProb(prob8)
	tilt,twist,scale,prob2 = _matrixToEulers(trans)
	perdiff = abs(abs(tilt)-dtilt)/dtilt
	prob5 = math.exp(-1.0*perdiff)
	prob6 = math.exp(-1.0*(twist/10.0)**2)

	matrix  = _rotMatrixDeg(tilt,twist,scale)
	print "tilt=",round(tilt,2),"("+\
		str(round(dtilt,1))+") twist=",round(twist,6)," scale=",round(scale,6)
	print "*** correct tilt prob(5)=",apDisplay.colorProb(prob5)
	print "*** corrct twist prob(6)=",apDisplay.colorProb(prob6)
	print "*** matrix fit prob (2) =",apDisplay.colorProb(prob2)
	prob3,prob4 = _makeOutput(blank1,blank2,trans,matrix,shift,name)
	print "*** better align prob(3)=",apDisplay.colorProb(prob3)
	print "*** good overlap prob(4)=",apDisplay.colorProb(prob4)

	totprob = prob1*prob2*prob3*prob4*prob5*prob6*prob7*prob8
	totprob = math.sqrt(totprob)
	print "\nTOTAL PROB = ",apDisplay.colorProb(totprob)
	#time.sleep(r)
	outfile=params['runid']+".dat"
	f = open(outfile,"a")
	f.write(name+" \t"+str(round(totprob,4)))
	for p in prob1,prob2,prob3,prob4,prob5,prob6,prob7,prob8:
		f.write("\t"+str(round(p,4)))
	f.write("\ttilt ="+str(round(tilt,4)))
	f.write("\ttwist="+str(round(twist,4)))
	f.write("\tscale="+str(round(scale,4)))
	f.write("\n")
	f.close()
	#sys.exit(1)

def _makeOutput(img1,img2,trans,matrix,shift,name):
	"""
	create JPEG output for two images (img1, img2) and trnasformation matrices
	"""
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
	if overlap1 > 0 and overlap2 > 0:
		prob4 = math.sqrt(overlap1*overlap2)
	else:
		prob4 = 0.0
	#print "overlap1=",overlap1*100.0
	#print "overlap2=",overlap2*100.0
	rho0    = apImage.correlationCoefficient(img1,img2)
	#rhoOut1 = apImage.correlationCoefficient(img1,output1,mask1)
	#rhoOut2 = apImage.correlationCoefficient(img2,output2,mask2)
	rhoMod1 = apImage.correlationCoefficient(img1,model1,mmask1)
	rhoMod2 = apImage.correlationCoefficient(img2,model2,mmask2)
	#print "rho0    =",rho0
	#print "rhoOut1 =",rhoOut1
	#print "rhoOut2 =",rhoOut2
	#print "rhoMod1 =",rhoMod1
	#print "rhoMod2 =",rhoMod2
	apImage.arrayToJpeg(img1*mmask1,name+"-1imgdata1.jpg")
	apImage.arrayToJpeg(img2*mmask2,name+"-2imgdata2.jpg")
	#apImage.arrayToJpeg((imgdata1-output1)*mask1,"1diff1.jpg")
	#apImage.arrayToJpeg((imgdata2-output2)*mask2,"2diff2.jpg")
	#apImage.arrayToJpeg(mask,"mask.jpg")
	apImage.arrayToJpeg(output1*mask1,name+"-1output1.jpg")
	apImage.arrayToJpeg(output2*mask2,name+"-2output2.jpg")
	apImage.arrayToJpeg(model1*mmask1,name+"-1model1.jpg")
	apImage.arrayToJpeg(model2*mmask2,name+"-2model2.jpg")
	rhoDiff = (rhoMod1 + rhoMod2)/2.0 - rho0 + 0.5
	if rhoDiff <= 0:
		return 0.0,prob4
	return math.sqrt(rhoDiff),prob4

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

def _rotMatrixRad(tilt,twist=0.0,scale=1.0):
	"""
	creates the tilt rotation matrix with radians
	"""
	costwist = math.cos(twist)
	sintwist = math.sin(twist)
	tiltmat  = numarray.array([[ 1.0, 0.0 ], [ 0.0, math.cos(tilt) ]])
	twistmat = numarray.array([[ costwist, -sintwist ], [ sintwist, costwist ]])
	scalemat = numarray.array([[ scale, 0.0 ], [ 0.0, scale ]])
	#return numarray.matrixmultiply(tiltmat,twistmat)
	return numarray.matrixmultiply(numarray.matrixmultiply(twistmat,tiltmat),scalemat)

def _rotMatrixDeg(tilt,twist=0.0,scale=1.0):
	"""
	creates the tilt rotation matrix with degrees
	"""
	tilt2 = tilt/180.0*math.pi
	twist2 = twist/180.0*math.pi
	return _rotMatrixRad(tilt2,twist2,scale)


def _matrixToEulers(trans, tilt0=15.0, twist0=0.0, scale0=1.0):
	"""
	given a matrix (trans), find the tilt, twist, and scale of that matrix
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
