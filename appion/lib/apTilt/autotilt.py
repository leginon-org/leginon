#!/usr/bin/env python

import os
import sys
import time
import wx
import numpy
import threading
import particleLoop2
import apFindEM
import appionData
import apDatabase
import apDisplay
import apParticle
import apPeaks
import apImage
import apParam
import ApTiltPicker
from apTilt import apTiltTransform, apTiltPair, tiltfile

class autoTilt(object):
	#---------------------------------------
	#---------------------------------------
	def __init__(self):
		return

	#---------------------------------------
	#---------------------------------------
	def importPicks(self, picks1, picks2, tight=False):
		t0 = time.time()
		apDisplay.printMsg("import picks")
		#print picks1
		#print self.currentpicks1
		curpicks1 = numpy.asarray(self.currentpicks1)
		curpicks2 = numpy.asarray(self.currentpicks2)
		#print curpicks1

		# get picks
		apTiltTransform.setPointsFromArrays(curpicks1, curpicks2, self.data)
		pixdiam = self.params['diam']/self.params['apix']/self.params['bin']
		if tight is True:
			pixdiam /= 4.0
		#print self.data, pixdiam
		list1, list2 = apTiltTransform.alignPicks2(picks1, picks2, self.data, limit=pixdiam)
		if list1.shape[0] == 0 or list2.shape[0] == 0:
			apDisplay.printWarning("No new picks were found")

		# merge picks
		newpicks1, newpicks2 = apTiltTransform.betterMergePicks(curpicks1, list1, curpicks2, list2)
		newparts = newpicks1.shape[0] - curpicks1.shape[0]

		# copy over picks
		self.currentpicks1 = newpicks1
		self.currentpicks2 = newpicks2

		apDisplay.printMsg("Inserted "+str(newparts)+" new particles in "+apDisplay.timeString(time.time()-t0))

		return True

	#---------------------------------------
	#---------------------------------------
	def optimizeAngles(self):
		apDisplay.printMsg("optimize angles")
		t0 = time.time()
		if len(self.currentpicks1) < 5 or len(self.currentpicks2) < 5:
			apDisplay.printWarning("Not enough particles ot run program on image pair")
			return
		### run find theta
		na1 = numpy.array(self.currentpicks1, dtype=numpy.int32)
		na2 = numpy.array(self.currentpicks2, dtype=numpy.int32)
		fittheta = radermacher.tiltang(na1, na2, 5000.0)
		if fittheta and 'wtheta' in fittheta:
			theta = fittheta['wtheta']
			thetadev = fittheta['wthetadev']
			thetastr = ("%3.3f +/- %2.2f" % (theta, thetadev))
			tristr = apDisplay.orderOfMag(fittheta['numtri'])+" of "+apDisplay.orderOfMag(fittheta['tottri'])
			percent = str("%")
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
		cut = mean + 4.0 * stdev + 2.0
		return cut

	#---------------------------------------
	#---------------------------------------
	def clearBadPicks(self):
		apDisplay.printMsg("clear bad picks")
		a1 = self.currentpicks1
		a2 = self.currentpicks2
		origpicks = max(len(a1), len(a2))
		if len(a1) != len(a2):
			apDisplay.printMsg("uneven arrays, get rid of extra")
			#uneven arrays, get rid of extra
			self.currentpicks1 = a1[0:len(a2),:]
			self.currentpicks2 = a2[0:len(a1),:]
			return
		err = self.getRmsdArray()
		cut = self.getCutoffCriteria(err)
		a1c = []
		a2c = []
		maxerr = 4.0
		worst1 = []
		worst2 = []
		for i,e in enumerate(err):
			if i != 0 and e > maxerr:
				if len(worst1) > 0 and maxerr < cut:
					a1c.append(worst1)
					a2c.append(worst2)
				maxerr = e
				worst1 = a1[i,:]
				worst2 = a2[i,:]
			elif e < cut and (i == 0 or e > 0):
				#good picks
				a1c.append(a1[i,:])
				a2c.append(a2[i,:])
		a1d = numpy.asarray(a1c)
		a2d = numpy.asarray(a2c)
		self.currentpicks1 = a1d
		self.currentpicks2 = a2d
		newpicks = len(a1d)
		apDisplay.printMsg("removed "+str(origpicks-newpicks)+" particles")
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
	def getOverlap(self, image1, image2):
		t0 = time.time()
		apDisplay.printMsg("get overlap")
		bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, self.data)
		overlapStr = str(round(100*bestOverlap,2))+"% and "+str(round(100*tiltOverlap,2))+"%"
		apDisplay.printMsg("found overlaps of "+overlapStr+" in "+apDisplay.timeString(time.time()-t0))
		self.data['overlap'] = bestOverlap

	#---------------------------------------	
	def saveData(imgfile1, imgfile2, picks1, picks2, tiltangle, outfile):
		"""
		savedata = {}
		savedata['theta'] = self.data['theta']
		savedata['gamma'] = self.data['gamma']
		savedata['phi'] = self.data['phi']
		savedata['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
		savedata['filetype'] = tiltfile.filetypes[self.data['filetypeindex']]
		savedata['picks1'] = self.getArray1()
		savedata['picks2'] = self.getArray2()
		savedata['align1'] = self.getAlignedArray1()
		savedata['align2'] = self.getAlignedArray2()
		savedata['rmsd'] = self.getRmsdArray()
		savedata['image1name'] = self.panel1.filename
		savedata['image2name'] = self.panel2.filename
		"""
		savedata = {}		
		savedata['theta'] = self.data['theta']
		savedata['gamma'] = self.data['gamma']
		savedata['phi'] = self.data['phi']
		savedata['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
		savedata['picks1'] = self.currentpicks1
		savedata['picks2'] = self.currentpicks2
		savedata['align1'] = self.getAlignedArray1()
		savedata['align2'] = self.getAlignedArray2()
		savedata['rmsd'] = self.getRmsdArray()
		savedata['image1name'] = self.panel1.filename
		savedata['image2name'] = self.panel2.filename

		tiltfile.savedata(savedata, filename)

	#---------------------------------------
	#---------------------------------------
	def processTiltPair(self, imgfile1, imgfile2, picks1, picks2, tiltangle, outfile):
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
			apDisplay.printWarning("Not enough particles ot run program on image pair")
			return None

		### set tilt
		self.data['theta'] = tiltangle
		self.data['shiftx'] = 0.0
		self.data['shifty'] = 0.0
		self.data['scale'] = 1.0

		### open image file 1
		img1 = apImage.mrcToArray(imgfile1)

		### open tilt file 2
		img2 = apImage.mrcToArray(imgfile2)

		### guess the shift
		t0 = time.time()
		origin, newpart, snr, bestang = apTiltShift.getTiltedCoordinates(img1, img2, tiltangle, picks1, angsearch=True)
		self.data['gamma'] = float(bestang)
		self.data['phi'] = float(bestang)
		if snr < 2.0:
			apDisplay.printWarning("Low confidence in initial shift")
			self.badprocess = True
			return None
		self.currentpicks1 = [origin]
		self.currentpicks2 = [newpart]

		### search for the correct particles
		self.importPicks(picks1, picks2, tight=False)
		self.deleteFirstPick()
		for i in range(3):
			self.clearBadPicks()
			self.optimizeAngles()
			self.clearBadPicks()
			self.clearBadPicks()
			self.optimizeAngles()
			self.clearBadPicks()
			self.importPicks(picks1, picks2, tight=False)
		self.clearBadPicks()
		self.optimizeAngles()
		self.getOverlap(img1,img2)
		apDisplay.printMsg("completed alignment of "+str(len(self.currentpicks1))
			+" particle pairs in "+apDisplay.timeString(time.time()-t0))

		print self.data
		# 1. tilt data are copied to self.tiltparams by app
		# 2. particles picks are copied to self.peaks1 and self.peaks2 by app
		# 3. particle errors are copied to self.peakerrors by app
		# 4. assessment status is  copied to self.assess
		self.peaktree1 = apPeaks.convertListToPeaks(self.currentpicks1, self.params)
		self.peaktree2 = apPeaks.convertListToPeaks(self.currentpicks2, self.params)
		self.peakerrors = self.getRmsdArray()



