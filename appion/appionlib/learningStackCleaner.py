#!/usr/bin/env python

import os
import wx
import sys
import time
import math
import numpy
import random
import scipy.stats
from pyami import imagefun
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apImagicFile
from appionlib.apImage import imageprocess
from appionlib.apImage import imagenorm
from appionlib.apCtf import ctftools
from sklearn import svm
from sklearn import decomposition

### TODO
# save/load particle data to file
# add button to clear decisions
# sort discrepancies, better sorting
# create web launcher
# work with larger stack
# auto update particles on change of clipping
# allow users to select what is input to dimension reducer:
#	input options: convolution filters
# allow users to choose system of dimension reducer (PCA, straight)
# allow users to choose system of classifier (SVm, CNN)

#=========================
class PCA(object):
	#---------------
	def __init__( self, data, n_components=20, pcaType='complete'):
		"""
		data = 2D array: rows of 1D images, columns of pixels
		n_components = number of components to keep
		"""
		t0 = time.time()
		self.n_components = n_components
		# calculate the covariance matrix
		#self.pca = decomposition.KernelPCA(n_components=n_components, kernel='rbf') #our data does not with this
		if pcaType.lower().startswith('complete'):
			print("using complete PCA")
			self.pca = decomposition.PCA(n_components=n_components, whiten=True)
		elif pcaType.lower().startswith('random'):
			print("using randomized PCA")
			self.pca = decomposition.RandomizedPCA(n_components=n_components, whiten=True)
		print("performing principal component analysis (pca)")
		try:
			self.pca.fit(data)
		except ValueError:
			print(data)
			raise ValueError
		print("pca finished in %.3f seconds"%(time.time()-t0))
		return

	#---------------
	def getEigenValue(self, dataVec):
		try:
			evals = self.pca.transform(dataVec.reshape(1, -1))[0]
		except ValueError:
			print(dataVec)
			raise ValueError
		return evals

	#---------------
	def getEigenValues(self, dataVecs):
		try:
			evals = self.pca.transform(dataVecs)
		except ValueError:
			print(dataVecs)
			raise ValueError
		return evals

