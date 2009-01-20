import math
import sys
import time
#PIL
import ImageDraw
#scipy
import numpy
from scipy import optimize, ndimage, misc
#appion
import apImage
import apDisplay
import apDog
#pyami
from pyami import peakfinder
from pyami import correlator

#================================
#================================
def getTiltedCoordinates(img1, img2, tiltdiff, picks1=[], angsearch=True, inittiltaxis=-7.2, msg=True):
	"""
	takes two images tilted 
	with respect to one another 
	and tries to find overlap
	
	img1 (as numpy array)
	img2 (as numpy array)
	tiltdiff (in degrees)
		negative, img1 is more compressed (tilted)
		positive, img2 is more compressed (tilted)
	picks1, list of particles picks for image 1
	"""
	t0 = time.time()
	#shrink images
	bin = 2
	binned1 = apImage.binImg(img1, bin)
	binned2 = apImage.binImg(img2, bin)
	#apImage.arrayToJpeg(binned1, "binned1.jpg")
	#apImage.arrayToJpeg(binned2, "binned2.jpg")
	filt1 = apImage.highPassFilter(binned1, apix=1.0, radius=20.0, localbin=4/bin)
	filt2 = apImage.highPassFilter(binned2, apix=1.0, radius=20.0, localbin=4/bin)
	#apImage.arrayToJpeg(filt1, "filt1.jpg")
	#apImage.arrayToJpeg(filt2, "filt2.jpg")

	if angsearch is True:
		bestsnr = 0
		bestangle = None
		### rough refine
		#for angle in [-6, -4, -2,]:
		#	sys.stderr.write(".")
		#	shift, xfactor, snr = getTiltedRotateShift(filt1, filt2, tiltdiff, angle, bin, msg=False)
		#	if snr > bestsnr:	
		#		bestsnr = snr
		#		bestangle = angle
		bestangle = inittiltaxis
		if msg is True:
			print "best=", bestsnr, bestangle
		### finer refine
		for angle in [bestangle-1, bestangle-0.5, bestangle+0.5, bestangle+1]:
			if msg is True:
				sys.stderr.write(".")
			shift, xfactor, snr = getTiltedRotateShift(filt1, filt2, tiltdiff, angle, bin, msg=False)
			if snr > bestsnr:	
				bestsnr = snr
				bestangle = angle
		if msg is True:
			print "best=", bestsnr, bestangle
		### really fine refine
		for angle in [bestangle-0.2, bestangle-0.1, bestangle+0.1, bestangle+0.2]:
			if msg is True:
				sys.stderr.write(".")
			shift, xfactor, snr = getTiltedRotateShift(filt1, filt2, tiltdiff, angle, bin, msg=False)
			if snr > bestsnr:	
				bestsnr = snr
				bestangle = angle
		if msg is True:
			print "best=", bestsnr, bestangle

		shift, xfactor, snr = getTiltedRotateShift(filt1, filt2, tiltdiff, bestangle, bin, msg=msg)
		if msg is True:
			print "best=", bestsnr, bestangle
	else:
		bestangle = 0.0
		shift, xfactor, snr = getTiltedRotateShift(img1, img2, tiltdiff, bestangle, bin)

	if msg and min(abs(shift)) < min(img1.shape)/16.0:
		apDisplay.printWarning("Overlap was too close to the edge and possibly wrong.")

	### case 1: find tilted center of first image
	center = numpy.asarray(img1.shape)/2.0
	newpoint = translatePoint(center, center, shift, bestangle, xfactor)
	#print "newpoint=", newpoint
	halfsh = (center + newpoint)/2.0
	origin = halfsh

	### case 2: using a list of picks
	if len(picks1) > 1:
		#get center most pick
		dmin = origin[0]/2.0
		for pick in picks1:
			da = numpy.hypot(pick[0]-halfsh[0], pick[1]-halfsh[1])
			if da < dmin:
				dmin = da
				origin = pick

	# origin is pick from image 1
	# newpart is pick from image 2
	newpart = translatePoint(origin, center, shift, bestangle, xfactor)
	newpart2 = numpy.array([(origin[0]*xfactor-shift[0])*xfactor, origin[1]-shift[1]])
	if msg is True:
		print "origin=",origin, "; newpart=",newpart, "; newpart2=",newpart2
		apDisplay.printMsg("completed in "+apDisplay.timeString(time.time()-t0))

	return origin, newpart, snr, bestangle

	### check to make sure points are not off the edge
	while newpart[0] < 10:
		newpart += numpy.asarray((20,0))
		origin += numpy.asarray((20,0))
	while newpart[1] < 10:
		newpart += numpy.asarray((0,20))
		origin += numpy.asarray((0,20))
	while newpart[0] > img1.shape[0]-10:
		newpart -= numpy.asarray((20,0))
		origin -= numpy.asarray((20,0))
	while newpart[1] > img1.shape[1]-10:
		newpart -= numpy.asarray((0,20))
		origin -= numpy.asarray((0,20))

	return origin, newpart

