# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
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

		self.imagepanel = leginon.gui.wx.TargetPanel.ShapeTargetImagePanel(self, -1)
		# standard tools
		self.addTargetTools()
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def addTargetTools(self):
		self.imagepanel.addTargetTool('preview', wx.Colour(255, 128, 255), target=True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True,exp=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('reference', wx.Colour(128, 0, 128), target=True, unique=True)
		self.imagepanel.selectiontool.setDisplayed('reference', True)
		self.imagepanel.addTargetTool('done', wx.Colour(218, 0, 0), numbers=True)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.addTargetTool('position', wx.Colour(218, 165, 32), shape='x')
		self.imagepanel.selectiontool.setDisplayed('position', True)


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