#=========================
class DataClass(object):
	#---------------
	def __init__(self, stackfile=None):
		self.inputdict = None
		if stackfile is not None and os.path.exists(stackfile):
			self.stackfile = stackfile
		elif len(sys.argv) > 1:
			tempfile = sys.argv[1]
			if os.path.exists(tempfile):
				self.stackfile = tempfile
		print("stackfile: ", self.stackfile)

		self.numpart = apFile.numImagesInStack(self.stackfile)
		self.boxsize = apFile.getBoxSize(self.stackfile)[0]

		self.keepfile = "keepfile.lst"
		self.rejectfile = "rejectfile.lst"

		#print "Num Part %d, Box Size %d"%(self.numpart, self.boxsize)
		self.imgproc = imageprocess.ImageFilter()
		self.imgproc.normalizeType = '256'
		self.imgproc.pixelLimitStDev = 6.0
		self.imgproc.msg = False
		### create a map to random particles
		self.particleMap = list(range(1, self.numpart+1))
		random.shuffle(self.particleMap)
		self.particleTarget = {} #0 = ???, 1 = good, 2 = bad
		self.lastImageRead = 0
		self.classifier = None
		self.count = 0
		self.accuracy = None
		self.numdatapoints = None
		self.statCache = {}
		self.pca = None

	#---------------
	def getSelectionStatistics(self):
		goodParticles = 0
		for key in list(self.particleTarget.keys()):
			if self.particleTarget[key] == 1:
				goodParticles += 1
		# goodParticles, assignedParticles, totalParticles
		return (goodParticles, len(self.particleTarget), self.numpart)

	#---------------
	def getStatsText(self):
		goodParticles, assignedParticles, totalParticles = self.getSelectionStatistics()
		remaining = totalParticles-assignedParticles
		badParticles = assignedParticles-goodParticles
		mytxt = ("%d of %d remaining (%d assigned; %d good / %d bad). "
			%(remaining, totalParticles, assignedParticles, goodParticles, badParticles, ))
		apDisplay.printMsg(mytxt)
		if self.classifier is None:
			return mytxt
		### add classifier stats
		if self.accuracy is not None and self.numdatapoints is not None:
			mytxt += "%.1f%s class accuracy (input %d pts)."%(self.accuracy*100, '%', self.numdatapoints)
		return mytxt

	#---------------
	def readAndProcessParticle(self, partnum):
		imgarray = apImagicFile.readSingleParticleFromStack(self.stackfile,
			partnum=partnum, boxsize=self.boxsize, msg=False)
		procarray = self.imgproc.processImage(imgarray)
		intarray = numpy.array(procarray, dtype=numpy.uint8)
		return intarray

	#---------------
	def getParticleTarget(self, partNum):
		return self.particleTarget.get(partNum,0)

	#---------------
	def updateParticleTarget(self, partNum, newvalue=None):
		if newvalue is None:
			value = self.particleTarget.get(partNum,0)
			newvalue = (value + 1) % 3
		self.particleTarget[partNum] = newvalue

	#---------------
	def predictParticleTarget(self, partnum):
		if self.classifier is None:
			return 0
		evals = self.getEigenValueFromPartNum(partnum)
		#print "evals.shape", evals.shape
		assignedClass = self.classifier.predict(evals.reshape(1, -1))[0]
		probClass = self.classifier.predict_proba(evals.reshape(1, -1))[0]
		#print "%04d assign: %d -- p1: %.3f -- p2: %.3f"%(partnum, assignedClass, probClass[0], probClass[1])
		if probClass[0] > probClass[1]:
			assignedClass = 1
		else:
			assignedClass = 2
		return assignedClass

	#---------------
	def predictParticleTargetProbability(self, partnum):
		if self.classifier is None:
			return None
		evals = self.getEigenValueFromPartNum(partnum)
		#print "evals.shape", evals.shape
		#assignedClass = self.classifier.predict(evals.reshape(1, -1))[0]
		probClass = self.classifier.predict_proba(evals.reshape(1, -1))[0]
		#print "%04d assign: %d -- p1: %.3f -- p2: %.3f"%(partnum, assignedClass, probClass[0], probClass[1])
		return probClass

	#---------------
	def partnumToInputVector(self, partnum):
		if self.inputdict is None:
			apDisplay.printError("major error: unknown input dict")
		datalist = []
		imgarray = self.readAndProcessParticle(partnum)
		boxsize = min(imgarray.shape)
		edgemap = imagefun.filled_circle((boxsize, boxsize), boxsize/2.0-1.0)
		if (self.inputdict['phaseSpectra'] is True
			 or self.inputdict['phaseStats'] is True
			 or self.inputdict['rotPhaseAvg'] is True
			 or self.inputdict['horizPhaseAvg'] is True):
			try:
				phasespec = imagefun.phase_spectrum(imgarray)
			except RuntimeWarning:
				phasespec = numpy.ones(imgarray.shape)
		if (self.inputdict['powerSpectra'] is True
			 or self.inputdict['powerStats'] is True
			 or self.inputdict['rotPowerAvg'] is True
			 or self.inputdict['horizPowerAvg'] is True):
			try:
				powerspec = imagefun.power(imgarray)
			except RuntimeWarning:
				powerspec = numpy.ones(imgarray.shape)
		if self.inputdict['imageStats'] is True:
			stats = self.extendedImageStats(imgarray, edgemap)
			datalist.append(stats)
		if self.inputdict['particlePixels'] is True:
			particlePixels = imgarray[edgemap == 1].ravel()
			datalist.append(particlePixels)
		if self.inputdict['rotAverage'] is True:
			xdata, ydata = ctftools.rotationalAverage(imgarray, 2, full=False)
			datalist.append(ydata)
		if self.inputdict['horizontalAverage'] is True:
			ydata = imgarray.mean(1)
			datalist.append(ydata)

		if self.inputdict['phaseSpectra'] is True:
			phasespecPixels = phasespec[edgemap == 1].ravel()
			datalist.append(phasespecPixels)
		if self.inputdict['phaseStats'] is True:
			stats = self.extendedImageStats(phasespec, edgemap)
			datalist.append(stats)
		if self.inputdict['rotPhaseAvg'] is True:
			xdata, ydata = ctftools.rotationalAverage(phasespec, 2, full=False)
			datalist.append(ydata)
		if self.inputdict['horizPhaseAvg'] is True:
			ydata = phasespec.mean(1)
			datalist.append(ydata)

		if self.inputdict['powerSpectra'] is True:
			powerspecPixels = powerspec[edgemap == 1].ravel()
			datalist.append(powerspecPixels)
		if self.inputdict['powerStats'] is True:
			stats = self.extendedImageStats(powerspec, edgemap)
			datalist.append(stats)
		if self.inputdict['rotPowerAvg'] is True:
			xdata, ydata = ctftools.rotationalAverage(powerspec, 2, full=False)
			datalist.append(ydata)
		if self.inputdict['horizPowerAvg'] is True:
			ydata = powerspec.mean(1)
			datalist.append(ydata)

		if len(datalist) == 0:
			apDisplay.printError("major error: no input vector from particle")
		statArray = numpy.hstack(datalist)
		statArray[numpy.isinf(statArray)] = 0
		statArray[numpy.isnan(statArray)] = 0
		self.numdatapoints = len(statArray)
		return statArray

	#---------------
	def extendedImageStats(self, imgarray, edgemap):
		"""
		rather than passing raw pixels, lets pass some key particle stats
		"""
		statList = []
		statList.extend(self.imageStats(imgarray.ravel()))
		statList.extend(self.imageStats(imgarray[edgemap==1].ravel()))
		statList.extend(self.imageStats(imgarray[edgemap==0].ravel()))
		statArray = numpy.array(statList)
		return statArray

	#---------------
	def imageStats(self, imgravel):
		N, (minval, maxval), mean, var, skew, kurt = scipy.stats.describe(imgravel)
		statsArray = [mean, var, minval, maxval, skew, kurt]
		absravel = numpy.abs(imgravel) + 1e-6
		statsArray.append(absravel.mean())
		statsArray.append(scipy.stats.gmean(imgravel))
		statsArray.append(scipy.stats.hmean(absravel))
		#statsArray.append(scipy.stats.trim_mean(imgravel, 0.1)) #creates error in CentOS6
		return numpy.array(statsArray)

	#---------------
	def getEigenValueFromPartNum(self, partnum):
		statArray = self.partnumToInputVector(partnum)
		evals = self.pca.getEigenValue(statArray)
		return evals

	#---------------
	def readRandomImage(self):
		partnum = self.particleMap[self.lastImageRead]
		imgarray = self.readAndProcessParticle(partnum)
		self.lastImageRead += 1
		if self.lastImageRead >= self.numpart:
			self.lastImageRead = 0
		return imgarray, partnum

	#---------------
	def getRandomImageSet(self, nimg):
		probParticleDict = {}
		count = 0
		while len(probParticleDict) < nimg and count < self.numpart-1:
			count += 1
			partnum = self.particleMap[self.lastImageRead]
			if self.particleTarget.get(partnum, 0) == 0:
				#only use unselected partices
				if self.classifier is None:
					probParticleDict[partnum] = partnum
				else:
					probClass = self.predictParticleTargetProbability(partnum)
					probParticleDict[partnum] = probClass[0]
			self.lastImageRead += 1
			if self.lastImageRead >= self.numpart:
				self.lastImageRead = 0
		particleNumberList = sorted(probParticleDict, key=lambda k: -probParticleDict[k])
		return particleNumberList

	#---------------
	def getParticleDiscrepancyList(self, nimg):
		if self.classifier is None:
			return None
		selectedParticleList = list(self.particleTarget.keys())
		if len(selectedParticleList) < nimg:
			return None
		probParticleDict = {}
		for partnum in selectedParticleList:
			probClass = self.predictParticleTargetProbability(partnum)
			setting = self.particleTarget[partnum]
			if setting == 1:
				probParticleDict[partnum] = probClass[0]
			elif setting == 2:
				probParticleDict[partnum] = probClass[1]
		particleNumberList = sorted(probParticleDict, key=lambda k: probParticleDict[k])
		newlist = particleNumberList[:nimg]
		print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
		probParticleDict2 = {}
		for partnum in newlist:
			probClass = self.predictParticleTargetProbability(partnum)
			probParticleDict2[partnum] = probClass[0]
		particleNumberList2 = sorted(probParticleDict2, key=lambda k: probParticleDict2[k])
		return particleNumberList2

	#---------------
	def readTargetImageStats(self):
		particleIndexes = list(self.particleTarget.keys())
		particleIndexes.sort()
		partdata = []
		for partIndex in particleIndexes:
			partdata.append(self.particleStats(partIndex))
		return partdata

	#---------------
	def readTargetImageData(self, choice=None, readData=True):
		t0 = time.time()
		particleIndexes = []
		if choice is None:
			choice = self.inputdict['inputTypeChoice']
		if choice.startswith('Good'):
			for partnum, assignedClass in list(self.particleTarget.items()):
				if assignedClass == 1:
					particleIndexes.append(partnum)
		elif choice.startswith('Bad'):
			for partnum, assignedClass in list(self.particleTarget.items()):
				if assignedClass == 2:
					particleIndexes.append(partnum)
		else:
			particleIndexes = list(self.particleTarget.keys())
		particleIndexes.sort()
		if readData is False:
			return particleIndexes
		partdata = []
		for partnum in particleIndexes:
			statArray = self.partnumToInputVector(partnum)
			partdata.append(statArray)
		print(("read image data for %d partilces in %.3f seconds"
			%(len(particleIndexes), time.time()-t0)))
		return numpy.array(partdata)

	#---------------
	def indexMapping(self, bigSortedList, subSortedList):
		matchIndex = []
		j = 0
		for i in range(len(bigSortedList)):
			index1 = bigSortedList[i]
			index2 = subSortedList[j]
			if index1 == index2:
				matchIndex.append(i)
				j += 1
		if len(matchIndex) != len(subSortedList):
			print(bigSortedList)
			print(subSortedList)
			raise ValueError
		return matchIndex

	#---------------
	def particlePCA(self):
		## get the data
		partdata = self.readTargetImageData('All', readData=True)
		AllParticleIndexes = self.readTargetImageData(readData=False)
		selectParticleIndexes = self.readTargetImageData(readData=False)
		matchIndex = self.indexMapping(AllParticleIndexes, selectParticleIndexes)
		pcaPartData = partdata[matchIndex, :]

		## pca
		n_components = self.inputdict['numComponents']
		if n_components > math.sqrt(pcaPartData.shape[0]):
			n_components = int(math.floor(math.sqrt(pcaPartData.shape[0])))
		pcaType = self.inputdict['dimensionReduceChoice'].lower()
		self.pca = PCA(pcaPartData, n_components, pcaType)

		## eigen values
		t1 = time.time()
		print("calculating eigen values")
		particleEigenValues = self.pca.getEigenValues(partdata)
		print("eigen values created in %.3f seconds"%(time.time()-t1))
		return particleEigenValues

	#---------------
	def trainSVM(self):
		t0 = time.time()
		targetData = numpy.array(self.targetDictToList())
		if len(targetData) < 3:
			print("pick more particles...")
			return
		self.writeListFiles()
		particleEigenValues = numpy.array(self.particlePCA())

		indices = list(range(len(targetData)))
		random.shuffle(indices)
		percentTest = 0.2
		testSize = int(math.ceil(percentTest*len(indices)))

		print("selecting %d particles for test set"%(testSize))

		trainSetIndex = indices[testSize:]
		testSetIndex = indices[:testSize]

		if len(numpy.unique(targetData)) < 2:
			return
		t1 = time.time()
		Cparameter = self.inputdict['Cparameter']
		gammaParameter = self.inputdict['gammaParameter']
		if gammaParameter <= 0:
			gammaParameter = 'auto'
		self.classifier = svm.SVC(C=Cparameter, gamma=gammaParameter, kernel='rbf', probability=True)
		"""
		http://scikit-learn.org/stable/auto_examples/svm/plot_rbf_parameters.html

		C: Penalty parameter C of the error term. float, optional (default=1.0)
		gamma: Kernel coefficient. If gamma is 'auto' then 1/n_features will be used instead. float, optional (default='auto')

		The behavior of the model is very sensitive to the gamma parameter.

		If gamma is too large, the radius of the area of influence of the support
		vectors only includes the support vector itself and no amount of regularization
		with C will be able to prevent overfitting.

		When gamma is very small, the model is too constrained and cannot capture the complexity
		or "shape" of the data. The region of influence of any selected support vector would
		include the whole training set. The resulting model will behave similarly to a linear
		model with a set of hyperplanes that separate the centers of high density of any pair
		of two classes.
		"""
		print("Training classifier... (please wait)")
		#particleEigenValues = 2d array, rows are individual particles, cols are amount of each eigenvalue
		#targetData = list of which class items are in, e.g., [2, 2, 2, 1, 2, 1, 1, 1, 1, 2, 1, 2, ]
		self.classifier.fit(particleEigenValues[trainSetIndex], targetData[trainSetIndex])
		print("training finished in %.3f seconds"%(time.time()-t1))
		self.testAccuracy(testSetIndex, particleEigenValues, targetData)
		print("complete training finished in %.3f seconds"%(time.time()-t0))

	#---------------
	def testAccuracy(self, testSetIndex, particleEigenValues, targetData):
		t0 = time.time()
		evals = particleEigenValues[testSetIndex]
		probClasses = self.classifier.predict_proba(evals)
		#probClass = self.classifier.predict_proba(evals.reshape(1, -1))[0]
		prob1 = probClasses[:,0]
		prob2 = probClasses[:,1]
		predictClass = numpy.where(prob1 > prob2, 1, 2)
		#print probClasses

		#print targetData[testSetIndex]
		#print predictClass
		match = numpy.where(targetData[testSetIndex] == predictClass, 1, 0)
		#print match
		self.accuracy = match.mean()
		print("accuracy testing finished in %.3f seconds"%(time.time()-t0))
		print("SVM accuracy %.4f"%(self.accuracy*100))
		return

	#---------------
	def targetDictToList(self):
		particleIndexes = list(self.particleTarget.keys())
		particleIndexes.sort()
		targetList = [self.particleTarget[i] for i in particleIndexes]
		return targetList

	#---------------
	def writeListFiles(self):
		keepf = open("keepfile.lst", "w")
		rejectf = open("rejectfile.lst", "w")
		for partNum in list(self.particleTarget.keys()):
			assignment = self.particleTarget[partNum]
			#write eman numbering starting at zero
			if assignment == 1:
				keepf.write("%d\n"%(partNum-1))
			elif assignment == 2:
				rejectf.write("%d\n"%(partNum-1))
		keepf.close()
		rejectf.close()

	#---------------
	def assignRemainingTargets(self):
		assignedSet = set(self.particleTarget.keys())
		allSet = set(range(1, self.numpart+1))
		print("assigned %d of %d particles"%(len(assignedSet), len(allSet)))

		## Get unassignedSet that are in allSet but not in assignedSet
		unassignedSet = allSet.difference(assignedSet)
		unassignedList = list(unassignedSet)
		unassignedList.sort()
		unassignedArray = numpy.array(unassignedList)
		apDisplay.printMsg("assigning %d unassigned particles"%(len(unassignedSet)))

		if len(unassignedArray) > 0:
			## break up into chunks of nimg to save memory
			nimg = max(self.inputdict['numDisplayImages'], 99)
			#subSetSize = len(unassignedArray)/nimg
			subSetsToCreate = numpy.arange(nimg, len(unassignedArray), nimg)
			print(subSetsToCreate)
			setsOfArrays = numpy.split(unassignedArray, subSetsToCreate)
			for unassignedSubArray in setsOfArrays:
				print("len(unassignedSubArray)", len(unassignedSubArray))
				## Read image data
				t0 = time.time()
				print("reading particle data from file...")
				unassignedPartData = []
				for partnum in unassignedSubArray:
					statArray = self.partnumToInputVector(partnum)
					unassignedPartData.append(statArray)
				print("particles read in %.3f seconds"%(time.time()-t0))
				unassignedPartData = numpy.array(unassignedPartData)

				## Eigen values
				t1 = time.time()
				print("calculating eigen values...")
				particleEigenValues = self.pca.getEigenValues(unassignedPartData)
				print("eigen values created in %.3f seconds"%(time.time()-t1))

				probClasses = self.classifier.predict_proba(particleEigenValues)
				prob1 = probClasses[:,0]
				prob2 = probClasses[:,1]
				predictedClassArray = numpy.where(prob1 > prob2, 1, 2)

				for i in range(len(unassignedSubArray)):
					partNum = unassignedSubArray[i]
					predictedClass = predictedClassArray[i]
					self.particleTarget[partNum] = predictedClass

		self.writeListFiles()
		print("finished assigning remaining particles")

