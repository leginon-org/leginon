# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx

from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.Settings
import leginon.gui.wx.MosaicClickTargetFinder
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.MosaicClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		leginon.gui.wx.MosaicClickTargetFinder.Panel.initialize(self)

	def addOtherTools(self):
		self.toolbar.InsertSeparator(10)
		self.toolbar.InsertTool(11, leginon.gui.wx.ToolBar.ID_ALIGN,
			'alignpresets', shortHelpString='Transfer targets')
		self.toolbar.InsertTool(12, leginon.gui.wx.ToolBar.ID_FIND_SQUARES,
			'squarefinder',shortHelpString='Find Squares')
		self.imagepanel.addTargetTool('Blobs', wx.Colour(0, 255, 255), shape='o')
		self.imagepanel.selectiontool.setDisplayed('Blobs', True)
		self.imagepanel.addTypeTool('Thresholded', display=True, settings=True)

	def onNodeInitialized(self):
		leginon.gui.wx.MosaicClickTargetFinder.Panel.onNodeInitialized(self)

		# need this enabled for new auto region target finding
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, True)

	def onImageSettings(self, evt):
		if evt.name == 'acquisition':
			dialog = leginon.gui.wx.MosaicClickTargetFinder.TargetSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'Thresholded':
			dialog = BlobSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

class BlobSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return BlobsScrolledSettings(self,self.scrsize,False)

class BlobsScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb2 = wx.StaticBox(self, -1, 'Blob Filtering (Set by example targets)')
		sbsz2 = wx.StaticBoxSizer(sb2, wx.VERTICAL)
		self.widgets['blob min score'] = FloatEntry(self, -1, chars=6)
		self.widgets['blob max score'] = FloatEntry(self, -1, chars=6)

		szrange2 = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Filter Blob Score:')
		szrange2.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szrange2.Add(self.widgets['blob min score'], (0, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange2.Add(self.widgets['blob max score'], (0, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz2 = wx.GridBagSizer(5, 5)
		sz2.Add(szrange2, (0, 0), (1, 2), wx.ALIGN_CENTER)
		sz2.AddGrowableCol(1)

		sbsz2.Add(sz2, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz2]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Score Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

