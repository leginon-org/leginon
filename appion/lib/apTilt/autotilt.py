#!/usr/bin/env python

#python
import os
import sys
import time
import wx
import numpy
import threading
import Image
from pyami import quietscipy
from scipy import ndimage, optimize
#appion
import apDisplay
import apPeaks
import apImage
import apParam
from apTilt import apTiltTransform, apTiltShift, apTiltPair, tiltfile
try:
	import radermacher
except:
	print "using slow tilt angle calculator"
	import slowmacher as radermacher

class autoTilt(object):
	#---------------------------------------
	#---------------------------------------
	def __init__(self):
		self.data = {}
		return

	#---------------------------------------
	#---------------------------------------
	def importPicks(self, picks1, picks2, tight=False, msg=True):
		t0 = time.time()
		#print picks1
		#print self.currentpicks1
		curpicks1 = numpy.asarray(self.currentpicks1)
		curpicks2 = numpy.asarray(self.currentpicks2)
		#print curpicks1

		# get picks
		apTiltTransform.setPointsFromArrays(curpicks1, curpicks2, self.data)
		pixdiam = self.data['pixdiam']
		if tight is True:
			pixdiam /= 4.0
		#print self.data, pixdiam
		list1, list2 = apTiltTransform.alignPicks2(picks1, picks2, self.data, limit=pixdiam, msg=msg)
		if list1.shape[0] == 0 or list2.shape[0] == 0:
			apDisplay.printWarning("No new picks were found")

		# merge picks
		newpicks1, newpicks2 = apTiltTransform.betterMergePicks(curpicks1, list1, curpicks2, list2, msg=msg)
		newparts = newpicks1.shape[0] - curpicks1.shape[0]

		# copy over picks
		self.currentpicks1 = newpicks1
		self.currentpicks2 = newpicks2

		if msg is True:
			apDisplay.printMsg("Inserted "+str(newparts)+" new particles in "+apDisplay.timeString(time.time()-t0))

		return True

	#---------------------------------------
	#---------------------------------------
	def optimizeAngles(self, msg=True):
		t0 = time.time()
		### run find theta
		na1 = numpy.array(self.currentpicks1, dtype=numpy.int32)
		na2 = numpy.array(self.currentpicks2, dtype=numpy.int32)
		fittheta = radermacher.tiltang(na1, na2, 5000.0)
		if fittheta and 'wtheta' in fittheta:
			theta = fittheta['wtheta']
			thetadev = fittheta['wthetadev']
			if msg is True:
				thetastr = ("%3.3f +/- %2.2f" % (theta, thetadev))
				tristr = apDisplay.orderOfMag(fittheta['numtri'])+" of "+apDisplay.orderOfMag(fittheta['tottri'])
				tristr = (" (%3.1f " % (100.0 * fittheta['numtri'] / float(fittheta['tottri'])))+"%) "
				apDisplay.printMsg("Tilt angle "+thetastr+tristr)
			self.data['theta'] = fittheta['wtheta']
		### run optimize angles
		lastiter = [80,80,80]
		count = 0
		totaliter = 0
		while max(lastiter) > 75 and count < 30:
			count += 1
			lsfit = self.runLeastSquares()
			lastiter[2] = lastiter[1]
			lastiter[1] = lastiter[0]
			lastiter[0] = lsfit['iter']
			totaliter += lsfit['iter']
			if msg is True:
				apDisplay.printMsg("Least Squares: "+str(count)+" rounds, "+str(totaliter)
				+" iters, rmsd of "+str(round(lsfit['rmsd'],4))+" pixels in "+apDisplay.timeString(time.time()-t0))
		return

	#---------------------------------------
	#---------------------------------------
	def runLeastSquares(self):
		#SET XSCALE
		xscale = numpy.array((1,1,1,0,1,1), dtype=numpy.float32)
		#GET TARGETS
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		if len(a1) > len(a2):
			print "shorten a1"
			a1 = a1[0:len(a2),:]
		elif len(a2) > len(a1):
			print "shorten a2"
			a2 = a2[0:len(a1),:]
		lsfit = apTiltTransform.willsq(a1, a2, self.data['theta'], self.data['gamma'],
			self.data['phi'], 1.0, self.data['shiftx'], self.data['shifty'], xscale)
		if lsfit['rmsd'] < 30:
			self.data['theta']  = lsfit['theta']
			self.data['gamma']  = lsfit['gamma']
			self.data['phi']    = lsfit['phi']
			self.data['shiftx'] = lsfit['shiftx']
			self.data['shifty']	= lsfit['shifty']
		return lsfit

	#---------------------------------------
	#---------------------------------------
	def getRmsdArray(self):
		targets1 = self.currentpicks1
		aligned1 = self.getAlignedArray2()
		if len(targets1) != len(aligned1):
			targets1 = numpy.vstack((targets1, aligned1[len(targets1):]))
			aligned1 = numpy.vstack((aligned1, targets1[len(aligned1):]))
		diffmat1 = (targets1 - aligned1)
		sqsum1 = diffmat1[:,0]**2 + diffmat1[:,1]**2
		rmsd1 = numpy.sqrt(sqsum1)
		return rmsd1

	#---------------------------------------
	#---------------------------------------
	def getAlignedArray2(self):
		apTiltTransform.setPointsFromArrays(self.currentpicks1, self.currentpicks2, self.data)
		a2b = apTiltTransform.a2Toa1Data(self.currentpicks2, self.data)
		return a2b

	#---------------------------------------
	#---------------------------------------
	def getAlignedArray1(self):
		apTiltTransform.setPointsFromArrays(self.currentpicks1, self.currentpicks2, self.data)
		a1b = apTiltTransform.a1Toa2Data(self.currentpicks1, self.data)
		return a1b

	#---------------------------------------
	#---------------------------------------
	def getCutoffCriteria(self, errorArray):
		#do a small minimum filter to  get rid of outliers
		size = int(len(errorArray)**0.3)+1
		errorArray2 = ndimage.minimum_filter(errorArray, size=size, mode='wrap')
		mean = ndimage.mean(errorArray2)
		stdev = ndimage.standard_deviation(errorArray2)
		### this is so arbitrary
		cut = mean + 5.0 * stdev + 2.0
		### anything bigger than 20 pixels is too big
		if cut > self.data['pixdiam']:
			cut = self.data['pixdiam']
		return cut


	#---------------------------------------
	#---------------------------------------
	def clearBadPicks(self, msg=True):
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		origpicks = max(len(a1), len(a2))
		if len(a1) != len(a2):
			if msg is True:
				apDisplay.printMsg("uneven arrays, get rid of extra")
			self.currentpicks1 = a1[0:len(a2),:]
			self.currentpicks2 = a2[0:len(a1),:]
			return (a1b, a2b)
		err = self.getRmsdArray()
		cut = self.getCutoffCriteria(err)
		a1c = []
		a2c = []
		minworsterr = 3.0
		### always set 5% as bad if cutoff > max rmsd
		worst1 = []
		worst2 = []
		worsterr = []
		numbad = int(len(a1)*0.05 + 1.0)
		for i,e in enumerate(err):
			if e > minworsterr:
				### find the worst overall picks
				if len(worst1) >= numbad and minworsterr < cut:
					j = numpy.argmax(numpy.asarray(worsterr))
					### take previous worst pick and make it good
					a1c.append(worst1[j])
					a2c.append(worst2[j])
					worst1[j] = a1[i,:]
					worst2[j] = a2[i,:]
					worsterr[j] = e
				else:
					### add the worst pick
					worst1.append(a1[i,:])
					worst2.append(a2[i,:])
					worsterr.append(e)
				### increase the min worst err
				if e > minworsterr:
					minworsterr = e
			elif e < cut and (i == 0 or e > 0):
				### this is a good pick
				a1c.append(a1[i,:])
				a2c.append(a2[i,:])
		if len(a1c) == 0:
			a1c.append(a1[0,:])
			a2c.append(a2[0,:])
		a1d = numpy.asarray(a1c)
		a2d = numpy.asarray(a2c)
		self.currentpicks1 = a1d
		self.currentpicks2 = a2d
		newpicks = len(a1d)
		if msg is True:
			apDisplay.printMsg("Removed "+str(origpicks-newpicks)+" bad particles")
		return

	#---------------------------------------
	#---------------------------------------
	def deleteFirstPick(self):
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		a1b = a1[1:]
		a2b = a2[1:]
		self.currentpicks1 = a1b
		self.currentpicks2 = a2b

	#---------------------------------------
	#---------------------------------------
	def getOverlap(self, image1, image2, msg=True):
		t0 = time.time()
		bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, self.data)
		overlapStr = str(round(100*bestOverlap,2))+"% and "+str(round(100*tiltOverlap,2))+"%"
		if msg is True:
			apDisplay.printMsg("Found overlaps of "+overlapStr+" in "+apDisplay.timeString(time.time()-t0))
		self.data['overlap'] = bestOverlap

	#---------------------------------------
	#---------------------------------------
	def saveData(self, imgfile1, imgfile2, outfile):
		savedata = {}
		savedata['theta'] = self.data['theta']
		savedata['gamma'] = self.data['gamma']
		savedata['phi'] = self.data['phi']
		savedata['picks1'] = self.currentpicks1
		savedata['picks2'] = self.currentpicks2
		savedata['align1'] = self.getAlignedArray1()
		savedata['align2'] = self.getAlignedArray2()
		savedata['rmsd'] = self.getRmsdArray()
		savedata['image1name'] = imgfile1
		savedata['image2name'] = imgfile2
		#savedata['filetype'] = tiltfile.filetypes[self.data['filetypeindex']]

		tiltfile.saveData(savedata, outfile)

	#---------------------------------------
	#---------------------------------------
	def openImageFile(self, filename):
		self.filename = filename
		if filename[-4:] == '.spi':
			array = apImage.spiderToArray(filename, msg=False)
			return array
		elif filename[-4:] == '.mrc':
			array = apImage.mrcToArray(filename, msg=False)
			return array
		else:
			image = Image.open(filename)
			array = apImage.imageToArray(image, msg=False)
			array = array.astype(numpy.float32)
			return array
		return None

	#---------------------------------------
	#---------------------------------------
	def printData(self, msg):
		if msg is False:
			return
		mystr = ( "theta=%.3f, gamma=%.3f, phi=%.3f, rmsd=%.4f, shifts=%.1f,%.1f, numpoints=%d,%d"
			%(self.data['theta'],self.data['gamma'],self.data['phi'],self.getRmsdArray().mean(),
			self.data['shiftx'],self.data['shifty'],len(self.currentpicks1),len(self.currentpicks2),
			))
		apDisplay.printColor(mystr, "green") 

	#---------------------------------------
	#---------------------------------------
	def processTiltPair(self, imgfile1, imgfile2, picks1, picks2, tiltangle, outfile, pixdiam=20.0, tiltaxis=-7.0, msg=True):
		"""
		Inputs:
			imgfile1
			imgfile2
			picks1, 2xN numpy array
			picks2, 2xN numpy array
			tiltangle
			outfile
		Modifies:
			outfile
		Output:
			None, failed
			True, success
		"""

		### pre-load particle picks
		if len(picks1) < 10 or len(picks2) < 10:
			if msg is True:
				apDisplay.printWarning("Not enough particles ot run program on image pair")
			return None

		### setup tilt data
		self.data['theta'] = tiltangle
		self.data['shiftx'] = 0.0
		self.data['shifty'] = 0.0
		self.data['gamma'] = tiltaxis
		self.data['phi'] = tiltaxis
		self.data['scale'] = 1.0
		self.data['pixdiam'] = pixdiam

		### open image file 1
		img1 = self.openImageFile(imgfile1)
		if img1 is None:
			apDisplay.printWarning("Could not read image: "+imgfile1)
			return None

		### open tilt file 2
		img2 = self.openImageFile(imgfile2)
		if img1 is None:
			apDisplay.printWarning("Could not read image: "+imgfile1)
			return None

		### guess the shift
		t0 = time.time()
		if msg is True:
			apDisplay.printMsg("Refining tilt axis angles")
		origin, newpart, snr, bestang = apTiltShift.getTiltedCoordinates(img1, img2, tiltangle, picks1, True, tiltaxis, msg=msg)
		self.data['gamma'] = float(bestang)
		self.data['phi'] = float(bestang)
		if snr < 2.0:
			if msg is True:
				apDisplay.printWarning("Low confidence in initial shift")
			return None
		self.currentpicks1 = [origin]
		self.currentpicks2 = [newpart]

		### search for the correct particles
		self.importPicks(picks1, picks2, tight=False, msg=msg)
		if len(self.currentpicks1) < 4:
			apDisplay.printWarning("Failed to find any particle matches")
			return None		
		self.deleteFirstPick()
		self.printData(msg)
		for i in range(3):
			self.clearBadPicks(msg)
			if len(self.currentpicks1) < 5 or len(self.currentpicks2) < 5:
				if msg is True:
					apDisplay.printWarning("Not enough particles to optimize angles")
				return None
			self.optimizeAngles(msg)
			self.printData(msg)
			self.clearBadPicks(msg)
			self.clearBadPicks(msg)
			if len(self.currentpicks1) < 5 or len(self.currentpicks2) < 5:
				if msg is True:
					apDisplay.printWarning("Not enough particles to optimize angles")
				return None
			self.optimizeAngles(msg)
			self.printData(msg)
			self.clearBadPicks(msg)
			self.importPicks(picks1, picks2, tight=False, msg=msg)
		self.clearBadPicks(msg)
		self.printData(msg)
		if len(self.currentpicks1) < 5 or len(self.currentpicks2) < 5:
			if msg is True:
				apDisplay.printWarning("Not enough particles to optimize angles")
			return None
		self.optimizeAngles(msg)
		self.printData(msg)
		self.getOverlap(img1,img2,msg)
		if msg is True:
			apDisplay.printMsg("Completed alignment of "+str(len(self.currentpicks1))
				+" particle pairs in "+apDisplay.timeString(time.time()-t0))

		self.saveData(imgfile1, imgfile2, outfile)
		self.printData(msg)

		return True



