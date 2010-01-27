# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx
import wx.lib.filebrowsebutton as filebrowse

import leginon.gui.wx.Events
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.TargetFinder.Panel):
	def initialize(self, focus=True):
		leginon.gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = SettingsDialog

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET,
													'simulatetarget',
													shortHelpString='Target Test Image')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh Targets')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_REFRESH, False)

		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)

		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('done', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.Bind(leginon.gui.wx.Events.EVT_FOUND_TARGETS, self.onFoundTargets)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)

	def onImageSettings(self, evt):
		if evt.name == 'Image':
			dialog = OriginalSettingsDialog(self,'Image')
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['test image']
				if filename:
					self.node.readImage(filename)
			dialog.Destroy()
			return

		dialog.ShowModal()
		dialog.Destroy()

	def onNodeInitialized(self):
		leginon.gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTargetTestImage,
											id=leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTool,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET, True)

	def onFoundTargets(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_REFRESH, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def foundTargets(self):
		evt = leginon.gui.wx.Events.FoundTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onRefreshTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_REFRESH, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)
		threading.Thread(target=self.node.matlabFindTargets).start()

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_REFRESH, False)
		leginon.gui.wx.TargetFinder.Panel.onSubmitTool(self, evt)

	def onTargetTestImage(self, evt):
		threading.Thread(target=self.node.targetTestImage).start()

class OriginalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return OriginalScrolledSettings(self,self.scrsize,False)

class OriginalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'test image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['test image'] = filebrowse.FileBrowseButton(self,
								labelText='Test Image:', fileMask='*.mrc')
		self.widgets['test image'].SetMinSize((500,50))
		self.dialog.bok.SetLabel('&Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['test image'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class SettingsDialog(leginon.gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.TargetFinder.ScrolledSettings):
	def initialize(self):
		tfsbsz = leginon.gui.wx.TargetFinder.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Matlab Module')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		#leginon.gui.wx.Settings.Dialog.initialize(self)

#		self.widgets['test image'] = filebrowse.FileBrowseButton(self,
#								labelText='Test Image:', fileMask='*.mrc')
		self.widgets['module path'] = filebrowse.FileBrowseButton(self,
								labelText='Matlab File:', fileMask='*.m')

		sz = wx.GridBagSizer(5, 5)
#		sz.Add(self.widgets['test image'], (0, 0), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['module path'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

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

