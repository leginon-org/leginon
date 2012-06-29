#!/usr/bin/env python

import os
import wx
import sys
import time
import math
import numpy
from PIL import Image, ImageDraw
#import subprocess
from appionlib import power
from appionlib import apParam
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apPrimeFactor
from appionlib import apDatabase
from appionlib import appionLoop2
from appionlib.apImage import imagefile, imagefilter, imagenorm
from appionlib.apCtf import ctftools, ctfnoise
#Leginon
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools
from pyami import mrc, fftfun, imagefun, ellipse

class ManualCTFPanel(TargetPanel.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		TargetPanel.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

	#---------------------------------------
	def addTarget(self, name, x, y):
		### check for out of bounds particles
		if x < 2 or y < 2:
			return
		if x > self.imagedata.shape[1] or y > self.imagedata.shape[0]:
			return
		### continue as normal
		return self._getSelectionTool().addTarget(name, x, y)

	#---------------------------------------
	def openImageFile(self, filename):
		self.filename = filename
		print filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = mrc.read(filename)
			self.imgshape = image.shape
			self.setImage(image.astype(numpy.float32))
		else:
			img = Image.open(filename)
			img.load()
			img = imagefile.imageToArray(img)
			self.imgshape = img.shape
			self.setImage(img)

##################################
##
##################################

class CTFApp(wx.App):
	def __init__(self, shape='+', size=16):
		self.shape = shape
		self.size = size
		self.ellipse_params = None
		self.ctfvalues = None
		self.ringwidth = 2
		self.freq = None
		wx.App.__init__(self)

	#---------------------------------------
	def OnInit(self):
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual CTF')
		self.sizer = wx.FlexGridSizer(3,1)

		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100,30))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ManualCTFPanel(self.frame, -1)
		self.panel.originaltargets = {}

		self.panel.addTargetTool('First Valley', color=wx.Color(220,20,20),
			target=True, shape='x')
		self.panel.setTargets('First Valley', [])
		self.panel.selectiontool.setDisplayed('First Valley', True)
		self.panel.selectiontool.setTargeting('First Valley', True)

		self.panel.addTargetTool('First Valley Fit', color=wx.Color(251,236,93),
			target=False, shape='polygon')
		self.panel.setTargets('First Valley Fit', [])
		self.panel.selectiontool.setDisplayed('First Valley Fit', True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,8)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((150,30))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.firstvalley = wx.Button(self.frame, -1, 'First &Valley')
		self.firstvalley.SetMinSize((90,30))
		self.Bind(wx.EVT_BUTTON, self.onCalcFirstValley, self.firstvalley)
		self.buttonrow.Add(self.firstvalley, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.subtnoise = wx.Button(self.frame, -1, 'Subtract &Noise')
		self.subtnoise.SetMinSize((120,30))
		self.Bind(wx.EVT_BUTTON, self.onSubtNoise, self.subtnoise)
		self.buttonrow.Add(self.subtnoise, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.rotavg = wx.Button(self.frame, -1, '&Rot Avg')
		self.rotavg.SetMinSize((80,30))
		self.Bind(wx.EVT_BUTTON, self.onRotAverage, self.rotavg)
		self.buttonrow.Add(self.rotavg, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.draw = wx.Button(self.frame, -1, '&Draw')
		self.draw.SetMinSize((70,30))
		self.Bind(wx.EVT_BUTTON, self.onDraw, self.draw)
		self.buttonrow.Add(self.draw, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, 'Clear')
		self.clear.SetMinSize((90,30))
		self.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.revert= wx.Button(self.frame, wx.ID_REVERT_TO_SAVED, 'Revert')
		self.revert.SetMinSize((90,30))
		self.Bind(wx.EVT_BUTTON, self.onRevert, self.revert)
		self.buttonrow.Add(self.revert, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Image Assessment:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessnone = wx.ToggleButton(self.frame, -1, "&None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetBackgroundColour(self.selectcolor)
		self.assessnone.SetMinSize((80,30))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetMinSize((80,30))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "Re&ject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		self.assessreject.SetMinSize((80,30))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		### END BUTTONS ROW

		self.sizer.Add(self.buttonrow, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		self.sizer.AddGrowableRow(1)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	#---------------------------------------
	def onQuit(self, evt):
		wx.Exit()

	#---------------------------------------
	def onCalcFirstValley(self, evt):
		center = numpy.array(self.panel.imgshape)/2.0

		points = self.panel.getTargetPositions('First Valley')
		apDisplay.printMsg("You have %d points to fit in the valley ring"%(len(points)))
		if len(points) >= 3:
			self.ellipse_params = ellipse.solveEllipseOLS(points, center)
			print self.ellipse_params
			rmsd = None
			epoints = ellipse.generate_ellipse(self.ellipse_params['a'], 
				self.ellipse_params['b'], self.ellipse_params['alpha'], self.ellipse_params['center'],
				numpoints=30, noise=None, method="step", integers=True)
			self.panel.setTargets('First Valley Fit', epoints)

	#---------------------------------------
	def convertEllipseToCtf(self):
		if self.ellipse_params is None:
			self.statbar.PushStatusText("ERROR: Please select the valley ring and click First Valley.", 0)
			dialog = wx.MessageDialog(self.frame, "Please select the valley ring and click First Valley.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

	#---------------------------------------
	def funcrad(self, r, rdata=None, zdata=None):
		return numpy.interp(r, rdata, zdata)

	#---------------------------------------
	def onRotAverage(self, evt):
		# do a rotational average to subtract
		imagedata = self.panel.imagedata
		pixelrdata, self.rotdata = ctftools.rotationalAverage(imagedata, self.ringwidth, full=False)
		rotavgimage = imagefun.fromRadialFunction(self.funcrad, imagedata.shape, 
			rdata=pixelrdata, zdata=self.rotdata)
		self.panel.setImage(rotavgimage)
		apDisplay.printColor("Rotational average complete", "cyan")

	#---------------------------------------
	def onSubtNoise(self, evt):
		# do a rotational average to subtract
		imagedata = self.panel.imagedata
		pixelrdata, self.rotdata = ctftools.rotationalAverage(imagedata, self.ringwidth, full=False)
		self.raddata = pixelrdata*self.freq
		CtfNoise = ctfnoise.CtfNoise()
		noisefitparams = CtfNoise.modelCTFNoise(self.raddata, self.rotdata, "below")
		noisedata = CtfNoise.noiseModel(noisefitparams, self.raddata)
		noise2d = imagefun.fromRadialFunction(self.funcrad, imagedata.shape, 
			rdata=self.raddata/self.freq, zdata=noisedata)
		normaldata = imagedata - noise2d
		normaldata = numpy.where(normaldata < 0, 0, normaldata)
		self.panel.setImage(normaldata)
		apDisplay.printColor("Subtract Noise complete", "cyan")

	#---------------------------------------
	def onNext(self, evt):
		#targets = self.panel.getTargets('Select Particles')
		#for target in targets:
		#	print '%s\t%s' % (target.x, target.y)
		vertices = self.panel.getTargetPositions('Polygon')
		if len(vertices) > 0:
			apDisplay.printMsg("Clearing %d polygon vertices"%(len(vertices)))
			self.panel.setTargets('Polygon', [])
		self.appionloop.targets = {}
		self.appionloop.assess = self.finalAssessment()
		self.Exit()

	#---------------------------------------
	def finalAssessment(self):
		if self.assessnone.GetValue() is True:
			return None
		elif self.assesskeep.GetValue() is True:
			return True
		elif self.assessreject.GetValue() is True:
			return False
		return None

	#---------------------------------------
	def setAssessStatus(self):
		if self.appionloop.assess is True:
			self.onToggleKeep(None)
		elif self.appionloop.assess is False:
			self.onToggleReject(None)
		else:
			self.onToggleNone(None)

	#---------------------------------------
	def onToggleNone(self, evt):
		self.assessnone.SetValue(1)
		self.assessnone.SetBackgroundColour(wx.Color(200,200,0))
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = None

	#---------------------------------------
	def onToggleKeep(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(1)
		self.assesskeep.SetBackgroundColour(wx.Color(0,200,0))
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = True

	#---------------------------------------
	def onToggleReject(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(1)
		self.assessreject.SetBackgroundColour(wx.Color(200,0,0))
		self.assess = False

	#---------------------------------------
	def onClear(self, evt):
		self.panel.setTargets('First Valley', [])

	#---------------------------------------
	def onRevert(self, evt):
		self.panel.openImageFile(self.panel.filename)

	#---------------------------------------
	def onDraw(self, evt):
		imagedata = self.panel.imagedata
		center = numpy.array(imagedata.shape, dtype=numpy.float)/2.0
		pilimage = imagefile.arrayToImage(imagedata, stdevLimit=2.0)
		pilimage = pilimage.convert("RGB")
		draw = ImageDraw.Draw(pilimage)
		x = -60*math.cos(math.radians(30))
		y = 60*math.sin(math.radians(30))
		xy = (x+center[0], y+center[1], -x+center[0], -y+center[1])
		draw.line(xy, fill="#f23d3d", width=10)
		self.panel.setPILImage(pilimage)

	#---------------------------------------
	def targetsToArray(self, targets):
		a = []
		for t in targets:
			if t.x and t.y:
				a.append([ int(t.x), int(t.y) ])
		na = numpy.array(a, dtype=numpy.int32)
		return na
		
##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class ManualCTF(appionLoop2.AppionLoop):
	def onInit(self):
		super(ManualCTF,self).onInit()
		self.trace = False
		
	#---------------------------------------
	def setApp(self):
		self.app = CTFApp(
			shape = self.canonicalShape(self.params['shape']),
			size =  self.params['shapesize'],
		)

	#---------------------------------------
	def preLoopFunctions(self):
		apParam.createDirectory(os.path.join(self.params['rundir'], "pikfiles"),warning=False)
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()

		self.setApp()
		self.app.appionloop = self
		self.threadJpeg = True

	#---------------------------------------
	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	#---------------------------------------
	def processImage(self, imgdata):
		fftpath = os.path.join(self.params['rundir'], imgdata['filename']+'.fft.jpg')
		if not os.path.isfile(fftpath):
			self.processAndSaveFFT(imgdata, fftpath)
		peaktree = self.runManualCTF(imgdata, fftpath)

		return peaktree

	#---------------------------------------
	def commitToDatabase(self, imgdata, rundata):
		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		return

	#---------------------------------------
	def setupParserOptions(self):
		### Input value options
		self.parser.add_option("--prebin", dest="prebin", default=2, type="int",
			help="pre-bin the images before the FFT calculation", metavar="#")
		self.parser.add_option("--shape", dest="shape", default='+',
			help="pick shape")
		self.parser.add_option("--shapesize", dest="shapesize", type="int", default=16,
			help="shape size")
		self.parser.add_option("--rotatestep", dest="rotatestep", type="float", default=1,
			help="rotation step size in degrees")
		self.parser.add_option("--rotations", dest="rotations", type="int", default=61,
			help="number of rotations to avearge")
		self.parser.add_option("--resolution-limit", dest="reslimit", type="float", default=10.0,
			help="outer resolution limit (in A) to clip the fft image")

	#---------------------------------------
	def checkConflicts(self):
		"""
		put in any additional conflicting parameters
		"""

		return


	###################################################
	##### END PRE-DEFINED PARTICLE LOOP FUNCTIONS #####
	###################################################

	def canonicalShape(self, shape):
		if shape == '.'    or shape == 'point':
			return '.'
		elif shape == '+'  or shape == 'plus':
			return '+'
		elif shape == '[]' or shape == 'square' or shape == 'box':
			return '[]'
		elif shape == '<>' or shape == 'diamond':
			return '<>'
		elif shape == 'x'  or shape == 'cross':
			return 'x'
		elif shape == '*'  or shape == 'star':
			return '*'
		elif shape == 'o'  or shape == 'circle':
			return 'o'
		else:
			apDisplay.printError("Unknown pointer shape: "+shape)

	#---------------------------------------
	def getParticlePicks(self, imgdata):
		return []

	#---------------------------------------
	def particlesToTargets(self, particles):
		targets = {}
		return targets

	#---------------------------------------
	def processAndSaveAllImages(self):
		sys.stderr.write("Pre-processing image FFTs\n")
		#print self.params
		count = 0
		total = len(self.imgtree)
		for imgdata in self.imgtree:
			count += 1
			fftpath = os.path.join(self.params['rundir'], imgdata['filename']+'.fft.jpg')
			if self.params['continue'] is True and os.path.isfile(fftpath):
				sys.stderr.write(".")
				#print "already processed: ",apDisplay.short(imgdata['filename'])
			else:
				if os.path.isfile(fftpath):
					os.remove(fftpath)
				sys.stderr.write("#")
				self.processAndSaveFFT(imgdata, fftpath)

			if count % 60 == 0:
				sys.stderr.write(" %d left\n" % (total-count))

	#---------------------------------------
	def processAndSaveFFT(self, imgdata, fftpath):
		if os.path.isfile(fftpath):
			return False

		### downsize and filter leginon image
		if self.params['uncorrected']:
			imgarray = imagefilter.correctImage(imgdata, params)
		else:
			imgarray = imgdata['image']
		fftarray = imagefun.bin2(imgarray, self.params['prebin'])

		### calculate power spectra
		fftarray = imagefun.power(fftarray, mask_radius=0.2)

		### clip image
		# convert res limit into pixel distance
		cols = fftarray.shape[0]
		pixelsize = apDatabase.getPixelSize(imgdata)*self.params['prebin']
		#print pixelsize
		pixellimit = int(math.ceil(pixelsize*cols/self.params['reslimit']))
		size = apPrimeFactor.getNextEvenPrime(pixellimit*2)
		newshape = (size, size)
		print newshape
		fftarray = imagefilter.frame_cut(fftarray, newshape)

		## preform a rotational blur
		#fftarray = power.rotationalBlur(fftarray, nsteps=self.params['rotations'], 
		#	stepsize=self.params['rotatestep'])

		### save to jpeg
		imagefile.arrayToJpeg(fftarray, fftpath, msg=False)

		return True

	#---------------------------------------
	def runManualCTF(self, imgdata, fftpath):
		#reset targets
		self.targets = {}
		self.app.panel.setTargets('First Valley', [])
		self.targets['First Valley'] = []

		#set the assessment and viewer status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()

		#open new file
		self.app.panel.openImageFile(fftpath)
		self.app.apix = apDatabase.getPixelSize(imgdata)
		mindim = min(imgdata['image'].shape)
		self.app.freq = 1./(self.app.apix * mindim)

		targets = self.getParticlePicks(imgdata)

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", inserted "+str(self.stats['peaksum'])+" picks, "
			+" image name: "+imgdata['filename'])
		#run the ctf
		self.app.MainLoop()

		return

#---------------------------------------
#---------------------------------------
def draw_ellipse(imgarray, ra,rb, ang, x0,y0, numpoints=32):
	"""
	ra - major axis length
	rb - minor axis length
	ang - angle (in degrees)
	x0,y0 - position of centre of ellipse
	Nb - No. of points that make an ellipse
	"""
	#x,y = get_ellipse(ra,rb,ang,x0,y0,numpoints)
	x,y = ellipse.generate_ellipse(ra, rb, ang, (x0,y0), numpoints, None, "step", True)
	## wrap around to end
	x = numpy.hstack((x, [x[0],]))
	y = numpy.hstack((y, [y[0],]))
	## convert image
	image = imagefile.arrayToImage(imgarray)
	image = image.convert("RGB")
	image2 = image.copy()
	draw = ImageDraw.Draw(image2)
	for i in range(len(x)-1):
		xy = (x[i], y[i], x[i+1], y[i+1]) 
		draw.line(xy, fill="#3d3df2", width=3)

	## create an alpha blend effect
	image = Image.blend(image, image2, 0.9)
	image.save("test.jpg", "JPEG", quality=95)
	return

#---------------------------------------
#---------------------------------------
if __name__ == '__main__':
	imgLoop = ManualCTF()
	imgLoop.run()
	#a = imagefile.readJPG("/data01/appion/11jul05a/extract/manctf2/11jul05a_11jan06b_00002sq_00002hl_v01_00002en2.fft.jpg")
	#draw_ellipse(a, 50, 100, 60, 1024, 1024)



