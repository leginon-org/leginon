#!/usr/bin/env python

## pythonlib
import os
import time
import math
from optparse import OptionParser
## wxPython
import wx
## PIL
from PIL import Image
## appion
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib.apTilt import tiltDialog, apTiltTransform, apTiltShift, tiltfile, autotilt
## leginon
import leginon.gui.wx.TargetPanel
## numpy/scipy
import numpy
import pyami.quietscipy
from scipy import ndimage

class TiltTargetPanel(leginon.gui.wx.TargetPanel.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True, name=None):
		leginon.gui.wx.TargetPanel.TargetImagePanel.__init__(self, parent, id,
			callback=callback, tool=tool, mode="vertical")
		if name is not None:
			self.outname = name
		else:
			self.outname="unknown"

	#---------------------------------------
	def setOtherPanel(self, panel):
		self.other = panel

	#---------------------------------------
	def addTarget(self, name, x, y):
		### check for out of bounds particles
		if x < 2 or y < 2:
			return
		if x > self.imagedata.shape[1] or y > self.imagedata.shape[0]:
			return
		numtargets = len(self.getTargets(name))
		numotargets = len(self.other.getTargets(name))
		#self.parent.statbar.PushStatusText("Added %d target at location (%d,%d)" % numtargets, x, y)
		if numtargets > 3 and numotargets > 3:
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
		elif filename[-4:] == '.spi':
			image = apImage.spiderToArray(filename, msg=False)
			self.setImage(image.astype(numpy.float32))
		elif filename[-4:] == '.mrc':
			image = apImage.mrcToArray(filename, msg=False)
			self.setImage(image.astype(numpy.float32))
		else:
			image = Image.open(filename)
			array = apImage.imageToArray(image, msg=False)
			array = array.astype(numpy.float32)
			self.setImage(array)

