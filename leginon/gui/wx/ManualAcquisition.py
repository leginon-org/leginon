# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ManualAcquisition.py,v $
# $Revision: 1.28 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-03 23:17:13 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import gui.wx.Camera
from gui.wx.Entry import Entry, FloatEntry
import gui.wx.Events
import gui.wx.ImagePanel
import gui.wx.Instrument
import gui.wx.Node
import gui.wx.Settings
import gui.wx.Stats
import gui.wx.ToolBar
import gui.wx.Dialog
import wx

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

ManualCheckEventType = wx.NewEventType()
EVT_MANUAL_CHECK = wx.PyEventBinder(ManualCheckEventType)
class ManualCheckEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckEventType, source.GetId())
		self.SetEventObject(source)

ManualCheckDoneEventType = wx.NewEventType()
EVT_MANUAL_CHECK_DONE = wx.PyEventBinder(ManualCheckDoneEventType)
class ManualCheckDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckDoneEventType, source.GetId())
		self.SetEventObject(source)

class Panel(gui.wx.Node.Panel, gui.wx.Instrument.SelectionMixin):
	icon = 'manualacquisition'
	imageclass = gui.wx.ImagePanel.ImagePanel
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)
		gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GRID,
													'grid',
													shortHelpString='Grid')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, False)
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MANUAL_DOSE,
													'dose',
													shortHelpString='Measure Dose')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'loop_play',
													shortHelpString='Continuous Acquire')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Stop')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_MANUAL_FOCUS, 'manualfocus',
							 shortHelpString='Manual Focus')
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
		self.manualdialog = ManualFocusDialog(self, self.node)
		self.Bind(EVT_MANUAL_CHECK, self.onManualCheck, self)
		self.Bind(EVT_MANUAL_CHECK_DONE, self.onManualCheckDone, self)
		
		
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureDoseTool,
											id=gui.wx.ToolBar.ID_MANUAL_DOSE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=gui.wx.ToolBar.ID_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onManualFocusTool,
						  id=gui.wx.ToolBar.ID_MANUAL_FOCUS)
		if self.node.projectdata is not None:
			self.toolbar.Bind(wx.EVT_TOOL, self.onGridTool,
												id=gui.wx.ToolBar.ID_GRID)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, True)

	def _acquisitionEnable(self, enable):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, enable)
		if self.node.projectdata is not None:
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_GRID, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ACQUIRE, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_MANUAL_DOSE, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def onSettingsTool(self, evt):
		self.settingsdialog.ShowModal()

	def onGridTool(self, evt):
		dialog = GridDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.gridbox = dialog.gridbox
			self.node.grid = dialog.grid
		dialog.Destroy()

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.acquireImage).start()

	def onMeasureDoseTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.acquireImage, kwargs={'dose':True}).start()

	def onManualFocusTool(self, evt):
		self.node.manualNow()

	def onManualCheck(self, evt):
		#self.manualdialog.MakeModal(True)
		self.manualdialog.Raise()
		self.manualdialog.Show()

	def onManualCheckDone(self, evt):
		self.manualdialog.Show(False)
		#self.manualdialog.MakeModal(False)

	def setManualImage(self, image, typename, stats={}):
		evt = gui.wx.Events.SetImageEvent(image, typename, stats)
		self.manualdialog.GetEventHandler().AddPendingEvent(evt)

	def manualUpdated(self):
		self.manualdialog.manualUpdated()

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

class GridDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node
		wx.Dialog.__init__(self, parent, -1, 'Grid Selection')

		choices = ['None'] + self.node.getGridBoxes()
		self.cgridbox = wx.Choice(self, -1, choices=choices)
		self.cgrid = wx.Choice(self, -1)

		if self.node.gridbox is None:
			self.cgridbox.SetStringSelection('None')
		else:
			self.cgridbox.SetStringSelection(self.node.gridbox)
		self.onGridBoxChoice()
		if self.node.grid is None:
			self.cgrid.SetStringSelection('None')
		else:
			self.cgrid.SetStringSelection(self.node.grid)
		self.onGridChoice()

		szgrid = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Grid box:')
		szgrid.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.Add(self.cgridbox, (0, 1), (1, 1), wx.EXPAND)
		label = wx.StaticText(self, -1, 'Grid:')
		szgrid.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.Add(self.cgrid, (1, 1), (1, 1), wx.EXPAND)
		szgrid.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Grid')
		sbszgrid = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszgrid.Add(szgrid, 1, wx.EXPAND|wx.ALL, 5)

		self.bselect = wx.Button(self, wx.ID_OK, 'Select')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bselect, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbszgrid, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_CHOICE, self.onGridBoxChoice, self.cgridbox)
		self.Bind(wx.EVT_CHOICE, self.onGridChoice, self.cgrid)

	def onGridBoxChoice(self, evt=None):
		if evt is None:
			gridbox = self.cgridbox.GetStringSelection()
		else:
			gridbox = evt.GetString()
		choices = ['None']
		if gridbox == 'None':
			self.gridbox = None
		else:
			choices += self.node.getGrids(gridbox)
			self.gridbox = gridbox

		self.cgrid.Clear()
		self.cgrid.AppendItems(choices)
		self.cgrid.SetSelection(0)
		self.onGridChoice()

	def onGridChoice(self, evt=None):
		if evt is None:
			grid = self.cgrid.GetStringSelection()
		else:
			grid = evt.GetString()
		if grid == 'None':
			self.grid = None
		else:
			self.grid = grid

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.instrumentselection = gui.wx.Instrument.SelectionPanel(self)
		self.GetParent().setInstrumentSelection(self.instrumentselection)

		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)
		self.widgets['screen up'] = wx.CheckBox(self, -1, 'Up before acquire')
		self.widgets['screen down'] = wx.CheckBox(self, -1, 'Down after acquired')
		self.widgets['correct image'] = wx.CheckBox(self, -1, 'Correct image')
		self.widgets['save image'] = wx.CheckBox(self, -1,
																							'Save image to the database')
		self.widgets['image label'] = Entry(self, -1, chars=12)
		self.widgets['loop pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
		self.widgets['low dose'] = wx.CheckBox(self, -1, 'Use low dose')
		self.widgets['low dose pause time'] = FloatEntry(self, -1, min=0.0, chars=4)

		szscreen = wx.GridBagSizer(5, 5)
		szscreen.Add(self.widgets['screen up'], (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		szscreen.Add(self.widgets['screen down'], (1, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Main Screen')
		sbszscreen = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszscreen.Add(szscreen, 1, wx.EXPAND|wx.ALL, 5)

		szlowdose = wx.GridBagSizer(5, 5)
		szlowdose.Add(self.widgets['low dose'], (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Low dose pause')
		szlowdose.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlowdose.Add(self.widgets['low dose pause time'], (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		szlowdose.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlowdose.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Dose')
		sbszlowdose = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlowdose.Add(szlowdose, 1, wx.EXPAND|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.instrumentselection, (0, 0), (1, 3), wx.EXPAND)
		sz.Add(self.widgets['camera settings'], (1, 0), (1, 3), wx.EXPAND)
		sz.Add(self.widgets['correct image'], (2, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['save image'], (3, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Loop pause')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['loop pause time'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		sz.Add(label, (4, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Label')
		sz.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['image label'], (5, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		sz.AddGrowableCol(1)
		self.widgets['dark'] = wx.CheckBox(self, -1, 'Dark Exposure')
		sz.Add(self.widgets['dark'], (6,0), (1,1))

		szdefocus= wx.GridBagSizer(5, 5)
		self.widgets['defocus1switch'] = wx.CheckBox(self, -1, 'Defocus 1')
		szdefocus.Add(self.widgets['defocus1switch'], (0,0), (1,1))
		self.widgets['defocus1'] = FloatEntry(self, -1, chars=6)
		szdefocus.Add(self.widgets['defocus1'], (0,1), (1,1))
		self.widgets['defocus2switch'] = wx.CheckBox(self, -1, 'Defocus 2')
		szdefocus.Add(self.widgets['defocus2switch'], (1,0), (1,1))
		self.widgets['defocus2'] = FloatEntry(self, -1, chars=6)
		szdefocus.Add(self.widgets['defocus2'], (1,1), (1,1))
		sb = wx.StaticBox(self, -1, 'Defocus Pair (leave both unchecked to use current defocus)')
		sbszdefocus = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszdefocus.Add(szdefocus, 1, wx.EXPAND|wx.ALL, 5)


		sb = wx.StaticBox(self, -1, 'Acquisition')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz, sbszscreen, sbszlowdose, sbszdefocus, ]

class ManualFocusSettingsDialog(gui.wx.Dialog.Dialog):
	def onInitialize(self):
		self.maskradius = FloatEntry(self, -1, allownone=False,
			chars=6,value='0.01')

		label = wx.StaticText(self, -1, 'Mask radius:')
		self.sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.maskradius, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of image')
		self.sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)


		label = wx.StaticText(self, -1, 'Exposure Time:')
		self.sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.focexptime = FloatEntry(self, -1, min=0,value='100', chars=7)
		self.sz.Add(self.focexptime, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'ms')
		self.sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)


		self.addButton('OK', wx.ID_OK)
		self.addButton('Cancel', wx.ID_CANCEL)


class ManualFocusDialog(wx.MiniFrame):
	def __init__(self, parent, node, title='Manual Focus'):
		wx.MiniFrame.__init__(self, parent, -1, title, size=(620,600),
			style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)
		self.node = node

		self.toolbar = wx.ToolBar(self, -1)

		bitmap = gui.wx.Icons.icon('settings')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS, bitmap,
													shortHelpString='Settings')

		self.toolbar.AddSeparator()

		bitmap = gui.wx.Icons.icon('play')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY, bitmap,
													shortHelpString='Play')
		bitmap = gui.wx.Icons.icon('pause')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PAUSE, bitmap,
													shortHelpString='Pause')
		bitmap = gui.wx.Icons.icon('stop')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP, bitmap,
													shortHelpString='Stop')

		self.toolbar.Realize()
		self.SetToolBar(self.toolbar)

		self.imagepanel = gui.wx.ImagePanel.ImagePanel(self, -1,imagesize=(512, 512))

		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.addTypeTool('Power', display=True)
		self.imagepanel.selectiontool.setDisplayed('Power', True)

		self.statusbar = wx.StatusBar(self, -1)
		self.SetStatusBar(self.statusbar)

		self.Fit()
	
		self.SetAutoLayout(True)

		self.settingsdialog = ManualFocusSettingsDialog(self,'Manual Focus Settings','Settings')

		self.Bind(gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.Bind(wx.EVT_TOOL, self.onSettingsTool, id=gui.wx.ToolBar.ID_SETTINGS)
		self.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
		self.Bind(wx.EVT_TOOL, self.onPauseTool, id=gui.wx.ToolBar.ID_PAUSE)
		self.Bind(wx.EVT_TOOL, self.onStopTool, id=gui.wx.ToolBar.ID_STOP)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(gui.wx.Events.EVT_MANUAL_UPDATED, self.onManualUpdated)

	def onSettingsTool(self, evt):
		self.settingsdialog.maskradius.SetValue(self.node.maskradius)
		#self.MakeModal(False)
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.maskradius = self.settingsdialog.maskradius.GetValue()
			self.node.focexptime = self.settingsdialog.focexptime.GetValue()

		#self.MakeModal(True)

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self.node.manualplayer.play()

	def onPauseTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self.node.manualplayer.pause()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self.node.manualplayer.stop()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False) 
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, True)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, True) 
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)

	def _manualEnable(self, enable):
		self.toolbar.Enable(enable)

	def onManualUpdated(self, evt):
		self._manualEnable(True)

	def manualUpdated(self):
		evt = gui.wx.Events.ManualUpdatedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onClose(self, evt):
		self.node.manualplayer.stop()

	def onSetImage(self, evt):
		self.imagepanel.setImageType(evt.typename, evt.image)


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Manual Acquisition Test')
			dialog = ManualFocusDialog(frame,None)
			dialog.Show()
#			panel = Panel(frame, 'Test')
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

