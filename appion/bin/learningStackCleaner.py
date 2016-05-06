#!/usr/bin/env python

import os
import wx
import sys
import cfg
import math
import numpy
import random
import scipy.stats
from pyami import imagefun
from appionlib import apFile
from appionlib import apImagicFile
from appionlib.apImage import imageprocess
from appionlib.apImage import imagenorm
from sklearn import svm
from sklearn import decomposition

### TODO
# rm import cfg
# save/load particle data to file
# - Color for probability
# add button to clear decisions
# create web launcher
# work with larger stack
# show discrepancies
# prevent crash on change of clipping

#=========================
class PCA(object):
	#---------------
	def __init__( self, data, boxsize, n_components):
		"""
		data = 2D array: rows of 1D images, columns of pixels
		n_components = number of components to keep
		"""
		self.n_components = n_components
		# calculate the covariance matrix
		#data -= data.mean()
		#data /= data.std()
		#self.pca = decomposition.RandomizedPCA(n_components=n_components, whiten=True)
		#self.pca = decomposition.KernelPCA(n_components=n_components, kernel='rbf')
		self.pca = decomposition.PCA(n_components=n_components, whiten=True)
		print "performing principal component analysis (pca)"
		try:
			self.pca.fit(data)
		except ValueError:
			print data
			raise ValueError
		print "pca complete"
		#print "self.pca.components_.shape", self.pca.components_.shape
		#print "(n_components, boxsize, boxsize)", n_components, boxsize, boxsize
		#self.eigenrows = numpy.copy(self.pca.components_)
		#print "data.shape", data.shape
		self.eigenvalues = self.pca.transform(data)
		#print numpy.around(self.eigenvalues, 3)
		return

	#---------------
	def getEigenValue(self, imgStats):
		try:
			#print "getEigenValue: imgStats.reshape(1, -1).shape", imgStats.reshape(1, -1).shape
			evals = self.pca.transform(imgStats.reshape(1, -1))[0]
		except ValueError:
			print imgStats
			raise ValueError
		#print "evals=", numpy.around(evals, 3)
		return evals