#---------------------------------------
class PickerApp(wx.App):
	def __init__(self, mode='default',
	 pickshape="circle", pshapesize=24,
	 alignshape="square", ashapesize=6,
	 worstshape="square", wshapesize=28,
	 tiltangle=None, tiltaxis=None, doinit=True):
		self.mode = mode
		self.pshape = self.canonicalShape(pickshape)
		self.pshapesize = int(pshapesize)
		self.ashape = self.canonicalShape(alignshape)
		self.ashapesize = int(ashapesize)
		self.eshape = self.canonicalShape(worstshape)
		self.wshapesize = int(wshapesize)
		self.inittiltangle = tiltangle
		self.inittiltaxis = tiltaxis
		wx.App.__init__(self)

	def OnInit(self):
		self.data = {}
		self.appionloop = None
		self.onInitParams(None, False)
		self.data['pixdiam'] = 20.0
		self.data['outfile'] = ""
		self.data['dirname'] = ""
		if self.inittiltangle is not None:
			self.data['theta'] = self.inittiltangle
		if self.inittiltaxis is not None:
			self.data['gamma'] = self.inittiltaxis
			self.data['phi'] = self.inittiltaxis
		self.appionloop = None
		self.data['filetypeindex'] = None
		self.data['thetarun'] = False
		self.data['optimrun'] = False
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
			shape=self.ashape, size=self.ashapesize, numbers=True)
		self.panel1.setTargets('Aligned', [])
		self.panel1.selectiontool.setDisplayed('Aligned', True)

		self.panel1.addTargetTool('Worst', color=wx.Color(250, 160, 32),
			shape=self.eshape, size=self.wshapesize)
		self.panel1.setTargets('Worst', [])
		self.panel1.selectiontool.setDisplayed('Worst', True)

		self.panel1.addTargetTool('Polygon', color=wx.Color(32, 215, 32),
			shape='polygon', target=True)
		self.panel1.setTargets('Polygon', [])
		self.panel1.selectiontool.setDisplayed('Polygon', True)

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
			shape=self.ashape, size=self.ashapesize, numbers=True)
		self.panel2.setTargets('Aligned', [])
		self.panel2.selectiontool.setDisplayed('Aligned', True)

		self.panel2.addTargetTool('Worst', color=wx.Color(250, 160, 32),
			shape=self.eshape, size=self.wshapesize)
		self.panel2.setTargets('Worst', [])
		self.panel2.selectiontool.setDisplayed('Worst', True)

		self.panel2.addTargetTool('Polygon', color=wx.Color(32, 215, 32),
			shape='polygon', target=True)
		self.panel2.setTargets('Polygon', [])
		self.panel2.selectiontool.setDisplayed('Polygon', True)

		#self.panel2.SetMinSize((256,256))
		#self.panel2.SetBackgroundColour("pink")

		self.panel1.setOtherPanel(self.panel2)
		self.panel2.setOtherPanel(self.panel1)

		### create menu buttons
		self.createMenuButtons()
		if self.mode == 'default':
			self.createStandAloneButtons()
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
		self.frame.SetMinSize((256,128))
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	#---------------------------------------
	def createMenuButtons(self):
		"""
		These are buttons related to both the standalone and pipeline versions of TiltPicker
		"""
		self.buttonrow = wx.FlexGridSizer(1,20)

		self.update = wx.Button(self.frame, wx.ID_APPLY, '&Apply')
		self.frame.Bind(wx.EVT_BUTTON, self.onUpdate, self.update)
		self.buttonrow.Add(self.update, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.theta_dialog = tiltDialog.FitThetaDialog(self)
		self.fittheta = wx.Button(self.frame, -1, '&Theta...')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitTheta, self.fittheta)
		self.buttonrow.Add(self.fittheta, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		self.fitall_dialog = tiltDialog.FitAllDialog(self)
		self.fitall = wx.Button(self.frame, -1, '&Optimize...')
		self.frame.Bind(wx.EVT_BUTTON, self.onFitAll, self.fitall)
		self.buttonrow.Add(self.fitall, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		self.maskregion = wx.Button(self.frame, -1, '&Mask')
		self.frame.Bind(wx.EVT_BUTTON, self.onMaskRegion, self.maskregion)
		self.buttonrow.Add(self.maskregion, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		self.autooptim = wx.Button(self.frame, -1, 'Auto Optimi&ze')
		self.frame.Bind(wx.EVT_BUTTON, self.onAutoOptim, self.autooptim)
		self.buttonrow.Add(self.autooptim, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.clear = wx.Button(self.frame, -1, 'Rm &Worst Picks')
		self.frame.Bind(wx.EVT_BUTTON, self.onClearBadPicks, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		self.particleCutoff = wx.Button(self.frame, -1, '&Cutoff...')
		self.Bind(wx.EVT_BUTTON, self.onParticleCutoff, self.particleCutoff)
		self.buttonrow.Add(self.particleCutoff, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.xferpick = wx.Button(self.frame, -1, '&Xfer picks')
		self.frame.Bind(wx.EVT_BUTTON, self.onXferPick, self.xferpick)
		self.buttonrow.Add(self.xferpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		self.clearPolygon = wx.Button(self.frame, wx.ID_REMOVE, 'Rm &Polygon')
		self.Bind(wx.EVT_BUTTON, self.onClearPolygon, self.clearPolygon)
		self.buttonrow.Add(self.clearPolygon, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.reset = wx.Button(self.frame, wx.ID_RESET, 'Reset...')
		self.frame.Bind(wx.EVT_BUTTON, self.onResetParams, self.reset)
		self.buttonrow.Add(self.reset, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

	#---------------------------------------
	def createStandAloneButtons(self):
		"""
		These are buttons related to the standalone version of TiltPicker
		"""

		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.dogpick_dialog = tiltDialog.DogPickerDialog(self)
		self.dogpick = wx.Button(self.frame, wx.ID_OPEN, '&DoG Pick...')
		self.frame.Bind(wx.EVT_BUTTON, self.onAutoDogPick, self.dogpick)
		self.buttonrow.Add(self.dogpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.quit = wx.Button(self.frame, wx.ID_EXIT, '&Quit')
		self.frame.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.buttonrow.Add(self.quit, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		return

	#---------------------------------------
	def createLoopButtons(self):
		"""
		These are buttons related to the Appion pipeline version of TiltPicker
		"""
		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.shift = wx.Button(self.frame,-1, '&Get Shift')
		self.frame.Bind(wx.EVT_BUTTON, self.onGuessShift, self.shift)
		self.buttonrow.Add(self.shift, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		self.importpicks = wx.Button(self.frame, -1, '&Import')
		self.frame.Bind(wx.EVT_BUTTON, self.onImportPicks, self.importpicks)
		self.buttonrow.Add(self.importpicks, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.quit = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.frame.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.buttonrow.Add(self.quit, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		#spacer
		self.buttonrow.Add((8,self.buttonheight), 0, wx.ALL, 1)

		self.assessnone = wx.ToggleButton(self.frame, -1, "None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetMinSize((70,self.buttonheight))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		#self.assesskeep.SetMinSize((70,self.buttonheight))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "&Reject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		#self.assessreject.SetMinSize((70,self.buttonheight))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		return

	#---------------------------------------
	def menuData(self):
		if self.mode == 'default':
			return [
				("&File", (
					( "&Open", "Open picked particles from file", self.onFileOpen, wx.ID_OPEN ),
					( "Open new left image", "Open new left image and restart TiltPicker", self.selectLeftImageToOpen ),
					( "Open new right image", "Open new right image and restart TiltPicker", self.selectRightImageToOpen ),
					( 0, 0, 0),
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
					( "&Init", "Initialize alignment parameters", self.onInitParams ),
					( "&Reset", "Clear picks and reset parameters", self.onResetParams, wx.ID_RESET ),
					( "Clear &Worst Picks", "Remove worst picked particles", self.onClearBadPicks ),
					( "Clear &Polygon", "Clear particle with polygon", self.onClearPolygon ),
				)),
				("Refine", (
					( "Auto Op&timize", "Find theta and optimize angles", self.onAutoOptim ),
					( 0, 0, 0),
					( "Find &Theta", "Calculate theta from picked particles", self.onFitTheta ),
					( "&Optimize Angles", "Optimize angles with least squares", self.onFitAll ),
					( "&Apply", "Apply picks", self.onUpdate, wx.ID_APPLY ),
					( "&Mask Overlapping Region", "Mask overlapping region", self.onMaskRegion ),
					( "&Calculate Percent Overlap", "Calculate percent overlap", self.onGetOverlap ),
				)),
				("Picking", (
					( "Auto &DoG pick particles", "Run DoG picker program", self.onAutoDogPick ),
					( "Tran&Xfer Picks", "Transfer picks from one image to another using fit parameters", self.onXferPick ),
					( "Remove &Worst particle picks", "Remove picks that with the largest error", self.onClearBadPicks ),
					( "Apply particle RMSD &Cutoff", "Remove picks with RMSD above a certain cutoff", self.onParticleCutoff ),
					( "Remove picks within &Polygon", "Remove picks within Polygon", self.onClearPolygon ),
					( "&Guess initial particle match", "Try to find an initial particle match using a cross-correlation search", self.onCheckGuessShift ),
					( "Repair picks", "Attempt to repair your picks if you accidentally deleted a pick and forgot where", self.onRepairList ),
					( 0, 0, 0),
					( "&Clear picks", "Clear all picked particles", self.onClearPicks, wx.ID_CLEAR ),
					( "&Reset TiltPicker", "Remove all picks and start over", self.onResetParams, wx.ID_RESET ),
				)),
				("&Help", (
					( "&About TiltPicker", "Show product information", self.onShowAboutTiltPicker, wx.ID_HELP),
				)),
			]
		else:
			return [
				("Pipeline", (
					( "&Import picks", "Import picked particles from previous run", self.onImportPicks ),
					( "&Forward", "Advance to next image", self.onQuit, wx.ID_FORWARD ),
				)),
				("&Edit", (
					( "&Clear", "Clear all picked particles", self.onClearPicks, wx.ID_CLEAR ),
					( "&Init", "Initialize alignment parameters", self.onInitParams ),
					( "&Reset", "Clear picks and reset parameters", self.onResetParams, wx.ID_RESET ),
					( "Clear &Worst Picks", "Remove worst picked particles", self.onClearBadPicks ),
					( "Clear &Polygon", "Clear particle with polygon", self.onClearPolygon ),
				)),
				("Refine", (
					( "Find &Theta", "Calculate theta from picked particles", self.onFitTheta ),
					( "&Optimize Angles", "Optimize angles with least squares", self.onFitAll ),
					( "Auto Op&timize", "Find theta and optimize angles", self.onAutoOptim ),
					( "&Apply", "Apply picks", self.onUpdate, wx.ID_APPLY ),
					( "&Mask Overlapping Region", "Mask overlapping region", self.onMaskRegion ),
					( "&Calculate Percent Overlap", "Calculate percent overlap", self.onGetOverlap ),
				)),
				("Picking", (
					( "Auto &DoG pick particles", "Run DoG picker program", self.onAutoDogPick ),
					( "Tran&Xfer Picks", "Transfer picks from one image to another using fit parameters", self.onXferPick ),
					( "Remove &Worst particle picks", "Remove picks that with the largest error", self.onClearBadPicks ),
					( "Apply particle RMSD &Cutoff", "Remove picks with RMSD above a certain cutoff", self.onParticleCutoff ),
					( "Remove picks within &Polygon", "Remove picks within Polygon", self.onClearPolygon ),
					( "&Guess initial particle match", "Try to find an initial particle match using a cross-correlation search", self.onCheckGuessShift ),
					( "Repair picks", "Attempt to repair your picks if you accidentally deleted a pick and forgot where", self.onRepairList ),
					( 0, 0, 0),
					( "&Clear picks", "Clear all picked particles", self.onClearPicks, wx.ID_CLEAR ),
					( "&Reset TiltPicker", "Remove all picks and start over", self.onResetParams, wx.ID_RESET ),
				)),
				("Assess", (
					( "&None", "Don't assess image pair", self.onToggleNone, -1, wx.ITEM_RADIO),
					( "&Keep", "Keep this image pair", self.onToggleKeep, -1, wx.ITEM_RADIO),
					( "&Reject", "Reject this image pair", self.onToggleReject, -1, wx.ITEM_RADIO),
				)),
				("&Help", (
					( "&About TiltPicker", "Show product information", self.onShowAboutTiltPicker, wx.ID_HELP ),
				)),
			]

	#---------------------------------------
	def createMenuBar(self):
		self.menubar = wx.MenuBar()
		self.about_dialog = tiltDialog.AboutTiltPickerDialog(self)
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
	def onClearPolygon(self, evt):
		t0 = time.time()
		### check particles
		targets1 = self.getArray1()
		targets2 = self.getArray2()
		if len(targets1) == 0 or len(targets2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot remove polygon. There are no picks.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot remove polygon.\nThere are no picks.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		### check polygon vertices
		vert1 = self.panel1.getTargetPositions('Polygon')
		vert2 = self.panel2.getTargetPositions('Polygon')
		### check polygon vertices
		if len(vert1) < 3 and len(vert2) < 3:
			self.statbar.PushStatusText("ERROR: Could not create a closed polygon. Select more vertices.", 0)
			dialog = wx.MessageDialog(self.frame,
				"Could not create a closed polygon.\nSelect more vertices.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		elif len(vert1) >= 3 and len(vert2) >= 3:
			self.statbar.PushStatusText("ERROR: Polygons on both images. Create a polygon on only one image.", 0)
			dialog = wx.MessageDialog(self.frame,
				"Polygons on both images.\nCreate a polygon on only one image.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			self.panel2.setTargets('Polygon', [])
			return False

		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot remove polygon. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot remove polygon.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		newpart1 = []
		newpart2 = []
		eliminated = 0

		apDisplay.printMsg("Removing points inside polygon")

		if len(vert1) > len(vert2):
			#draw transformed polygon
			v1 = numpy.asarray(vert1, dtype=numpy.float32)
			v2 = apTiltTransform.a1Toa2Data(v1, self.data)
			self.panel2.setTargets('Polygon', v2)
			self.panel2.UpdateDrawing()
			for i in range(targets1.shape[0]):
				point = tuple((targets1[i,0], targets1[i,1]))
				#print coord
				if self.insidePolygon(point, v1):
					eliminated += 1
				else:
					newpart1.append(targets1[i])
					newpart2.append(targets2[i])

		elif len(vert2) > len(vert1):
			#draw transformed polygon
			v2 = numpy.asarray(vert2, dtype=numpy.float32)
			v1 = apTiltTransform.a2Toa1Data(v2, self.data)
			self.panel1.setTargets('Polygon', v1)
			self.panel1.UpdateDrawing()
			for i in range(targets2.shape[0]):
				point = tuple((targets2[i,0], targets2[i,1]))
				if self.insidePolygon(point, v2):
					eliminated += 1
				else:
					newpart1.append(targets1[i])
					newpart2.append(targets2[i])

		self.panel1.setTargets('Picked',newpart1)
		self.panel2.setTargets('Picked',newpart2)
		self.panel1.UpdateDrawing()
		self.panel2.UpdateDrawing()

		apDisplay.printMsg("Removed %d particles inside polygon in %s"%(eliminated, apDisplay.timeString(time.time()-t0)))
		self.statbar.PushStatusText("Removed %d particles inside polygon"%(eliminated), 0)
		dialog = wx.MessageDialog(self.frame,
			"Removed %d particles inside polygon"%(eliminated), 'INFORMATION', wx.OK|wx.ICON_INFORMATION)
		if dialog.ShowModal() == wx.ID_OK:
			dialog.Destroy()
		self.panel1.setTargets('Polygon', [])
		self.panel2.setTargets('Polygon', [])
		self.onUpdate(evt)

	#---------------------------------------
	def insidePolygon(self, point, verts):
		"""Test whether the points are inside the specified polygon.
		The shape is specified by 'verts'
		Arguments:
		points - (x,y) point
		verts - (N,2) array of x,y vertices

		Returns:
		- True/False based on result of in/out test.

		Uses the 'ray to infinity' even-odd test.
		Let the ray be the horizontal ray starting at p and going to +inf in x.
		"""
		verts = numpy.asarray(verts)
		x,y = point

		### setup edge list
		N = verts.shape[0]
		### create edge pairs
		edges = numpy.column_stack([range(N),range(1, N+1)])
		### wrap last vertex
		edges[N-1,1] = 0

		inside = False
		for e in edges:
			v0,v1 = verts[e[0]], verts[e[1]]
			# Check if both verts to the left of ray
			if v0[0]<x and v1[0]<x:
				continue
			# check if both on the same side of ray
			if (v0[1]<y and v1[1]<y) or (v0[1]>y and v1[1]>y):
				continue
			#check for horizontal line - another horz line can't intersect it
			if (v0[1]==v1[1]):
				continue
			# compute x intersection value
			xisect = v0[0] + (v1[0]-v0[0])*((y-v0[1])/(v1[1]-v0[1]))
			if xisect >= x:
				inside = not inside
		return inside

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

		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot mask images. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot mask images.\nNo alignment parameters.",\
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

		#GET THE VALUE
		bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, self.data)
		overlapStr = str(round(100*bestOverlap,2))+"% and "+str(round(100*tiltOverlap,2))+"%"
		self.statbar.PushStatusText("Overlap percentage of "+overlapStr, 0)
		self.data['overlap'] = round(bestOverlap,5)

	#---------------------------------------
	def onGetOverlap(self, evt):
		"""
		This function gets the overlap between the two images based on the alignment parameters
		"""
		#GET THE ARRAYS
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		a1 = self.targetsToArray(targets1)
		a2 = self.targetsToArray(targets2)

		#GET THE POINT VALUES
		apTiltTransform.setPointsFromArrays(a1, a2, self.data)

		#CHECK IF WE HAVE POINTS
		if len(a1) == 0 or len(a2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot get overlap. Not enough picks", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot get overlap.\nThere are no picks.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot get overlap. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot get overlap.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		#GET IMAGES
		image1 = numpy.asarray(self.panel1.imagedata, dtype=numpy.float32)
		image2 = numpy.asarray(self.panel2.imagedata, dtype=numpy.float32)

		#GET THE VALUE
		bestOverlap, tiltOverlap = apTiltTransform.getOverlapPercent(image1, image2, self.data)
		overlapStr = str(round(100*bestOverlap,2))+"% and "+str(round(100*tiltOverlap,2))+"%"
		self.statbar.PushStatusText("Overlap percentage of "+overlapStr, 0)
		self.data['overlap'] = round(bestOverlap,5)

	#---------------------------------------
	def onUpdate(self, evt):
		"""
		This function updates the aligned particles to the picked particles
		"""
		#GET ARRAYS
		a1 = self.getArray1()
		a2 = self.getArray2()
		#CHECK TO SEE IF IT OKAY TO PROCEED
		if len(a1) == 0 or len(a2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot transfer picks. There are no picks.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot transfer picks.\nThere are no picks.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		#SORT PARTICLES
		#self.sortParticles(None)
		#GET ARRAYS
		a1b = self.getAlignedArray1()
		a2b = self.getAlignedArray2()
		#SET THE ALIGNED ARRAYS
		self.panel2.setTargets('Aligned', a1b )
		self.panel1.setTargets('Aligned', a2b )
		#FIND PARTICLES WITH LARGE ERROR
		(a1c, a2c) = self.getBadPicks()
		if len(a1c) > 0:
			self.panel1.setTargets('Worst', a1c )
		if len(a2c) > 0:
			self.panel2.setTargets('Worst', a2c )
		#for target in targets1:
		#	target['stats']['RMSD'] = rmsd

	#---------------------------------------
	def onXferPick(self, evt):
		"""
		This function transfers any picked particles without a corresponding pair
		to the other image using the alignment parameters
		"""
		#GET ARRAYS
		a1 = self.getArray1()
		a2 = self.getArray2()
		#CHECK TO SEE IF IT OKAY TO PROCEED
		if len(a1) == 0 or len(a2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot transfer picks. There are no picks.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot transfer picks.\nThere are no picks.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot transfer picks. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot transfer picks.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		if len(a1) - len(a2) == 0:
			self.statbar.PushStatusText("ERROR: Cannot transfer picks. Same number picks for each panel.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot transfer picks.\nSame number picks for each panel.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		### Case 1: left panel has more than right panel
		if len(a1) > len(a2):
			a1b = self.getAlignedArray1()
			lastpick = a1b[len(a2):]
			a2list = self.panel2.getTargets('Picked')
			a2list.extend(lastpick)
			self.panel2.setTargets('Picked', a2list )
		elif len(a2) > len(a1):
			a2b = self.getAlignedArray2()
			lastpick = a2b[len(a1):]
			a1list = self.panel1.getTargets('Picked')
			a1list.extend(lastpick)
			self.panel1.setTargets('Picked', a1list )
		self.onUpdate(evt)

	#---------------------------------------
	def sortParticles(self, evt):
		#GET ARRAYS
		a1 = self.getArray1()
		a2 = self.getArray2()
		if len(a1) != len(a2):
			return False
		#MERGE INTO ONE
		#a3 = numpy.hstack((a1, a2))
		a3 = []
		for i in range(len(a1)):
			a3.append([a1[i,0], a1[i,1], a2[i,0], a2[i,1],])
		#SORT PARTICLES
		def _distSortFunc(a, b):
			if 5*a[0]+a[1] > 5*b[0]+b[1]:
				return 1
			return -1
		a3.sort(_distSortFunc)
		a3b = numpy.asarray(a3)
		#SPLIT BACK UP
		a1b = a3b[:,0:2]
		a2b = a3b[:,2:4]
		#fix first particle???
		#a1c = numpy.vstack(([[a1[0,0], a1[0,1]],a1b)
		#a2c = numpy.vstack(([[a2[0,0], a2[0,1]],a2b)
		#SET SORTED TARGETS
		self.panel1.setTargets('Picked', a1b )
		self.panel2.setTargets('Picked', a2b )

	#---------------------------------------
	def onCheckGuessShift(self, evt):
		if ( self.data['theta'] == 0.0
		 or self.data['gamma'] == 0.0
		 or self.data['phi'] == 0.0 ):
			self.shift_dialog.Show()
		else:
			self.onGuessShift(evt)
		return

	#---------------------------------------
	def onGuessShift(self, evt):
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		if len(targets1) > 2 or len(targets2) > 2:
			self.statbar.PushStatusText("ERROR: Abort guess shift; more than 2 particles", 0)
			dialog = wx.MessageDialog(self.frame,
				"Will not guess shift when you have more than 2 particles.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		#cross-corrlate to get shift
		img1 = numpy.asarray(self.panel1.imagedata, dtype=numpy.float32)
		tiltdiff = self.data['theta']
		img2 = numpy.asarray(self.panel2.imagedata, dtype=numpy.float32)
		tiltaxis = (self.data['phi'] + self.data['gamma'])/2.0
		if tiltaxis == 0.0:
			tiltaxis = -7.2

		# snr > than arbitrary value run some other stuff
		if len(self.picks1) > 10 and len(self.picks2) > 10:
			### PIPELINE MODE

			### set important parameters
			imgfile1 = self.panel1.filename
			imgfile2 = self.panel2.filename
			outfile = self.data['outfile']
			pixdiam = self.data['pixdiam']

			if False:
				### run old tilt automation scheme
				origin, newpart, snr, ang = apTiltShift.getTiltedCoordinates(img1, img2, tiltdiff, 
					self.picks1, angsearch=True, inittiltaxis=tiltaxis)
				self.panel1.setTargets('Picked', [origin])
				self.panel2.setTargets('Picked', [newpart])

				self.shift.SetBackgroundColour(self.deselectcolor)
				time.sleep(0.5)

				self.onMaskRegion(None)
				time.sleep(0.5)
				self.onImportPicks(None, msg=False, tight=False)
				time.sleep(0.5)
				self.deleteFirstPick()
				time.sleep(0.5)
				self.onAutoOptim(None)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onAutoOptim(None)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onImportPicks(None, msg=False, tight=False)
				time.sleep(0.5)
				self.onAutoOptim(None)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onAutoOptim(None)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onImportPicks(None, msg=False, tight=False)
				time.sleep(0.5)
				self.onAutoOptim(None)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onAutoOptim(None)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onImportPicks(None, msg=False, tight=True)
				time.sleep(0.5)
				self.onClearBadPicks(None)
				time.sleep(0.5)
				self.onAutoOptim(None)
			else:
				### run new tilt automation scheme
				autotilter = autotilt.autoTilt()
				result = autotilter.processTiltPair(imgfile1, imgfile2, self.picks1, 
					self.picks2, tiltdiff, outfile, pixdiam, tiltaxis)
				if result is not None:
					self.readData(outfile)
		else:
			### STAND ALONE MODE
			#dialog = wx.MessageDialog(self.frame,
			#	"Unsure about initial shift", 'INFORMATION', wx.OK|wx.ICON_INFORMATION)
			#if dialog.ShowModal() == wx.ID_OK:
			#	dialog.Destroy()
			origin, newpart, snr, ang = apTiltShift.getTiltedCoordinates(img1, img2, tiltdiff, 
				self.picks1, True, tiltaxis)
			self.panel1.setTargets('Picked', [origin])
			self.panel2.setTargets('Picked', [newpart])
			self.shift.SetBackgroundColour(self.deselectcolor)

		return

	#---------------------------------------
	def getCutoffCriteria(self, errorArray):
		#do a small minimum filter to get rid of outliers
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
	def deleteFirstPick(self):
		a1 = self.getArray1()
		a2 = self.getArray2()
		a1b = a1[1:]
		a2b = a2[1:]
		self.panel1.setTargets('Picked', a1b)
		self.panel2.setTargets('Picked', a2b)

	#---------------------------------------
	def getBadPicks(self):
		good = self.getGoodPicks()
		a1 = self.getArray1()
		a2 = self.getArray2()
		if good.sum() < 2:
			return ([],[])
		b1 = []
		b2 = []
		for i,v in enumerate(good):
			if bool(v) is False:
				b1.append(a1[i])
				b2.append(a2[i])
		return (b1, b2)

	#---------------------------------------
	def getGoodPicks(self):
		a1 = self.getArray1()
		a2 = self.getArray2()
		numpoints = max(a1.shape[0], a2.shape[0])
		good = numpy.zeros((numpoints), dtype=numpy.bool)
		if len(a1) != len(a2):
			good[len(a1):] = True
			good[len(a2):] = True
		err = self.getRmsdArray()
		cut = self.getCutoffCriteria(err)

		self.minworsterr = 1.0
		worstindex = []
		worsterr = []
		### always set 3% as bad if cutoff > max rmsd
		numbad = int(len(a1)*0.03 + 1.0)
		for i,e in enumerate(err):
			if e > self.minworsterr:
				### find the worst overall picks
				if len(worstindex) >= numbad:
					j = numpy.argmin(numpy.asarray(worsterr))
					### take previous worst pick and make it good
					k = worstindex[j]
					good[k] = True
					good[i] = False
					worstindex[j] = i
					worsterr[j] = e
					### increase the min worst err
					self.minworsterr = numpy.asarray(worsterr).min()
				else:
					### add the worst pick
					good[i] = False
					worstindex.append(i)
					worsterr.append(e)
			elif e < cut and (i == 0 or e > 0):
				### this is a good pick
				good[i] = True
		if good.sum() == 0:
			good[0] = True
		sumstr = ("%d of %d good (%d bad) particles; min worst error=%.3f"
			%(good.sum(),numpoints,numpoints-good.sum(),self.minworsterr))
		apDisplay.printMsg(sumstr)
		self.statbar.PushStatusText(sumstr, 0)
		return good

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
	def onImportPicks(self, evt, pixdiam=None, msg=True, tight=True, showmaps=False):
		"""
		take unmatched particles picks (self.picks1, self.picks2)
		match them using alignment parameters and merge them with current picks
		"""
		### Picks are imported from tiltaligner or DoG picker
		len1 = len(self.picks1)
		len2 = len(self.picks2)

		### make sure we have some picks
		if len1 < 1 or len2 < 1:
			dialog = wx.MessageDialog(self.frame,
				"There are no picks to import: "+str(len1)+", "+str(len2),
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		### get existing picks
		a1 = self.getArray1()
		a2 = self.getArray2()
		### make sure we have some picks
		if len(a1) < 1 or len(a2) < 1:
			dialog = wx.MessageDialog(self.frame,
				"You must pick a particle pair first",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		### make sure we have alignment
		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot import picks. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot import picks.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		### save existing picks to revert
		olda1 = a1
		olda2 = a2

		### update alignment parameters
		apTiltTransform.setPointsFromArrays(a1, a2, self.data)

		### set additional parameters
		if pixdiam is None:
			pixdiam = self.data['pixdiam']
		if tight is True:
			pixdiam /= 2.0

		### match picks to one another
		list1, list2 = apTiltTransform.alignPicks2(self.picks1, self.picks2, self.data, limit=pixdiam)

		### confirm we have new picks
		if list1.shape[0] == 0 or list2.shape[0] == 0:
			dialog = wx.MessageDialog(self.frame,
				"No new picks were found",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		### merge picks with existing picks
		newa1, newa2 = apTiltTransform.betterMergePicks(a1, list1, a2, list2)
		newparts = newa1.shape[0] - a1.shape[0]
		self.panel1.setTargets('Picked', newa1)
		self.panel2.setTargets('Picked', newa2)
		self.onUpdate(None)

		### show results
		self.statbar.PushStatusText("Inserted "+str(newparts)+" new particles", 0)

		### pop up to confirm that picks are good.
		if msg is True:
			dialog = wx.MessageDialog(self.frame,
				"Do you want to keep the "+str(newparts)+" inserted particles", 
				'Keep particles?', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_NO:
				self.panel1.setTargets('Picked', olda1)
				self.panel2.setTargets('Picked', olda2)
			dialog.Destroy()

		### this is the case where dog picker was run
		if showmaps is True:
			dialog = wx.MessageDialog(self.frame,
				"Inserted "+str(newparts)+" new particles\n\nShow DoG maps?", 
				'DoG picker results', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_YES:
				### show the dog maps in a loop
				self.dogimgnum = 1
				dialog.Destroy()
				self.viewdogmaps_frame = tiltDialog.viewDogMapsFrame(self)
				self.viewdogmaps_frame.Show()
				if self.viewdogmaps_frame.ShowModal() == wx.ID_OK:
					self.viewdogmaps_frame.Destroy()
			else:
				dialog.Destroy()


		return True

	#---------------------------------------
	def onParticleCutoff(self, env):
		"""
		This function removes all particles worse than a set cutoff value
		"""
		### check to see if this request is valid
		if len(self.getArray1()) < 5 or len(self.getArray2()) < 5:
			dialog = wx.MessageDialog(self.frame,
				"You should pick at least 5 particle pairs first", 'Error',
				 wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		### make sure we have alignment
		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot remove picks. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot remove picks.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		### show cutoff dialog
		self.onUpdate(env)
		self.partcutdialog = tiltDialog.PartCutoffDialog(self)
		self.partcutdialog.Show()
		if self.partcutdialog.ShowModal() == wx.ID_APPLY:
			self.onUpdate(env)

	#---------------------------------------
	def onFitTheta(self, evt):
		if len(self.getArray1()) < 5 or len(self.getArray2()) < 5:
			dialog = wx.MessageDialog(self.frame,
				"You should pick at least 5 particle pairs first", 'Error',
				 wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		self.theta_dialog.tiltvalue.SetLabel(label=("       %3.3f       " % self.data['theta']))
		self.theta_dialog.Show()

	#---------------------------------------
	def onFitAll(self, evt):
		self.onUpdate(None)
		if len(self.getArray1()) < 5 or len(self.getArray2()) < 5:
			dialog = wx.MessageDialog(self.frame,
				"You should pick at least 5 particle pairs first", 'Error',
				 wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		if self.data['theta'] == 0.0 and self.data['thetarun'] is False:
			dialog = wx.MessageDialog(self.frame,
				"You should run 'Find Theta' first", 'Error', wx.OK|wx.ICON_WARNING)
			dialog.ShowModal()
			dialog.Destroy()

		self.fitall_dialog.thetavalue.SetValue(round(self.data['theta'],4))
		self.fitall_dialog.gammavalue.SetValue(round(self.data['gamma'],4))
		self.fitall_dialog.phivalue.SetValue(round(self.data['phi'],4))
		self.fitall_dialog.scalevalue.SetValue(round(self.data['scale'],4))
		self.fitall_dialog.shiftxvalue.SetValue(round(self.data['shiftx'],4))
		self.fitall_dialog.shiftyvalue.SetValue(round(self.data['shifty'],4))
		self.fitall_dialog.Show()
		#values are then modified, if the user selected apply in tiltDialog

	#---------------------------------------
	def onRepairList(self, evt):
		### pop up to confirm that picks are good.
		if msg is True:
			dialog = wx.MessageDialog(self.frame,
				"This fucntion attempts to repairs your picks when you delete "
				+"an unmatched pair or from one image and not the other", 
				'Try to repair picks?', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_NO:
				dialog.Destroy()
				return
			dialog.Destroy()
		a1 = self.getArray1()
		a2 = self.getArray2()
		rmsd = self.getRmsdArray()
		a1b, a2b = apTiltTransform.repairPicks(a1, a2, rmsd)
		self.panel1.setTargets('Picked', a1b)
		rmsd1 = ndimage.sum(self.getRmsdArray())
		self.panel1.setTargets('Picked', a1)
		self.panel2.setTargets('Picked', a2b)
		rmsd2 = ndimage.sum(self.getRmsdArray())
		if rmsd1 < rmsd2:
			self.panel1.setTargets('Picked', a1b)
			self.panel2.setTargets('Picked', a2)
		else:
			self.panel1.setTargets('Picked', a1)
			self.panel2.setTargets('Picked', a2b)
		return

	#---------------------------------------
	def onAutoOptim(self, evt):
		if len(self.getArray1()) < 5 or len(self.getArray2()) < 5:
			dialog = wx.MessageDialog(self.frame,
				"You should pick at least 5 particle pairs first", 'Error',
				 wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		### run find theta
		self.theta_dialog.onRunTiltAng(None)
		self.theta_dialog.onApplyTiltAng(None)

		### run optimize angles
		self.fitall_dialog.thetavalue.SetValue(round(self.data['theta'],4))
		self.fitall_dialog.gammavalue.SetValue(round(self.data['gamma'],4))
		self.fitall_dialog.phivalue.SetValue(round(self.data['phi'],4))
		self.fitall_dialog.scalevalue.SetValue(round(self.data['scale'],4))
		self.fitall_dialog.shiftxvalue.SetValue(round(self.data['shiftx'],4))
		self.fitall_dialog.shiftyvalue.SetValue(round(self.data['shifty'],4))
		if self.data['optimrun'] is False:
			if self.fitall_dialog.thetatog.GetValue() is False:
				self.fitall_dialog.onToggleTheta(None)
			if self.fitall_dialog.gammatog.GetValue() is False:
				self.fitall_dialog.onToggleGamma(None)
			if self.fitall_dialog.phitog.GetValue() is False:
				self.fitall_dialog.onTogglePhi(None)
			if self.fitall_dialog.scaletog.GetValue() is True:
				self.fitall_dialog.onToggleScale(None)
			if self.fitall_dialog.shifttog.GetValue() is False:
				self.fitall_dialog.onToggleShift(None)
		lastiter = [80,80,80]
		count = 0
		totaliter = 0
		while max(lastiter) > 75 and count < 30:
			count += 1
			self.fitall_dialog.onRunLeastSquares(None)
			lastiter[2] = lastiter[1]
			lastiter[1] = lastiter[0]
			lastiter[0] = self.fitall_dialog.lsfit['iter']
			totaliter += lastiter[0]
			apDisplay.printMsg("Least squares: %d rounds, %d iterations, final rmsd %.3f"
				%(count,totaliter,self.fitall_dialog.lsfit['rmsd']))
		self.fitall_dialog.onApplyLeastSquares(None)
		self.onMaskRegion(None)

	#---------------------------------------
	def onClearBadPicks(self, evt):
		"""
		Remove picks with RMSD > mean + 3 * stdev
		"""
		### make sure we have alignment
		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot remove picks. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot remove picks.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		good = self.getGoodPicks()
		a1 = self.getArray1()
		a2 = self.getArray2()
		if good.sum() < 2:
			return
		g1 = []
		g2 = []
		for i,v in enumerate(good):
			if bool(v) is True:
				g1.append(a1[i])
				g2.append(a2[i])
		apDisplay.printMsg( "Eliminated "+str(len(a1)-len(g1))+" particles")
		self.panel1.setTargets('Worst', [] )
		self.panel2.setTargets('Worst', [] )
		self.panel1.setTargets('Picked', g1 )
		self.panel2.setTargets('Picked', g2 )
		self.onUpdate(None)
		self.statbar.PushStatusText("Removed "+str(len(a1)-len(g1))+" particles", 0)

	#---------------------------------------
	def onShowAboutTiltPicker(self, evt):
		self.about_dialog.Show()

	#---------------------------------------
	def onAutoDogPick(self, evt):
		"""
		Automatically picks image pairs using dog picker
		"""
		if self.data['theta'] == 0.0 and self.data['thetarun'] is False:
			dialog = wx.MessageDialog(self.frame,
				"You must run 'Find Theta' first", 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		if self.data['optimrun'] is False:
			self.statbar.PushStatusText("ERROR: Cannot run Dog picker. No alignment parameters.", 0)
			dialog = wx.MessageDialog(self.frame, "Cannot run Dog picker.\nNo alignment parameters.",\
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		self.dogpick_dialog.Show()

	#---------------------------------------
	def onClearPicks(self, evt, msg=True):
		### pop up to confirm that picks are good.
		if msg is True:
			dialog = wx.MessageDialog(self.frame,
				"Are you sure you want to delete all picked particles?", 
				'Clear picks?', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_NO:
				dialog.Destroy()
				return
			dialog.Destroy()
		self.panel1.setTargets('Picked', [])
		self.panel1.setTargets('Aligned', [])
		self.panel1.setTargets('Worst', [] )
		self.panel1.setTargets('Polygon', [] )
		self.panel2.setTargets('Picked', [])
		self.panel2.setTargets('Aligned', [])
		self.panel2.setTargets('Worst', [] )
		self.panel2.setTargets('Polygon', [] )
		self.statbar.PushStatusText("Cleared all particle picks", 0)
		if msg is True:
			self.onUpdate(evt)

	#---------------------------------------
	def onInitParams(self, evt, msg=True):
		### pop up to confirm that picks are good.
		if msg is True:
			dialog = wx.MessageDialog(self.frame,
				"Are you sure you want to reset all alignment parameters?", 
				'Reset?', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_NO:
				dialog.Destroy()
				return
			dialog.Destroy()

		self.data['thetarun'] = False
		self.data['optimrun'] = False
		self.data['arealim'] = 5000.0
		if self.appionloop is None:
			self.data['theta'] = 0.0
		else:
			self.data['theta'] = self.appionloop.theta
		self.data['gamma'] = 0.0
		self.data['phi'] = 0.0
		self.data['shiftx'] = 0.0
		self.data['shifty'] = 0.0
		self.data['point1'] = (0.0, 0.0)
		self.data['point2'] = (0.0, 0.0)
		self.data['scale'] = 1.0
		if msg is True:
			self.statbar.PushStatusText("Reset all parameters", 0)
			self.onUpdate(evt)

	#---------------------------------------
	def onResetParams(self, evt, msg=True):
		### pop up to confirm that picks are good.
		if msg is True:
			dialog = wx.MessageDialog(self.frame,
				"Are you sure you want to delete all picks and parameters?", 
				'Reset?', wx.NO|wx.YES|wx.ICON_QUESTION)
			if dialog.ShowModal() == wx.ID_NO:
				dialog.Destroy()
				return
			dialog.Destroy()

		self.onInitParams(evt, msg=False)
		#reset fit values
		self.fitall_dialog.thetavalue.SetValue(round(self.data['theta'],4))
		self.fitall_dialog.gammavalue.SetValue(round(self.data['gamma'],4))
		self.fitall_dialog.phivalue.SetValue(round(self.data['phi'],4))
		self.fitall_dialog.scalevalue.SetValue(round(self.data['scale'],4))
		self.fitall_dialog.shiftxvalue.SetValue(round(self.data['shiftx'],4))
		self.fitall_dialog.shiftyvalue.SetValue(round(self.data['shifty'],4))
		#reset toggle buttons
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
		#reset images
		try:
			self.panel1.openImageFile(self.panel1.filename)
			self.panel2.openImageFile(self.panel2.filename)
			self.panel1.setBitmap()
			self.panel1.setVirtualSize()
			self.panel1.setBuffer()
			self.panel1.UpdateDrawing()
			self.panel2.setBitmap()
			self.panel2.setVirtualSize()
			self.panel2.setBuffer()
			self.panel2.UpdateDrawing()
		except:
			pass
		self.onClearPicks(None, False)
		self.statbar.PushStatusText("Reset all picks and parameters", 0)
		if msg is True:
			self.onUpdate(evt)

	#---------------------------------------
	def onFileSave(self, evt):
		if self.data['outfile'] == "" or self.data['dirname'] == "":
			#First Save, Run SaveAs...
			return self.onFileSaveAs(evt)
		self.saveData()

	#---------------------------------------
	def onFileSaveAs(self, evt):
		dlg = wx.FileDialog(self.frame, "Choose a pick file to save as", self.data['dirname'], "", \
			tiltfile.filetypefilter, wx.SAVE|wx.OVERWRITE_PROMPT)
		if 'filetypeindex' in self.data and self.data['filetypeindex'] is not None:
			dlg.SetFilterIndex(self.data['filetypeindex'])
		#alt1 = "*.[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]"
		#alt2 = "Text Files (*.txt)|*.txt|All Files|*.*"
		if dlg.ShowModal() == wx.ID_OK:
			self.data['outfile'] = dlg.GetFilename()
			self.data['dirname']  = os.path.abspath(dlg.GetDirectory())
			self.data['filetypeindex'] = dlg.GetFilterIndex()
			self.saveData()
		dlg.Destroy()

	#---------------------------------------
	def saveData(self):
		targets1 = self.panel1.getTargets('Picked')
		targets2 = self.panel2.getTargets('Picked')
		if len(targets1) < 1 or len(targets2) < 1:
			if not self.appionloop:
				self.statbar.PushStatusText("ERROR: Cannot save file. Not enough picks", 0)
				dialog = wx.MessageDialog(self.frame, "Cannot save file.\nNot enough picks\n(less than 4 particle pairs)",\
					'Error', wx.OK|wx.ICON_ERROR)
				dialog.ShowModal()
				dialog.Destroy()
			return False

		if len(targets1) != len(targets2):
			return False
		filetype = None
		if self.data['filetypeindex'] is not None:
			filetype = tiltfile.filetypes[self.data['filetypeindex']]
		filename = os.path.join(self.data['dirname'], self.data['outfile'])
		savedata = {
			'image1name': self.data['image1file'],
			'image2name': self.data['image2file'],
			'gamma': self.data['gamma'],
			'theta': self.data['theta'],
			'phi': self.data['phi'],
			'shiftx': self.data['shiftx'],
			'shifty': self.data['shifty'],
			'picks1': self.getArray1(),
			'picks2': self.getArray2(),
			'align1': self.getAlignedArray2(),
			'align2': self.getAlignedArray1(),
			'rmsd': self.getRmsdArray(),
		}
		tiltfile.saveData(savedata, filename, filetype)
		self.statbar.PushStatusText("Saved "+str(len(targets1))+" particles to "+self.data['outfile'], 0)
		return True

	#---------------------------------------
	def onFileOpen(self, evt):
		dlg = wx.FileDialog(self.frame, "Choose a pick file to open", self.data['dirname'], "", \
			tiltfile.filetypefilter, wx.OPEN)
		if 'filetypeindex' in self.data and self.data['filetypeindex'] is not None:
			dlg.SetFilterIndex(self.data['filetypeindex'])
		if dlg.ShowModal() == wx.ID_OK:
			self.data['outfile'] = dlg.GetFilename()
			self.data['dirname']  = os.path.abspath(dlg.GetDirectory())
			self.data['filetypeindex'] = dlg.GetFilterIndex()
			self.data['filetype'] = tiltfile.filetypes[self.data['filetypeindex']]
			self.readData()
		dlg.Destroy()

	#---------------------------------------
	def readData(self, filename=None):
		filetype = None
		if self.data['filetypeindex'] is not None:
			filetype = tiltfile.filetypes[self.data['filetypeindex']]

		if filename is None:
			filename = os.path.join(self.data['dirname'], self.data['outfile'])

		print "Reading file: %s of type %s"%(filename,filetype)
		savedata = tiltfile.readData(filename, filetype)

		if len(savedata['picks1']) > 2 and len(savedata['picks2']) > 2:
			self.panel1.setTargets('Picked', savedata['picks1'])
			self.panel2.setTargets('Picked', savedata['picks2'])
			self.data.update(savedata)
		self.statbar.PushStatusText("Read "+str(len(savedata['picks1']))+" particles and parameters from file "+filename, 0)

	#---------------------------------------
	def getExtension(self):
		if self.data['filetypeindex'] == 0:
			self.data['extension'] = "spi"
		elif self.data['filetypeindex'] == 1:
			self.data['extension'] = "txt"
		elif self.data['filetypeindex'] == 2:
			self.data['extension'] = "pickle"
		elif self.data['filetypeindex'] == 3:
			self.data['extension'] = "xml"
		else:
			return "spi"
		return self.data['extension']

	#---------------------------------------
	def onQuit(self, evt):
		dialog = wx.MessageDialog(self.frame,
			"Are you sure you want to Quit?", 
			'Quit?', wx.NO|wx.YES|wx.ICON_QUESTION)
		if dialog.ShowModal() == wx.ID_NO:
			dialog.Destroy()
			return
		dialog.Destroy()

		a1 = self.getArray1()
		a2 = self.getArray2()
		if len(a1) > len(a2):
			self.statbar.PushStatusText(
				"ERROR: Left image ("+str(len(a2))+") has more picks than the right ("
				+str(len(a1))+"). Quit cancelled.", 0)
			dialog = wx.MessageDialog(self.frame,
				"Left image ("+str(len(a2))+") has more picks than the right ("
				+str(len(a1))+"). Quit cancelled.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False
		if len(a1) < len(a2):
			self.statbar.PushStatusText(
				"ERROR: Right image ("+str(len(a2))+") has more picks than the left ("
				+str(len(a1))+"). Quit cancelled.", 0)
			dialog = wx.MessageDialog(self.frame,
				"Right image ("+str(len(a2))+") has more picks than the left ("
				+str(len(a1))+"). Quit cancelled.",
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return False

		if self.appionloop:
			self.copyDataToAppionLoop()
			self.data['filetypeindex'] = self.appionloop.params['outtypeindex']
			self.data['outfile'] = os.path.basename(self.panel1.filename)+"."+self.getExtension()
			self.data['dirname'] = self.appionloop.params['pickdatadir']
			self.saveData()
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
				"""print "skipping key: "+str(i)+" of type "+str(type(v))"""
		self.appionloop.tiltparams['x1'] = self.data['point1'][0]
		self.appionloop.tiltparams['y1'] = self.data['point1'][1]
		self.appionloop.tiltparams['x2'] = self.data['point2'][0]
		self.appionloop.tiltparams['y2'] = self.data['point2'][1]
		self.appionloop.assess = self.assess

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
	def selectRightImageToOpen(self, env=None):
		dlg = wx.FileDialog(self.frame, "Choose a right image file to open", self.data['dirname'], "", \
			tiltfile.imagetypefilter, wx.OPEN)
		if 'imagetypeindex' in self.data and self.data['imagetypeindex'] is not None:
			dlg.SetFilterIndex(self.data['imagetypeindex'])
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetFilename()
			pathname = os.path.abspath(dlg.GetDirectory())
			filepath = os.path.join(pathname, filename)
			if os.path.isfile(filepath):
				self.data['image2file'] = filename
				self.data['image2path'] = pathname
				app.panel2.openImageFile(filepath)
				self.onResetParams(None, False)
		dlg.Destroy()

	#---------------------------------------
	def selectLeftImageToOpen(self, env=None):
		dlg = wx.FileDialog(self.frame, "Choose a left image file to open", self.data['dirname'], "", \
			tiltfile.imagetypefilter, wx.OPEN)
		if 'imagetypeindex' in self.data and self.data['imagetypeindex'] is not None:
			dlg.SetFilterIndex(self.data['imagetypeindex'])
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetFilename()
			pathname = os.path.abspath(dlg.GetDirectory())
			filepath = os.path.join(pathname, filename)
			if os.path.isfile(filepath):
				self.data['image1file'] = filename
				self.data['image1path'] = pathname
				app.panel1.openImageFile(filepath)
				self.onResetParams(None, False)
		dlg.Destroy()

	#---------------------------------------
	def canonicalShape(self, shape):
		if shape == '.'    or shape == 'point' or shape == 'dot':
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
	shapes = ("circle","square","diamond","plus","cross","dot")

	parser = OptionParser(usage=usage)
	parser.add_option("-1", "-l", "--left-image", dest="img1file",
		help="First input image (left)", metavar="FILE")
	parser.add_option("-2", "-r", "--right-image", dest="img2file",
		help="Second input image (right)", metavar="FILE")
	parser.add_option("-p", "--pick-file", dest="pickfile",
		help="Particle pick file", metavar="FILE")
	parser.add_option("-t", "--tiltangle", dest="tiltangle", type="float",
		help="Initial tilt angle", metavar="#")
	parser.add_option("-x", "--tiltaxis", dest="tiltaxis", type="float",
		help="Initial tilt axis angle", metavar="#")

	parser.add_option("-s", "--pick-shape", dest="pickshape",
		help="Particle picking shape", metavar="SHAPE",
		type="choice", choices=shapes, default="circle" )
	parser.add_option("-S", "--pick-shape-size", dest="pshapesize",
		help="Particle picking shape size", metavar="INT",
		type="int", default=30 )
	parser.add_option("-a", "--align-shape", dest="alignshape",
		help="Algined particles shape", metavar="SHAPE",
		type="choice", choices=shapes, default="circle" )
	parser.add_option("-A", "--align-shape-size", dest="ashapesize",
		help="Algined particles shape size", metavar="INT",
		type="int", default=12 )
	parser.add_option("-w", "--worst-shape", dest="worstshape",
		help="Worst particles shape", metavar="SHAPE",
		type="choice", choices=shapes, default="plus" )
	parser.add_option("-W", "--worst-shape-size", dest="wshapesize",
		help="Worst particles shape size", metavar="INT",
		type="int", default=24 )

	params = apParam.convertParserToParams(parser)

	print "=================================="
	print "If you find this program useful please cite: "+tiltDialog.citationlogo
	print "ApTiltPicker, version "+tiltDialog.version
	print "Released on "+tiltDialog.releasedate
	print "=================================="

	app = PickerApp(
		pickshape=params['pickshape'],   pshapesize=params['pshapesize'],
		alignshape=params['alignshape'], ashapesize=params['ashapesize'],
		worstshape=params['worstshape'], wshapesize=params['wshapesize'],
		tiltangle=params['tiltangle'], tiltaxis=params['tiltaxis'],
	)
	app.openLeftImage(params['img1file'])
	app.openRightImage(params['img2file'])
	if params['pickfile'] is not None:
		app.readData(params['pickfile'])
	app.MainLoop()



