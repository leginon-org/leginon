# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx
import wx.lib.filebrowsebutton as filebrowse

from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.Events
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.ToolBar

import os.path

class Panel(leginon.gui.wx.TargetFinder.Panel):
	def initialize(self, focus=True):
		leginon.gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = SettingsDialog

		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)

		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('done', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.Bind(leginon.gui.wx.Events.EVT_FOUND_TARGETS, self.onFoundTargets)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onImageSettings(self, evt):
		if evt.name == 'Image':
			dialog = OriginalSettingsDialog(self,'Image')
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['test image']
				if filename:
					self.node.readImage(filename)
			dialog.Destroy()
			return
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()

	def onNodeInitialized(self):
		leginon.gui.wx.TargetFinder.Panel.onNodeInitialized(self)

	def onFoundTargets(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def foundTargets(self):
		evt = leginon.gui.wx.Events.FoundTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onSubmitTool(self, evt):
		leginon.gui.wx.TargetFinder.Panel.onSubmitTool(self, evt)

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
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.TargetFinder.ScrolledSettings):
	def addBasicSettings(self):
		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of selected targets')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz

	def addSettings(self):
		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of selected targets')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		return sz

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		self.btest = wx.Button(self, -1, 'Test')
		self.ctarget = wx.Button(self, -1, '&Clear targets')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.ctarget, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.Add(self.btest, (0, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		settings_sz = self.createSettingsSizer()
	
		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.ctarget)

		return [settings_sz, szbutton]

	def createSettingsSizer(self):
		sb = wx.StaticBox(self, -1, 'Stitch Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.GridBagSizer(5, 10)
		self.widgets['overlap'] = FloatEntry(self, -1, max=100.0, chars=6)
		label = wx.StaticText(self, -1, 'Overlap:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['overlap'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '%')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(1)

		sz2 = wx.GridBagSizer(5, 10)
		self.widgets['coverage'] = FloatEntry(self, -1, max=20.0, chars=6)
		label = wx.StaticText(self, -1, 'Diameter of a circle to cover:')
		sz2.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz2.Add(self.widgets['coverage'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '(multiple of this image size)')
		sz2.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz2.AddGrowableCol(1)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sbsz.Add(sz2, 1, wx.ALIGN_CENTER|wx.ALL, 5)

		return sbsz

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.testTargeting).start()

	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.clearTargets('acquisition')
		self.node.clearTargets('focus')

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Stitch Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