#=========================
class DataClass(object):
	#---------------
	def __init__(self):
		self.stackfile = "/emg/data/appion/06jul12a/stacks/stack1b/start.hed"
		if len(sys.argv) >1:
			tempfile = sys.argv[1]
			if os.path.isfile(tempfile):
				self.stackfile = tempfile
		self.numpart = apFile.numImagesInStack(self.stackfile)
		self.boxsize = apFile.getBoxSize(self.stackfile)[0]
		print "Num Part %d, Box Size %d"%(self.numpart, self.boxsize)
		self.edgemap = imagefun.filled_circle((self.boxsize, self.boxsize), self.boxsize/2.0-1.0)

		self.imgproc = imageprocess.ImageFilter()
		self.imgproc.normalizeType = '256'
		self.imgproc.pixelLimitStDev = 6.0

		self.imgproc.msg = False

		### create a map to random particles
		self.particleMap = range(1, self.numpart+1)
		random.shuffle(self.particleMap)
		self.particleTarget = {} #0 = ???, 1 = good, 2 = bad
		self.lastImageRead = 0
		self.classifier = None
		self.count = 0
		self.statCache = {}
		self.pca = None

	#---------------
	def readAndProcessParticle(self, partnum):
		imgarray = apImagicFile.readSingleParticleFromStack(self.stackfile,
			partnum=partnum, boxsize=self.boxsize, msg=False)
		procarray = self.imgproc.processImage(imgarray)
		intarray = numpy.array(procarray, dtype=numpy.uint8)
		newboxsize = min(intarray.shape)
		if newboxsize != self.boxsize:
			self.edgemap = imagefun.filled_circle((newboxsize, newboxsize), newboxsize/2.0-1.0)
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
		print "assignedClass: %.1f -- probClass1: %.3f -- probClass2: %.3f"%(assignedClass, probClass[0], probClass[1])
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
		assignedClass = self.classifier.predict(evals.reshape(1, -1))[0]
		probClass = self.classifier.predict_proba(evals.reshape(1, -1))[0]
		print "assignedClass: %.1f -- probClass1: %.3f -- probClass2: %.3f"%(assignedClass, probClass[0], probClass[1])
		return probClass

	#---------------
	def partnumToInputVector(self, partnum):
		imgarray = self.readAndProcessParticle(partnum)
		powerspec = imagefun.power(imgarray)
		partstats = self.particleStats(partnum, powerspec)
		statArray = numpy.hstack((partstats, imgarray.ravel(), powerspec.ravel()))
		statArray[numpy.isinf(statArray)] = 0
		statArray[numpy.isnan(statArray)] = 0
		return statArray

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
		selectedParticleList = self.particleTarget.keys()
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
		print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
		for partnum in newlist:
			probClass = self.predictParticleTargetProbability(partnum)
		return particleNumberList[:nimg]

	#---------------
	def readTargetImageStats(self):
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		partdata = []
		for partIndex in particleIndexes:
			partdata.append(self.particleStats(partIndex))
		return partdata

	#---------------
	def readGoodTargetImageData(self):
		particleIndexes = []
		for partnum, assignedClass in self.particleTarget.items():
			if assignedClass == 1:
				particleIndexes.append(partnum)
		particleIndexes.sort()
		partdata = []
		for partnum in particleIndexes:
			statArray = self.partnumToInputVector(partnum)
			partdata.append(statArray)
		return numpy.array(partdata)

	#---------------
	def particlePCA(self):
		partdata = self.readGoodTargetImageData()
		#print "performing principal component analysis (pca)"
		#print "partdata.shape", partdata.shape
		n_components = 20
		if n_components > math.sqrt(partdata.shape[0]):
			n_components = int(math.floor(math.sqrt(partdata.shape[0])))
		self.pca = PCA(partdata, self.boxsize, n_components)
		#print "pca complete"
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		particleEigenValues = []
		print "calculating eigen values"
		for partnum in particleIndexes:
			evals = self.getEigenValueFromPartNum(partnum)
			particleEigenValues.append(evals)
		print "eigen values complete"
		return particleEigenValues

	#---------------
	def trainSVM(self):
		particleEigenValues = self.particlePCA()
		targetData = self.targetDictToList()
		if len(numpy.unique(targetData)) < 2:
			return
		self.classifier = svm.SVC(gamma=0.001, kernel='rbf', probability=True)
		"""
		http://scikit-learn.org/stable/auto_examples/svm/plot_rbf_parameters.html

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
		print "Training classifier... (please wait)"
		self.classifier.fit(particleEigenValues, targetData)
		print "training complete"
		#predicted = classifier.predict()

	#---------------
	def particleStats(self, partnum, powerspec=None):
		"""
		rather than passing raw pixels, lets pass some key particle stats
		"""
		imgarray = self.readAndProcessParticle(partnum)
		statList = []
		if self.edgemap.shape != imgarray.shape:
			newboxsize = min(imgarray.shape)
			self.edgemap = imagefun.filled_circle((newboxsize, newboxsize), newboxsize/2.0-1.0)
		statList.extend(self.imageStats(imgarray))
		statList.extend(self.imageStats(imgarray*self.edgemap))
		statList.extend(self.imageStats(imgarray*(1-self.edgemap)))
		if powerspec is None:
			powerspec = imagefun.power(imgarray)
		statList.extend(self.imageStats(powerspec))
		statList.extend(self.imageStats(powerspec*self.edgemap))
		statList.extend(self.imageStats(powerspec*(1-self.edgemap)))
		statArray = numpy.array(statList)
		return statArray

	#---------------
	def imageStats(self, imgarray):
		imgravel = numpy.ravel(imgarray)
		mean = imgarray.mean()
		std = imgarray.std()
		minval = imgarray.min()
		maxval = imgarray.max()
		skew = scipy.stats.skew(imgravel)
		kurt = scipy.stats.kurtosis(imgravel)
		return [mean,std,minval,maxval,skew,kurt]

	#---------------
	def targetDictToList(self):
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		targetList = [self.particleTarget[i] for i in particleIndexes]
		return targetList

	#---------------
	def trainSVMOLD(self):
		partdata = self.readTargetImageData()
		targetData = self.targetDictToList()
		if len(numpy.unique(targetData)) < 2:
			return
		self.classifier = svm.SVC(gamma=0.001, kernel='rbf', probability=True)
		print "Training classifier... (please wait)"
		self.classifier.fit(partdata, targetData)
		print "training complete"
		#predicted = classifier.predict()


#=========================
class HelpAbout(wx.MessageDialog):
	#---------------
	def __init__(self, parent):
		title = 'About Learning Stack Cleaner'
		msg = ("Learning Stack Cleaner v"+parent.config.version
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

		# Initiate data class
		self.config = cfg.DataClass()

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
		self.workPanel = WorkPanel(self.scrolled_window, self.main)
		self.sizer_scroll.Add(self.workPanel, pos=(2, 1))

		# Spacers
		self.sizer_scroll.AddSpacer((10, 10), (0, 0))
		self.sizer_scroll.AddSpacer((10, 10), (1, 2))
		self.sizer_scroll.AddSpacer((10, 10), (2, 4))

		# Set up scrolling on window resize
		self.Bind(wx.EVT_SIZE, self.OnSize)

		# Set up Displays
		self.SetSize((900, 600))
		self.CreateStatusBar()
		self.SetTitle('Learning Stack Cleaner '+self.config.version)

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
		self.sizer_nav.AddSpacer((2, 2), (0, 0))
		self.sizer_nav.AddSpacer((2, 2), (2, 3))

		# Buttons for navigation
		self.button1 = wx.ToggleButton(self, label='Step 1. Training')
		self.sizer_nav.Add(self.button1, pos=(1, 1), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(1), self.button1)

		self.button2 = wx.ToggleButton(self, label='Step 2. Classify')
		self.sizer_nav.Add(self.button2, pos=(1, 2), flag=wx.EXPAND)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.EvtButton(2), self.button2)

		self.SetSizerAndFit(self.sizer_nav)
		self.buttonsList = [self.button1, self.button2, ]

	#---------------
	def EvtButton(self, pan):
		return lambda event: self.showpan(pan)

	#---------------
	def showpan(self, pan):
		self.panelsList = [ main.workPanel.trainingPanel, main.workPanel.classPanel, ]
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
		self.medianfilter = wx.TextCtrl(self.panel_stats)
		self.medianfilter.ChangeValue("2")
		self.sizer_stats.Add(self.medianfilter, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Median filter (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.lowpass = wx.TextCtrl(self.panel_stats)
		self.lowpass.ChangeValue('10')
		self.sizer_stats.Add(self.lowpass, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Low Pass (Angstroms)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.highpass = wx.TextCtrl(self.panel_stats)
		self.highpass.ChangeValue('500')
		self.sizer_stats.Add(self.highpass, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='High Pass (Angstroms)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow = 0
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		itemrow += 1
		self.pixelLimitStDev = wx.TextCtrl(self.panel_stats)
		self.pixelLimitStDev.ChangeValue('-1')
		self.sizer_stats.Add(self.pixelLimitStDev, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Pixel Limit (StdDevs)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.binning = wx.TextCtrl(self.panel_stats)
		self.binning.ChangeValue('1')
		self.sizer_stats.Add(self.binning, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Binning (integer)'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.clipping = wx.TextCtrl(self.panel_stats)
		self.clipping.ChangeValue("%d"%(data.boxsize))
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
			pos=(itemrow, itemcol), span=(1, 2), flag=wx.ALIGN_BOTTOM)

		itemrow += 1
		self.nrows = wx.TextCtrl(self.panel_stats)
		self.nrows.ChangeValue(str(displayRows))
		self.sizer_stats.Add(self.nrows, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NRows'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.ncols = wx.TextCtrl(self.panel_stats)
		self.ncols.ChangeValue(str(displayCols))
		self.sizer_stats.Add(self.ncols, pos=(itemrow, itemcol))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NCols'),
			pos=(itemrow, itemcol+1), flag=wx.ALIGN_CENTER_VERTICAL)

		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1

		self.buttonShowDiscrepancies = wx.Button(self.panel_stats, label='&Show Discrepancies', size=(120, 30))
		self.sizer_stats.Add(self.buttonShowDiscrepancies, pos=(1, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtShowDiscrepancies, self.buttonShowDiscrepancies)

		self.buttonAcceptPredict = wx.Button(self.panel_stats, label='&Accept Predictions', size=(120, 30))
		self.sizer_stats.Add(self.buttonAcceptPredict, pos=(3, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtAcceptPredict, self.buttonAcceptPredict)

		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
		itemcol += 1
		
		# New set
		self.buttonNewSet = wx.Button(self.panel_stats, label='&Refresh Set', size=(120, 30))
		self.sizer_stats.Add(self.buttonNewSet, pos=(1, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtRefreshSet, self.buttonNewSet)

		self.buttonTrainClass = wx.Button(self.panel_stats, label='&Train and Refresh', size=(120, 30))
		self.sizer_stats.Add(self.buttonTrainClass, pos=(3, itemcol), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtTrainClass, self.buttonTrainClass)

		itemcol += 1
		self.sizer_stats.AddSpacer((2, 2), (0, itemcol))
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
	def EvtRefreshSet(self, event):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		particleNumberList = main.data.getRandomImageSet(nimg)
		self.MakeDisplay(particleNumberList)

	#---------------
	def EvtTrainClass(self, event):
		self.main.data.trainSVM()
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		particleNumberList = main.data.getRandomImageSet(nimg)
		self.MakeDisplay(particleNumberList)

	#---------------
	def EvtShowDiscrepancies(self, event):
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols
		discrepancyList = main.data.getParticleDiscrepancyList(nimg)
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

		data.imgproc.lowPass = float(self.lowpass.GetValue())
		data.imgproc.lowPassType = 'tanh'
		data.imgproc.median = int(self.medianfilter.GetValue())
		data.imgproc.highPass = float(self.highpass.GetValue())
		data.imgproc.pixelLimitStDev = float(self.pixelLimitStDev.GetValue())
		clipVal = int(self.clipping.GetValue())
		if clipVal > 1 and clipVal < data.boxsize:
			data.imgproc.clipping = clipVal
		data.imgproc.bin = int(self.binning.GetValue())

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
			imgarray = main.data.readAndProcessParticle(partnum)
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

		self.main.SetStatusText('Finished generating new image set.')

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
		image.SetData(bigarray.tostring())
		wxBitmap = image.ConvertToBitmap()
		return wxBitmap

#=========================
class ClassPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel, main):
		wx.Panel.__init__(self, parentPanel)
		self.main = main

		"""
		# Set up panels
		self.panel_stats = wx.Panel(self, style=wx.SUNKEN_BORDER)
		self.panel_make_class = wx.Panel(self, style=wx.SUNKEN_BORDER)
		self.classPanel_parts = wx.Panel(self, style=wx.SUNKEN_BORDER)

		# Set up sizers
		self.sizer_class = wx.GridBagSizer(5, 5)
		self.sizer_stats = wx.GridBagSizer(5, 5)
		self.sizer_make_class = wx.GridBagSizer(5, 5)
		self.sizer_class_parts = wx.GridBagSizer(5, 5)

		# Make spacers
		self.sizer_stats.AddSpacer((10, 10), (0, 0))
		self.sizer_stats.AddSpacer((10, 10), (12, 3))
		self.sizer_make_class.AddSpacer((10, 10), (0, 0))
		self.sizer_make_class.AddSpacer((10, 10), (7, 0))
		self.sizer_make_class.AddSpacer((10, 10), (0, 3))
		self.sizer_make_class.Add(wx.StaticLine(self.panel_make_class, style=wx.LI_VERTICAL), pos=(2, 4), span=(7, 1), flag=wx.EXPAND, border=20)
		self.sizer_make_class.AddSpacer((10, 10), (0, 5))
		self.sizer_make_class.AddSpacer((10, 10), (9, 11))
		self.sizer_class_parts.AddSpacer((10, 10), (0, 0))
		self.sizer_class_parts.AddSpacer((10, 10), (4, 0))
		self.sizer_class_parts.Add(wx.StaticLine(self.classPanel_parts, style=wx.LI_VERTICAL), pos=(1, 4), span=(5, 1), flag=wx.EXPAND, border=20)
		self.sizer_class_parts.AddSpacer((10, 10), (6, 3))
		self.sizer_class_parts.AddSpacer((10, 10), (6, 5))

		# Stats panel
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='CLASSIFIER INFORMATION'), pos=(1, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='# particle images:'), pos=(2, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='# non-particle images:'), pos=(3, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Box Size (pixels):'), pos=(4, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Low Pass (Angstroms):'), pos=(5, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='High Pass (Angstroms):'), pos=(6, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Binning (Angstroms):'), pos=(7, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Clipping (Angstroms):'), pos=(8, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='# PCA bases:'), pos=(10, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Accuracy:'), pos=(11, 1))
		self.stext_npartim = wx.StaticText(self.panel_stats, label='0')
		self.stext_nnonpartim = wx.StaticText(self.panel_stats, label='0')
		self.stext_imdim = wx.StaticText(self.panel_stats, label='0x0')
		self.stext_lowpass = wx.StaticText(self.panel_stats, label='0')
		self.stext_highpass = wx.StaticText(self.panel_stats, label='0')
		self.stext_clipping = wx.StaticText(self.panel_stats, label='0')
		self.stext_rmask = wx.StaticText(self.panel_stats, label='0')
		self.stext_binning = wx.StaticText(self.panel_stats, label='0')
		self.stext_nbasis = wx.StaticText(self.panel_stats, label='0')
		self.stext_accuracy = wx.StaticText(self.panel_stats, label='0')
		self.button_load_class = wx.Button(self.panel_stats, label='Load Classifier')
		self.sizer_stats.Add(self.button_load_class, pos=(1, 2))
		self.button_reset_score = wx.Button(self.panel_stats, label='Reset Score')
		self.sizer_stats.Add(self.button_reset_score, pos=(1, 3))
		self.sizer_stats.Add(self.stext_npartim, pos=(2, 2))
		self.sizer_stats.Add(self.stext_nnonpartim, pos=(3, 2))
		self.sizer_stats.Add(self.stext_imdim, pos=(4, 2))
		self.sizer_stats.Add(self.stext_lowpass, pos=(5, 2))
		self.sizer_stats.Add(self.stext_highpass, pos=(6, 2))
		self.sizer_stats.Add(self.stext_clipping, pos=(7, 2))
		self.sizer_stats.Add(self.stext_rmask, pos=(8, 2))
		self.sizer_stats.Add(self.stext_binning, pos=(9, 2))
		self.sizer_stats.Add(self.stext_nbasis, pos=(10, 2))
		self.sizer_stats.Add(self.stext_accuracy, pos=(11, 2))
		self.Bind(wx.EVT_BUTTON, self.EvtLoadClass, self.button_load_class)
		self.Bind(wx.EVT_BUTTON, self.EvtResetScore, self.button_reset_score)

		# Make class panel left
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='CREATE CLASSIFIER'), pos=(1, 1), span=(1, 2))
		self.lowpass1 = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.lowpass1, pos=(2, 1))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='PSize (Angstroms)'), pos=(2, 2), flag=wx.ALIGN_CENTER_VERTICAL)
		self.highpass = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.highpass, pos=(3, 1))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='RMax1 (Angstroms)'), pos=(3, 2), flag=wx.ALIGN_CENTER_VERTICAL)
		self.clipping = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.clipping, pos=(4, 1))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='RMax2 (Angstroms)'), pos=(4, 2), flag=wx.ALIGN_CENTER_VERTICAL)
		self.maskrad = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.maskrad, pos=(5, 1))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='RMask (Angstroms)'), pos=(5, 2), flag=wx.ALIGN_CENTER_VERTICAL)
		self.binning = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.binning, pos=(6, 1))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Downsize (integer)'), pos=(6, 2), flag=wx.ALIGN_CENTER_VERTICAL)
		self.buttonMakeClass = wx.Button(self.panel_make_class, label='Train classifier', size=(200, 40))
		self.sizer_make_class.Add(self.buttonMakeClass, pos=(8, 1), span=(1, 2), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtTrainClass, self.buttonMakeClass)

		# Make class panel right
		self.niter = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.niter, pos=(1, 7))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='NIterations (integer)'), pos=(1, 6), flag=wx.ALIGN_CENTER_VERTICAL)
		self.lowpass2 = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.lowpass2, pos=(2, 7))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='PSize (Angstroms)'), pos=(2, 6), flag=wx.ALIGN_CENTER_VERTICAL)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Optimize RMax1 from'), pos=(3, 6), flag=wx.ALIGN_CENTER_VERTICAL)
		self.opt_highpass_min = wx.TextCtrl(self.panel_make_class)
		self.opt_highpass_max = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.opt_highpass_min, pos=(3, 7))
		self.sizer_make_class.Add(self.opt_highpass_max, pos=(3, 9))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='to'), pos=(3, 8), flag=wx.ALIGN_CENTER)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Angstroms'), pos=(3, 10), flag=wx.ALIGN_CENTER_VERTICAL)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Optimize RMax2 from'), pos=(4, 6), flag=wx.ALIGN_CENTER_VERTICAL)
		self.opt_clipping_min = wx.TextCtrl(self.panel_make_class)
		self.opt_clipping_max = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.opt_clipping_min, pos=(4, 7))
		self.sizer_make_class.Add(self.opt_clipping_max, pos=(4, 9))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='to'), pos=(4, 8), flag=wx.ALIGN_CENTER)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Angstroms'), pos=(4, 10), flag=wx.ALIGN_CENTER_VERTICAL)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Optimize RMask from'), pos=(5, 6), flag=wx.ALIGN_CENTER_VERTICAL)
		self.opt_rmask_min = wx.TextCtrl(self.panel_make_class)
		self.opt_rmask_max = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.opt_rmask_min, pos=(5, 7))
		self.sizer_make_class.Add(self.opt_rmask_max, pos=(5, 9))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='to'), pos=(5, 8), flag=wx.ALIGN_CENTER)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Angstroms'), pos=(5, 10), flag=wx.ALIGN_CENTER_VERTICAL)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='Optimize Downsize from'), pos=(6, 6), flag=wx.ALIGN_CENTER_VERTICAL)
		self.opt_binning_min = wx.TextCtrl(self.panel_make_class)
		self.opt_binning_max = wx.TextCtrl(self.panel_make_class)
		self.sizer_make_class.Add(self.opt_binning_min, pos=(6, 7))
		self.sizer_make_class.Add(self.opt_binning_max, pos=(6, 9))
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='to'), pos=(6, 8), flag=wx.ALIGN_CENTER)
		self.sizer_make_class.Add(wx.StaticText(self.panel_make_class, label='factors'), pos=(6, 10), flag=wx.ALIGN_CENTER_VERTICAL)
		self.buttonOptimize = wx.Button(self.panel_make_class, label='Optimize classifier', size=(250, 40))
		self.sizer_make_class.Add(self.buttonOptimize, pos=(8, 6), span=(1, 5), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtOptimizeTrainClass, self.buttonOptimize)

		# Classify parts panel
		self.sizer_class_parts.Add(wx.StaticText(self.classPanel_parts, label='CLASSIFY IMAGES'), pos=(1, 1), span=(1, 2))
		self.sizer_class_parts.Add(wx.StaticText(self.classPanel_parts, label='Images imported:'), pos=(2, 1))
		self.stext_nparts = wx.StaticText(self.classPanel_parts, label='0')
		self.sizer_class_parts.Add(self.stext_nparts, pos=(2, 2))
		self.sizer_class_parts.Add(wx.StaticText(self.classPanel_parts, label='Images labeled:'), pos=(3, 1))
		self.stext_nlabel = wx.StaticText(self.classPanel_parts, label='0 (0 %)')
		self.sizer_class_parts.Add(self.stext_nlabel, pos=(3, 2))
		self.buttonClass = wx.Button(self.classPanel_parts, label='Classify images', size=(200, 40))
		self.sizer_class_parts.Add(self.buttonClass, pos=(5, 1), span=(1, 2), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtClassParts, self.buttonClass)

		# Set sizers
		self.sizer_class.Add(self.panel_stats, pos=(0, 0), flag=wx.EXPAND)
		self.sizer_class.Add(self.panel_make_class, pos=(2, 0), flag=wx.EXPAND)
		self.sizer_class.Add(self.classPanel_parts, pos=(4, 0), flag=wx.EXPAND)
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_make_class.SetSizerAndFit(self.sizer_make_class)
		self.classPanel_parts.SetSizerAndFit(self.sizer_class_parts)
		self.SetSizerAndFit(self.sizer_class)

	#---------------
	def EvtTrainClass(self, event):
		TrainClass(0)

	#---------------
	def EvtOptimizeTrainClass(self, event):
		TrainClass(1)

	#---------------
	def EvtClassParts(self, event):
		ClassParts()

	#---------------
	def EvtLoadClass(self, event):
		try:
			with func.BrowseOpenFile(main) as dlg:
				temp = pickle.load(open(dlg.path, 'rb'))
				self.main.data.imdim = temp.imdim
				self.main.data.bases = temp.bases
				self.main.data.model = temp.model
				self.main.data.nbas = temp.nbas
				self.main.data.n_true = temp.n_true
				self.main.data.n_false = temp.n_false
				self.main.data.lowpass_class = temp.lowpass_class
				self.main.data.highpass_class = temp.highpass_class
				self.main.data.clipping_class = temp.clipping_class
				self.main.data.maskrad_class = temp.maskrad_class
				self.main.data.binning_class = temp.binning_class
				self.main.data.score_class = temp.score_class
				self.main.data.param = temp.param

				# Update classifier info
				self.stext_npartim.SetLabel(str(self.main.data.n_true))
				self.stext_nnonpartim.SetLabel(str(self.main.data.n_false))
				self.stext_imdim.SetLabel(self.main.data.imdim)
				self.stext_lowpass.SetLabel(self.main.data.lowpass_class)
				self.stext_highpass.SetLabel(self.main.data.highpass_class)
				self.stext_clipping.SetLabel(self.main.data.clipping_class)
				self.stext_rmask.SetLabel(self.main.data.maskrad_class)
				self.stext_binning.SetLabel(self.main.data.binning_class)
				self.stext_nbasis.SetLabel(str(self.main.data.nbas))
		except:
				self.main.SetStatusText("ERROR: could not load classifier")

	#---------------
	def EvtResetScore(self, event):
		self.main.data.score_class = 0
	"""

# Classify functions
class TrainClass:
	def __init__(self,optimize):
		self.main.SetStatusText('Compiling new training set...')

		# Define variables
		nfilms = len(self.main.data.fileList)
		ind = main.data.imdim.find('x')
		dim = int(self.main.data.imdim[:ind])
		psize = float(self.main.panel_work.panel_class.psize1.GetValue())
		rmax1 = float(self.main.panel_work.panel_class.rmax1.GetValue())
		rmax2 = float(self.main.panel_work.panel_class.rmax2.GetValue())
		mask = float(self.main.panel_work.panel_class.maskrad.GetValue())
		downsize = int(self.main.panel_work.panel_class.downsize.GetValue())
		niter = int(self.main.panel_work.panel_class.niter.GetValue())
		# Train
		new_class = func.TrainNewClass(optimize,nfilms,dim,kwrds,main.data.score_class,main.data.partsList,main.data.partclass,main.data.fileList)
		self.main.data.model = new_class.model
		self.main.data.bases = new_class.bases
		self.main.data.class_par = new_class.class_par
		self.main.panel_work.panel_class.stext_accuracy.SetLabel('N/A')
		self.main.data.n_true = new_class.n_true
		self.main.data.n_false = new_class.n_false
		self.main.data.nbas = new_class.nbas
		self.main.data.score_class = new_class.score_class

		self.score_class = score_class
		self.n_true = n_true
		self.n_false = n_false
		self.nbas = nbas #number of pixels

		# Import images and create training sets
		if optimize == 0:
			self.train_set_true = numpy.zeros((n_true,im_dim*im_dim))
			self.train_set_false = numpy.zeros((n_false,im_dim*im_dim))
		if optimize == 1:
			self.im_set_true = numpy.zeros((n_true,dim,dim))
			self.im_set_false = numpy.zeros((n_false,dim,dim))
		i_true = -1
		i_false = -1
		progress1 = 0
		for i in range(nfilms):
				progress2 = int(100*i/nfilms)
				if progress2>progress1:
					print 'Compiling training sets...'+str(progress2)+'%'
					progress1 = progress2
				imagestk = mrc.mrc_image(fileList[i])
				imagestk.read()
				for j in range(n_true):
					if i == trainList_true[j][0]:
						i_true = i_true + 1
						if optimize == 0:
								im_mod = PreTreat(imagestk.image_data[trainList_true[j][1],:,:],psize,rmax1,rmax2,mask,downsize)
								self.train_set_true[i_true,:] = im_mod.im_mod2.reshape(im_dim*im_dim)
						elif optimize == 1:
								self.im_set_true[i_true,:,:] = imagestk.image_data[trainList_true[j][1],:,:]
				for j in range(n_false):
					if i == trainList_false[j][0]:
						i_false = i_false + 1
						if optimize == 0:
								im_mod = PreTreat(imagestk.image_data[trainList_false[j][1],:,:],psize,rmax1,rmax2,mask,downsize)
								self.train_set_false[i_false,:] = im_mod.im_mod2.reshape(im_dim*im_dim)
						elif optimize ==1:
								self.im_set_false[i_false,:,:] = imagestk.image_data[trainList_false[j][1],:,:]

		self.labels = numpy.zeros(n_true+n_false)
		self.labels[:n_true] = 1
		self.labels[n_true:] = 2

		# Train
		if optimize == 0:
				self.train(n_true,n_false,nbas)
		elif optimize == 1:
				self.optimize_parameters(niter,n_true,n_false,nbas,dim,psize,rmax1_min,rmax1_max,rmax2_min,rmax2_max,mask_min,mask_max,downsize_min,downsize_max)

	def train(self,n_true,n_false,nbas):
		print 'Training classifier...'
		self.train_set_true = self.train_set_true.transpose()
		self.train_set_false = self.train_set_false.transpose()

		# Perform SVD
		U_true,s_true,V_true = numpy.linalg.svd(self.train_set_true,full_matrices=0)

		# Construct training set
		train_set_svd = numpy.zeros((n_true+n_false,U_true.shape[1]))
		train_set_svd[:n_true,:] = numpy.dot(U_true[:,:].transpose(),self.train_set_true).transpose()
		train_set_svd[n_true:,:] = numpy.dot(U_true[:,:].transpose(),self.train_set_false).transpose()

		# Train classifier
		param = mlk.svm_raw_mod(C=1,kernel=milk.supervised.svm.rbf_kernel(nbas))
		learner_svm = milk.supervised.multi.one_against_one(milk.supervised.svm.svm_to_binary(param))
		self.model = learner_svm.train(train_set_svd,self.labels)
		self.bases = U_true
		self.class_par = 1

	def optimize_parameters(self,niter,n_true,n_false,nbas,dim,psize,rmax1_min,rmax1_max,rmax2_min,rmax2_max,mask_min,mask_max,downsize_min,downsize_max):

		def function_ncrossval(param,n_true,n_false,nbas,dim,psize,rmax1_min,rmax1_max,rmax2_min,rmax2_max,mask_min,mask_max,downsize_min,downsize_max,downsize):

				# Prepare training sets
				for i in range(n_true):
					im_mod = PreTreat(self.im_set_true[i,:,:],psize,param[0],param[1],param[2],downsize)
					self.train_set_true[i,:] = im_mod.im_mod2.reshape(dim*dim)
				for i in range(n_false):
					im_mod = PreTreat(self.im_set_false[i,:,:],psize,param[0],param[1],param[2],downsize)
					self.train_set_false[i,:] = im_mod.im_mod2.reshape(dim*dim)

				# Perform 10-fold cross-validation
				nparts = n_true + n_false
				n_fold = int(nparts/10)
				queue = range(nparts)
				cmatrix = numpy.zeros((2,2))

				for i in range(10):

					# Pick random test set
					list_test = []
					n_true_train = n_true
					n_false_train = n_false
					n_true_test = 0
					n_false_test = 0
					if i<9:
						for j in range(n_fold):
								list_test.append(random.choice(queue))
								if list_test[j] < n_true:
									n_true_train = n_true_train - 1
									n_true_test = n_true_test + 1
								elif list_test[j] >= n_true:
									n_false_train = n_false_train - 1
									n_false_test = n_false_test + 1
								del queue[queue.index(list_test[j])]
					elif i ==9:
						for j in range(nparts-9*n_fold):
								list_test.append(random.choice(queue))
								if list_test[j] < n_true:
									n_true_train = n_true_train - 1
									n_true_test = n_true_test + 1
								elif list_test[j] >= n_true:
									n_false_train = n_false_train - 1
									n_false_test = n_false_test + 1
								del queue[queue.index(list_test[j])]

				# Construct training sets
					train_true = numpy.zeros((n_true_train,dim*dim))
					train_false = numpy.zeros((n_false_train,dim*dim))
					test_set = numpy.zeros((n_true_test+n_false_test,dim*dim))
					k = 0
					l = 0
					for j in range(n_true):
						try:
								list_test.index(j)
								test_set[l,:] = self.train_set_true[j,:]
								l = l + 1
						except:
								train_true[k,:] = self.train_set_true[j,:]
								k = k + 1
					k = 0
					for j in range(n_false):
						try:
								list_test.index(j+n_true)
								test_set[l,:] = self.train_set_false[j,:]
								l = l + 1
						except:
								train_false[k,:] = self.train_set_false[j,:]
								k = k + 1
					train_true = train_true.transpose()
					train_false = train_false.transpose()
					test_set = test_set.transpose()

					# Perform SVD
					for i in range(n_true_train):
						dummy = numpy.where(numpy.isnan(train_true[:,i])==True)
						n_dummy = len(dummy[0])
						if n_dummy>0:
								print '********NaN ERROR********: image=',i,', #NaN=',n_dummy
					U_true,s_true,V_true = numpy.linalg.svd(train_true,full_matrices=0)
					U_true = U_true.transpose()

					# Construct training set
					train_set_svd = numpy.zeros((n_true_train+n_false_train,U_true.shape[0]))
					train_set_svd[:n_true_train,:] = numpy.dot(U_true[:,:],train_true).transpose()
					train_set_svd[n_true_train:,:] = numpy.dot(U_true[:,:],train_false).transpose()
					labels = numpy.zeros(n_true_train+n_false_train)
					labels[:n_true_train] = 1
					labels[n_true_train:] = 2

					# Train classifier
					parameter = mlk.svm_raw_mod(C=1,kernel=milk.supervised.svm.rbf_kernel(n_true_train))
					learner_svm = milk.supervised.multi.one_against_one(milk.supervised.svm.svm_to_binary(parameter))
					model = learner_svm.train(train_set_svd,labels)

					# Test classifier
					labels = numpy.zeros(n_true_test+n_false_test)
					labels[:n_true_test] = 1
					labels[n_true_test:] = 2
					test_set_svd = numpy.dot(U_true[:,:],test_set).transpose()
					for j in range(n_true_test+n_false_test):
						output = model.apply(test_set_svd[j,:])
						if output == labels[j]:
								if output == 1:
									cmatrix[0,0] = cmatrix[0,0] + 1
								elif output == 2:
									cmatrix[1,1] = cmatrix[1,1] + 1
						elif output != labels[j]:
								if output == 1:
									cmatrix[1,0] = cmatrix[1,0] + 1
								elif output == 2:
									cmatrix[0,1] = cmatrix[0,1] + 1

				# Output
				print 'R_max1 =',param[0],', R_max2 =',param[1],', Mask radius =',param[2],', Downsize =',downsize
				accur = cmatrix.trace()/float(cmatrix.sum())
				print 'Accuracy:', accur
				return -accur

		# Loop
		print 'Optimizing classifier...'

		self.param = [0,0,0,0]
		dotrain = 0

		for y in range(int(downsize_max-downsize_min+1)):
				downsize = int(downsize_min + y)
				print 'Downsize =', downsize

				# Correct for downsize
				dim_new = int(dim/downsize)
				self.train_set_true = numpy.zeros((n_true,dim_new*dim_new))
				self.train_set_false = numpy.zeros((n_false,dim_new*dim_new))

				try:
					for x in range(niter):
						print 'Iteration: ',x+1

						# Initiate random variables within range
						param = numpy.zeros(3)
						param_best = numpy.zeros(3)
						score_best = 0
						for i in range(10):
								param[0] = random.random()*(rmax1_max-rmax1_min) + rmax1_min
								param[1] = random.random()*(rmax2_max-rmax2_min) + rmax2_min
								param[2] = random.random()*(mask_max-mask_min) + mask_min
								print "Random point:", i+1

								# Perform 10-fold cross-validation
								test1 = function_ncrossval(param,n_true,n_false,nbas,dim_new,psize,rmax1_min,rmax1_max,rmax2_min,rmax2_max,mask_min,mask_max,downsize_min,downsize_max,downsize)
								if -test1 > score_best:
									param_best[0] = param[0]
									param_best[1] = param[1]
									param_best[2] = param[2]
									score_best = -test1

						# Optimize function
						print 'Optimizing around ', param_best
						min_func = scipy.optimize.fmin(function_ncrossval,param_best,
																	args=(n_true,n_false,nbas,dim_new,psize,rmax1_min,
																			rmax1_max,rmax2_min,rmax2_max,mask_min,mask_max,
																			downsize_min,downsize_max,downsize),maxiter=5,full_output=True)
						if -min_func[1] > self.score_class:
							self.param[0] = min_func[0][0]
							self.param[1] = min_func[0][1]
							self.param[2] = min_func[0][2]
							self.param[3] = downsize
							self.score_class = -min_func[1]
							dotrain = 1
				except:
					print "Skipping downsize = ",downsize
					raise

		print 'Best score =',self.score_class,', Parameters =',self.param

		# Construct training set and train
		if dotrain == 1:
			dim = int(dim/self.param[3])
			self.train_set_true = numpy.zeros((n_true,dim*dim))
			self.train_set_false = numpy.zeros((n_false,dim*dim))
			for i in range(n_true):
				im_mod = PreTreat(self.im_set_true[i,:,:],psize,self.param[0],self.param[1],self.param[2],self.param[3])
				self.train_set_true[i,:] = im_mod.im_mod2.reshape(dim*dim)
			for i in range(n_false):
				im_mod = PreTreat(self.im_set_false[i,:,:],psize,self.param[0],self.param[1],self.param[2],self.param[3])
				self.train_set_false[i,:] = im_mod.im_mod2.reshape(dim*dim)
			self.train(n_true,n_false,nbas)


#=========================
#=========================
if __name__=='__main__':
	app = wx.App()
	data = DataClass()
	main = MainWindow(data)
	main.Show()
	app.MainLoop()
