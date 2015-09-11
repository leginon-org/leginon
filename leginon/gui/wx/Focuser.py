#!/usr/bin/env python

# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/Focuser.py,v $
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
from leginon.gui.wx.Presets import EditPresetOrder
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar
import leginon.gui.wx.FocusSequence
import leginon.gui.wx.ManualFocus

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

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = leginon.gui.wx.TargetPanel.TargetImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)

		self.toolbar.InsertTool(2, leginon.gui.wx.ToolBar.ID_FOCUS_SEQUENCE, 'focus_sequence',
								shortHelpString='Focus Sequence')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MANUAL_FOCUS, 'manualfocus',
							 shortHelpString='Manual Focus')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ALIGN, 'rotcenter',
							 shortHelpString='Align rotation center')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE_TILT_AXIS, 'tiltaxis',
							 shortHelpString='Measure stage tilt axis')
		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Colour(255, 128, 0))

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.measure_dialog = MeasureTiltAxisDialog(self)
		self.Bind(EVT_MEASURE_TILT_AXIS, self.onMeasureTiltAxis, self)
		self.align_dialog = AlignRotationCenterDialog(self)
		self.Bind(EVT_ALIGN, self.onAlignRotationCenter, self)
		self.manualdialog = leginon.gui.wx.ManualFocus.ManualFocusDialog(self, self.node)
		self.Bind(EVT_MANUAL_CHECK, self.onManualCheck, self)
		self.Bind(EVT_MANUAL_CHECK_DONE, self.onManualCheckDone, self)

		leginon.gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.toolbar.Bind(wx.EVT_TOOL, self.onFocusSequenceTool,
						  id=leginon.gui.wx.ToolBar.ID_FOCUS_SEQUENCE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onManualFocusTool,
						  id=leginon.gui.wx.ToolBar.ID_MANUAL_FOCUS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTiltAxis,
						  id=leginon.gui.wx.ToolBar.ID_MEASURE_TILT_AXIS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAlignRotationCenter,
						  id=leginon.gui.wx.ToolBar.ID_ALIGN)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onFocusSequenceTool(self, evt):
		preset_names = self.node.presetsclient.getPresetNames()
		if not preset_names:
			self.node.logger.error('No presets available for focus settings.')
			return
		focus_methods = self.node.focus_methods.keys()
		correction_types = self.node.correction_types.keys()
		correlation_types = self.node.correlation_types
		default_setting = self.node.default_setting
		sequence = self.node.getFocusSequence()
		dialog_settings = leginon.gui.wx.FocusSequence.DialogSettings(
			preset_names,
			focus_methods,
			correction_types,
			correlation_types,
			default_setting,
			sequence)
		title = 'Focus Sequence (%s)' % self.node.name
		dialog = leginon.gui.wx.FocusSequence.Dialog(self, title, dialog_settings)
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
		evt = leginon.gui.wx.Events.SetImageEvent(image, typename, stats)
		self.manualdialog.GetEventHandler().AddPendingEvent(evt)

	def manualUpdated(self):
		self.manualdialog.manualUpdated()

	def onMeasureTiltAxis(self, evt):
		self.measure_dialog.Show()

	def onAlignRotationCenter(self, evt):
		self.align_dialog.Show()

	def onNewPixelSize(self, pixelsize,center,hightension,cs):
		self.manualdialog.center = center
		self.manualdialog.onNewPixelSize(pixelsize,center,hightension,cs)

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sbsz = self.addFocusSettings()
		return sizers + [sbsz]

	def addFocusSettings(self):
		sb = wx.StaticBox(self, -1, 'Focusing')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.szmain = wx.GridBagSizer(5, 5)

		self.presetnames = self.node.presetsclient.getPresetNames()

		newrow,newcol = self.createManualFocusPresetSelector((0,0))
		newrow,newcol = self.createMeltPresetSelector((newrow,0))
		newrow,newcol = self.createMeltTimeEntry((newrow,0))
		newrow,newcol = self.createAcquireFinalCheckBox((newrow,0))
		newrow,newcol = self.createBeamTiltSettleTimeEntry((newrow,0))


		sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		return sbsz

	def createAcquireFinalCheckBox(self,start_position):
		self.widgets['acquire final'] = \
				wx.CheckBox(self, -1, 'Acquire post-focus image')

		total_length = (1,2)
		self.szmain.Add(self.widgets['acquire final'], start_position, (1, 2),
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createMeltTimeEntry(self,start_position):
		self.widgets['melt time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		melt_sizer = wx.GridBagSizer(5, 5)
		melt_sizer.Add(self.widgets['melt time'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		melt_sizer.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Melt time:')

		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(melt_sizer, (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createManualFocusPresetSelector(self,start_position):
		sizer = wx.GridBagSizer(5, 5)
		self.widgets['manual focus preset'] = leginon.gui.wx.Presets.PresetChoice(self, -1)
		self.widgets['manual focus preset'].setChoices(self.presetnames)
		label = wx.StaticText(self, -1, 'Manual focus tool preset:')

		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.widgets['manual focus preset'], (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createMeltPresetSelector(self,start_position):
		sizer = wx.GridBagSizer(5, 5)
		self.widgets['melt preset'] = leginon.gui.wx.Presets.PresetChoice(self, -1)
		self.widgets['melt preset'].setChoices(self.presetnames)
		label = wx.StaticText(self, -1, 'Melt preset:')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['melt preset'], (1, 1), (1, 1), wx.ALIGN_CENTER)
		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.widgets['melt preset'], (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createBeamTiltSettleTimeEntry(self,start_position):
		self.widgets['beam tilt settle time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		melt_sizer = wx.GridBagSizer(5, 5)
		melt_sizer.Add(self.widgets['beam tilt settle time'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		melt_sizer.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Beam Tilt Settle time:')

		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(melt_sizer, (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]
	
class MeasureTiltAxisDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, "Measure Stage Tilt Axis Location")
		sb = wx.StaticBox(self, -1, 'Tilt Axis Params')
		sbsz2 = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sbsz = wx.GridBagSizer(3,6)

		row = int(0)
		label = wx.StaticText(self, -1, "Tilt angle: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.tiltvalue = FloatEntry(self, -1, allownone=False, chars=5, value='15.0')
		label2 = wx.StaticText(self, -1, " degrees", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label, (row,0), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(self.tiltvalue, (row,1), (1,1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label2, (row,2), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		row += 1
		self.tilttwice = wx.CheckBox(self, -1, "Tilt both directions")
		sbsz.Add(self.tilttwice, (row,0), (1,3), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		row += 1
		label = wx.StaticText(self, -1, "Average ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		label2 = wx.StaticText(self, -1, " tilts", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.numtilts = IntEntry(self, -1, allownone=False, chars=1, value='1')
		sbsz.Add(label, (row,0), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(self.numtilts, (row,1), (1,1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label2, (row,2), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		row += 1
		label = wx.StaticText(self, -1, "SNR cutoff: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.snrvalue = FloatEntry(self, -1, allownone=False, chars=5, value='10.0')
		label2 = wx.StaticText(self, -1, " levels")
		sbsz.Add(label, (row,0), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(self.snrvalue, (row,1), (1,1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label2, (row,2), (1,1), wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		row += 1
		label = wx.StaticText(self, -1, "Correlation: ", style=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.phasecorr = wx.RadioButton(self, -1, "Phase", style=wx.RB_GROUP|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		self.crosscorr = wx.RadioButton(self, -1, "Cross", style=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(label, (row,0), (1,1))
		sbsz.Add(self.phasecorr, (row,1), (1,1))
		sbsz.Add(self.crosscorr, (row,2), (1,1))

		row += 1
		self.medfilt = wx.CheckBox(self, -1, "Median filter phase correlation")
		self.medfilt.SetValue(True)
		sbsz.Add(self.medfilt, (row,0), (1,3), wx.EXPAND|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

		self.measurecancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.measureinit = wx.Button(self,  -1, 'Initial\nOffset')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButtonInit, self.measureinit)
		self.measureupdate = wx.Button(self,  -1, 'Update\nOffset')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButtonUpdate, self.measureupdate)

		sbsz2.Add(sbsz, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 1)

		buttonrow = wx.GridSizer(1,3)
		self.measurecancel.SetMinSize((85, 46))
		self.measureinit.SetMinSize((85, 46))
		self.measureupdate.SetMinSize((85, 46))
		buttonrow.Add(self.measurecancel, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
		buttonrow.Add(self.measureinit, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
		buttonrow.Add(self.measureupdate, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)

		self.sizer = wx.FlexGridSizer(3,1)
		sbsz2.SetMinSize((270, 200))
		self.sizer.Add(sbsz2, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
		#self.sizer.Add((10, 10), 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE|wx.ALL, 3)
		self.sizer.Add(buttonrow, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE|wx.ALL, 3)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButtonInit(self, evt):
		self.node.logger.info('Obtain new beam tilt axis')
		self.onMeasure(evt, update=False)

	def onMeasureButtonUpdate(self, evt):
		self.node.logger.info('Updating beam tilt axis')
		self.onMeasure(evt, update=True)

	def onMeasure(self, evt, update):
		self.Close()
		atilt = self.tiltvalue.GetValue()
		asnr  = self.snrvalue.GetValue()
		if asnr <= 0:
			self.node.logger.error('SNR cannot be less than or equal to zero')
			return
		amedfilt = self.medfilt.GetValue()
		anumtilts = self.numtilts.GetValue()
		if(self.crosscorr.GetValue() and not self.phasecorr.GetValue()):
			acorr = 'cross'
		else:
			acorr = 'phase'
		atilttwice = self.tilttwice.GetValue()
		#RUN THE Measurement
		threading.Thread(target=self.node.measureTiltAxis, args=(atilt, anumtilts, atilttwice, update, asnr, acorr, amedfilt)).start()

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
		self.Close()
		d1 = self.d1value.GetValue()
		d2 = self.d2value.GetValue()
		threading.Thread(target=self.node.alignRotationCenter, args=(d1,d2,)).start()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = leginon.gui.wx.ManualFocus.ManualFocusDialog(frame, None)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

