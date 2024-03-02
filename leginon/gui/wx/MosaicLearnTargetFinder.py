# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import wx.lib.filebrowsebutton as filebrowse

from leginon.gui.wx.Entry import Entry, FloatEntry
import leginon.gui.wx.Settings
import leginon.gui.wx.MosaicScoreTargetFinder
import leginon.gui.wx.MosaicClickTargetFinder
import leginon.gui.wx.ToolBar
import threading

class Panel(leginon.gui.wx.MosaicScoreTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		leginon.gui.wx.MosaicScoreTargetFinder.Panel.initialize(self)

	def addOtherTools(self):
		leginon.gui.wx.MosaicScoreTargetFinder.Panel.addOtherTools(self)
		self.toolbar.InsertTool(13, leginon.gui.wx.ToolBar.ID_UPDATE_LEARNING,
			'learning',shortHelpString='Update learning')

	def onNodeInitialized(self):
		leginon.gui.wx.MosaicScoreTargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onUpdateLearningButton,
											id=leginon.gui.wx.ToolBar.ID_UPDATE_LEARNING)

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_UPDATE_LEARNING, False)
		self.find_square_button_clicked = False

	def onImageSettings(self, evt):
		if evt.name == 'acquisition':
			dialog = leginon.gui.wx.MosaicClickTargetFinder.TargetSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'Blobs':
			dialog = BlobSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'Thresholded':
			dialog = ThresholdSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

	def onFindSquaresButton(self, evt):
		threading.Thread(target=self.node.updatePtolemyTargets).start()
		self.find_square_button_clicked = True

	def _enable_on_tile_loaded(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_UPDATE_LEARNING, True)

	def onUpdateLearningButton(self, evt):
		threading.Thread(target=self.node.updateSquareTargetOrder).start()

	def onTargetsSubmitted(self, evt):
		leginon.gui.wx.MosaicScoreTargetFinder.Panel.onTargetsSubmitted(self,evt)
		if self.find_square_button_clicked:
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_UPDATE_LEARNING, True)


class BlobSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return BlobsScrolledSettings(self,self.scrsize,False)

class BlobsScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Ptolemy Active Learning and Scoring')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.GridBagSizer(5, 5)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		return [sbsz]

class ThresholdSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ThresholdScrolledSettings(self,self.scrsize,False)

class ThresholdScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb2 = wx.StaticBox(self, -1, 'Blob Filtering (Set by example targets)')
		sbsz2 = wx.StaticBoxSizer(sb2, wx.VERTICAL)
		self.widgets['filter-key'] = Entry(self, -1, chars=10)
		self.widgets['filter-min'] = FloatEntry(self, -1, chars=6)
		self.widgets['filter-max'] = FloatEntry(self, -1, chars=6)


		keysz = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Filter Key Used:')
		keysz.Add(label, (0, 0), (1, 1), wx.ALIGN_LEFT|wx.EXPAND)
		keysz.Add(self.widgets['filter-key'], (0, 1), (1, 1), wx.ALIGN_RIGHT)
		keysz.AddGrowableCol(0)

		szrange2 = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Filter Range:')
		szrange2.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szrange2.Add(self.widgets['filter-min'], (0, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange2.Add(self.widgets['filter-max'], (0, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz2 = wx.GridBagSizer(5, 5)
		sz2.Add(keysz, (0, 0), (1, 2), wx.ALIGN_LEFT|wx.EXPAND)
		sz2.Add(szrange2, (1, 0), (1, 2), wx.ALIGN_CENTER)
		sz2.AddGrowableCol(1)

		sbsz2.Add(sz2, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz2]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Learn Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

