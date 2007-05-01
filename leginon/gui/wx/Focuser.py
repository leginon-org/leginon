# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Focuser.py,v $
# $Revision: 1.47 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-01 22:33:30 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import threading
import sys
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
from gui.wx.Presets import EditPresetOrder
import gui.wx.Acquisition
import gui.wx.Dialog
import gui.wx.Events
import gui.wx.Icons
import gui.wx.ImageViewer
import gui.wx.ToolBar
import gui.wx.FocusSequence

UpdateImagesEventType = wx.NewEventType()
ManualCheckEventType = wx.NewEventType()
ManualCheckDoneEventType = wx.NewEventType()
MeasureTiltAxisEventType = wx.NewEventType()
AlignRotationCenterEventType = wx.NewEventType()

EVT_UPDATE_IMAGES = wx.PyEventBinder(UpdateImagesEventType)
EVT_MANUAL_CHECK = wx.PyEventBinder(ManualCheckEventType)
EVT_MANUAL_CHECK_DONE = wx.PyEventBinder(ManualCheckDoneEventType)
EVT_MEASURE_TILT_AXIS= wx.PyEventBinder(MeasureTiltAxisEventType)
EVT_ALIGN = wx.PyEventBinder(AlignRotationCenterEventType)

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

		self.toolbar.InsertTool(2, gui.wx.ToolBar.ID_FOCUS_SEQUENCE, 'focus_sequence',
								shortHelpString='Focus Sequence')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MANUAL_FOCUS, 'manualfocus',
							 shortHelpString='Manual Focus')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ALIGN, 'rotcenter',
							 shortHelpString='Align rotation center')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MEASURE_TILT_AXIS, 'tiltaxis',
							 shortHelpString='Measure stage tilt axis')
		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255, 128, 0))

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.measure_dialog = MeasureTiltAxisDialog(self)
		self.Bind(EVT_MEASURE_TILT_AXIS, self.onMeasureTiltAxis, self)
		self.align_dialog = AlignRotationCenterDialog(self)
		self.Bind(EVT_ALIGN, self.onAlignRotationCenter, self)
		self.manualdialog = ManualFocusDialog(self, self.node)
		self.Bind(EVT_MANUAL_CHECK, self.onManualCheck, self)
		self.Bind(EVT_MANUAL_CHECK_DONE, self.onManualCheckDone, self)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.toolbar.Bind(wx.EVT_TOOL, self.onFocusSequenceTool,
						  id=gui.wx.ToolBar.ID_FOCUS_SEQUENCE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onManualFocusTool,
						  id=gui.wx.ToolBar.ID_MANUAL_FOCUS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTiltAxis,
						  id=gui.wx.ToolBar.ID_MEASURE_TILT_AXIS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAlignRotationCenter,
						  id=gui.wx.ToolBar.ID_ALIGN)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onFocusSequenceTool(self, evt):
		preset_names = self.node.presetsclient.getPresetNames()
		if not preset_names:
			self.node.logger.error('No presets available for focus settings.')
			return
		focus_methods = self.node.focus_methods
		correction_types = self.node.correction_types.keys()
		correction_types.sort()
		correlation_types = self.node.correlation_types
		default_setting = self.node.default_setting
		sequence = self.node.getFocusSequence()
		dialog_settings = gui.wx.FocusSequence.DialogSettings(
			preset_names,
			focus_methods,
			correction_types,
			correlation_types,
			default_setting,
			sequence)
		title = 'Focus Sequence (%s)' % self.node.name
		dialog = gui.wx.FocusSequence.Dialog(self, title, dialog_settings)
		if dialog.ShowModal() == wx.ID_OK:
			dialog.saveCurrent()
			self.node.setFocusSequence(dialog.settings.sequence)
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

	def onMeasureTiltAxis(self, evt):
		self.measure_dialog.Show()

	def onAlignRotationCenter(self, evt):
		self.align_dialog.Show()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		sizers = gui.wx.Acquisition.SettingsDialog.initialize(self)

		sizer = wx.GridBagSizer(5, 5)
		self.widgets['melt time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		melt_sizer = wx.GridBagSizer(5, 5)
		melt_sizer.Add(self.widgets['melt time'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		melt_sizer.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		self.widgets['acquire final'] = \
				wx.CheckBox(self, -1, 'Acquire post-focus image')

		presetnames = self.node.presetsclient.getPresetNames()
		self.widgets['melt preset'] = gui.wx.Presets.PresetChoice(self, -1)
		self.widgets['melt preset'].setChoices(presetnames)
		label = wx.StaticText(self, -1, 'Melt preset:')
		sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['melt preset'], (0, 1), (1, 1), wx.ALIGN_CENTER)

		label = wx.StaticText(self, -1, 'Melt time:')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(melt_sizer, (1, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.widgets['acquire final'], (2, 0), (1, 2),
				  wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Focusing')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return sizers + [sbsz]

class MeasureTiltAxisDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, "Measure Stage Tilt Axis Location")

		sbsz = wx.GridBagSizer(5,5)

		label = wx.StaticText(self, -1, "Tilt angle: ")
		self.tiltvalue = FloatEntry(self, -1, allownone=False, chars=5, value='30.0')
		label2 = wx.StaticText(self, -1, " degrees")
		sbsz.Add(label, (0,0), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(self.tiltvalue, (0,1), (1,1), wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label2, (0,2), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "SNR cutoff: ")
		self.snrvalue = FloatEntry(self, -1, allownone=False, chars=5, value='2.5')
		label2 = wx.StaticText(self, -1, " levels")
		sbsz.Add(label, (1,0), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(self.snrvalue, (1,1), (1,1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label2, (1,2), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "Median filter: ")
		self.medfiltvalue = IntEntry(self, -1, allownone=False, chars=5, value='3')
		label2 = wx.StaticText(self, -1, " pixels")
		sbsz.Add(label, (2,0), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(self.medfiltvalue, (2,1), (1,1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label2, (2,2), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, "Number tilts: ")
		self.onetilt = wx.RadioButton(self, -1, "Once", style=wx.RB_GROUP|wx.ALIGN_CENTER_VERTICAL)
		self.twotilt = wx.RadioButton(self, -1, "Twice", style=wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label, (3,0), (1,1))
		sbsz.Add(self.onetilt, (3,1), (1,1))
		sbsz.Add(self.twotilt, (3,2), (1,1))

		label = wx.StaticText(self, -1, "Correlation: ")
		self.phasecorr = wx.RadioButton(self, -1, "Phase", style=wx.RB_GROUP|wx.ALIGN_CENTER_VERTICAL)
		self.crosscorr = wx.RadioButton(self, -1, "Cross", style=wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label, (4,0), (1,1))
		sbsz.Add(self.phasecorr, (4,1), (1,1))
		sbsz.Add(self.crosscorr, (4,2), (1,1))

		self.measurecancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.measureinit = wx.Button(self,  -1, 'Initial Offset')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButtonInit, self.measureinit)
		self.measureupdate = wx.Button(self,  -1, 'Update Offset')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButtonUpdate, self.measureupdate)

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 3), wx.EXPAND|wx.ALL|wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)
		self.sizer.Add(self.measurecancel, (1, 0), (1, 1), wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)
		self.sizer.Add(self.measureinit, (1, 1), (1, 1), wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)
		self.sizer.Add(self.measureupdate, (1, 2), (1, 1), wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButtonInit(self, evt):
		self.onMeasure(evt, update=False)

	def onMeasureButtonUpdate(self, evt):
		self.onMeasure(evt, update=True)

	def onMeasure(self, evt, update):
		atilt = self.tiltvalue.GetValue()
		asnr  = self.snrvalue.GetValue()
		amedfilt  = self.medfiltvalue.GetValue()
		if(self.crosscorr.GetValue() and not self.phasecorr.GetValue()):
			acorr = 'cross'
		else:  acorr = 'phase'
		if(self.twotilt.GetValue() and not self.onetilt.GetValue()):
			atilttwice = True
		else:  atilttwice = False
		threading.Thread(target=self.node.measureTiltAxis, args=(atilt,update,asnr,acorr,atilttwice,amedfilt)).start()

class AlignRotationCenterDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Align Rotation Center')

		self.measure = wx.Button(self, -1, 'Align')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.measure, (0, 0), (1, 1), wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Defocus 1:')
		self.d1value = FloatEntry(self, -1, allownone=False, chars=5, value='-2e-6')
		sbsz.Add(label, (0,0), (1,1))
		sbsz.Add(self.d1value, (0,1), (1,1))
		label = wx.StaticText(self, -1, 'Defocus 2:')
		self.d2value = FloatEntry(self, -1, allownone=False, chars=5, value='-4e-6')
		sbsz.Add(label, (1,0), (1,1))
		sbsz.Add(self.d2value, (1,1), (1,1))

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(self.measure, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButton(self, evt):
		d1 = self.d1value.GetValue()
		d2 = self.d2value.GetValue()
		self.EndModal(wx.ID_OK)
		threading.Thread(target=self.node.alignRotationCenter, args=(d1,d2,)).start()

class ManualFocusSettingsDialog(gui.wx.Dialog.Dialog):
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

		self.parameter = Choice(self.toolbar, -1, choices=['Defocus', 'Stage Z'])
		self.parameter.SetStringSelection('Defocus')
		self.toolbar.AddControl(self.parameter)
		bitmap = gui.wx.Icons.icon('plus')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLUS, bitmap,
													shortHelpString='Increment up')
		bitmap = gui.wx.Icons.icon('minus')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MINUS, bitmap,
													shortHelpString='Increment down')

		self.toolbar.AddSeparator()

		self.value = FloatEntry(self.toolbar, -1, allownone=False, chars=6, value='0.0')
		self.toolbar.AddControl(self.value)
	# size is defined because some wxPython installation lack good wxDefaultSize
		self.toolbar.AddControl(wx.StaticText(self.toolbar, -1, ' m',size=(20,20)))
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
	
		self.SetAutoLayout(True)

		self.settingsdialog = ManualFocusSettingsDialog(self,'Manual Focus Settings','Settings')

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
		par = self.parameter.GetStringSelection()
		threading.Thread(target=self.node.onFocusUp, args=(par,)).start()

	def onMinusTool(self, evt):
		self._manualEnable(False)
		par = self.parameter.GetStringSelection()
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

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = ManualFocusDialog(frame,None)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

