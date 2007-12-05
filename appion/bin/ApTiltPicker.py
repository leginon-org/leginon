#!/usr/bin/python -O

## pythonlib
import sys
import re
import os
import time
import math
import cPickle
from optparse import OptionParser
## wxPython
import wx
## numpy/scipy
import numpy
from scipy import ndimage, optimize
## PIL
import Image
## local install
import apSpider
import apXml
import apImage
import apDisplay
import apParam
from gui.wx import TargetPanel, ImagePanelTools
from apTilt import tiltDialog, apTiltTransform

class TiltTargetPanel(TargetPanel.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True, name=None):
		TargetPanel.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool, mode="vertical")
		if name is not None:
			self.outname = name
		else:
			self.outname="unknown"

	#---------------------------------------
	def setOtherPanel(self, panel):
		self.other = panel

	#---------------------------------------
	def addTarget(self, name, x, y):
		#sys.stderr.write("%s: (%4d,%4d),\n" % (self.outname,x,y))
		numtargets = len(self.getTargets(name))
		#self.parent.statbar.PushStatusText("Added %d target at location (%d,%d)" % numtargets, x, y)
		if numtargets > 3:
			self.app.onFileSave(None)
		return self._getSelectionTool().addTarget(name, x, y)

	#---------------------------------------
	def deleteTarget(self, target):
		return self._getSelectionTool().deleteTarget(target)

	#---------------------------------------
	def openImageFile(self, filename):
		self.filename = filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = apImage.mrcToArray(filename)
			self.setImage(image.astype(numpy.float32))
		else:
			image = Image.open(filename)
			array = apImage.imageToArray(image)
			array = array.astype(numpy.float32)
			self.setImage(array)