#======================
#======================
#======================
#======================
class AverageStack(apImagicFile.processStack):
	#===============
	def preLoop(self):
		self.average = numpy.zeros((self.boxsize,self.boxsize))
		#override self.partlist to get a subset
		self.count = 0

	#===============
	def processStack(self, stackarray):
		if isinstance(stackarray, list):
			stackarray = numpy.array(stackarray)
		self.index += stackarray.shape[0]
		self.average += stackarray.sum(0)

	#===============
	def save(self, avgfile):
		mrc.write(self.average/self.index, avgfile)

	#===============
	def getdata(self):
		return self.average/self.index

#=========================
class HelpAbout(wx.MessageDialog):
	#---------------
	def __init__(self, parent):
		title = 'About Learning Stack Cleaner'
		msg = ("Learning Stack Cleaner "
			+"\n\nDeveloped by Neil R. Voss"
			+"\n\nPlease send questions and comments to:\nvossman77@yahoo.com"
			+"\n\nOriginal Code from TMaCS 1.14 developed by Jianhua Zhao, Marcus A. Brubaker, and John L. Rubinstein"
		)
		wx.MessageDialog.__init__(self, parent, message=msg, caption=title, style=wx.OK)
		self.ShowModal()

#=========================
class MainWindow(wx.Frame):
	#---------------
	def __init__(self, data):
		wx.Frame.__init__(self, None)
		self.data = data
		self.main = self

		# Set up scrolling window
		self.scrolled_window = wx.ScrolledWindow(self)
		self.scrolled_window.SetScrollRate(3, 3)
		self.scrolled_window.EnableScrolling(True, True)
		self.sizer_scroll = wx.GridBagSizer(5, 5)

		# Set up menu bar
		menubar = wx.MenuBar()
		self.SetMenuBar(menubar)

		# File menu
		filemenu = wx.Menu()
		menubar.Append(filemenu, '&File')
		filequit = filemenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
		self.Bind(wx.EVT_MENU, self.EvtOnQuit, filequit)

		# Help menu
		helpmenu = wx.Menu()
		menubar.Append(helpmenu, '&Help')
		helpabout = helpmenu.Append(-1, 'About')
		self.Bind(wx.EVT_MENU, self.EvtOnHelpAbout, helpabout)

		# Create navigation and working panel
		self.navigationPanel = NavPanel(self.scrolled_window, self.main)
		self.sizer_scroll.Add(self.navigationPanel, pos=(1, 1))
		statsText = self.data.getStatsText()
		self.mainStatsText = wx.StaticText(self.scrolled_window, label=statsText, style=wx.ALIGN_LEFT)
		self.sizer_scroll.Add(self.mainStatsText, pos=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)

		self.workPanel = WorkPanel(self.scrolled_window, self.main)
		self.sizer_scroll.Add(self.workPanel, pos=(2, 1), span=(1, 2))

		# Spacers
		self.sizer_scroll.AddSpacer((10, 10), (0, 0))
		self.sizer_scroll.AddSpacer((10, 10), (1, 3))
		self.sizer_scroll.AddSpacer((10, 10), (2, 4))

		# Set up scrolling on window resize
		self.Bind(wx.EVT_SIZE, self.OnSize)

		# Set up Displays
		self.SetSize((980, 500))
		self.CreateStatusBar()
		self.SetTitle('Learning Stack Cleaner')

		# Set sizers
		self.scrolled_window.SetSizer(self.sizer_scroll)

	#---------------
	def OnSize(self, event):
		self.scrolled_window.SetSize(self.GetClientSize())

	#---------------
	def EvtOnQuit(self, event):
		self.Close()

	#---------------
	def EvtOnHelpAbout(self, event):
		HelpAbout(main)

