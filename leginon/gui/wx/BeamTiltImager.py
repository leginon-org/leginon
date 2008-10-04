# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Focuser.py,v $
# $Revision: 1.60 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-31 02:37:06 $
# $Author: acheng $
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
import gui.wx.ImagePanel
import gui.wx.TargetPanel
import gui.wx.ToolBar

AlignRotationCenterEventType = wx.NewEventType()

EVT_ALIGN = wx.PyEventBinder(AlignRotationCenterEventType)

		self.SetEventObject(source)

class Panel(gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = gui.wx.TargetPanel.TargetImagePanel
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ALIGN, 'rotcenter',
							 shortHelpString='Align rotation center')
		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255, 128, 0))

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.align_dialog = AlignRotationCenterDialog(self)
		self.Bind(EVT_ALIGN, self.onAlignRotationCenter, self)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.toolbar.Bind(wx.EVT_TOOL, self.onAlignRotationCenter,
						  id=gui.wx.ToolBar.ID_ALIGN)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onAlignRotationCenter(self, evt):
		self.align_dialog.Show()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		sizers = gui.wx.Acquisition.SettingsDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Focusing')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 5)
		self.widgets['beam tilt'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.01')
		melt_sizer = wx.GridBagSizer(5, 5)
		melt_sizer.Add(self.widgets['beam tilt'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		melt_sizer.Add(wx.StaticText(self, -1, 'radian'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Melt time:')
		sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(melt_sizer, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.widgets['sites'] = IntEntry(self, -1, min=0, allownone=False, chars=4, value='0')
		melt_sizer = wx.GridBagSizer(5, 5)
		melt_sizer.Add(self.widgets['sites'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Number of tilt directions:')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(melt_sizer, (1, 1), (1, 1), wx.ALIGN_CENTER)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		return sizers + [sbsz]

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

	def onSettingsTool(self, evt):
		self.settingsdialog.maskradius.SetValue(self.node.maskradius)
		self.settingsdialog.increment.SetValue(self.node.increment)
		#self.MakeModal(False)
		if self.settingsdialog.ShowModal() == wx.ID_OK:
			self.node.maskradius = self.settingsdialog.maskradius.GetValue()
			self.node.increment = self.settingsdialog.increment.GetValue()
		#self.MakeModal(True)

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

