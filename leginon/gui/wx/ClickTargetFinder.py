# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ClickTargetFinder.py,v $
# $Revision: 1.12 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import gui.wx.ToolBar

class Panel(gui.wx.TargetFinder.Panel):
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('acquisition', target=wx.GREEN, display=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTypeTool('focus', target=wx.BLUE, display=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTypeTool('done', target=wx.RED, display=True)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.addTypeTool('position', target=wx.Color(255, 128, 0),
																	display=True)
		self.imagepanel.selectiontool.setDisplayed('position', True)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def getTargetPositions(self, typename):
		return self.imagepanel.getTargetPositions(typename)

	def onNodeInitialized(self):
		gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=gui.wx.ToolBar.ID_SUBMIT)

	def onSubmitTool(self, evt):
		self.node.submitTargets()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	pass

	'''
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)

		self.widgets['no resubmit'] = wx.CheckBox(self, -1,
				'Do not allow targets to be resubmitted for an image')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['no resubmit'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Click target finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return tfsbsz + [sbsz]
	'''

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

