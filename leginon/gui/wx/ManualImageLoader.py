# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ManualAcquisition.py,v $
# $Revision: 1.38 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-22 22:49:45 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
from gui.wx.Entry import Entry, FloatEntry, IntEntry
import gui.wx.Events
import gui.wx.ImagePanel
import gui.wx.Instrument
import gui.wx.Node
import gui.wx.Settings
import gui.wx.Stats
import gui.wx.ToolBar
import gui.wx.Dialog
import wx
import wx.lib.filebrowsebutton as filebrowse

LoopStartedEventType = wx.NewEventType()
EVT_LOOP_STARTED = wx.PyEventBinder(LoopStartedEventType)
class LoopStartedEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, LoopStartedEventType, source.GetId())
		self.SetEventObject(source)

LoopStoppedEventType = wx.NewEventType()
EVT_LOOP_STOPPED = wx.PyEventBinder(LoopStoppedEventType)
class LoopStoppedEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, LoopStoppedEventType, source.GetId())
		self.SetEventObject(source)

class Panel(gui.wx.Node.Panel, gui.wx.Instrument.SelectionMixin):
	icon = 'manualacquisition'
	imageclass = gui.wx.ImagePanel.ImagePanel
	def __init__(self, *args, **kwargs):
		gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		#self.toolbar.AddTool(gui.wx.ToolBar.ID_ACQUIRE,
		#											'acquire',
		#											shortHelpString='Acquire')
		#self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'loop_play',
													shortHelpString='Continuous Acquire')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Stop')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)

		self.initialize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def initialize(self):
		# image
		self.imagepanel = self.imageclass(self, -1)
		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

		self.Bind(EVT_LOOP_STARTED, self.onLoopStarted)
		self.Bind(EVT_LOOP_STOPPED, self.onLoopStopped)

	def onNodeInitialized(self):
		gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.settingsdialog = SettingsDialog(self)
		
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=gui.wx.ToolBar.ID_STOP)

	def _acquisitionEnable(self, enable):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, enable)
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_ACQUIRE, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def onSettingsTool(self, evt):
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.initSameCorrection()

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.acquireImage).start()

	def onLoopStopped(self, evt):
		self._acquisitionEnable(True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)

	def loopStopped(self):
		evt = LoopStoppedEvent(self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onLoopStarted(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, True)

	def loopStarted(self):
		evt = LoopStartedEvent(self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPlayTool(self, evt):
		self._acquisitionEnable(False)
		self.node.acquisitionLoopStart()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self._acquisitionEnable(False)
		self.node.acquisitionLoopStop()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Image Loading')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['instruments'] = gui.wx.Instrument.SelectionPanel(self)
		self.panel.setInstrumentSelection(self.widgets['instruments'])

		self.widgets['save image'] = wx.CheckBox(self, -1,
																							'Save image to the database')

		self.widgets['batch script'] = filebrowse.FileBrowseButton(self, -1)
		self.widgets['batch script'].SetMinSize((500,50))
		self.widgets['tilt group'] = IntEntry(self, -1, min=1, chars=6)

		sz = wx.GridBagSizer(5, 5)

		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].Show(False)
		#self.widgets['camera settings'].setSize(self.node.instrument.camerasize)
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['instruments'], (0, 0), (1, 3), wx.EXPAND)
		sz.Add(self.widgets['batch script'], (1, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
		sz.Add(self.widgets['save image'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['tilt group'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(1)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		
		return [sbsz, ]

