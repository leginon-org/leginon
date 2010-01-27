# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/ClickTargetFinder.py,v $
# $Revision: 1.23 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-18 21:14:00 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.TargetFinder.Panel):
	icon = 'clicktargetfinder'
	def initialize(self):
		leginon.gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = leginon.gui.wx.TargetFinder.SettingsDialog

		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTargetTool('preview', wx.Color(255, 128, 255), target=True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('reference', wx.Color(128, 0, 128), target=True, unique=True)
		self.imagepanel.selectiontool.setDisplayed('reference', True)
		self.imagepanel.addTargetTool('done', wx.Color(218, 0, 0))
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.addTargetTool('position', wx.Color(218, 165, 32), shape='x')
		self.imagepanel.selectiontool.setDisplayed('position', True)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Click Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