#---------------------------------------
class PickerApp(wx.App):
	def __init__(self, mode='default', 
	 pickshape="cross", pshapesize=16, 
	 alignshape="circle", ashapesize=16,
	 errorshape="plus", eshapesize=16):
		self.mode = mode
		self.pshape = self.canonicalShape(pickshape)
		self.pshapesize = int(pshapesize)
		self.ashape = self.canonicalShape(alignshape)
		self.ashapesize = int(ashapesize)
		self.eshape = self.canonicalShape(errorshape)
		self.eshapesize = int(eshapesize)
		wx.App.__init__(self)

	def OnInit(self):
		self.data = {}
		self.onInitParams(None)
		self.data['outfile'] = ""
		self.data['dirname'] = ""
		self.appionloop = None
		self.filetypes = ['text', 'xml', 'spider', 'pickle',]
		self.filetypesel = (
			"Text Files (*.txt)|*.txt" 
			+ "|XML Files (*.xml)|*.xml"
			+ "|Spider Files (*.spi)|*.[a-z][a-z][a-z]" 
			+ "|Python Pickle File (*.pik)|*.pik" )
		self.data['filetypeindex'] = None
		self.data['thetarun'] = False
		self.picks1 = []
		self.picks2 = []
		self.buttonheight = 15
		self.deselectcolor = wx.Color(240,240,240)

		self.frame = wx.Frame(None, -1, 'Image Viewer')
		splitter = wx.SplitterWindow(self.frame)

		self.panel1 = TiltTargetPanel(splitter, -1, name="untilt")
		self.panel1.parent = self.frame
		self.panel1.app = self
		self.panel1.addTargetTool('Picked', color=wx.Color(215, 32, 32), 
			shape=self.pshape, size=self.pshapesize, target=True, numbers=True)
		self.panel1.setTargets('Picked', [])
		self.panel1.selectiontool.setTargeting('Picked', True)
		self.panel1.addTargetTool('Aligned', color=wx.Color(32, 128, 215), 
			shape=self.ashape, size=self.ashapesize)
		self.panel1.setTargets('Aligned', [])
		self.panel1.selectiontool.setDisplayed('Aligned', True)
		self.panel1.addTargetTool('Errors', color=wx.Color(215, 215, 32), 
			shape=self.eshape, size=self.eshapesize)
		self.panel1.setTargets('Errors', [])
		self.panel1.selectiontool.setDisplayed('Errors', True)
		#self.panel1.SetMinSize((256,256))
		#self.panel1.SetBackgroundColour("sky blue")

		self.panel2 = TiltTargetPanel(splitter, -1, name="tilt")
		self.panel2.parent = self.frame
		self.panel2.app = self
		self.panel2.addTargetTool('Picked', color=wx.Color(32, 128, 215), 
			shape=self.pshape, size=self.pshapesize, target=True, numbers=True)
		self.panel2.setTargets('Picked', [])
		self.panel2.selectiontool.setTargeting('Picked', True)
		self.panel2.addTargetTool('Aligned', color=wx.Color(215, 32, 32), 
			shape=self.ashape, size=self.ashapesize)
		self.panel2.setTargets('Aligned', [])
		self.panel2.selectiontool.setDisplayed('Aligned', True)
		self.panel2.addTargetTool('Errors', color=wx.Color(215, 215, 32), 
			shape=self.eshape, size=self.eshapesize)
		self.panel2.setTargets('Errors', [])
		self.panel2.selectiontool.setDisplayed('Errors', True)
		#self.panel2.SetMinSize((256,256))
		#self.panel2.SetBackgroundColour("pink")

		self.panel1.setOtherPanel(self.panel2)
		self.panel2.setOtherPanel(self.panel1)

		self.buttonrow = wx.FlexGridSizer(1,20)

		self.theta_dialog = tiltDialog.FitThetaDialog(self)
		self.fittheta = wx.Button(self.frame, -1, 'Find &Theta')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitTheta, self.fittheta)
		self.buttonrow.Add(self.fittheta, 0, wx.ALL, 1)

		self.fitall_dialog = tiltDialog.FitAllDialog(self)
		self.fitall = wx.Button(self.frame, -1, '&Optimize Angles')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitAll, self.fitall)
		self.buttonrow.Add(self.fitall, 0, wx.ALL, 1)

		self.update = wx.Button(self.frame, wx.ID_APPLY, '&Apply')
		self.frame.Bind(wx.EVT_BUTTON, self.onUpdate, self.update)
		self.buttonrow.Add(self.update, 0, wx.ALL, 1)

		self.maskregion = wx.Button(self.frame, -1, '&Mask Region')
		self.frame.Bind(wx.EVT_BUTTON, self.onMaskRegion, self.maskregion)
		self.buttonrow.Add(self.maskregion, 0, wx.ALL, 1)

		if self.mode == 'default':
			self.createMenuButtons()
		else:
			self.createLoopButtons()

		self.sizer = wx.GridBagSizer(2,2)

		#splitter.Initialize(self.panel1)
		splitter.SplitVertically(self.panel1, self.panel2)
		splitter.SetMinimumPaneSize(10)
		self.sizer.Add(splitter, (0,0), (1,2), wx.EXPAND|wx.ALL, 3)
		#self.sizer.Add(self.panel1, (0,0), (1,1), wx.EXPAND|wx.ALL, 3)
		#self.sizer.Add(self.panel2, (0,1), (1,1), wx.EXPAND|wx.ALL, 3)
		self.sizer.Add(self.buttonrow, (1,0), (1,2), wx.EXPAND|wx.ALL|wx.CENTER, 3)
		self.sizer.AddGrowableRow(0)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.statbar = self.frame.CreateStatusBar(3)
		self.statbar.SetStatusWidths([-1, 65, 150])
		self.statbar.PushStatusText("Ready", 0)

		self.createMenuBar()

		self.frame.SetSizer(self.sizer)
		self.frame.SetMinSize((768,384))
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	#---------------------------------------
	def createMenuButtons(self):
		self.buttonrow.Add((40,10), 0, wx.ALL, 1)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.frame.Bind(wx.EVT_BUTTON, self.onClearPicks, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALL, 1)

		self.reset = wx.Button(self.frame, wx.ID_RESET, '&Reset')
		self.frame.Bind(wx.EVT_BUTTON, self.onResetParams, self.reset)
		self.buttonrow.Add(self.reset, 0, wx.ALL, 1)

		self.buttonrow.Add((40,10), 0, wx.ALL, 1)

		"""
		self.load = wx.Button(self.frame, wx.ID_OPEN, '&Open')
		self.frame.Bind(wx.EVT_BUTTON, self.onFileOpen, self.load)
		self.buttonrow.Add(self.load, 0, wx.ALL, 1)

		self.save = wx.Button(self.frame, wx.ID_SAVE, '&Save')
		self.frame.Bind(wx.EVT_BUTTON, self.onFileSave, self.save)
		self.buttonrow.Add(self.save, 0, wx.ALL, 1)

		self.saveas = wx.Button(self.frame, wx.ID_SAVEAS, 'Sa&ve As...')
		self.frame.Bind(wx.EVT_BUTTON, self.onFileSaveAs, self.saveas)
		self.buttonrow.Add(self.saveas, 0, wx.ALL, 1)
		"""

		self.quit = wx.Button(self.frame, wx.ID_EXIT, '&Quit')
		self.frame.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.buttonrow.Add(self.quit, 0, wx.ALL, 1)
		
		return

	#---------------------------------------
	def createLoopButtons(self):
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.frame.Bind(wx.EVT_BUTTON, self.onClearPicks, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALL, 1)

		self.reset = wx.Button(self.frame, wx.ID_RESET, '&Reset')
		self.frame.Bind(wx.EVT_BUTTON, self.onResetParams, self.reset)
		self.buttonrow.Add(self.reset, 0, wx.ALL, 1)

		self.quit = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.frame.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.buttonrow.Add(self.quit, 0, wx.ALL, 1)

		self.importpicks = wx.Button(self.frame, -1, '&Import Picks')
		self.frame.Bind(wx.EVT_BUTTON, self.onImportPicks, self.importpicks)
		self.buttonrow.Add(self.importpicks, 0, wx.ALL, 1)

		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		#label = wx.StaticText(self.frame, -1, "Assessment:  ", style=wx.ALIGN_RIGHT)
		#self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessnone = wx.ToggleButton(self.frame, -1, "&None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetMinSize((70,self.buttonheight))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		#self.assesskeep.SetMinSize((70,self.buttonheight))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "Re&ject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		#self.assessreject.SetMinSize((70,self.buttonheight))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		return

	#---------------------------------------
	def menuData(self):
		if self.mode == 'default':
			return [
				("&File", (
					( "&Open", "Open picked particles from file", self.onFileOpen, wx.ID_OPEN ),
					( "&Save", "Save picked particles to file", self.onFileSave, wx.ID_SAVE ),
					( "Save &As...", "Save picked particles to new file", self.onFileSaveAs, wx.ID_SAVEAS ),
					( "Save file type", (
						( "&Text", "Readable text file", self.onSetFileType, -1, wx.ITEM_RADIO),
						( "&XML", "XML file", self.onSetFileType, -1, wx.ITEM_RADIO),
						( "&Spider", "Spider format file", self.onSetFileType, -1, wx.ITEM_RADIO),
						( "&Pickle", "Python pickle file", self.onSetFileType, -1, wx.ITEM_RADIO),
					)),
					( 0, 0, 0),
					( "&Quit", "Exit the program / advance to next image", self.onQuit, wx.ID_EXIT ),
				)),
				("&Edit", (
					( "&Clear", "Clear all picked particles", self.onClearPicks, wx.ID_CLEAR ),
					( "&Reset", "Reset parameters", self.onResetParams, wx.ID_RESET ),		
				)),
				("&Refine", (
					( "Find &Theta", "Calculate theta from picked particles", self.onFitTheta ),
					( "&Optimize Angles", "Optimize angles with least squares", self.onFitAll ),
					( "&Apply", "Apply picks", self.onUpdate, wx.ID_APPLY ),
					( "&Mask Overlapping Region", "Mask overlapping region", self.onMaskRegion ),
				)),
			]
		else:
			return [
				("&Pipeline", (
					( "&Import picks", "Import picked particles from previous run", self.onImportPicks ),
					( "&Forward", "Advance to next image", self.onQuit, wx.ID_FORWARD ),
				)),
				("&Edit", (
					( "&Clear", "Clear all picked particles", self.onClearPicks, wx.ID_CLEAR ),
					( "&Reset", "Reset parameters", self.onResetParams, wx.ID_RESET ),		
				)),
				("&Refine", (
					( "Find &Theta", "Calculate theta from picked particles", self.onFitTheta ),
					( "&Optimize Angles", "Optimize angles with least squares", self.onFitAll ),
					( "&Apply", "Apply picks", self.onUpdate, wx.ID_APPLY ),
					( "&Mask Overlapping Region", "Mask overlapping region", self.onMaskRegion ),
				)),
				("&Assess", (
					( "&None", "Don't assess image pair", self.onToggleNone, -1, wx.ITEM_RADIO),
					( "&Keep", "Keep this image pair", self.onToggleKeep, -1, wx.ITEM_RADIO),
					( "&Reject", "Reject this image pair", self.onToggleReject, -1, wx.ITEM_RADIO),
				)),
			]			

	#---------------------------------------
	def createMenuBar(self):
		self.menubar = wx.MenuBar()
		for eachMenuData in self.menuData():
			menuLabel = eachMenuData[0]
			menuItems = eachMenuData[1]
			self.menubar.Append(self.createMenu(menuItems), menuLabel)
		self.frame.SetMenuBar(self.menubar)

	#---------------------------------------
	def createMenu(self, menudata):
		menu = wx.Menu()
		for eachItem in menudata:
			if len(eachItem) == 2:
				label = eachItem[0]
				subMenu = self.createMenu(eachItem[1])
				menu.AppendMenu(wx.NewId(), label, subMenu)
			else:
				self.createMenuItem(menu, *eachItem)
		return menu

	#---------------------------------------
	def createMenuItem(self, menu, label, status, handler, wid=-1, kind=wx.ITEM_NORMAL):
		if not label:
			menu.AppendSeparator()
			return
		menuItem = menu.Append(wid, label, status, kind)
		self.Bind(wx.EVT_MENU, handler, menuItem)

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
	def onSetFileType(self, evt):
		print dir(evt)

	#---------------------------------------
	def onMaskRegion(self, evt):
		#GET THE ARRAYS
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		a1 = self.targetsToArray(targets1)
		a2 = self.targetsToArray(targets2)

		#GET THE POINT VALUES
		apTiltTransform.setPointsFromArrays(a1, a2, self.data)

		#CHECK IF WE HAVE POINTS
		if len(a1) == 0 or len(a2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot mask images. Not enough picks", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot mask images.\nThere are no picks.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		#GET IMAGES
		self.panel1.openImageFile(self.panel1.filename)
		self.panel2.openImageFile(self.panel2.filename)
		image1 = numpy.asarray(self.panel1.imagedata, dtype=numpy.float32)
		image2 = numpy.asarray(self.panel2.imagedata, dtype=numpy.float32)

		#DO THE MASKING
		image1, image2 = apTiltTransform.maskOverlapRegion(image1, image2, self.data)

		#SET IMAGES AND REFRESH SCREEN
		self.panel1.setImage(image1)
		self.panel2.setImage(image2)
		self.panel1.setBitmap()
		self.panel1.setVirtualSize()
		self.panel1.setBuffer()
		self.panel1.UpdateDrawing()
		self.panel2.setBitmap()
		self.panel2.setVirtualSize()
		self.panel2.setBuffer()
		self.panel2.UpdateDrawing()

	#---------------------------------------
	def onUpdate(self, evt):
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		if len(targets1) == 0 or len(targets2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot transfer picks. There are no picks.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot transfer picks.\nThere are no picks.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		#GET ARRAYS
		a1 = self.getArray1()
		a2 = self.getArray2()
		a1b = self.getAlignedArray1()
		a2b = self.getAlignedArray2()
		#SET THE ALIGNED ARRAYS
		self.panel2.setTargets('Aligned', a1b )
		self.panel1.setTargets('Aligned', a2b )
		#FIND PARTICLES WITH LARGE ERROR
		if len(a1) == len(a2):
			err = self.getRmsdArray()
			mean = ndimage.mean(err)
			stdev = ndimage.standard_deviation(err)
			cut = mean + 3*stdev
			errb = numpy.transpose(numpy.vstack([err,err]))
			a1c = []
			a2c = []
			for i,e in enumerate(err):
				if e > cut:
					a1c.append(a1[i,:])
					a2c.append(a2[i,:])
			self.statbar.PushStatusText(str(len(a1c))+" particles had an RMSD greater than "
				+str(int(cut))+ " pixels", 0)
			self.panel1.setTargets('Errors', a1c )
			self.panel2.setTargets('Errors', a2c )

	#---------------------------------------
	def getArray1(self):
		targets1 = self.panel1.getTargets('Picked')
		a1 = self.targetsToArray(targets1)
		return a1

	#---------------------------------------
	def getArray2(self):
		targets2 = self.panel2.getTargets('Picked')
		a2 = self.targetsToArray(targets2)
		return a2

	#---------------------------------------
	def getAlignedArray1(self):
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		a1 = self.targetsToArray(targets1)
		a2 = self.targetsToArray(targets2)

		apTiltTransform.setPointsFromArrays(a1, a2, self.data)
		a1b = apTiltTransform.a1Toa2Data(a1, self.data)

		return a1b

	#---------------------------------------
	def getAlignedArray2(self):
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		a1 = self.targetsToArray(targets1)
		a2 = self.targetsToArray(targets2)

		apTiltTransform.setPointsFromArrays(a1, a2, self.data)
		a2b = apTiltTransform.a2Toa1Data(a2, self.data)

		return a2b

	#---------------------------------------
	def getRmsdArray(self):
		targets1 = self.getArray1()
		aligned1 = self.getAlignedArray2()
		if len(targets1) != len(aligned1):
			targets1 = numpy.vstack((targets1, aligned1[len(targets1):]))
			aligned1 = numpy.vstack((aligned1, targets1[len(aligned1):]))
		diffmat1 = (targets1 - aligned1)
		sqsum1 = diffmat1[:,0]**2 + diffmat1[:,1]**2
		rmsd1 = numpy.sqrt(sqsum1)
		return rmsd1

	#---------------------------------------
	def targetsToArray(self, targets):
		a = []
		for t in targets:
			if t.x and t.y:
				a.append([ int(t.x), int(t.y) ])
		na = numpy.array(a, dtype=numpy.int32)
		return na

	#---------------------------------------
	def onImportPicks(self, evt):
		#a1 = numpy.array([[512,512]], dtype=numpy.float32)
		#a2 = apTiltTransform.a1Toa2Data(a1, self.data)
		#a1b = apTiltTransform.a2Toa1Data(a2, self.data)
		#print a1,a2,a1b

		#Picks are imported from tiltaligner
		len1 = len(self.picks1)
		len2 = len(self.picks2)
		if len1 < 1 or len2 < 1:
			dialog = wx.MessageDialog(self.frame, "There are no picks to import: "+str(len1)+", "+str(len2), 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		a1 = self.targetsToArray(targets1)
		a2 = self.targetsToArray(targets2)
		if len(a1) < 1 or len(a2) < 1:
			dialog = wx.MessageDialog(self.frame, "You must pick a particle pair first", 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		apTiltTransform.setPointsFromArrays(a1, a2, self.data)
		list1, list2 = apTiltTransform.alignPicks(self.picks1, self.picks2, self.data)
		if list1.shape[0] == 0 or list2.shape[0] == 0:
			apDisplay.printMsg("no new picks found")
			return False
		if a1.shape[0] > 0:
			newa1 = apTiltTransform.mergePicks(a1, list1)
		else:
			newa1 = list1
		if a2.shape[0] > 0:
			newa2 = apTiltTransform.mergePicks(a2, list2)
		else:
			newa2 = list2
		self.panel1.setTargets('Picked', newa1)
		self.panel2.setTargets('Picked', newa2)
		return True

	#---------------------------------------
	def onFitTheta(self, evt):
		if len(self.panel1.getTargets('Picked')) > 3 and len(self.panel2.getTargets('Picked')) > 3:
			self.data['thetarun'] = True
			self.theta_dialog.tiltvalue.SetLabel(label=("       %3.3f       " % self.data['theta']))
			self.theta_dialog.Show()

	#---------------------------------------
	def onFitAll(self, evt):
		if self.data['theta'] == 0.0 and self.data['thetarun'] is False:
			dialog = wx.MessageDialog(self.frame, "You must run 'Find Theta' first", 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		if False and (len(self.panel1.getTargets('Picked')) < 5 or len(self.panel2.getTargets('Picked')) < 5):
			dialog = wx.MessageDialog(self.frame, "You must pick at least 5 particle pairs first", 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		self.fitall_dialog.thetavalue.SetValue(round(self.data['theta'],4))
		self.fitall_dialog.gammavalue.SetValue(round(self.data['gamma'],4))
		self.fitall_dialog.phivalue.SetValue(round(self.data['phi'],4))
		self.fitall_dialog.scalevalue.SetValue(round(self.data['scale'],4))
		self.fitall_dialog.shiftxvalue.SetValue(round(self.data['shiftx'],4))
		self.fitall_dialog.shiftyvalue.SetValue(round(self.data['shifty'],4))
		self.fitall_dialog.Show()
		#values are then modified, if the user selected apply in tiltDialog

	#---------------------------------------
	def onClearPicks(self, evt):
		self.panel1.setTargets('Picked', [])
		self.panel1.setTargets('Aligned', [])
		self.panel2.setTargets('Picked', [])
		self.panel2.setTargets('Aligned', [])

	#---------------------------------------
	def onInitParams(self, evt):
		self.data['arealim'] = 50000.0
		self.data['theta'] = 0.0
		self.data['gamma'] = 0.0
		self.data['phi'] = 0.0
		self.data['shiftx'] = 0.0
		self.data['shifty'] = 0.0
		self.data['point1'] = (0.0, 0.0)
		self.data['point2'] = (0.0, 0.0)
		self.data['scale'] = 1.0

	#---------------------------------------
	def onResetParams(self, evt):
		self.onInitParams(evt)
		self.data['thetarun'] = False
		self.fitall_dialog.thetavalue.SetValue(round(self.data['theta'],4))
		self.fitall_dialog.gammavalue.SetValue(round(self.data['gamma'],4))
		self.fitall_dialog.phivalue.SetValue(round(self.data['phi'],4))
		self.fitall_dialog.scalevalue.SetValue(round(self.data['scale'],4))
		self.fitall_dialog.shiftxvalue.SetValue(round(self.data['shiftx'],4))
		self.fitall_dialog.shiftyvalue.SetValue(round(self.data['shifty'],4))
		if self.fitall_dialog.thetatog.GetValue() is True:
			self.fitall_dialog.thetavalue.Enable(False)
			self.fitall_dialog.thetatog.SetLabel("Locked")
		if self.fitall_dialog.gammatog.GetValue() is False:
			self.fitall_dialog.gammavalue.Enable(True)
			self.fitall_dialog.gammatog.SetLabel("Refine")
		if self.fitall_dialog.phitog.GetValue() is False:
			self.fitall_dialog.phivalue.Enable(True)
			self.fitall_dialog.phitog.SetLabel("Refine")
		if self.fitall_dialog.scaletog.GetValue() is True:
			self.fitall_dialog.scalevalue.Enable(False)
			self.fitall_dialog.scaletog.SetLabel("Locked")
		if self.fitall_dialog.shifttog.GetValue() is True:
			self.fitall_dialog.shiftxvalue.Enable(False)
			self.fitall_dialog.shiftyvalue.Enable(False)
			self.fitall_dialog.shifttog.SetLabel("Locked")

	#---------------------------------------
	def onFileSave(self, evt):
		if self.data['outfile'] == "" or self.data['dirname'] == "":
			#First Save, Run SaveAs...
			return self.onFileSaveAs(evt)
		self.savePicks()

	#---------------------------------------
	def onFileSaveAs(self, evt):
		dlg = wx.FileDialog(self.frame, "Choose a pick file to save as", self.data['dirname'], "", \
			self.filetypesel, wx.SAVE|wx.OVERWRITE_PROMPT)
		if 'filetypeindex' in self.data and self.data['filetypeindex'] is not None:
			dlg.SetFilterIndex(self.data['filetypeindex'])
		#alt1 = "*.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]"
		#alt2 = "Text Files (*.txt)|*.txt|All Files|*.*"
		if dlg.ShowModal() == wx.ID_OK:
			self.data['outfile'] = dlg.GetFilename()
			self.data['dirname']  = os.path.abspath(dlg.GetDirectory())
			self.data['filetypeindex'] = dlg.GetFilterIndex()
			self.data['filetype'] = self.filetypes[self.data['filetypeindex']]
			self.savePicks()
		dlg.Destroy()

	#---------------------------------------	
	def savePicks(self):
		self.data['savetime'] = time.asctime()+" "+time.tzname[time.daylight]
		self.data['filetype'] = self.filetypes[self.data['filetypeindex']]
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		if len(targets1) < 1 or len(targets2) < 1:
			self.statbar.PushStatusText("ERROR: Cannot save file. Not enough picks", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot save file.\nNot enough picks\n(less than 4 particle pairs)",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		if True: #try:
			if self.data['filetypeindex'] == 0:
				self.savePicksToTextFile()
			elif self.data['filetypeindex'] == 1:
				self.savePicksToXMLFile()
			elif self.data['filetypeindex'] == 2:
				self.savePicksToSpiderFile()
			elif self.data['filetypeindex'] == 3:
				self.savePicksToPickleFile()
			else:
				raise NotImplementedError
			#sys.stderr.write("Saved particles and parameters to '"+self.data['outfile']+\
			#	"' of type "+self.data['filetype']+"\n")
		elif False: #except:
			self.statbar.PushStatusText("ERROR: Saving to file '"+self.data['outfile']+"' failed", 0)
			dialog = wx.MessageDialog(self.frame, "Saving to file '"+self.data['outfile']+"' failed", 'Error', wx.OK|wx.ICON_ERROR)
			if dialog.ShowModal() == wx.ID_OK:
				dialog.Destroy()		

	#---------------------------------------
	def savePicksToTextFile(self):
		filepath = os.path.join(self.data['dirname'], self.data['outfile'])
		targets1 = self.getArray1()
		targets2 = self.getArray2()
		rmsd = self.getRmsdArray()
		filename = os.path.basename(filepath)
		f = open(filepath, "w")
		f.write( "image 1: "+self.panel1.filename+" (x,y,err)\n" )
		for i, target in enumerate(targets1):
			f.write( '%d,%d,%.3f\n' % (target[0], target[1], rmsd[i]) )
		f.write( "image 2: "+self.panel2.filename+" (x,y,err)\n" )
		for i, target in enumerate(targets2):
			f.write( '%d,%d,%.3f\n' % (target[0], target[1], rmsd[i]) )
		f.close()
		self.statbar.PushStatusText("Saved "+str(len(targets1))+" particles to "+self.data['outfile'], 0)
		return True

	#---------------------------------------
	def savePicksToXMLFile(self):
		filepath = os.path.join(self.data['dirname'], self.data['outfile'])
		self.data['targets1'] = self.targetsToArray(self.panel1.getTargets('Picked'))
		self.data['targets2'] = self.targetsToArray(self.panel2.getTargets('Picked'))
		filename = os.path.basename(filepath)
		apXml.writeDictToXml(self.data, filepath, title='aptiltpicker')
		self.statbar.PushStatusText("Saved "+str(len(self.data['targets1']))+" particles and parameters to "+self.data['outfile'], 0)
		return True

	#---------------------------------------
	def savePicksToSpiderFile(self):
		filepath = os.path.join(self.data['dirname'], self.data['outfile'])
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		filename = os.path.basename(filepath)
		f = open(filepath, "w")
		f.write(" ; ApTiltPicker complete parameter dump:\n")
		f.write( " ;   parameter : value\n")
		for k,v in self.data.items():
			if type(v) in [type(1), type(1.0), type(""),]:
				f.write( " ;   "+str(k)+" : "+str(v)+"\n")
		#PARAMETERS
		f.write(" ; \n; \n; PARAMETERS\n")
		f.write(apSpider.spiderOutputLine(1, 6, 0.0, 0.0, 0.0, 0.0, 111.0, 1.0))
		f.write(" ; FITTED FLAG\n")
		f.write(apSpider.spiderOutputLine(2, 6, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0))
		f.write(" ; (X0,Y0) FOR LEFT IMAGE1, (X0s,Y0s) FOR RIGHT IMAGE2, REDUCTION FACTOR\n")
		f.write(apSpider.spiderOutputLine(3, 6, 
			self.data['point1'][0], self.data['point1'][1], 
			self.data['point2'][0], self.data['point2'][1], 
			1.0, 0.0))
		f.write(" ; TILT ANGLE (THETA), LEFT IMAGE1 ROTATION (GAMMA), RIGHT IMAGE2 ROTATION (PHI)\n")
		f.write(apSpider.spiderOutputLine(4, 6, 
			self.data['theta'], self.data['gamma'], self.data['phi'],
			0.0, 0.0, 0.0))

		#IMAGE 1
		f.write( " ; left image 1: "+self.panel1.filename+"\n" )
		for i,target in enumerate(targets1):
			line = apSpider.spiderOutputLine(i+1, 6, i+1, target.x, target.y, target.x, target.y, 1.0)
			f.write(line)

		#IMAGE 2
		f.write( " ; right image 2: "+self.panel2.filename+"\n" )
		for i,target in enumerate(targets2):
			line = apSpider.spiderOutputLine(i+1, 6, i+1, target.x, target.y, target.x, target.y, 1.0)
			f.write(line)

		f.close()
		self.statbar.PushStatusText("Saved "+str(len(targets1))+" particles and parameters to "+self.data['outfile'], 0)
		return True


	#---------------------------------------
	def savePicksToPickleFile(self):
		filepath = os.path.join(self.data['dirname'], self.data['outfile'])
		self.data['targets1'] = self.targetsToArray(self.panel1.getTargets('Picked'))
		self.data['targets2'] = self.targetsToArray(self.panel2.getTargets('Picked'))
		f = open(filepath, 'w')
		cPickle.dump(self.data, f)
		f.close()
		self.statbar.PushStatusText("Saved "+str(len(self.data['targets1']))+" particles and parameters to "+self.data['outfile'], 0)
		return True

	#---------------------------------------
	def guessFileType(self, filepath):
		if filepath is None or filepath == "":
			return None
		print filepath
		self.data['outfile'] = os.path.basename(filepath)
		self.data['extension'] = self.data['outfile'][-3:]
		if self.data['extension'] == "txt":
			self.data['filetypeindex'] = 0
		elif self.data['extension'] == "xml":
			self.data['filetypeindex'] = 1
		elif self.data['extension'] == "spi":
			self.data['filetypeindex'] = 2
		elif self.data['extension'] == "pik":
			self.data['filetypeindex'] = 3
		else:
			raise "Could not determine filetype of picks file (argument 3)"
		self.data['filetype'] = self.filetypes[self.data['filetypeindex']]
		return

	#---------------------------------------
	def getExtension(self):
		if self.data['filetypeindex'] == 0:
			self.data['extension'] = "txt"
		elif self.data['filetypeindex'] == 1:
			self.data['extension'] = "xml"
		elif self.data['filetypeindex'] == 2:
			self.data['extension'] = "spi"
		elif self.data['filetypeindex'] == 3:
			self.data['extension'] = "pik"
		else:
			return "pik"
		return self.data['extension']

	#---------------------------------------
	def onFileOpen(self, evt):
		dlg = wx.FileDialog(self.frame, "Choose a pick file to open", self.data['dirname'], "", \
			self.filetypesel, wx.OPEN)
		if 'filetypeindex' in self.data and self.data['filetypeindex'] is not None:
			dlg.SetFilterIndex(self.data['filetypeindex'])
		if dlg.ShowModal() == wx.ID_OK:
			self.data['outfile'] = dlg.GetFilename()
			self.data['dirname']  = os.path.abspath(dlg.GetDirectory())
			self.data['filetypeindex'] = dlg.GetFilterIndex()
			self.data['filetype'] = self.filetypes[self.data['filetypeindex']]
			self.openPicks()
		dlg.Destroy()

	#---------------------------------------
	def openPicks(self, filepath=None):
		if filepath is None or filepath is "":
			filepath = os.path.join(self.data['dirname'],self.data['outfile'])
		if filepath is None or filepath is "":
			return None
		if self.data['filetypeindex'] is None:
			self.guessFileType(filepath)
		if True: #try:
			if self.data['filetypeindex'] == 0:
				self.openPicksFromTextFile(filepath)
			elif self.data['filetypeindex'] == 1:
				raise NotImplementedError
			elif self.data['filetypeindex'] == 2:
				raise NotImplementedError
			elif self.data['filetypeindex'] == 3:
				self.openPicksFromPickleFile(filepath)
			else:
				raise NotImplementedError
			sys.stderr.write("Opened particles and parameters from '"+self.data['outfile']+\
				"' of type "+self.data['filetype']+"\n")
		if False: #except:
			self.statbar.PushStatusText("ERROR: Opening file '"+self.data['outfile']+"' failed", 0)
			dialog = wx.MessageDialog(self.frame, "Opening file '"+self.data['outfile']+"' failed", 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()	
		self.data['opentime'] = time.asctime()+" "+time.tzname[time.daylight]

	#---------------------------------------
	def openPicksFromTextFile(self, filepath=None):
		if filepath is None or filepath == "" or not os.path.isfile(filepath):
			return
		f = open(filepath,"r")
		size = int(len(f.readlines())/2-1)
		f.close()
		self.data['outfile'] = os.path.basename(filepath)
		self.data['dirname'] = os.path.dirname(filepath)
		f = open(filepath,"r")
		strarrays = ["","",""]
		arrays = [
			numpy.zeros((size,2), dtype=numpy.int32),
			numpy.zeros((size,2), dtype=numpy.int32),
			numpy.zeros((size,2), dtype=numpy.int32),
		]
		i = 0
		for line in f:
			if line[:5] == "image":
				i += 1
				j = 0
				self.statbar.PushStatusText("Reading picks for image "+str(i),0)
			else:
				line = line.strip()
				seps = line.split(",")
				for k in range(2):
					#print "'"+seps[k]+"'"
					if seps[k]:
						arrays[i][j,k] = int(seps[k])
				j += 1
		#print arrays[1]
		f.close()
		#sys.exit(1)
		a1 = arrays[1]
		a2 = arrays[2]
		self.panel1.setTargets('Picked', a1)
		self.panel2.setTargets('Picked', a2)
		#self.panel1.setTargets('Numbered', a1)
		#self.panel2.setTargets('Numbered', a2)
		self.statbar.PushStatusText("Read "+str(len(a1))+" particles and parameters from file "+filepath, 0)

	#---------------------------------------
	def openPicksFromPickleFile(self, filepath=None):
		if filepath is None or filepath == "" or not os.path.isfile(filepath):
			return
		f = open(filepath,'r')
		self.data = cPickle.load(f)
		f.close()
		a1 = self.data['targets1']
		a2 = self.data['targets2']
		self.panel1.setTargets('Picked', a1)
		self.panel2.setTargets('Picked', a2)
		self.statbar.PushStatusText("Read "+str(len(a1))+" particles and parameters from file "+filepath, 0)
		return True

	#---------------------------------------
	def onQuit(self, evt):
		"""
		self.data['theta'] = 0.0
		self.data['gamma'] = 0.0
		self.data['phi'] = 0.0
		self.data['shiftx'] = 0.0
		self.data['shifty'] = 0.0
		self.data['scale'] = 1.0
		"""
		if self.appionloop:
			self.copyDataToAppionLoop()
			self.data['filetypeindex'] = self.appionloop.params['outtypeindex']
			self.data['outfile'] = os.path.basename(self.panel1.filename)+"."+self.getExtension()
			self.data['dirname'] = self.appionloop.params['pickdatadir']
			self.savePicks()
			self.Exit()
		else:
			wx.Exit()

	#---------------------------------------
	def copyDataToAppionLoop(self):
		#Need global shift data not local data
		a1 = self.getArray1()
		a2 = self.getArray2()
		if len(a1) == 0 or len(a2) == 0:
			self.appionloop.peaks1 = []
			self.appionloop.peaks2 = []
		else:
			#copy over the peaks
			self.appionloop.peaks1 = a1
			self.appionloop.peaks2 = a2
			a2b = self.getAlignedArray2()
			sqdev = numpy.sum( (a1 - a2b)**2, axis=1 )
			self.appionloop.peakerrors = numpy.sqrt( sqdev )
			self.data['rmsd'] = math.sqrt(float(ndimage.mean(sqdev)))
		#self.data['overlap'] = ...
		#copy over the data
		for i,v in self.data.items():
			if type(v) in [type(1), type(1.0), type(""), ]:
				self.appionloop.tiltparams[i] = v
			elif 'point' in i:
				self.appionloop.tiltparams[i] = v
			else:
				print "skipping key: "+str(i)+" of type "+str(type(v))
		self.appionloop.tiltparams['x1'] = self.data['point1'][0]
		self.appionloop.tiltparams['y1'] = self.data['point1'][1]
		self.appionloop.tiltparams['x2'] = self.data['point2'][0]
		self.appionloop.tiltparams['y2'] = self.data['point2'][1]

	#---------------------------------------
	def openLeftImage(self,filename):
		if filename:
			self.data['image1file'] = os.path.basename(filename)
			self.data['image1path'] = os.path.abspath(os.path.dirname(filename))
			app.panel1.openImageFile(filename)

	#---------------------------------------
	def openRightImage(self,filename):
		if filename:
			self.data['image2file'] = os.path.basename(filename)
			self.data['image2path'] = os.path.abspath(os.path.dirname(filename))
			app.panel2.openImageFile(filename)

	#---------------------------------------
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

if __name__ == '__main__':
	usage = "Usage: %prog --left-image=image1.mrc --right-image=image2.mrc [--pick-file=picksfile.txt] [options]"
	shapes = ("circle","square","diamond","plus","cross")
	parser = OptionParser(usage=usage)
	parser.add_option("-1", "-l", "--left-image", dest="img1file",
		help="First input image (left)", metavar="FILE")
	parser.add_option("-2", "-r", "--right-image", dest="img2file",
		help="Second input image (right)", metavar="FILE")
	parser.add_option("-p", "--pick-file", dest="pickfile",
		help="Particle pick file", metavar="FILE")
	parser.add_option("-s", "--pick-shape", dest="pickshape",
		help="Particle picking shape", metavar="SHAPE", 
		type="choice", choices=shapes, default="cross" )
	parser.add_option("-S", "--pick-shape-size", dest="pshapesize",
		help="Particle picking shape size", metavar="INT", 
		type="int", default=16 )
	parser.add_option("-a", "--align-shape", dest="alignshape",
		help="Algined particles shape", metavar="SHAPE", 
		type="choice", choices=shapes, default="circle" )
	parser.add_option("-A", "--align-shape-size", dest="ashapesize",
		help="Algined particles shape size", metavar="INT", 
		type="int", default=16 )
	params = apParam.convertParserToParams(parser)

	app = PickerApp(
		pickshape=params['pickshape'], alignshape=params['alignshape'],
		pshapesize=params['pshapesize'], ashapesize=params['ashapesize'],
	)
	app.openLeftImage(params['img1file'])
	app.openRightImage(params['img2file'])
	app.openPicks(params['pickfile'])

	app.MainLoop()



