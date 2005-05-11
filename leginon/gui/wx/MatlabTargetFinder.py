# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MatlabTargetFinder.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2005-05-11 23:49:31 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
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
		self.SettingsDialog = SettingsDialog

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SIMULATE_TARGET,
													'simulatetarget',
													shortHelpString='Target Test Image')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh Targets')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SIMULATE_TARGET, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		#self.imagepanel.addTargetTool('done', wx.RED)
		#self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.Bind(gui.wx.Events.EVT_FOUND_TARGETS, self.onFoundTargets)

	def onNodeInitialized(self):
		gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTargetTestImage,
											id=gui.wx.ToolBar.ID_SIMULATE_TARGET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTool,
											id=gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SIMULATE_TARGET, True)

	def onFoundTargets(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, True)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def foundTargets(self):
		evt = gui.wx.Events.FoundTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onRefreshTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		threading.Thread(target=self.node.matlabFindTargets).start()

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_REFRESH, False)
		gui.wx.TargetFinder.onSubmitTool(self, evt)

	def onTargetTestImage(self, evt):
		threading.Thread(target=self.node.targetTestImage).start()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)
		#gui.wx.Settings.Dialog.initialize(self)

		self.widgets['test image'] = filebrowse.FileBrowseButton(self,
																			labelText='Test Image:', fileMask='*.mrc')
		self.widgets['module path'] = filebrowse.FileBrowseButton(self,
																			labelText='Matlab File:', fileMask='*.m')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['test image'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['module path'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

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

