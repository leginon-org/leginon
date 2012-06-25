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
from appionlib.apImage import imagefile, imagefilter
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
		wx.App.__init__(self)

	def OnInit(self):
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Manual CTF')
		self.sizer = wx.FlexGridSizer(3,1)

		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100,40))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ManualCTFPanel(self.frame, -1)
		self.panel.originaltargets = {}

		self.panel.addTargetTool('First Ring', color=wx.Color(220,20,20),
			target=True, shape='x')
		self.panel.setTargets('First Ring', [])
		self.panel.selectiontool.setDisplayed('First Ring', True)
		self.panel.selectiontool.setTargeting('First Ring', True)

		self.panel.addTargetTool('Second Ring', color=wx.Color(20,20,220),
			target=True, shape='+')
		self.panel.setTargets('Second Ring', [])
		self.panel.selectiontool.setDisplayed('Second Ring', True)
		self.panel.selectiontool.setTargeting('Second Ring', True)

		self.panel.addTargetTool('First Ring Fit', color=wx.Color(220,20,20),
			target=False, shape='polygon')
		self.panel.setTargets('First Ring Fit', [])
		self.panel.selectiontool.setDisplayed('First Ring Fit', True)

		self.panel.addTargetTool('Second Ring Fit', color=wx.Color(20,20,220),
			target=False, shape='polygon')
		self.panel.setTargets('Second Ring Fit', [])
		self.panel.selectiontool.setDisplayed('Second Ring Fit', True)

		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,8)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.add = wx.Button(self.frame, wx.ID_REMOVE, '&Calc CTF')
		self.add.SetMinSize((150,40))
		self.Bind(wx.EVT_BUTTON, self.onCalcCTF, self.add)
		self.buttonrow.Add(self.add, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.clear.SetMinSize((100,40))
		self.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.revert= wx.Button(self.frame, wx.ID_REVERT_TO_SAVED, 'Revert to Saved')
		self.revert.SetMinSize((80,40))
		self.Bind(wx.EVT_BUTTON, self.onRevert, self.revert)
		self.buttonrow.Add(self.revert, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Image Assessment:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessnone = wx.ToggleButton(self.frame, -1, "&None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetBackgroundColour(self.selectcolor)
		self.assessnone.SetMinSize((100,40))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetMinSize((100,40))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "Re&ject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		self.assessreject.SetMinSize((100,40))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		### END BUTTONS ROW

		self.sizer.Add(self.buttonrow, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		self.sizer.AddGrowableRow(1)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	def onQuit(self, evt):
		wx.Exit()

	def onCalcCTF(self, evt):
		center = numpy.array(self.panel.imgshape)/2.0

		points = self.panel.getTargetPositions('First Ring')
		apDisplay.printMsg("You have %d points to fit in the first ring"%(len(points)))
		if len(points) >= 3:
			params = ellipse.solveEllipseOLS(points, center)
			print params
			rmsd = None
			epoints = ellipse.generate_ellipse(params['a'], 
				params['b'], params['alpha'], params['center'],
				numpoints=30, noise=None, method="step", integers=True)
			self.panel.setTargets('First Ring Fit', epoints)

		points = self.panel.getTargetPositions('Second Ring')
		apDisplay.printMsg("You have %d points to fit in the second ring"%(len(points)))
		if len(points) >= 3:
			params = ellipse.solveEllipseOLS(points, center)
			print params
			rmsd = None
			epoints = ellipse.generate_ellipse(params['a'], 
				params['b'], params['alpha'], params['center'],
				numpoints=30, noise=None, method="step", integers=True)
			self.panel.setTargets('Second Ring Fit', epoints)


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

	def finalAssessment(self):
		if self.assessnone.GetValue() is True:
			return None
		elif self.assesskeep.GetValue() is True:
			return True
		elif self.assessreject.GetValue() is True:
			return False
		return None

	def setAssessStatus(self):
		if self.appionloop.assess is True:
			self.onToggleKeep(None)
		elif self.appionloop.assess is False:
			self.onToggleReject(None)
		else:
			self.onToggleNone(None)

	def onToggleNone(self, evt):
		self.assessnone.SetValue(1)
		self.assessnone.SetBackgroundColour(wx.Color(200,200,0))
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = None

	def onToggleKeep(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(1)
		self.assesskeep.SetBackgroundColour(wx.Color(0,200,0))
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = True


	def onToggleReject(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(1)
		self.assessreject.SetBackgroundColour(wx.Color(200,0,0))
		self.assess = False

	def onClear(self, evt):
		self.panel.setTargets('First Ring', [])
		self.panel.setTargets('Polygon', [])

	def onRevert(self, evt):
		if self.panel.originaltargets:
			for label,targets in self.panel.originaltargets.items():
				self.panel.setTargets(label, targets)

	def targetsToArray(self, targets):
		a = []
		for t in targets:
			if t.x and t.y:
				a.append([ int(t.x), int(t.y) ])
		na = numpy.array(a, dtype=numpy.int32)
		return na

	def onHelicalInsert(self, evt):
		"""
		connect the last two targets by filling inbetween
		copied from EMAN1 boxer
		"""
		### determine which particle label to operate on
		userlabel = 'user'
		helicallabel = 'helical'
		### get last two user targets
		usertargets = self.panel.getTargets(userlabel)
		helicaltargets = self.panel.getTargets(helicallabel)
		if len(usertargets) == 2:
			self.angles = {}
		if len(usertargets) < 2:
			apDisplay.printWarning("not enough targets")
			return
		if len(usertargets) > 2 and not helicaltargets:
			apDisplay.printWarning("too many targets")
			return
		userarray = self.targetsToArray(usertargets)
		helicalarray = self.targetsToArray(helicaltargets)
		### get pixelsize
		apix = self.appionloop.params['apix']
		if not apix or apix == 0.0:
			apDisplay.printWarning("unknown pixel size")
			return
		### get helicalstep
		ovrlp = self.appionloop.params['ovrlp']/100.00
		if ovrlp == 0:
			helicalstep = self.appionloop.params['helicalstep']
		else:
			helicalstep = int(self.appionloop.params['helicalstep']*ovrlp)
		if not helicalstep:
			apDisplay.printWarning("unknown helical step size")
			return

		first = userarray[-2]
		last = userarray[-1]
		### Do tan(y,x) to be consistend with ruler tool, convert to x,y in makestack
		angle = math.degrees(math.atan2((last[1]*1.0 - first[1]),(last[0] - first[0])))
		stats = {'angle': angle}	
		pixeldistance = math.hypot(first[0] - last[0], first[1] - last[1])
		if pixeldistance == 0:
			### this will probably never happen since mouse does not let you click same point twice
			apDisplay.printWarning("points have zero distance")
			return
		stepsize = helicalstep/(pixeldistance*apix*self.appionloop.params['bin'])
		### parameterization of a line btw points (x1,y1) and (x2,y2):
		# x = (1 - t)*x1 + t*x2,
		# y = (1 - t)*y1 + t*y2,
		# t { [0,1] ; t is a real number btw 0 and 1
		helicalpoints = list(helicalarray)
		t = 0.0
		while t < 1.0:
			x = int(round( (1.0 - t)*first[0] + t*last[0], 0))
			y = int(round( (1.0 - t)*first[1] + t*last[1], 0))
			helicalpoints.append((x,y))
			self.angles[x,y] = angle
			t += stepsize
		newhelicalpoints = []
		for point in helicalpoints:
			x = point[0]
			y = point[1]
			stats = {'angle': self.angles[x,y]}
			newhelicalpoints.append({'x': x, 'y': y, 'stats': stats})	

		self.panel.setTargets(helicallabel, newhelicalpoints)
		
		
		
		


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
		
	def setApp(self):
		self.app = CTFApp(
			shape = self.canonicalShape(self.params['shape']),
			size =  self.params['shapesize'],
		)

	##=======================
	def preLoopFunctions(self):
		apParam.createDirectory(os.path.join(self.params['rundir'], "pikfiles"),warning=False)
		if self.params['sessionname'] is not None:
			self.processAndSaveAllImages()

		self.setApp()
		self.app.appionloop = self
		self.threadJpeg = True

	##=======================
	def postLoopFunctions(self):
		self.app.frame.Destroy()
		apDisplay.printMsg("Finishing up")
		time.sleep(20)
		apDisplay.printMsg("finished")
		wx.Exit()

	##=======================
	def processImage(self, imgdata):
		fftpath = os.path.join(self.params['rundir'], imgdata['filename']+'.fft.jpg')
		if not os.path.isfile(fftpath):
			self.processAndSaveFFT(imgdata, fftpath)
		peaktree = self.runManualCTF(imgdata, fftpath)

		return peaktree

	##=======================
	def commitToDatabase(self, imgdata, rundata):
		if self.assess != self.assessold and self.assess is not None:
			#imageaccessor run is always named run1
			apDatabase.insertImgAssessmentStatus(imgdata, 'run1', self.assess)
		return

	##=======================
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

	##=======================
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

	#==========================
	def getParticlePicks(self, imgdata):
		return []

	#==========================
	def particlesToTargets(self, particles):
		targets = {}
		return targets

	#==========================
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

	#==========================
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

		### do a LOWESS fit to subtract envelope
		miniarray = imagefun.bin2(fftarray, 8)
		fit = power.Lowess2D(miniarray)
		fit = imagefilter.scaleImage(fit, 8)
		fftarray = fftarray - fit

		## preform a rotational blur
		#fftarray = power.rotationalBlur(fftarray, nsteps=self.params['rotations'], 
		#	stepsize=self.params['rotatestep'])

		### save to jpeg
		imagefile.arrayToJpeg(fftarray, fftpath, msg=False)

		return True

	#==========================
	def runManualCTF(self, imgdata, fftpath):
		#reset targets
		self.targets = {}
		self.app.panel.setTargets('First Ring', [])
		self.targets['First Ring'] = []
		self.app.panel.setTargets('Second Ring', [])
		self.targets['Second Ring'] = []

		#set the assessment and viewer status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()

		#open new file
		self.app.panel.openImageFile(fftpath)

		targets = self.getParticlePicks(imgdata)

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", inserted "+str(self.stats['peaksum'])+" picks, "
			+" image name: "+imgdata['filename'])
		#run the ctf
		self.app.MainLoop()

		return

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


if __name__ == '__main__':
	imgLoop = ManualCTF()
	imgLoop.run()
	#a = imagefile.readJPG("/data01/appion/11jul05a/extract/manctf2/11jul05a_11jan06b_00002sq_00002hl_v01_00002en2.fft.jpg")
	#draw_ellipse(a, 50, 100, 60, 1024, 1024)



