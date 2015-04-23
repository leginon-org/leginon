
#!/usr/bin/env python

# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/ManualFocus.py,v $
# $Revision: 1.60 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-31 02:37:06 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import threading
import sys
import math
import wx

from pyami import fftfun

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar

UpdateImagesEventType = wx.NewEventType()
ManualCheckEventType = wx.NewEventType()
ManualCheckDoneEventType = wx.NewEventType()

class ManualFocusSettingsDialog(leginon.gui.wx.Dialog.Dialog):
	def onInitialize(self):
		self.maskradius = FloatEntry(self, -1, allownone=False,
			chars=6,value='0.01')

		self.increment = FloatEntry(self, -1, min=0.0,
			allownone=False,chars=6,value='5e-7')

		label = wx.StaticText(self, -1, 'Mask radius:')
		self.sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.maskradius, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of image')
		self.sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Increment:')
		self.sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.increment, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		self.moreOnInitialize()

		self.addButton('OK', wx.ID_OK)
		self.addButton('Cancel', wx.ID_CANCEL)

	def moreOnInitialize(self):
		'''set increment unit here so that it can be change in the subclass'''
		label = wx.StaticText(self, -1, 'm')
		self.sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

class ManualFocusDialog(wx.Frame):
	def __init__(self, parent, node, title='Manual Focus'):
		wx.Frame.__init__(self, parent, -1, title, size=(650,600),
			style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)
		self.node = node
		self.center = (256,256)
		self.toolbar = wx.ToolBar(self, -1)

		bitmap = leginon.gui.wx.Icons.icon('settings')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, bitmap, shortHelpString='Settings')

		self.toolbar.AddSeparator()

		bitmap = leginon.gui.wx.Icons.icon('play')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, bitmap, shortHelpString='Play')
		bitmap = leginon.gui.wx.Icons.icon('pause')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PAUSE, bitmap, shortHelpString='Pause')
		bitmap = leginon.gui.wx.Icons.icon('stop')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STOP, bitmap, shortHelpString='Stop')

		self.toolbar.AddSeparator()

		self.initParameterChoice()
		self.toolbar.AddControl(self.parameter_choice)
		bitmap = leginon.gui.wx.Icons.icon('plus')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLUS, bitmap,
			shortHelpString='Increment up')
		bitmap = leginon.gui.wx.Icons.icon('minus')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MINUS, bitmap,
			shortHelpString='Increment down')

		self.toolbar.AddSeparator()

		self.value = FloatEntry(self.toolbar, -1, allownone=False, chars=6, value='0.0')
		self.toolbar.AddControl(self.value)
		# size is defined because some wxPython installation lack good wxDefaultSize
		self.toolbar.AddControl(wx.StaticText(self.toolbar, -1, ' m',size=(20,20)))
		bitmap = leginon.gui.wx.Icons.icon('instrumentset')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_VALUE, bitmap,
			shortHelpString='Set instrument')

		self.toolbar.AddSeparator()

		bitmap = leginon.gui.wx.Icons.icon('instrumentsetnew')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET, bitmap,
			shortHelpString='Reset Defocus')

		self.toolbar.AddSeparator()

		bitmap = leginon.gui.wx.Icons.icon('instrumentget')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT, bitmap,
			shortHelpString='Eucentric from instrument')

		bitmap = leginon.gui.wx.Icons.icon('instrumentset')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT, bitmap,
			shortHelpString='Eucentric to instrument')

		self.moreToolbar()

		self.SetToolBar(self.toolbar)
		self.toolbar.Realize()

		self.imagepanel = leginon.gui.wx.TargetPanel.FFTTargetImagePanel(self, -1,imagesize=(512,512))

		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.addTypeTool('Power', display=True)
		self.imagepanel.selectiontool.setDisplayed('Power', True)

		self.statusbar = wx.StatusBar(self, -1)
		self.SetStatusBar(self.statusbar)

		self.Fit()
		#self.SetAutoLayout(True)

		self.settingsdialog = ManualFocusSettingsDialog(self, 'Manual Focus Settings', 'Settings')

		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.Bind(wx.EVT_TOOL, self.onSettingsTool, id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.Bind(wx.EVT_TOOL, self.onPlayTool, id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.Bind(wx.EVT_TOOL, self.onPauseTool, id=leginon.gui.wx.ToolBar.ID_PAUSE)
		self.Bind(wx.EVT_TOOL, self.onStopTool, id=leginon.gui.wx.ToolBar.ID_STOP)
		self.Bind(wx.EVT_TOOL, self.onPlusTool, id=leginon.gui.wx.ToolBar.ID_PLUS)
		self.Bind(wx.EVT_TOOL, self.onMinusTool, id=leginon.gui.wx.ToolBar.ID_MINUS)
		self.Bind(wx.EVT_TOOL, self.onValueTool, id=leginon.gui.wx.ToolBar.ID_VALUE)
		self.Bind(wx.EVT_TOOL, self.onResetTool, id=leginon.gui.wx.ToolBar.ID_RESET)
		self.Bind(wx.EVT_TOOL, self.onGetInstrumentTool, id=leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT)
		self.Bind(wx.EVT_TOOL, self.onSetInstrumentTool, id=leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(leginon.gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(leginon.gui.wx.Events.EVT_MANUAL_UPDATED, self.onManualUpdated)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SHAPE_FOUND, self.onShapeFound, self.imagepanel)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)
		self.parameter_choice.Bind(wx.EVT_CHOICE, self.onParameterChoice)
		self.moreOnInit()

	def moreToolbar(self):
		pass

	def moreOnInit(self):
		self.beamtilt = False
		pass

	def initParameterChoice(self):
		self.parameter_choice = Choice(self.toolbar, -1, choices=['Defocus', 'Stage Z'])
		par = 'Defocus'
		self.parameter_choice.SetStringSelection(par)
		threading.Thread(target=self.node.setParameterChoice, args=(par,)).start()

	def onParameterChoice(self,evt):
		par = self.parameter_choice.GetStringSelection()
		threading.Thread(target=self.node.setParameterChoice, args=(par,)).start()

	def onSettingsTool(self, evt):
		self.settingsdialog.maskradius.SetValue(self.node.maskradius)
		self.settingsdialog.increment.SetValue(self.node.increment)
		print 'set increment to ',self.node.increment
		#self.MakeModal(False)
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.maskradius = self.settingsdialog.maskradius.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
		#self.MakeModal(True)

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.node.manualplayer.play()

	def onPauseTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.node.manualplayer.pause()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.node.manualplayer.stop()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)

	def _manualEnable(self, enable):
		self.toolbar.Enable(enable)

	def onManualUpdated(self, evt):
		self._manualEnable(True)

	def manualUpdated(self):
		evt = leginon.gui.wx.Events.ManualUpdatedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onPlusTool(self, evt):
		self._manualEnable(False)
		par = self.parameter_choice.GetStringSelection()
		threading.Thread(target=self.node.onFocusUp, args=(par,)).start()

	def onMinusTool(self, evt):
		self._manualEnable(False)
		par = self.parameter_choice.GetStringSelection()
		threading.Thread(target=self.node.onFocusDown, args=(par,)).start()

	def onValueTool(self, evt):
		self._manualEnable(False)
		value = self.value.GetValue()
		threading.Thread(target=self.node.setFocus, args=(value,)).start()

	def onResetTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.onResetDefocus).start()

	def onGetInstrumentTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.onEucentricFromScope).start()

	def onSetInstrumentTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.onChangeToEucentric).start()

	def onClose(self, evt):
		self.node.manualplayer.stop()

	def onSetImage(self, evt):
		self.imagepanel.setImageType(evt.typename, evt.image)

	def onNewPixelSize(self, pixelsize,center,hightension, cs):
		idcevt = leginon.gui.wx.ImagePanelTools.ImageNewPixelSizeEvent(self.imagepanel, pixelsize,center,hightension,cs)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
		self.center = center
		self.pixelsize = pixelsize
		self.hightension = hightension
		self.cs = cs

	def onShapeFound(self, evt):
		centers = [(self.center['y'],self.center['x']),]
		idcevt = leginon.gui.wx.ImagePanelTools.ShapeNewCenterEvent(self.imagepanel, centers)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
		threading.Thread(target=self.node.estimateAstigmation, args=(evt.params,)).start()

	def onImageClicked(self, evt):
		if not self.imagepanel.selectiontool.isDisplayed('Power'):
			return
		resolution = 1/math.sqrt(((evt.xy[0]-self.center['x'])*self.pixelsize['x'])**2+((evt.xy[1]-self.center['y'])*self.pixelsize['y'])**2)
		defocus = fftfun.calculateDefocus(self.hightension,1/resolution,self.cs)
		self.node.increment = defocus
		self.settingsdialog.increment.SetValue(self.node.increment)