#================================
#================================
def translatePoint(point, center, shift, tiltaxis, xf):
	### take a point in image1 space;
	#p1 : x[206,444];
	### translate point to cc-space: rotate about center then compress;
	#tp1 : tran[xf] . ( rot[-phi] . (p1 - half) + half );
	### apply xy shift;
	#tp2 : tp1 - xyshift;
	### translate point to image2 space: expand then rotate about center;
	#p2 : rot[phi] . (tran[xf] . tp2  - half) + half;
	(a, b) = point
	(hx, hy) = center
	(sx, sy) = shift
	ang = tiltaxis*math.pi/180.0
	p1 = ( ((hy-b)*math.cos(ang)*math.sin(ang) + (a-hx)*math.cos(ang)**2 + hx*math.cos(ang))*xf**2 
			- math.cos(ang)*sx*xf - math.sin(ang)*sy + (a - hx)*math.sin(ang)**2 
			+ (b - hy)*math.cos(ang)*math.sin(ang) - hx*math.cos(ang) + hx )
	p2 = ( ((b - hy)*math.sin(ang)**2 + ((hx - a)*math.cos(ang) - hx)*math.sin(ang))*xf**2 
			+ math.sin(ang)*sx*xf - math.cos(ang)*sy + ((a - hx)*math.cos(ang) + hx)*math.sin(ang) 
			+ (b - hy)*math.cos(ang)**2 + hy )
	return (p1,p2)

#================================
#================================
def getTiltedRotateShift(img1, img2, tiltdiff, angle=0, bin=1, msg=True):
	"""
	takes two images tilted 
	with respect to one another 
	and tries to find overlap
	
	img1 (as numpy array)
	img2 (as numpy array)
	tiltdiff (in degrees)
		negative, img1 is more compressed (tilted)
		positive, img2 is more compressed (tilted)
	"""

	### untilt images by stretching and compressing
	# choose angle s/t compressFactor = 1/stretchFactor
	# this only works if one image is untilted (RCT) of both images are opposite tilt (OTR)
	#halftilt = abs(tiltdiff)/2.0
	halftiltrad = math.acos(math.sqrt(math.cos(abs(tiltdiff)/180.0*math.pi)))
	# go from zero tilt to half tilt
	compressFactor = math.cos(halftiltrad)
	# go from max tilt to half tilt
	stretchFactor = math.cos(halftiltrad) / math.cos(abs(tiltdiff)/180.0*math.pi)
	if tiltdiff > 0:
		if msg is True:
			apDisplay.printMsg("compress image 1")
		untilt1 = transformImage(img1, compressFactor, angle)
		untilt2 = transformImage(img2, stretchFactor, angle)
		xfactor = compressFactor
	else:
		if msg is True:
			apDisplay.printMsg("stretch image 1")
		untilt1 = transformImage(img1, stretchFactor, angle)
		untilt2 = transformImage(img2, compressFactor, angle)
		xfactor = stretchFactor

	### filtering was done earlier
	filt1 = untilt1
	filt2 = untilt2

	if filt1.shape != filt2.shape:
		newshape = ( max(filt1.shape[0],filt2.shape[0]), max(filt1.shape[1],filt2.shape[1]) )
		print "Resizing images to: ",newshape
		filt1 = apImage.frame_constant(filt1, newshape, filt1.mean())
		filt2 = apImage.frame_constant(filt2, newshape, filt2.mean())

	### cross-correlate
	cc = correlator.cross_correlate(filt1, filt2, pad=True)
	rad = min(cc.shape)/20.0
	cc = apImage.highPassFilter(cc, radius=rad)
	cc = apImage.normRange(cc)
	cc = blackEdges(cc)
	cc = apImage.normRange(cc)
	cc = blackEdges(cc)
	cc = apImage.normRange(cc)
	cc = apImage.lowPassFilter(cc, radius=10.0)

	#find peak
	peakdict = peakfinder.findSubpixelPeak(cc, lpf=0)
	#import pprint
	#pprint.pprint(peak)
	pixpeak = peakdict['subpixel peak']
	if msg is True:
		print pixpeak
		apImage.arrayToJpegPlusPeak(cc, "guess-cross-ang"+str(abs(angle))+".jpg", pixpeak)

	rawpeak = numpy.array([pixpeak[1], pixpeak[0]]) #swap coord
	shift = numpy.asarray(correlator.wrap_coord(rawpeak, cc.shape))*bin

	if msg is True:
		apDisplay.printMsg("Found xy-shift btw two images"
			+";\n\t SNR= "+str(round(peakdict['snr'],2))
			+";\n\t halftilt= "+str(round(halftiltrad*180/math.pi, 3))
			+";\n\t compressFactor= "+str(round(compressFactor, 3))
			+";\n\t stretchFactor= "+str(round(stretchFactor, 3))
			+";\n\t xFactor= "+str(round(xfactor, 3))
			+";\n\t rawpeak= "+str(numpy.around(rawpeak*bin, 1))
			+";\n\t shift= "+str(numpy.around(shift, 1))
		)

	return shift, xfactor, peakdict['snr']

