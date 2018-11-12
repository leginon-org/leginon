# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry, EVT_ENTRY
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = leginon.gui.wx.TargetPanel.TargetImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)

		self.toolbar.RemoveTool(leginon.gui.wx.ToolBar.ID_BROWSE_IMAGES)

		self.szmain.Layout()

	def onSimulateTargetTool(self, evt):
		dialog = PhasePlateTestImagerSettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()
		threading.Thread(target=self.node.simulateTarget).start()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

class PhasePlateTestImagerSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		scrolling = not self.show_basic
		return PhasePlateTestImagerScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class PhasePlateTestImagerScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Phase Plate Testing Options')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.szmain = wx.GridBagSizer(5, 5)

		newrow,newcol = self.createPhasePlateNumberEntry((0,0))

		sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		return [sbsz]

	def createPhasePlateNumberEntry(self,start_position):
		# define widget
		self.widgets['phase plate number'] = IntEntry(self, -1, min=1, chars=4)
		# make sizer
		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Phase Plate Number:')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['phase plate number'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		# add to main
		total_length = (1,1)
		self.szmain.Add(szminmag, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return leginon.gui.wx.Acquisition.ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)
