# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Reference.py,v $
# $Revision: 1.4 $
# $Name: not supported by cvs2svn $
# $Date: 2006-08-22 19:22:33 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry
from gui.wx.Presets import PresetChoice
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.Reference

class SettingsDialog(gui.wx.Reference.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Reference.ScrolledSettings):
	def initialize(self):
		szr = gui.wx.Reference.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Check Zero Loss Peak Shift')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['check preset'] = PresetChoice(self, -1)
		presets = self.node.presets_client.getPresetNames()
		self.widgets['check preset'].setChoices(presets)
		szcheck = wx.GridBagSizer(5, 5)
		szcheck.Add(wx.StaticText(self, -1, 'Use'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcheck.Add(self.widgets['check preset'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcheck.Add(wx.StaticText(self, -1, 'to check if needing realignment'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.widgets['threshold'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szt = wx.GridBagSizer(5, 5)
		szt.Add(wx.StaticText(self, -1, 'Start ALP if the image standard deviation is larger than'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szt.Add(self.widgets['threshold'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szt.Add(wx.StaticText(self, -1, 'times since last alignment'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szcheck, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szt, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [szr[0],sbsz]

class AlignZeroLossPeakPanel(gui.wx.Reference.ReferencePanel):
	icon = 'alignzlp'
	def __init__(self, *args, **kwargs):
		gui.wx.Reference.ReferencePanel.__init__(self, *args, **kwargs)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()