#================================
#================================
def blackEdges(img, rad=None, black=None):
	shape = img.shape
	if rad is None:
		rad = min(shape)/64.0
	if black is None:
		black = ndimage.minimum(img[int(rad/2.0):int(shape[0]-rad/2.0), int(rad/2.0):int(shape[1]-rad/2.0)])
	img2 = img
	edgesize = 2
	#left edge
	img2[0:edgesize, 0:shape[1]] = black
	#right edge
	img2[int(shape[0]-edgesize):shape[0], 0:shape[1]] = black
	#top edge
	img2[0:shape[0], 0:edgesize] = black
	#bottom edge
	img2[0:shape[0], int(shape[1]-edgesize):shape[1]] = black
	#top-left corner
	img2[0:int(rad/2.0), 0:int(rad/2.0)] = black
	#bottom-left corner
	img2[int(shape[0]-rad/2.0):shape[0], 0:int(rad/2.0)] = black
	#top-right corner
	img2[0:int(rad/2.0), int(shape[1]-rad/2.0):shape[1]] = black
	#bottom-right corner
	img2[int(shape[0]-rad/2.0):shape[0], int(shape[1]-rad/2.0):shape[1]] = black
	#vertical bar
	img2[int(shape[0]/2.0-rad):int(shape[0]/2.0+rad),0:shape[1]] = black
	#horizontal bar
	img2[0:shape[0],int(shape[1]/2.0-rad):int(shape[1]/2.0+rad)] = black
	return img2

#================================
#================================
def transformImage(img, xfactor, angle=0, msg=False):
	"""
	rotates then stretches or compresses an image only along the x-axis
	"""
	if xfactor > 1.0:
		mystr = "_S"
	else:
		mystr = "_C"

	if msg is True:
		if xfactor > 1:
			apDisplay.printMsg("stretching image by "+str(round(xfactor,3)))
		else:
			apDisplay.printMsg("compressing image by "+str(round(xfactor,3)))
	### image has swapped coordinates (y,x) from particles
	transMat = numpy.array([[ 1.0, 0.0 ], [ 0.0, 1.0/xfactor ]])
	#print "transMat\n",transMat
	#apImage.arrayToJpeg(img, "img"+mystr+".jpg")

	stepimg  = ndimage.rotate(img, -1.0*angle, mode='reflect')
	stepimg = apImage.frame_cut(stepimg, img.shape)
	#apImage.arrayToJpeg(stepimg, "rotate"+mystr+".jpg")

	newimg  = ndimage.affine_transform(stepimg, transMat, mode='reflect')
	#apImage.arrayToJpeg(newimg, "last_transform"+mystr+".jpg")

	return newimg







