# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MatlabTargetFinder.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2005-01-19 00:00:47 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.Events
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import gui.wx.ToolBar
import wx.lib.filebrowsebutton as filebrowse

class Panel(gui.wx.TargetFinder.Panel):
	def initialize(self, focus=True):
		gui.wx.TargetFinder.Panel.initialize(self)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Reload Targets')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		#self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True)
		#self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		#self.imagepanel.addTargetTool('focus', wx.BLUE, target=True)
		#self.imagepanel.selectiontool.setDisplayed('focus', True)
		#self.imagepanel.addTargetTool('done', wx.RED)
		#self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.Bind(gui.wx.Events.EVT_FOUND_TARGETS, self.onFoundTargets)

	def getTargetPositions(self, typename):
		return self.imagepanel.getTargetPositions(typename)

	def onNodeInitialized(self):
		gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTool,
											id=gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=gui.wx.ToolBar.ID_SUBMIT)

	def onFoundTargets(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def foundTargets(self):
		evt = gui.wx.Events.FoundTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onRefreshTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.node.matlabFindTargets()
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.node.submitTargets()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['module path'] = filebrowse.FileBrowseButton(self, -1)
		self.widgets['user check'] = wx.CheckBox(self, -1,
																				'Wait for user verification of targets')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['module path'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sz.Add(self.widgets['user check'], (1, 0), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Matlab Module')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return tfsbsz + [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Matlab Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