#=========================
class NavPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel, style=wx.SIMPLE_BORDER)
		self.main = main
		# Set up sizer
		self.sizer_nav = wx.GridBagSizer(5, 5)

		# Spacers
		itemcol = 0
		self.sizer_nav.AddSpacer((2, 2), (0, itemcol))

		# Buttons for navigation
		itemcol += 1
		self.button1 = wx.ToggleButton(self, label='Step %d. Training'%(itemcol))
		self.sizer_nav.Add(self.button1, pos=(1, itemcol), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(itemcol), self.button1)

		itemcol += 1
		self.button2 = wx.ToggleButton(self, label='Step %d. Classify'%(itemcol))
		self.sizer_nav.Add(self.button2, pos=(1, itemcol), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(itemcol), self.button2)

		itemcol += 1
		self.button3 = wx.ToggleButton(self, label='Step %d. Finish'%(itemcol))
		self.sizer_nav.Add(self.button3, pos=(1, itemcol), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(itemcol), self.button3)

		itemcol += 1
		self.sizer_nav.AddSpacer((2, 2), (2, itemcol))

		self.SetSizerAndFit(self.sizer_nav)
		self.buttonsList = [self.button1, self.button2, self.button3, ]

	#---------------
	def EvtButton(self, pan):
		#panel_list = self.GetChildren()
		return lambda event: self.showpan(pan)

	#---------------
	def showpan(self, pan):
		self.panelsList = [ self.main.workPanel.trainingPanel, self.main.workPanel.classPanel, self.main.workPanel.finishPanel, ]
		for i in range(len(self.buttonsList)):
				self.buttonsList[i].SetValue(0)
				self.panelsList[i].Hide()
		self.main.workPanel.sizer_work = wx.GridBagSizer(0, 0)
		self.buttonsList[pan-1].SetValue(1)
		self.main.workPanel.sizer_work.Add(self.panelsList[pan-1], (0, 0))
		self.panelsList[pan-1].Show()
		self.main.workPanel.SetSizerAndFit(self.main.workPanel.sizer_work)
		self.main.scrolled_window.SetSize(self.main.GetClientSize())

