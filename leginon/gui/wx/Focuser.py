# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Focuser.py,v $
# $Revision: 1.27 $
# $Name: not supported by cvs2svn $
# $Date: 2005-04-07 17:46:51 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Acquisition
import gui.wx.Dialog
import gui.wx.Events
import gui.wx.Icons
import gui.wx.ImageViewer
import gui.wx.ToolBar

UpdateImagesEventType = wx.NewEventType()
ManualCheckEventType = wx.NewEventType()
ManualCheckDoneEventType = wx.NewEventType()

EVT_UPDATE_IMAGES = wx.PyEventBinder(UpdateImagesEventType)
EVT_MANUAL_CHECK = wx.PyEventBinder(ManualCheckEventType)
EVT_MANUAL_CHECK_DONE = wx.PyEventBinder(ManualCheckDoneEventType)

class UpdateImagesEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, UpdateImagesEventType, source.GetId())
		self.SetEventObject(source)

class ManualCheckEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckEventType, source.GetId())
		self.SetEventObject(source)

class ManualCheckDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckDoneEventType, source.GetId())
		self.SetEventObject(source)

class Panel(gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = gui.wx.ImageViewer.TargetImagePanel
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MANUAL_FOCUS,
													'manualfocus',
													shortHelpString='Manual Focus')
		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255, 128, 0))

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.manualdialog = ManualFocusDialog(self, self.node)
		self.Bind(EVT_MANUAL_CHECK, self.onManualCheck, self)
		self.Bind(EVT_MANUAL_CHECK_DONE, self.onManualCheckDone, self)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.toolbar.Bind(wx.EVT_TOOL, self.onManualFocusTool,
											id=gui.wx.ToolBar.ID_MANUAL_FOCUS)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

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

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		asz = gui.wx.Acquisition.SettingsDialog.initialize(self)

		self.widgets['autofocus'] = wx.CheckBox(self, -1, 'Autofocus')

		focustypes = self.node.focus_methods.keys()
		self.widgets['correction type'] = Choice(self, -1, choices=focustypes)

		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = Choice(self, -1, choices=presets)

		self.widgets['melt time'] = FloatEntry(self, -1,
																						min=0.0,
																						allownone=False,
																						chars=4,
																						value='0.0')
		szmelt = wx.GridBagSizer(5, 5)
		szmelt.Add(self.widgets['melt time'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szmelt.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		self.widgets['beam tilt'] = FloatEntry(self, -1,
																						allownone=False,
																						chars=9,
																						value='0.0')

		self.widgets['fit limit'] = FloatEntry(self, -1,
																						allownone=False,
																						chars=9,
																						value='0.0')

		self.widgets['check drift'] = wx.CheckBox(self, -1,
																								'Check for drift greater than')
		self.widgets['drift threshold'] = FloatEntry(self, -1,
																									min=0.0,
																									allownone=False,
																									chars=4,
																									value='0.0')
		szdrift = wx.GridBagSizer(5, 5)
		szdrift.Add(self.widgets['check drift'], (0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szdrift.Add(self.widgets['drift threshold'], (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szdrift.Add(wx.StaticText(self, -1, 'm/s'), (0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		self.widgets['correlation type'] = Choice(self, -1,
																							choices=self.node.cortypes)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['correlation type'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.widgets['check before'] = wx.CheckBox(self, -1,
																			'Manual focus check before autofocus')
		self.widgets['check after'] = wx.CheckBox(self, -1,
																			'Manual focus check after autofocus')

		self.widgets['stig correction'] = wx.CheckBox(self, -1, 'Correct')
		self.widgets['stig defocus min'] = FloatEntry(self, -1,
																									allownone=False,
																									chars=9,
																									value='0.0')
		self.widgets['stig defocus max'] = FloatEntry(self, -1,
																									allownone=False,
																									chars=9,
																									value='0.0')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['stig correction'], (0, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Min.'), (1, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Max.'), (1, 2), (1, 1), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Defocus:'), (2, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig defocus min'], (2, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(self.widgets['stig defocus max'], (2, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szstig = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Stigmator'), wx.VERTICAL)
		szstig.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.widgets['acquire final'] = wx.CheckBox(self, -1, 'Acquire final image')
		self.widgets['drift on z'] = wx.CheckBox(self, -1,
																						'Declare drift after Z corrected')

		# settings sizer
		sz = wx.GridBagSizer(10, 5)
		sz.Add(self.widgets['autofocus'], (0, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Correction type'), (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['correction type'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Preset'), (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Melt time:'), (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szmelt, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Beam tilt:'), (4, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['beam tilt'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'Fit limit:'), (5, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['fit limit'], (5, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(szdrift, (6, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szcor, (7, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sz.Add(self.widgets['check before'], (1, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['check after'], (2, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['acquire final'], (3, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['drift on z'], (4, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szstig, (5, 2), (3, 1), wx.ALIGN_CENTER)
		#sz.AddGrowableRow(6)

		sb = wx.StaticBox(self, -1, 'Autofocus')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return asz + [sbsz]

class ManualFocusSettingsDialog(gui.wx.Dialog.Dialog):
	def onInitialize(self):
		self.maskradius = FloatEntry(self, -1, allownone=False,
																						chars=6,
																						value='0.01')

		self.increment = FloatEntry(self, -1, min=0.0,
																					allownone=False,
																					chars=6,
																					value='5e-7')

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
		label = wx.StaticText(self, -1, 'm')
		self.sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.addButton('OK', wx.ID_OK)
		self.addButton('Cancel', wx.ID_CANCEL)

class ManualFocusDialog(wx.MiniFrame):
	def __init__(self, parent, node, title='Manual Focus'):
		wx.MiniFrame.__init__(self, parent, -1, title,
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

		self.toolbar.AddSeparator()

		self.parameter = wx.Choice(self.toolbar, -1, choices=['Defocus', 'Stage Z'])
		self.toolbar.AddControl(self.parameter)
		bitmap = gui.wx.Icons.icon('plus')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLUS, bitmap,
													shortHelpString='Increment up')
		bitmap = gui.wx.Icons.icon('minus')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MINUS, bitmap,
													shortHelpString='Increment down')

		self.toolbar.AddSeparator()

		self.value = FloatEntry(self.toolbar, -1, allownone=False, chars=6,
														value='0.0')
		self.toolbar.AddControl(self.value)
		self.toolbar.AddControl(wx.StaticText(self.toolbar, -1, ' m'))
		bitmap = gui.wx.Icons.icon('instrumentset')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_VALUE, bitmap,
													shortHelpString='Set instrument')

		self.toolbar.AddSeparator()

		bitmap = gui.wx.Icons.icon('instrumentsetnew')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_RESET, bitmap,
													shortHelpString='Reset Defocus')

		self.toolbar.AddSeparator()

		bitmap = gui.wx.Icons.icon('instrumentget')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GET_INSTRUMENT, bitmap,
													shortHelpString='Eucentric from instrument')

		bitmap = gui.wx.Icons.icon('instrumentset')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SET_INSTRUMENT, bitmap,
													shortHelpString='Eucentric to instrument')

		self.toolbar.Realize()

		self.SetToolBar(self.toolbar)

		self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.addTypeTool('Power', display=True)
		self.imagepanel.selectiontool.setDisplayed('Power', True)

		self.statusbar = wx.StatusBar(self, -1)
		self.SetStatusBar(self.statusbar)

		self.Fit()

		self.settingsdialog = ManualFocusSettingsDialog(self,
																										'Manual Focus Settings',
																										'Settings')

		n = self.parameter.FindString(self.node.parameter)
		if n == wx.NOT_FOUND:
			raise RuntimeError
		self.parameter.SetSelection(n)

		self.Bind(gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.Bind(wx.EVT_TOOL, self.onSettingsTool, id=gui.wx.ToolBar.ID_SETTINGS)
		self.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
		self.Bind(wx.EVT_TOOL, self.onPauseTool, id=gui.wx.ToolBar.ID_PAUSE)
		self.Bind(wx.EVT_TOOL, self.onStopTool, id=gui.wx.ToolBar.ID_STOP)
		self.Bind(wx.EVT_TOOL, self.onPlusTool, id=gui.wx.ToolBar.ID_PLUS)
		self.Bind(wx.EVT_TOOL, self.onMinusTool, id=gui.wx.ToolBar.ID_MINUS)
		self.Bind(wx.EVT_TOOL, self.onValueTool, id=gui.wx.ToolBar.ID_VALUE)
		self.Bind(wx.EVT_TOOL, self.onResetTool, id=gui.wx.ToolBar.ID_RESET)
		self.Bind(wx.EVT_TOOL, self.onGetInstrumentTool,
							id=gui.wx.ToolBar.ID_GET_INSTRUMENT)
		self.Bind(wx.EVT_TOOL, self.onSetInstrumentTool,
							id=gui.wx.ToolBar.ID_SET_INSTRUMENT)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(gui.wx.Events.EVT_MANUAL_UPDATED, self.onManualUpdated)

	def onSettingsTool(self, evt):
		self.settingsdialog.maskradius.SetValue(self.node.maskradius)
		self.settingsdialog.increment.SetValue(self.node.increment)
		#self.MakeModal(False)
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.maskradius = self.settingsdialog.maskradius.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
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

	def onPlusTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.uiFocusUp).start()

	def onMinusTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.uiFocusDown).start()

	def onValueTool(self, evt):
		self._manualEnable(False)
		value = self.value.GetValue()
		threading.Thread(target=self.node.setFocus, args=(value,)).start()

	def onResetTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.uiResetDefocus).start()

	def onGetInstrumentTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.uiEucentricFromScope).start()

	def onSetInstrumentTool(self, evt):
		self._manualEnable(False)
		threading.Thread(target=self.node.uiChangeToEucentric).start()

	def onClose(self, evt):
		self.node.manualplayer.stop()

	def onSetImage(self, evt):
		self.imagepanel.setImageType(evt.typename, evt.image)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = ManualFocusDialog(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

