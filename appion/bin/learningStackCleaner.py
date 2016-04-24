#!/usr/bin/env python

import os
import wx
import cfg
import numpy
import random
from appionlib import apFile
from appionlib import apImagicFile
from appionlib.apImage import imageprocess
from appionlib.apImage import imagenorm

#=========================
class DataClass(object):
	def __init__(self):
		self.stackfile = "/emg/data/appion/06jul12a/stacks/stack1/start.hed"
		self.numpart = apFile.numImagesInStack(self.stackfile)
		self.boxsize = apFile.getBoxSize(self.stackfile)[0]
		print "Num Part %d, Box Size %d"%(self.numpart, self.boxsize)

		### create a map to random particles
		self.particleMap = range(self.numpart)
		random.shuffle(self.particleMap)
		self.particleTarget = {} #0 = ???, 1 = good, 2 = bad
		self.lastImageRead = 0

	def getParticleTarget(self, partNum):
		return self.particleTarget.get(partNum,0)

	def updateParticleTarget(self, partNum):
		value = self.particleTarget.get(partNum,0)
		print self.particleTarget
		self.particleTarget[partNum] = (value + 1) % 3

	def readRandomImage(self):
		partnum = self.particleMap[self.lastImageRead]
		imgarray = apImagicFile.readSingleParticleFromStack(main.data.stackfile, 
			partnum=(partnum+1), boxsize=main.data.boxsize, msg=False)
		self.lastImageRead += 1
		return imgarray, partnum

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
		self.lowpass.ChangeValue('10')
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
		displayCols = 4 #int(self.workPanel.MainWindow.GetClientSize()[1]/128.)
		self.nrows.ChangeValue(str(displayRows))
		self.sizer_stats.Add(self.nrows, pos=(2, 4))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NRows'), pos=(2, 5), flag=wx.ALIGN_CENTER_VERTICAL)
		self.ncols = wx.TextCtrl(self.panel_stats)
		self.ncols.ChangeValue(str(displayCols))
		self.sizer_stats.Add(self.ncols, pos=(3, 4))
		self.sizer_stats.Add(wx.StaticText(self.panel_stats, label='NCols'), pos=(3, 5), flag=wx.ALIGN_CENTER_VERTICAL)

		# New set
		self.buttonNewSet = wx.Button(self.panel_stats, label='REFRESH SET', size=(120, 40))
		self.sizer_stats.Add(self.buttonNewSet, pos=(1, 7), span=(4, 1), flag=wx.ALIGN_CENTER)
		self.Bind(wx.EVT_BUTTON, self.EvtNewSet, self.buttonNewSet)

		# Set sizers
		self.sizer_train.Add(self.panel_stats, pos=(0, 0))
		self.sizer_train.AddSpacer((2, 2), (1, 0))
		self.sizer_train.Add(self.panel_image, pos=(2, 0))
		self.panel_stats.SetSizerAndFit(self.sizer_stats)
		self.panel_image.SetSizerAndFit(self.sizer_image)
		self.SetSizerAndFit(self.sizer_train)

	#---------------
	def EvtAppFilt(self, event):
		try:
			self.part_display.MakeDisplay()
		except:
			pass

	#---------------
	def EvtNewSet(self, event):
		self.part_display = ParticleSet(self)

#=========================
class ParticleSet(object):
	#---------------
	def __init__(self, parentPanel):
		self.trainingPanel = parentPanel
		self.imgproc = imageprocess.ImageFilter()
		self.imgproc.msg = False
		self.MakeDisplay()

	#---------------
	def MakeDisplay(self):
		nrows = int(self.trainingPanel.nrows.GetValue())
		ncols = int(self.trainingPanel.ncols.GetValue())
		nimg = nrows*ncols

		self.imgproc.lowPass = float(self.trainingPanel.lowpass.GetValue())
		self.imgproc.lowPassType = 'tanh'
		self.imgproc.highPass = float(self.trainingPanel.highpass.GetValue())
		#self.imgproc.clipping = float(self.trainingPanel.clipping.GetValue())
		self.imgproc.bin = int(self.trainingPanel.binning.GetValue())

		# Delete previous objects
		#self.trainingPanel.panel_image.Destroy()
		self.trainingPanel.sizer_image.Destroy()
		#self.trainingPanel.panel_image = wx.Panel(self.trainingPanel, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
		self.trainingPanel.sizer_image = wx.GridBagSizer(nrows, ncols)
		imagePanel = self.trainingPanel.panel_image
		imageSizer = self.trainingPanel.sizer_image

		imgbutton_list = []
		for i in range(nimg):
			row = int(i / ncols)
			col = i % ncols
			#print row, col
			main.SetStatusText("Preparing image %d of %d for display..."%(i, nimg))
			filepartnum = main.data.particleMap[i]+1
			imgarray, partnum = main.data.readRandomImage()
			procarray = self.imgproc.processImage(imgarray)

			imgbutton = ImageButton(imagePanel, procarray, partnum)
			imageSizer.Add(imgbutton, pos=(row, col))
			imgbutton_list.append(imgbutton)

		imagePanel.SetSizerAndFit(imageSizer)
		self.trainingPanel.panel_stats.SetSizerAndFit(self.trainingPanel.sizer_stats)
		self.trainingPanel.panel_image.SetSizerAndFit(self.trainingPanel.sizer_image)
		self.trainingPanel.SetSizerAndFit(self.trainingPanel.sizer_train)
		self.trainingPanel.workPanel.SetSizerAndFit(self.trainingPanel.workPanel.sizer_work)

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
	def ImageClick(self, event):
		# Set background colour of particle images based on class
		main.data.updateParticleTarget(self.particleNum)
		setting = main.data.getParticleTarget(self.particleNum)
		if setting == 1:
			self.SetBackgroundColour('Green')
		elif setting == 2:
			self.SetBackgroundColour('Red')
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

		# Set up panels
		self.panel_stats = wx.Panel(self, style=wx.SUNKEN_BORDER)
		self.panel_make_class = wx.Panel(self, style=wx.SUNKEN_BORDER)
		self.classPanel_parts = wx.Panel(self, style=wx.SUNKEN_BORDER)

		"""
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

#=========================
#=========================
if __name__=='__main__':
	app = wx.App()
	data = DataClass()
	main = MainWindow(data)
	main.Show()
	app.MainLoop()
