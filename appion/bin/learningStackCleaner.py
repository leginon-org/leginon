#!/usr/bin/env python

import os
import wx
import cfg
import numpy
import random
import scipy.stats
from pyami import imagefun
from appionlib import apFile
from appionlib import apImagicFile
from appionlib.apImage import imageprocess
from appionlib.apImage import imagenorm
from sklearn import svm

### TODO
# rm import cfg
# save/load particle data to file (prevent crash on refresh)
# fix refresh seg fault

#=========================
class DataClass(object):
	#---------------
	def __init__(self):
		self.stackfile = "/emg/data/appion/06jul12a/stacks/stack1/start.hed"
		self.numpart = apFile.numImagesInStack(self.stackfile)
		self.boxsize = apFile.getBoxSize(self.stackfile)[0]
		print "Num Part %d, Box Size %d"%(self.numpart, self.boxsize)
		self.edgemap = imagefun.filled_circle((self.boxsize, self.boxsize), self.boxsize/2.0-1.0)

		### create a map to random particles
		self.particleMap = range(self.numpart)
		random.shuffle(self.particleMap)
		self.particleTarget = {} #0 = ???, 1 = good, 2 = bad
		self.lastImageRead = 0
		self.classifier = None
		self.count = 0
		self.statCache = {}

	#---------------
	def getParticleTarget(self, partNum):
		return self.particleTarget.get(partNum,0)

	#---------------
	def updateParticleTarget(self, partNum):
		value = self.particleTarget.get(partNum,0)
		print self.particleTarget
		self.particleTarget[partNum] = (value + 1) % 3

	#---------------
	def readRandomImage(self):
		partnum = self.particleMap[self.lastImageRead]
		imgarray = apImagicFile.readSingleParticleFromStack(self.stackfile, 
			partnum=(partnum+1), boxsize=self.boxsize, msg=False)
		self.lastImageRead += 1
		if self.classifier is None:
			assignedClass = 0
		else:
			partstats = self.particleStats(partnum)
			print partnum, len(partstats), numpy.around(partstats[3:6],3)
			assignedClass = self.classifier.predict(partstats)[0]
			probClass = self.classifier.predict_proba(partstats)[0]
			print "assignedClass: %d -- probClass1: %.3f"%(assignedClass, probClass[0])
		return imgarray, partnum, assignedClass

	#---------------
	def readTargetImageData(self):
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		partdata = []
		for partIndex in particleIndexes:
			partdata.append(self.particleStats(partIndex))
		return partdata

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
	def particleStats(self, partnum):
		"""
		rather than passing raw pixels, lets pass some key particle stats
		
		use cache to prevent double reading
		"""
		try:
			return self.statCache[partnum]
		except KeyError:
			pass
		imgarray = apImagicFile.readSingleParticleFromStack(self.stackfile, 
			partnum=(partnum+1), boxsize=self.boxsize, msg=False)
		statList = []
		statList.extend(self.imageStats(imgarray))
		statList.extend(self.imageStats(imgarray*self.edgemap))
		statList.extend(self.imageStats(imgarray*(1-self.edgemap)))
		powerspec = imagefun.power(imgarray)
		statList.extend(self.imageStats(powerspec))
		statList.extend(self.imageStats(powerspec*self.edgemap))
		statList.extend(self.imageStats(powerspec*(1-self.edgemap)))
		statArray = numpy.hstack((statList, imgarray.ravel()))
		self.statCache[partnum] = statArray
		return statArray

	#---------------
	def targetDictToList(self):
		particleIndexes = self.particleTarget.keys()
		particleIndexes.sort()
		targetList = [self.particleTarget[i] for i in particleIndexes]
		return targetList

	#---------------
	def trainSVM(self):
		partdata = self.readTargetImageData()
		targetData = self.targetDictToList()
		if len(numpy.unique(targetData)) < 2:
			return
		self.classifier = svm.SVC(gamma=0.001, kernel='rbf', probability=True)
		print "Training classifier... (please wait)"
		"""
		'cache_size', 'class_weight', 'coef0', 'coef_', 'decision_function', 'degree',
		'epsilon', 'fit', 'gamma', 'get_params', 'kernel', 'label_', 'max_iter', 'nu',
		'predict', 'predict_log_proba', 'predict_proba', 'probability', 'random_state',
		'score', 'set_params', 'shrinking', 'tol', 'verbose'
		"""
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
		self.navigationPanel = NavPanel(self.scrolled_window)
		self.sizer_scroll.Add(self.navigationPanel, pos=(1, 1))
		self.workPanel = WorkPanel(self.scrolled_window)
		self.sizer_scroll.Add(self.workPanel, pos=(2, 1))

		# Spacers
		self.sizer_scroll.AddSpacer((10, 10), (0, 0))
		self.sizer_scroll.AddSpacer((10, 10), (1, 2))
		self.sizer_scroll.AddSpacer((10, 10), (2, 4))

		# Set up scrolling on window resize
		self.Bind(wx.EVT_SIZE, self.OnSize)

		# Set up Displays
		self.SetSize((900, 500))
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
	def __init__(self, parentPanel):
		wx.Panel.__init__(self, parentPanel, style=wx.SIMPLE_BORDER)

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
		main.workPanel.sizer_work = wx.GridBagSizer(0, 0)
		self.buttonsList[pan-1].SetValue(1)
		main.workPanel.sizer_work.Add(self.panelsList[pan-1], (0, 0))
		self.panelsList[pan-1].Show()
		main.workPanel.SetSizerAndFit(main.workPanel.sizer_work)
		main.scrolled_window.SetSize(main.GetClientSize())

