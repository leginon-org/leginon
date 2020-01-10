# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/MosaicClickTargetFinder.py,v $
# $Revision: 1.36 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-14 20:02:52 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.ClickTargetFinder
import leginon.gui.wx.JAHCFinder
import leginon.gui.wx.ToolBar
import threading
from leginon.gui.wx.Presets import PresetChoice

class Panel(leginon.gui.wx.ClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		leginon.gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = leginon.gui.wx.TargetFinder.SettingsDialog

		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.addJAHCFinderTesting()
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True,exp=True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('focus', False)
		self.imagepanel.selectiontool.setEnableSettings('acquisition', True)
		self.imagepanel.addTargetTool('done', wx.Colour(218, 0, 0), numbers=True)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.addTargetTool('position', wx.Colour(218, 165, 32), shape='x')
		self.imagepanel.selectiontool.setDisplayed('position', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.toolbar.InsertSeparator(4)

		self.toolbar.InsertTool(5, leginon.gui.wx.ToolBar.ID_TILES,
			'tiles',shortHelpString='Tiles')
		self.toolbar.InsertTool(6, leginon.gui.wx.ToolBar.ID_MOSAIC,
			'atlasmaker',shortHelpString='Mosaic')
		self.toolbar.InsertSeparator(7)
		self.toolbar.InsertTool(8, leginon.gui.wx.ToolBar.ID_REFRESH,
			'refresh', shortHelpString='Refresh')
		self.toolbar.InsertTool(9, leginon.gui.wx.ToolBar.ID_CURRENT_POSITION,
			'currentposition', shortHelpString='Show Position')
		self.addOtherTools()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)

	def addOtherTools(self):
		self.toolbar.InsertSeparator(10)
		self.toolbar.InsertTool(11, leginon.gui.wx.ToolBar.ID_FIND_SQUARES,
			'squarefinder',shortHelpString='Find Squares')

	def addJAHCFinderTesting(self):
		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.addTypeTool('Template', display=True, settings=True)
		self.imagepanel.addTypeTool('Threshold', display=True, settings=True)
		self.imagepanel.addTargetTool('Blobs', wx.Colour(0, 255, 255), shape='o')
		self.imagepanel.selectiontool.setDisplayed('Blobs', True)
		self.imagepanel.addTargetTool('Lattice', wx.Colour(255, 0, 255), settings=True)

	def onNodeInitialized(self):
		leginon.gui.wx.ClickTargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTilesButton,
											id=leginon.gui.wx.ToolBar.ID_TILES)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMosaicButton,
											id=leginon.gui.wx.ToolBar.ID_MOSAIC)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTargetsButton,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onShowPositionButton,
											id=leginon.gui.wx.ToolBar.ID_CURRENT_POSITION)

		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)
		self.addOtherBindings()

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, False)

	def addOtherBindings(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onFindSquaresButton,
											id=leginon.gui.wx.ToolBar.ID_FIND_SQUARES)

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)
		threading.Thread(target=self._onSubmitTool, args=(evt,)).start()

	def _onSubmitTool(self, evt):
		self.node.submitTargets()

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def onTilesButton(self, evt):
		choices = self.node.getMosaicNames()
		dialog = TilesDialog(self, choices)
		result = dialog.ShowModal()
		if result == wx.ID_OK:
			selection = dialog.cmosaic.GetStringSelection()
			if selection:
				self.node.setMosaicName(selection)
				self.node.loadMosaicTiles(selection)
				self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)
		elif result == wx.ID_RESET:
			self.node.clearTiles()
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)
		dialog.Destroy()

	def onMosaicButton(self, evt):
		dialog = MosaicSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onShow(self):
		if self.imagepanel.imagedata is not None:
			self.onRefreshTargetsButton(None)

	def onRefreshTargetsButton(self, evt):
		self.node.displayDatabaseTargets()

	def onShowPositionButton(self, evt):
		self.node.refreshCurrentPosition()

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
		if evt.name == 'Template':
			dialog = LPFSettingsDialog(self)
		elif evt.name == 'Threshold':
			dialog = BlobSettingsDialog(self)
		elif evt.name == 'Lattice':
			dialog = LatticeSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onFindSquaresButton(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_FIND_SQUARES, False)
		# set up what to display before running.  Got an X error and crash
		# if doing it after.
		self.imagepanel.showTypeToolDisplays(['Image'])
		self.imagepanel.hideTypeToolDisplays(['Blobs'])
		self.imagepanel.showTypeToolDisplays(['acquisition','focus'])
		threading.Thread(target=self.node.findSquares).start()

	def squaresFound(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_FIND_SQUARES, True)

	def doneTargetList(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def doneTargetDisplay(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

class TilesDialog(wx.Dialog):
	def __init__(self, parent, choices):
		wx.Dialog.__init__(self, parent, -1, 'Tiles')

		self.cmosaic = wx.Choice(self, -1, choices=choices)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Load tiles from mosaic:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.cmosaic, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		bload = wx.Button(self, wx.ID_OK, 'Load')
		breset = wx.Button(self, -1, 'Reset')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		if not choices:
			self.cmosaic.Enable(False)
			self.cmosaic.Append('(No mosaics)')
			bload.Enable(False)
		self.cmosaic.SetSelection(0)

		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(bload, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(breset, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(bcancel, (0, 2), (1, 1), wx.ALIGN_CENTER)

		szdialog = wx.GridBagSizer(5, 5)
		szdialog.Add(sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		szdialog.Add(szbuttons, (1, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(szdialog)

		self.Bind(wx.EVT_BUTTON, self.onResetButton, breset)

	def onResetButton(self, evt):
		self.EndModal(wx.ID_RESET)

class MosaicSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def __init__(self, parent):
		leginon.gui.wx.Settings.Dialog.__init__(self, parent, 'Mosaic Settings')
	def initialize(self):
		return MosaicScrolledSettings(self,self.scrsize,False)

class MosaicScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Mosaics')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		choices = self.node.calclients.keys()
		self.widgets['calibration parameter'] = Choice(self, -1, choices=choices)
		self.widgets['scale image'] = wx.CheckBox(self, -1, 'Scale image to')
		self.widgets['scale size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['create on tile change'] = Choice(self, -1, choices=['all', 'final', 'none'])

		self.bcreate = wx.Button(self, -1, 'Create')
		self.bsave = wx.Button(self, -1, 'Save')

		szp = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Calibration parameter')
		szp.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szp.Add(self.widgets['calibration parameter'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		szs = wx.GridBagSizer(5, 5)
		szs.Add(self.widgets['scale image'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		szs.Add(self.widgets['scale size'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'pixels in largest dimension')
		szs.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szb = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mosaic image:')
		szb.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szb.Add(self.bcreate, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szb.Add(self.bsave, (0, 2), (1, 1), wx.ALIGN_CENTER)

		szc = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Auto create mosaic for new tiles')
		szc.Add(label, (0, 0), (1, 1))
		szc.Add(self.widgets['create on tile change'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szp, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szs, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szc, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szb, (3, 0), (1, 1), wx.ALIGN_CENTER)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		self.bcreate.Enable(self.node.mosaic.hasTiles())
		self.bsave.Enable(self.node.hasMosaicImage())

		self.Bind(wx.EVT_BUTTON, self.onCreateButton, self.bcreate)
		self.Bind(wx.EVT_BUTTON, self.onSaveButton, self.bsave)

		return [sbsz]

	def onCreateButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.createMosaicImage()
		self.dialog.scrsettings.bsave.Enable(self.node.hasMosaicImage())

	def onSaveButton(self, evt):
		self.node.publishMosaicImage()

class OriginalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return OriginalScrolledSettings(self,self.scrsize,False)

	def onShow(self):
		self.scrsettings.setTileChoices()
class OriginalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		self.ctile = wx.Choice(self, -1, choices=self.node.getTileChoices())
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Load tile from current mosaic at index:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.ctile, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		return [sz, szbutton]

	def setTileChoices(self):
		choices = self.node.getTileChoices()
		self.ctile.Clear()
		for c in choices:
			self.ctile.Append(c)

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		try:
			index = int(self.ctile.GetStringSelection())
		except ValueError:
			index = 0
		self.node.setOriginal(index)
		self.panel.imagepanel.showTypeToolDisplays(['Original'])

class LPFSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return leginon.gui.wx.JAHCFinder.TemplateScrolledSettings(self,self.scrsize,False)

class LPFScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['template lpf'] = {}
		self.widgets['template lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['template lpf']['sigma'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.AddGrowableCol(1)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]


class BlobSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return BlobsScrolledSettings(self,self.scrsize,False)

class BlobsScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Blob Finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['threshold'] = FloatEntry(self, -1, min=0, chars=6)
		self.widgets['blobs border'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs max'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs min size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs max size'] = IntEntry(self, -1, min=0, chars=6)

		szrange = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min.')
		szrange.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Max.')
		szrange.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Blob size:')
		szrange.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['blobs min size'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['blobs max size'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Threshold:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['threshold'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Border:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['blobs border'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. number of blobs:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['blobs max'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(szrange, (3, 0), (1, 2), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.thresholdAndFindBlobs()
		self.panel.imagepanel.hideTypeToolDisplays(['Lattice','acquisition','focus'])
		self.panel.imagepanel.showTypeToolDisplays(['Blobs','Threshold'])


class LatticeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return leginon.gui.wx.JAHCFinder.LatticeScrolledSettings(self,self.scrsize,False)

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return leginon.gui.wx.JAHCFinder.FinalScrolledSettings(self,self.scrsize,False)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Click Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

