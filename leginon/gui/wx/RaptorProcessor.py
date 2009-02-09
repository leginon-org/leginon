# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/FFTMaker.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import Entry, FloatEntry, IntEntry, EVT_ENTRY
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.ImagePanel

class Panel(gui.wx.ImageProcessor.Panel):
	icon = 'fftmaker'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.Realize()

		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Raptor Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Process images when event received')
		self.widgets['path'] = Entry(self, -1)
		self.widgets['time'] = IntEntry(self, -1)
		self.widgets['binning'] = IntEntry(self, -1)

		sbsz.Add(self.widgets['process'])
		sbsz.Add(self.widgets['path'])
		sbsz.Add(self.widgets['time'])
		sbsz.Add(self.widgets['binning'])

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Raptor Processor Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

