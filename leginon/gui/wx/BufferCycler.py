# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx
import threading

import leginon.gui.wx.Conditioner
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Entry import IntEntry

class Panel(leginon.gui.wx.Conditioner.Panel):
	icon = 'targetfilter'
	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Conditioner.SettingsDialog):
	def _initializeScrolledSettings(self,show_scrollbar=False):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return ScrolledSettings(self,self.scrsize,show_scrollbar)

class ScrolledSettings(leginon.gui.wx.Conditioner.ScrolledSettings):
	def getTitle(self):
		return 'Buffer Cycler'
