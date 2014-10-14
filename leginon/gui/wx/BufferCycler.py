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
	'''
	Panel shown in Leginon gui.
	'''
	# icon displayed for the node. Choose from png files in leginon/icons
	icon = 'targetfilter'
	def onSettingsTool(self, evt):
		'''
		Respond to a mouse left click on Settings Tool on the node toolbar
		'''
		# Redefining this function that calls SettingsDialog class makes sure
		# that the class in this module is loaded, not the one in the module
		# containing the parent class
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Conditioner.SettingsDialog):
	'''
	Wrapper Settings Dialog class called from the panel and contains
	ScrolledSettings and basic "OK/Cancel/Apply" buttons
	'''
	def _initializeScrolledSettings(self,show_scrollbar=False):
		# Alternative way of ensuring class in this module is loaded:
		# Use a "private call" like this.
		return ScrolledSettings(self,self.scrsize,show_scrollbar)

class ScrolledSettings(leginon.gui.wx.Conditioner.ScrolledSettings):
	'''
	The actual class where the settings gui is defined.
	'''
	def getTitle(self):
		'''
		Give a unique title for the settings box
		'''
		return 'Buffer Cycler'
