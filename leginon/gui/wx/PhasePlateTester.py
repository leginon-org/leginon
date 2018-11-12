# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry, EVT_ENTRY
from leginon.gui.wx.Presets import PresetChoice
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
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
		dialog = PhasePlateSettingsDialog(self,show_basic=True)
		state = dialog.ShowModal()
		dialog.Destroy()
		if state == wx.ID_OK:
			is_valid = self.node.uiSetStartPosition()
			if is_valid:
				threading.Thread(target=self.node.simulateTarget).start()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

class PhasePlateSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		scrolling = not self.show_basic
		return PhasePlateScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class PhasePlateScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Phase Plate Configuration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.szmain = wx.GridBagSizer(5, 5)

		newrow,newcol = self.createPhasePlateNumberEntry((0,0))
		newrow,newcol = self.createTotalPositionsEntry((newrow,0))
	
		sb1 = wx.StaticBox(self, -1, 'Phase Plate Testing Options')
		sbsz1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
		self.szmain1 = wx.GridBagSizer(5, 5)

		newrow,newcol = self.createCurrentPositionEntry((0,0))
		newrow,newcol = self.createStartPositionEntry((newrow,0))
		newrow,newcol = self.createTotalTestPositionEntry((newrow,0))


		sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sbsz1.Add(self.szmain1, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz, sbsz1]

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
				  wx.ALIGN_LEFT)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createTotalPositionsEntry(self,start_position):
		# define widget
		self.widgets['total positions'] = IntEntry(self, -1, min=1, chars=4)
		# make sizer
		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Patch positions per plate:')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['total positions'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		# add to main
		total_length = (1,1)
		self.szmain.Add(szminmag, start_position, total_length,
				  wx.ALIGN_LEFT)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createStartPositionEntry(self,start_position):
		# define widget
		self.widgets['start position'] = IntEntry(self, -1, min=1, chars=4)
		# make sizer
		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'patch position to start testing:')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['start position'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		# add to main1, not main so it looks nicer
		total_length = (1,1)
		self.szmain1.Add(szminmag, start_position, total_length,
				  wx.ALIGN_LEFT)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createCurrentPositionEntry(self,start_position):
		# define widget
		self.widgets['current position'] = IntEntry(self, -1, min=1, chars=4)
		# make sizer
		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Current patch position:')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['current position'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		# add to main1, not main so it looks nicer
		total_length = (1,1)
		self.szmain1.Add(szminmag, start_position, total_length,
				  wx.ALIGN_LEFT)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createTotalTestPositionEntry(self,start_position):
		# define widget
		self.widgets['total test positions'] = IntEntry(self, -1, min=1, chars=4)
		# make sizer
		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Number of patch positions to test:')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['total test positions'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		# add to main1, not main so it looks nicer
		total_length = (1,1)
		self.szmain1.Add(szminmag, start_position, total_length,
				  wx.ALIGN_LEFT)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return leginon.gui.wx.Acquisition.ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)