#=========================
class WorkPanel(wx.Panel):
	#---------------
	def __init__(self, parentWindow):
		wx.Panel.__init__(self, parentWindow)
		self.MainWindow = parentWindow

		# Make panels
		self.trainingPanel = TrainPanel(self)
		self.trainingPanel.Hide()
		self.classPanel = ClassPanel(self)
		self.classPanel.Hide()

#=========================
class TrainPanel(wx.Panel):
	#---------------
	def __init__(self, parentPanel):
		wx.Panel.__init__(self, parentPanel)
		self.workPanel = parentPanel
		self.part_display = False

		self.imgproc = imageprocess.ImageFilter()
		self.imgproc.msg = False

		# Set up panels
		self.panel_stats = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.panel_image = wx.Panel(self, style=wx.SUNKEN_BORDER)

		# Set up sizers
		self.sizer_train = wx.GridBagSizer(5, 5)
		self.sizer_stats = wx.GridBagSizer(5, 5)
		self.sizer_image = wx.GridBagSizer(5, 5)

		self.sizer_stats.AddSpacer((2, 2), (0, 0))
		self.sizer_stats.AddSpacer((2, 2), (0, 3))
		self.sizer_stats.AddSpacer((2, 2), (0, 6))

		itemrow = 0
		# Image pretreatment options
		itemrow += 1
		self.lowpass = wx.TextCtrl(self.panel_stats)
		self.lowpass.ChangeValue('15')
		self.sizer_stats.Add(self.lowpass, pos=(itemrow, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Low Pass (Angstroms)'), pos=(itemrow, 2), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.highpass = wx.TextCtrl(self.panel_stats)
		self.highpass.ChangeValue('1000')
		self.sizer_stats.Add(self.highpass, pos=(itemrow, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='High Pass (Angstroms)'), pos=(itemrow, 2), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.binning = wx.TextCtrl(self.panel_stats)
		self.binning.ChangeValue('2')
		self.sizer_stats.Add(self.binning, pos=(itemrow, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Binning (integer)'), pos=(itemrow, 2), flag=wx.ALIGN_CENTER_VERTICAL)

		itemrow += 1
		self.clipping = wx.TextCtrl(self.panel_stats)
		self.clipping.ChangeValue('0')
		self.sizer_stats.Add(self.clipping, pos=(itemrow, 1))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Clipping (integer)'), pos=(itemrow, 2), flag=wx.ALIGN_CENTER_VERTICAL)

		# Display info
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='Particle image display:'), pos=(1, 4), span=(1, 2), flag=wx.ALIGN_BOTTOM)
		self.nrows = wx.TextCtrl(self.panel_stats)
		displayRows = 2 #int(self.workPanel.MainWindow.GetClientSize()[0]/128.)
		displayCols = 6 #int(self.workPanel.MainWindow.GetClientSize()[1]/128.)
		self.nrows.ChangeValue(str(displayRows))
		self.sizer_stats.Add(self.nrows, pos=(2, 4))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NRows'), pos=(2, 5), flag=wx.ALIGN_CENTER_VERTICAL)
		self.ncols = wx.TextCtrl(self.panel_stats)
		self.ncols.ChangeValue(str(displayCols))
		self.sizer_stats.Add(self.ncols, pos=(3, 4))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NCols'), pos=(3, 5), flag=wx.ALIGN_CENTER_VERTICAL)

		# New set
		self.buttonNewSet = wx.Button(self.panel_stats, label='Refresh Set', size=(120, 40))
		self.sizer_stats.Add(self.buttonNewSet, pos=(1, 7), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtRefreshSet, self.buttonNewSet)

		self.buttonTrainClass = wx.Button(self.panel_stats, label='Train and Refresh', size=(120, 40))
		self.sizer_stats.Add(self.buttonTrainClass, pos=(3, 7), span=(2, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtTrainClass, self.buttonTrainClass)

		# Set sizers
		self.sizer_train.Add(self.panel_stats, pos=(0, 0))
		self.sizer_train.AddSpacer((2, 2), (1, 0))
		self.sizer_train.Add(self.panel_image, pos=(2, 0))
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_image.SetSizerAndFit(self.sizer_image)
		self.SetSizerAndFit(self.sizer_train)

	#---------------
	def EvtRefreshSet(self, event):
		self.MakeDisplay()

	#---------------
	def EvtTrainClass(self, event):
		main.data.trainSVM()
		self.MakeDisplay()

	#---------------
	def MakeDisplay(self):
		print "MakeDisplay 1"
		nrows = int(self.nrows.GetValue())
		ncols = int(self.ncols.GetValue())
		nimg = nrows*ncols

		self.imgproc.lowPass = float(self.lowpass.GetValue())
		self.imgproc.lowPassType = 'tanh'
		self.imgproc.highPass = float(self.highpass.GetValue())
		#self.imgproc.clipping = float(self.clipping.GetValue())
		self.imgproc.bin = int(self.binning.GetValue())

		print "MakeDisplay 2"

		# Delete previous objects
		#self.sizer_image.Destroy()
		self.panel_image.DestroyChildren()
		#self.panel_image.Destroy()
		#self.panel_image = wx.Panel(self, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.sizer_image = wx.GridBagSizer(nrows, ncols)
		imagePanel = self.panel_image
		imageSizer = self.sizer_image

		print "MakeDisplay 3"

		imgbutton_list = []
		for i in range(nimg):
			row = int(i / ncols)
			col = i % ncols
			#print row, col
			main.SetStatusText("Preparing image %d of %d for display..."%(i, nimg))
			filepartnum = main.data.particleMap[i]+1
			imgarray, partnum, assignedClass = main.data.readRandomImage()
			procarray = self.imgproc.processImage(imgarray)
			imgbutton = ImageButton(imagePanel, procarray, partnum)
			imgbutton.SetPredictedClass(assignedClass)
			imageSizer.Add(imgbutton, pos=(row, col))
			imgbutton_list.append(imgbutton)

		print "MakeDisplay 4"

		print "MakeDisplay 4a - hidden"
		#imagePanel.SetSizerAndFit(imageSizer)
		print "MakeDisplay 4b - hidden"
		#self.panel_stats.SetSizerAndFit(self.sizer_stats)
		print "MakeDisplay 4c - required / crash here"
		self.panel_image.SetSizerAndFit(self.sizer_image)
		print "MakeDisplay 4d - required"
		self.SetSizerAndFit(self.sizer_train)
		print "MakeDisplay 4e - required"
		self.workPanel.SetSizerAndFit(self.workPanel.sizer_work)

		print "MakeDisplay 5"

		main.scrolled_window.SetSize(main.GetClientSize())
		main.SetStatusText('Finished generating new image set.')

#=========================
class ImageButton(wx.Panel):
	#---------------
	def __init__(self, parentPanel, imgarray, particleNum):
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
	def SetPredictedClass(self, assignedClass):
		if assignedClass == 1:
			self.SetBackgroundColour('GREEN YELLOW')
		elif assignedClass == 2:
			self.SetBackgroundColour('PINK')
		else:
			self.SetBackgroundColour(wx.NullColor)

	#---------------
	def ImageClick(self, event):
		# Set background colour of particle images based on class
		main.data.updateParticleTarget(self.particleNum)
		setting = main.data.getParticleTarget(self.particleNum)
		if setting == 1:
			self.SetBackgroundColour('FOREST GREEN')
		elif setting == 2:
			self.SetBackgroundColour('FIREBRICK')
		else:
			self.SetBackgroundColour(wx.NullColor)
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
	def __init__(self, parentPanel):
		wx.Panel.__init__(self, parentPanel)

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
				main.data.imdim = temp.imdim
				main.data.bases = temp.bases
				main.data.model = temp.model
				main.data.nbas = temp.nbas
				main.data.n_true = temp.n_true
				main.data.n_false = temp.n_false
				main.data.lowpass_class = temp.lowpass_class
				main.data.highpass_class = temp.highpass_class
				main.data.clipping_class = temp.clipping_class
				main.data.maskrad_class = temp.maskrad_class
				main.data.binning_class = temp.binning_class
				main.data.score_class = temp.score_class
				main.data.param = temp.param

				# Update classifier info
				self.stext_npartim.SetLabel(str(main.data.n_true))
				self.stext_nnonpartim.SetLabel(str(main.data.n_false))
				self.stext_imdim.SetLabel(main.data.imdim)
				self.stext_lowpass.SetLabel(main.data.lowpass_class)
				self.stext_highpass.SetLabel(main.data.highpass_class)
				self.stext_clipping.SetLabel(main.data.clipping_class)
				self.stext_rmask.SetLabel(main.data.maskrad_class)
				self.stext_binning.SetLabel(main.data.binning_class)
				self.stext_nbasis.SetLabel(str(main.data.nbas))
		except:
				main.SetStatusText("ERROR: could not load classifier")

	#---------------
	def EvtResetScore(self, event):
		main.data.score_class = 0
	"""

# Classify functions
class TrainClass:
	def __init__(self,optimize):
		main.SetStatusText('Compiling new training set...')

		# Define variables
		nfilms = len(main.data.fileList)
		ind = main.data.imdim.find('x')
		dim = int(main.data.imdim[:ind])
		if optimize == 0:
			psize = float(main.panel_work.panel_class.psize1.GetValue())
			rmax1 = float(main.panel_work.panel_class.rmax1.GetValue())
			rmax2 = float(main.panel_work.panel_class.rmax2.GetValue())
			mask = float(main.panel_work.panel_class.maskrad.GetValue())
			downsize = int(main.panel_work.panel_class.downsize.GetValue())
			kwrds = [psize,rmax1,rmax2,mask,downsize]
			main.SetStatusText('Training classifier...(see terminal for details)')
		elif optimize == 1:
			niter = int(main.panel_work.panel_class.niter.GetValue())
			psize = float(main.panel_work.panel_class.psize2.GetValue())
			rmax1_min = float(main.panel_work.panel_class.opt_rmax1_min.GetValue())
			rmax1_max = float(main.panel_work.panel_class.opt_rmax1_max.GetValue())
			rmax2_min = float(main.panel_work.panel_class.opt_rmax2_min.GetValue())
			rmax2_max = float(main.panel_work.panel_class.opt_rmax2_max.GetValue())
			mask_min = float(main.panel_work.panel_class.opt_rmask_min.GetValue())
			mask_max = float(main.panel_work.panel_class.opt_rmask_max.GetValue())
			downsize_min = float(main.panel_work.panel_class.opt_downsize_min.GetValue())
			downsize_max = float(main.panel_work.panel_class.opt_downsize_max.GetValue())
			kwrds = [niter,psize,rmax1_min,rmax1_max,rmax2_min,rmax2_max,mask_min,mask_max,downsize_min,downsize_max]
			main.SetStatusText('Optimizing classifier...(see terminal for details)')

		# Train
		new_class = func.TrainNewClass(optimize,nfilms,dim,kwrds,main.data.score_class,main.data.partsList,main.data.partclass,main.data.fileList)
		if optimize == 0:
			main.data.model = new_class.model
			main.data.bases = new_class.bases
			main.data.class_par = new_class.class_par
			main.data.psize_class = main.panel_work.panel_class.psize1.GetValue()
			main.data.rmax1_class = main.panel_work.panel_class.rmax1.GetValue()
			main.data.rmax2_class = main.panel_work.panel_class.rmax2.GetValue()
			main.data.maskrad_class = main.panel_work.panel_class.maskrad.GetValue()
			main.data.downsize_class = main.panel_work.panel_class.downsize.GetValue()
			main.panel_work.panel_class.stext_accuracy.SetLabel('N/A')
			main.data.n_true = new_class.n_true
			main.data.n_false = new_class.n_false
			main.data.nbas = new_class.nbas
		elif optimize == 1:
			if new_class.score_class > main.data.score_class:
				main.data.model = new_class.model
				main.data.bases = new_class.bases
				main.data.class_par = new_class.class_par
				main.data.psize_class = main.panel_work.panel_class.psize2.GetValue()
				main.data.rmax1_class = str(new_class.param[0])
				main.data.rmax2_class = str(new_class.param[1])
				main.data.maskrad_class = str(new_class.param[2])
				main.data.downsize_class = str(new_class.param[3])
				main.data.score_class = new_class.score_class
				main.panel_work.panel_class.stext_accuracy.SetLabel(str(main.data.score_class))
				main.data.n_true = new_class.n_true
				main.data.n_false = new_class.n_false
				main.data.nbas = new_class.nbas

		# Update classifier info
		main.panel_work.panel_class.stext_npartim.SetLabel(str(main.data.n_true))
		main.panel_work.panel_class.stext_nnonpartim.SetLabel(str(main.data.n_false))
		main.panel_work.panel_class.stext_imdim.SetLabel(main.data.imdim)
		main.panel_work.panel_class.stext_psize.SetLabel(main.data.psize_class)
		main.panel_work.panel_class.stext_rmax1.SetLabel(main.data.rmax1_class)
		main.panel_work.panel_class.stext_rmax2.SetLabel(main.data.rmax2_class)
		main.panel_work.panel_class.stext_rmask.SetLabel(main.data.maskrad_class)
		main.panel_work.panel_class.stext_downsize.SetLabel(main.data.downsize_class)
		main.panel_work.panel_class.stext_nbasis.SetLabel(str(main.data.nbas))

		main.SetStatusText('Training classifier...COMPLETE')
		print 'Training classifier...COMPLETE'



class TrainNewClass(object):
	def __init__(self, data):

		#optimize,nfilms,dim,kwrds,score_class,partsList,partclass,fileList):
		self.score_class = score_class
		self.n_true = n_true
		self.n_false = n_false
		self.nbas = nbas #size of basis / number of pixels

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