class ManualBeamTiltWobbleDialog(ManualFocusDialog):
	def moreOnInit(self):
		self.beamtilt = True
		self.settingsdialog = ManualBeamTiltWobbleSettingsDialog(self, 'Manual Beam Tilt Wobble Settings', 'Settings')

	def moreToolbar(self):
		bitmap = leginon.gui.wx.Icons.icon('beamtiltget')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_BEAMTILT, bitmap, shortHelpString='Rotation Center From Scope')
		bitmap = leginon.gui.wx.Icons.icon('beamtiltset')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_BEAMTILT, bitmap, shortHelpString='Rotation Center To Scope')

		self.toolbar.Bind(wx.EVT_TOOL, self.onRotationCenterFromScope, id=leginon.gui.wx.ToolBar.ID_GET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRotationCenterToScope, id=leginon.gui.wx.ToolBar.ID_SET_BEAMTILT)

	def initParameterChoice(self):
		self.parameter_choice = Choice(self.toolbar, -1, choices=['Beam Tilt X','Beam Tilt Y','Defocus', 'Stage Z'])
		par = 'Beam Tilt X'
		self.parameter_choice.SetStringSelection(par)
		threading.Thread(target=self.node.setParameterChoice, args=(par,)).start()

	def onSettingsTool(self, evt):
		self.settingsdialog.maskradius.SetValue(self.node.maskradius)
		self.settingsdialog.increment.SetValue(self.node.increment)
		self.settingsdialog.tiltdelta.SetValue(self.node.tiltdelta)
		#self.MakeModal(False)
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.maskradius = self.settingsdialog.maskradius.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
			self.node.tiltdelta = self.settingsdialog.tiltdelta.GetValue()
		#self.MakeModal(True)

	def onRotationCenterToScope(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.rotationCenterToScope).start()

	def onRotationCenterFromScope(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.rotationCenterFromScope).start()

class ManualBeamTiltWobbleSettingsDialog(ManualFocusSettingsDialog):
	def moreOnInitialize(self):
		label = wx.StaticText(self, -1, 'm or radian')
		self.sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.tiltdelta = FloatEntry(self, -1, min=0.0,
			allownone=False,chars=6,value='5e-3')

		label = wx.StaticText(self, -1, 'Beam Tilt Wobble Size:')
		self.sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.tiltdelta, (2, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'radian')
		self.sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

	

if __name__ == '__main__':
	class Node(object):
		def __init__(self):
			self.maskradius = 1.0
			self.increment = 5e-7
			self.man_power = None
			self.man_image = None

		def setParameterChoice(self,parameter):
			self.parameter_choice = parameter

	class App(wx.App):
		def OnInit(self):
			node = Node()
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = ManualFocusDialog(frame, node)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