#=========================
class WorkPanel(wx.Panel):
	#---------------
	def __init__(self, parentWindow, main):
		wx.Panel.__init__(self, parentWindow)
		self.scrolled_window = parentWindow
		self.main = main
		self.sizer_work = wx.GridBagSizer(1, 1)

		# Make panels
		self.trainingPanel = TrainPanel(self, self.main)
		self.trainingPanel.Hide()
		self.classPanel = ClassPanel(self, self.main)
		self.classPanel.Hide()
		self.finishPanel = FinishPanel(self, self.main)
		self.finishPanel.Hide()

#=========================
class TrainPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel)
		self.main = main

		displayRows = 2 #int(self.workPanel.MainWindow.GetClientSize()[0]/128.)
		displayCols = 6 #int(self.workPanel.MainWindow.GetClientSize()[1]/128.)

		self.workPanel = parentPanel
		self.part_display = False

		# Set up panels
		self.panel_stats = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.panel_image = wx.Panel(self, style=wx.SUNKEN_BORDER)

		# Set up sizers
		self.sizer_train = wx.GridBagSizer(5, 5)
		self.sizer_stats = wx.GridBagSizer(5, 5)
		self.sizer_image = wx.GridBagSizer(5, 5)

		itemrow = 0
		itemcol = 1
		self.sizer_stats.AddSpacer((2, 2), (0, 0))

		# Image pretreatment options
		itemrow += 1
		self.medianfilter = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.medianfilter.ChangeValue("2")
		self.sizer_stats.Add(self.medianfilter, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Median filter (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.lowpass = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.lowpass.ChangeValue('10')
		self.sizer_stats.Add(self.lowpass, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Low Pass (Angstroms)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.highpass = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.highpass.ChangeValue('500')
		self.sizer_stats.Add(self.highpass, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='High Pass (Angstroms)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		itemrow += 1
		self.pixelLimitStDev = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.pixelLimitStDev.ChangeValue('-1')
		self.sizer_stats.Add(self.pixelLimitStDev, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Pixel Limit (StdDevs)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.binning = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.binning.ChangeValue('1')
		self.sizer_stats.Add(self.binning, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Binning (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.clipping = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.clipping.ChangeValue("%d"%(self.main.data.boxsize))
		self.sizer_stats.Add(self.clipping, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Clipping (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		# Display info
		itemrow += 1
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Particle image display:'),
			pos=(itemrow, itemcol), span=(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.nrows = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.nrows.ChangeValue(str(displayRows))
		self.sizer_stats.Add(self.nrows, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NRows'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.ncols = wx.TextCtrl(self.panel_stats, size=(40,-1), style=wx.TE_CENTRE)
		self.ncols.ChangeValue(str(displayCols))
		self.sizer_stats.Add(self.ncols, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NCols'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		itemrow += 1
		### add extra button here

		itemrow += 1
		self.buttonShowDiscrepancies = wx.Button(self.panel_stats, wx.ID_REDO, label='&Show Discrepancies', size=(-1, -1))
		self.sizer_stats.Add(self.buttonShowDiscrepancies, pos=(itemrow, itemcol), span=(1, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtShowDiscrepancies, self.buttonShowDiscrepancies)

		itemrow += 1
		self.buttonAcceptPredict = wx.Button(self.panel_stats, wx.ID_APPLY, label='&Accept Predictions', size=(-1, -1))
		self.sizer_stats.Add(self.buttonAcceptPredict, pos=(itemrow, itemcol), span=(1, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtAcceptPredict, self.buttonAcceptPredict)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		# New set
		itemrow += 1
		self.autoFitParticles = wx.Button(self.panel_stats, wx.ID_ZOOM_FIT, label='Auto &Fit Window', size=(-1, -1))
		self.sizer_stats.Add(self.autoFitParticles, pos=(itemrow, itemcol), span=(1, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtAutoFitParticles, self.autoFitParticles)

		itemrow += 1
		self.buttonNewSet = wx.Button(self.panel_stats, wx.ID_REFRESH, label='&Refresh Set', size=(-1, -1))
		self.sizer_stats.Add(self.buttonNewSet, pos=(itemrow, itemcol), span=(1, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtRefreshSet, self.buttonNewSet)

		itemrow += 1
		self.buttonTrainClass = wx.Button(self.panel_stats, label='&Train and Refresh', size=(-1, -1))
		self.sizer_stats.Add(self.buttonTrainClass, pos=(itemrow, itemcol), span=(1, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtTrainClass, self.buttonTrainClass)

		itemrow += 1
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (itemrow, itemcol))
		itemcol += 1

		# Set sizers
		self.sizer_train.Add(self.panel_stats, pos=(0, 0))
		self.sizer_train.AddSpacer((2, 2), (1, 0))
		self.sizer_train.Add(self.panel_image, pos=(2, 0))
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_image.SetSizerAndFit(self.sizer_image)
		self.SetSizerAndFit(self.sizer_train)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)

	#---------------
	def EvtAutoFitParticles(self, event):
		(colPixels, rowPixels) = self.main.GetClientSize()
		particleSize = int(self.clipping.GetValue())
		if particleSize < 1:
			particleSize = self.data.boxsize
		binSize = int(self.binning.GetValue())
		gapsize = 20
		header = 140
		particleWindow = particleSize/binSize + gapsize
		nrows = int(math.floor((rowPixels-header)/particleWindow))
		ncols = int(math.floor(colPixels/particleWindow))
		self.nrows.SetValue(str(nrows))
		self.ncols.SetValue(str(ncols))
		### refresh window
		self.EvtRefreshSet(event)

	#---------------
	def EvtRefreshSet(self, event):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		particleNumberList = self.main.data.getRandomImageSet(nimg)
		self.MakeDisplay(particleNumberList)

	#---------------
	def EvtTrainClass(self, event):
		self.main.data.inputdict = self.main.workPanel.classPanel.getInputDict()
		self.main.data.trainSVM()
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		particleNumberList = self.main.data.getRandomImageSet(nimg)
		self.MakeDisplay(particleNumberList)

	#---------------
	def EvtShowDiscrepancies(self, event):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		discrepancyList = self.main.data.getParticleDiscrepancyList(nimg)
		if discrepancyList is None:
			return
		self.MakeDisplay(discrepancyList)

	#---------------
	def EvtAcceptPredict(self, event):
		partList = []
		for imgbutton in self.imgbuttonList:
			setting = self.main.data.getParticleTarget(imgbutton.particleNum)
			if setting == 0:
				imgbutton.SetPredictedClass()
				self.main.data.updateParticleTarget(imgbutton.particleNum, imgbutton.particleSetting)
			partList.append(imgbutton.particleNum)
		self.MakeDisplay(partList)

	#---------------
	def MakeDisplay(self, particleNumberList):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols

		self.main.data.imgproc.lowPass = float(self.lowpass.GetValue())
		self.main.data.imgproc.lowPassType = 'tanh'
		self.main.data.imgproc.median = int(self.medianfilter.GetValue())
		self.main.data.imgproc.highPass = float(self.highpass.GetValue())
		self.main.data.imgproc.pixelLimitStDev = float(self.pixelLimitStDev.GetValue())
		clipVal = int(self.clipping.GetValue())
		if clipVal > 1 and clipVal < self.main.data.boxsize:
			self.main.data.imgproc.clipping = clipVal
		self.main.data.imgproc.bin = int(self.binning.GetValue())

		# Delete previous objects
		#self.sizer_image.Destroy()
		self.panel_image.DestroyChildren()
		#self.panel_image.Destroy()
		#self.panel_image = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_image = wx.GridBagSizer(nrows, ncols)
		imagePanel = self.panel_image
		imageSizer = self.sizer_image

		self.imgbuttonList = []
		for i, partnum in enumerate(particleNumberList):
			row = int(i / ncols)
			col = i % ncols
			#print row, col
			self.main.SetStatusText("Preparing image %d of %d for display..."%(i, nimg))
			imgarray = self.main.data.readAndProcessParticle(partnum)
			imgbutton = ImageButton(imagePanel, self.main, imgarray, partnum)
			imageSizer.Add(imgbutton, pos=(row, col))
			imgbutton.SetBackgroundColour(wx.NullColour)
			self.imgbuttonList.append(imgbutton)

		### FIXME -- setsizer
		imagePanel.SetSizerAndFit(imageSizer)
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_image.SetSizerAndFit(self.sizer_image)
		self.SetSizerAndFit(self.sizer_train)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)
		self.main.scrolled_window.SetSize(self.main.GetClientSize())

		for imgbutton in self.imgbuttonList:
			imgbutton.SetPredictedClass()

		#print "GetClientSize", self.main.GetClientSize() ##use this for particle sizing
		statsText = self.main.data.getStatsText()
		self.main.mainStatsText.SetLabel(statsText)
		self.main.SetStatusText('Finished generating new image set. '+statsText)

#=========================
class ImageButton(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main, imgarray, particleNum):
		self.main = main
		self.particleNum = particleNum
		self.imgpanel = wx.Panel.__init__(self, parentPanel)
		self.imgsizer = wx.GridBagSizer(2, 2)
		self.mybitmap = self.GetWxBitmapFromNumpy(imgarray)
		rowcol = (imgarray.shape[1], imgarray.shape[0])
		self.imgbutton = wx.BitmapButton(self, -1, self.mybitmap, size=rowcol)
		self.imgsizer.AddSpacer((2, 2), (0, 0))
		self.imgsizer.Add(self.imgbutton, pos=(1, 1))
		self.imgsizer.AddSpacer((2, 2), (2, 2))
		parentPanel.Bind(wx.EVT_BUTTON, self.ImageClick, self.imgbutton)
		self.SetSizerAndFit(self.imgsizer)
		return

	#---------------
	def SetPredictedClass(self):
		partnum = 	self.particleNum
		setting = self.main.data.getParticleTarget(partnum)
		self.particleSetting = setting
		if setting == 1:
			self.SetBackgroundColour('FOREST GREEN')
			return
		elif setting == 2:
			self.SetBackgroundColour('FIREBRICK')
			return
		classProbs = self.main.data.predictParticleTargetProbability(partnum)
		if classProbs is None:
			self.SetBackgroundColour(wx.NullColour)
			return
		elif classProbs[0] > 0.5:
			classProb = classProbs[0]
			#Good particles 0.5 -> 1; 1 -> 0
			red = int( (255-107)*(2-2*classProb) + 107 )
			green = int( (255-142)*(2-2*classProb) + 142 )
			blue = int( (255-35)*(2-2*classProb) + 35 )
			self.SetBackgroundColour((red, green, blue))
			#rgb(173,255,47) #light lime green
			#rgb(107,142,35) #dark olive green
			self.particleSetting = 1 #good
			return
		elif classProbs[1] > 0.5:
			classProb = classProbs[1]
			#Bad particles 0.5 -> 1; 0 -> 0
			red = int( (255-199)*(2-2*classProb) + 199 )
			green = int( (255-21)*(2-2*classProb) + 21 )
			blue = int( (255-133)*(2-2*classProb) + 133 )
			self.SetBackgroundColour((red, green, blue))
			self.particleSetting = 2 #bad
			#rgb(199,21,133) #dark pink
			#rgb(255,192,203) #light pink
			return
		self.SetBackgroundColour(wx.NullColour)
		return

	#---------------
	def ImageClick(self, event):
		# Set background colour of particle images based on class
		self.main.data.updateParticleTarget(self.particleNum)
		setting = self.main.data.getParticleTarget(self.particleNum)
		if setting == 1:
			self.SetBackgroundColour('FOREST GREEN')
			self.imgbutton.SetBackgroundColour('FOREST GREEN')
		elif setting == 2:
			self.SetBackgroundColour('FIREBRICK')
			self.imgbutton.SetBackgroundColour('FIREBRICK')
		else:
			self.SetBackgroundColour(wx.NullColour)
			self.imgbutton.SetBackgroundColour(wx.NullColour)
		return

	#---------------
	def GetWxBitmapFromNumpy(self, imgarray):
		imgnorm = imagenorm.normalizeImage(imgarray.copy())
		bigarray = numpy.dstack((imgnorm, imgnorm, imgnorm))
		bigarray = numpy.array(bigarray, dtype='uint8')
		image = wx.EmptyImage(imgarray.shape[1], imgarray.shape[0])
		image.SetData(bigarray.tobytes())
		wxBitmap = image.ConvertToBitmap()
		return wxBitmap

#=========================
class ClassPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel)
		self.main = main
		self.workPanel = parentPanel
		self.inputdictcache = None

		# Set up sizers
		self.sizer_class_head = wx.GridBagSizer(5, 5)

		self.statsPanel()
		self.inputSelect()
		self.dimensionReduce()
		self.classifierMethod()

		# Set sizers
		itemrow = 0
		self.sizer_class_head.Add(self.panel_stats, pos=(itemrow, 0))
		self.buttonTrainClass = wx.Button(self, label='Train Classifier')
		self.sizer_class_head.Add(self.buttonTrainClass, pos=(itemrow, 1), flag=wx.ALIGN_CENTER)

		itemrow += 1
		self.sizer_class_head.AddSpacer((2, 2), (itemrow, 0))
		itemrow += 1
		self.sizer_class_head.Add(self.panel_input_select, pos=(itemrow, 0), span=(1,2))
		itemrow += 1
		self.sizer_class_head.AddSpacer((2, 2), (itemrow, 0))
		itemrow += 1
		self.sizer_class_head.Add(self.panel_dimension_reduce, pos=(itemrow, 0), span=(1,2))
		itemrow += 1
		self.sizer_class_head.AddSpacer((2, 2), (itemrow, 0))
		itemrow += 1
		self.sizer_class_head.Add(self.panel_classifier, pos=(itemrow, 0), span=(1,2))

		# Set up scrolling on window resize
		self.Bind(wx.EVT_PAINT, self.OnRefresh)
		self.Bind(wx.EVT_BUTTON, self.EvtTrainClass, self.buttonTrainClass)

		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_input_select.SetSizerAndFit(self.sizer_input_select)
		self.panel_dimension_reduce.SetSizerAndFit(self.sizer_dimension_reduce)
		self.panel_classifier.SetSizerAndFit(self.sizer_classifier)


		self.SetSizerAndFit(self.sizer_class_head)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)

	#---------------
	def EvtTrainClass(self, evt):
		self.main.data.inputdict = self.getInputDict()
		self.main.data.trainSVM()
		self.OnRefresh(evt)

	#---------------
	def statsPanel(self):
		self.panel_stats = wx.Panel(self, style=wx.SUNKEN_BORDER)
		self.sizer_stats = wx.GridBagSizer(5, 5)
		itemrow = 0
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='# Data Points'), pos=(itemrow, 0))
		self.dataPointsDisplay = wx.StaticText(self.panel_stats, label='#####',
			style=wx.ALIGN_LEFT)
		self.sizer_stats.Add(self.dataPointsDisplay, pos=(itemrow, 1))
		itemrow += 1
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Accuracy'), pos=(itemrow, 0))
		self.accuracyDisplay = wx.StaticText(self.panel_stats, label='???? %',
			style=wx.ALIGN_LEFT)
		self.sizer_stats.Add(self.accuracyDisplay, pos=(itemrow, 1))

	#---------------
	def OnRefresh(self, evt):
		if self.main.data.accuracy is not None:
			self.accuracyDisplay.SetLabel("%.1f %s"%(self.main.data.accuracy*100, '%'))

		inputdict = self.getInputDict()
		self.main.data.inputdict = inputdict
		if self.inputdictcache is None or inputdict != self.inputdictcache:
			self.main.data.numdatapoints = len(self.main.data.partnumToInputVector(1))
			self.dataPointsDisplay.SetLabel("%d"%self.main.data.numdatapoints)
		self.inputdictcache = inputdict

	#---------------
	def inputSelect(self):
		self.panel_input_select = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_input_select = wx.GridBagSizer(5, 5)
		self.sizer_input_select.Add(wx.StaticText(self.panel_input_select,
				label='SELECT DATA TO ANALYZE'), span=(1,3), pos=(0, 0))
		self.sizer_input_select.AddSpacer((2, 2), (1, 0))

		itemrow = 0
		itemcol = 1

		itemrow += 1
		self.particlePixels = wx.CheckBox(self.panel_input_select, label='Particle Pixels')
		self.particlePixels.SetValue(False)
		self.sizer_input_select.Add(self.particlePixels, pos=(itemrow, itemcol))

		itemrow += 1
		self.imageStats = wx.CheckBox(self.panel_input_select, label='Image Stats')
		self.imageStats.SetValue(True)
		self.sizer_input_select.Add(self.imageStats, pos=(itemrow, itemcol))

		itemrow += 1
		self.rotAverage = wx.CheckBox(self.panel_input_select, label='Rotational Average')
		self.rotAverage.SetValue(True)
		self.sizer_input_select.Add(self.rotAverage, pos=(itemrow, itemcol))

		itemrow += 1
		self.horizontalAverage = wx.CheckBox(self.panel_input_select, label='Horizontal Average')
		self.horizontalAverage.SetValue(True)
		self.sizer_input_select.Add(self.horizontalAverage, pos=(itemrow, itemcol))

		itemcol += 1
		itemrow = 0

		itemrow += 1
		self.phaseSpectra = wx.CheckBox(self.panel_input_select, label='Phase Spectra')
		self.phaseSpectra.SetValue(False)
		self.sizer_input_select.Add(self.phaseSpectra, pos=(itemrow, itemcol))

		itemrow += 1
		self.phaseStats = wx.CheckBox(self.panel_input_select, label='Phase Pixel Stats')
		self.phaseStats.SetValue(False)
		self.sizer_input_select.Add(self.phaseStats, pos=(itemrow, itemcol))

		itemrow += 1
		self.rotPhaseAvg = wx.CheckBox(self.panel_input_select, label='Rotational Phase Average')
		self.rotPhaseAvg.SetValue(False)
		self.sizer_input_select.Add(self.rotPhaseAvg, pos=(itemrow, itemcol))

		itemrow += 1
		self.horizPhaseAvg = wx.CheckBox(self.panel_input_select, label='Horizontal Phase Average')
		self.horizPhaseAvg.SetValue(False)
		self.sizer_input_select.Add(self.horizPhaseAvg, pos=(itemrow, itemcol))

		itemcol += 1
		itemrow = 0

		itemrow += 1
		self.powerSpectra = wx.CheckBox(self.panel_input_select, label='Power Spectra')
		self.powerSpectra.SetValue(False)
		self.sizer_input_select.Add(self.powerSpectra, pos=(itemrow, itemcol))

		itemrow += 1
		self.powerStats = wx.CheckBox(self.panel_input_select, label='Power Pixel Stats')
		self.powerStats.SetValue(False)
		self.sizer_input_select.Add(self.powerStats, pos=(itemrow, itemcol))

		itemrow += 1
		self.rotPowerAvg = wx.CheckBox(self.panel_input_select, label='Rotational Power Average')
		self.rotPowerAvg.SetValue(False)
		self.sizer_input_select.Add(self.rotPowerAvg, pos=(itemrow, itemcol))

		itemrow += 1
		self.horizPowerAvg = wx.CheckBox(self.panel_input_select, label='Horizontal Power Average')
		self.horizPowerAvg.SetValue(False)
		self.sizer_input_select.Add(self.horizPowerAvg, pos=(itemrow, itemcol))

		self.sizer_input_select.AddSpacer((2, 2), pos=(itemrow+1, itemcol+1))
		return

	#---------------
	def getInputDict(self):
		nrows = int(self.main.workPanel.trainingPanel.nrows.GetValue())
		ncols = int(self.main.workPanel.trainingPanel.ncols.GetValue())
		nimg = nrows*ncols

		inputDict = {
			'numDisplayImages': nimg,

			'imageStats': self.imageStats.GetValue(),
			'particlePixels': self.particlePixels.GetValue(),
			'rotAverage': self.rotAverage.GetValue(),
			'horizontalAverage': self.horizontalAverage.GetValue(),

			'phaseSpectra': self.phaseSpectra.GetValue(),
			'phaseStats': self.phaseStats.GetValue(),
			'rotPhaseAvg': self.rotPhaseAvg.GetValue(),
			'horizPhaseAvg': self.horizPhaseAvg.GetValue(),

			'powerSpectra': self.powerSpectra.GetValue(),
			'powerStats': self.powerStats.GetValue(),
			'rotPowerAvg': self.rotPowerAvg.GetValue(),
			'horizPowerAvg': self.horizPowerAvg.GetValue(),

			'inputTypeChoice': self.input_types[self.inputTypeChoice.GetSelection()],
			'dimensionReduceChoice': self.dr_methods[self.dimensionReduceChoice.GetSelection()],
			'numComponents': self.numComponents.GetValue(),

			'classifierChoice': self.class_methods[self.classifierChoice.GetSelection()],
			'Cparameter': float(self.Cparameter.GetValue()),
			'gammaParameter': float(self.gammaParameter.GetValue()),

		}
		inputTotal = 0
		for key in list(inputDict.keys()):
			if inputDict[key] is True:
				inputTotal += 1
		if inputTotal == 0:
			print("Error: no inputs selected, auto-check imageStats")
			self.imageStats.SetValue(True)
			inputDict['imageStats'] = True
		return inputDict

	#---------------
	def dimensionReduce(self):
		self.panel_dimension_reduce = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_dimension_reduce = wx.GridBagSizer(5, 5)
		self.sizer_dimension_reduce.Add(wx.StaticText(self.panel_dimension_reduce,
				label='REDUCE DATA DIMENSIONALITY'), span=(1,3), pos=(0, 0))
		self.sizer_dimension_reduce.AddSpacer((2, 2), pos=(1, 0))

		itemrow = 0
		itemcol = 1

		itemrow += 1
		self.input_types = ['Good: Particles only', 'All: Particles + Rejects', 'Bad: Rejects only', ]
		self.sizer_dimension_reduce.Add(wx.StaticText(self.panel_dimension_reduce, label='training data:'),
			pos=(itemrow, itemcol), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.inputTypeChoice = wx.Choice(self.panel_dimension_reduce, choices=self.input_types, style=wx.CB_READONLY)
		self.sizer_dimension_reduce.Add(self.inputTypeChoice, pos=(itemrow, itemcol+1), span=(1,3))

		itemrow += 1
		#dr_methods = ['Principal Components', 'Random Projection', 'Convolution Kernels', 'None / Everything', ]
		self.sizer_dimension_reduce.Add(wx.StaticText(self.panel_dimension_reduce, label='PCA type:'),
			pos=(itemrow, itemcol), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.dr_methods = ['Complete Principal Components (more accurate)', 'Randomized Principal Components (faster)', ]
		self.dimensionReduceChoice = wx.Choice(self.panel_dimension_reduce, choices=self.dr_methods, style=wx.CB_READONLY)
		self.sizer_dimension_reduce.Add(self.dimensionReduceChoice, pos=(itemrow, itemcol+1))

		itemrow += 1
		self.numComponents = wx.TextCtrl(self.panel_dimension_reduce, size=(40,-1), style=wx.TE_CENTRE)
		self.numComponents.ChangeValue(str(20))
		self.sizer_dimension_reduce.Add(wx.StaticText(self.panel_dimension_reduce, label='number of components:'),
			pos=(itemrow, itemcol), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.sizer_dimension_reduce.Add(self.numComponents, pos=(itemrow, itemcol+1))

		self.sizer_dimension_reduce.AddSpacer((2, 2), pos=(itemrow+1, itemcol+2))
		return

	#---------------
	def classifierMethod(self):
		self.panel_classifier = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_classifier = wx.GridBagSizer(5, 5)
		self.sizer_classifier.Add(wx.StaticText(self.panel_classifier,
				label='CLASSIFICATION'), span=(1,3), pos=(0, 0))
		self.sizer_classifier.AddSpacer((2, 2), pos=(1, 0))

		itemrow = 0
		itemcol = 1
		#class_methods = ['Simple Vector Machine', 'TensorFlow Conv. Neural Network']
		self.class_methods = ['Simple Vector Machine', ]

		itemrow += 1
		self.sizer_classifier.Add(wx.StaticText(self.panel_classifier, label='Classifier method:'),
			pos=(itemrow, itemcol), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.classifierChoice = wx.Choice(self.panel_classifier, choices=self.class_methods, style=wx.CB_READONLY)
		self.sizer_classifier.Add(self.classifierChoice, pos=(itemrow, itemcol+1), span=(1,2), )

		itemrow += 1
		self.Cparameter = wx.TextCtrl(self.panel_classifier, size=(60,-1), style=wx.TE_CENTRE)
		self.Cparameter.ChangeValue(str(1.0))
		self.sizer_classifier.Add(wx.StaticText(self.panel_classifier, label='Penalty parameter C:'),
			pos=(itemrow, itemcol), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.sizer_classifier.Add(self.Cparameter, pos=(itemrow, itemcol+1))

		itemrow += 1
		self.gammaParameter = wx.TextCtrl(self.panel_classifier, size=(60,-1), style=wx.TE_CENTRE)
		self.gammaParameter.ChangeValue(str("0.05"))
		self.sizer_classifier.Add(wx.StaticText(self.panel_classifier, label='Kernel coefficient (gamma):'),
			pos=(itemrow, itemcol), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.sizer_classifier.Add(self.gammaParameter, pos=(itemrow, itemcol+1))
		self.sizer_classifier.Add(wx.StaticText(self.panel_classifier, label='(-1 for auto)'),
			pos=(itemrow, itemcol+2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)

		self.sizer_classifier.AddSpacer((2, 2), pos=(itemrow+1, itemcol+3))
		return

#=========================
class FinishPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel)
		self.main = main
		self.workPanel = parentPanel

		self.sizer_finish = wx.GridBagSizer(5,1)

		itemrow = 0
		self.sizer_finish.AddSpacer((2, 2), pos=(itemrow, 0))

		itemrow += 1
		self.save = wx.Button(self, wx.ID_SAVE, '&Save Picks to File')
		self.Bind(wx.EVT_BUTTON, self.onSave, self.save)
		self.sizer_finish.Add(self.save, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, pos=(itemrow, 0))

		itemrow += 1
		self.sizer_finish.AddSpacer((2, 2), pos=(itemrow, 0))

		itemrow += 1
		self.quit = wx.Button(self, wx.ID_EXIT, 'Save and &Quit')
		self.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.sizer_finish.Add(self.quit, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, pos=(itemrow, 0))

		itemrow += 1
		self.sizer_finish.AddSpacer((2, 2), pos=(itemrow, 0))

		self.SetSizerAndFit(self.sizer_finish)
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)
		self.main.scrolled_window.SetSizerAndFit(self.main.sizer_scroll)

	#---------------
	def onSave(self, evt):
		self.main.data.writeListFiles()
		return

	#---------------
	def onQuit(self, evt):
		self.onSave(evt)
		wx.Exit()


#=========================
#=========================
if __name__=='__main__':
	app = wx.App()
	data = DataClass()
	main = MainWindow(data)
	main.Show()
	app.MainLoop()
