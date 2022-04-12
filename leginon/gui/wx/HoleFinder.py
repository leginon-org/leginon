# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx
import wx.lib.filebrowsebutton as filebrowse

import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.AutoTargetFinder
import leginon.gui.wx.Rings
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry
import leginon.gui.wx.TargetTemplate
import leginon.gui.wx.ToolBar
import leginon.gui.wx.JAHCFinder

class Panel(leginon.gui.wx.AutoTargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		leginon.gui.wx.AutoTargetFinder.Panel.initialize(self)
		self.SettingsDialog = leginon.gui.wx.AutoTargetFinder.SettingsDialog

		self.imagepanel.addTypeTool('Edge', display=True, settings=True)
		self.imagepanel.addTypeTool('Template', display=True, settings=True)
		self.imagepanel.addTypeTool('Threshold', display=True, settings=True)
		self.imagepanel.addTargetTool('Blobs', wx.Colour(0, 255, 255), shape='o', settings=True)
		self.imagepanel.addTargetTool('Lattice', wx.Colour(255, 0, 255), settings=True)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True,exp=True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.addTargetTool('preview', wx.Colour(255, 128, 255), target=True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = leginon.gui.wx.AutoTargetFinder.OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'Edge':
			dialog = EdgeSettingsDialog(self)
		elif evt.name == 'Template':
			dialog = TemplateSettingsDialog(self)
		elif evt.name == 'Threshold':
			dialog = ThresholdSettingsDialog(self)
		elif evt.name == 'Blobs':
			dialog = BlobsSettingsDialog(self)
		elif evt.name == 'Lattice':
			dialog = LatticeSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		# modeless display
		dialog.Show(True)

class TemplateSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return TemplateScrolledSettings(self,self.scrsize,False)

class TemplateScrolledSettings(leginon.gui.wx.JAHCFinder.TemplateScrolledSettings):
	pass

class EdgeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return EdgeScrolledSettings(self,self.scrsize,False)

class EdgeScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['edge lpf'] = {}
		self.widgets['edge lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['edge lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

		sb = wx.StaticBox(self, -1, 'Edge Finding')
		sbszedge = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['edge threshold'] = FloatEntry(self, -1, chars=9)

		szedge = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Threshold:')
		szedge.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge threshold'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szedge.AddGrowableCol(1)

		sbszedge.Add(szedge, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlpf, sbszedge, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.findEdges()
		self.panel.imagepanel.showTypeToolDisplays(['Edge'])

class ThresholdSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ThresholdScrolledSettings(self,self.scrsize,False)

class ThresholdScrolledSettings(leginon.gui.wx.JAHCFinder.ThresholdScrolledSettings):
	pass

class BlobsSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return BlobsScrolledSettings(self,self.scrsize,False)

class BlobsScrolledSettings(leginon.gui.wx.JAHCFinder.BlobsScrolledSettings):
	pass

class LatticeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return LatticeScrolledSettings(self,self.scrsize,False)

	def onShow(self):
		self.panel.imagepanel.showTypeToolDisplays(['Original'])
		
class LatticeScrolledSettings(leginon.gui.wx.JAHCFinder.LatticeScrolledSettings):
	pass

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.JAHCFinder.FinalScrolledSettings):
	pass

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Hole Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

