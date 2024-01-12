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
import leginon.gui.wx.MosaicAligner
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.ClickTargetFinder
import leginon.gui.wx.ToolBar
import threading
from leginon.gui.wx.Presets import PresetChoice

class Panel(leginon.gui.wx.ClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		leginon.gui.wx.ClickTargetFinder.Panel.initialize(self)
		self.SettingsDialog = SettingsDialog
		self.imagepanel.selectiontool.setEnableSettings('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('focus', False)
		self.imagepanel.selectiontool.setEnableSettings('focus', False)

		self.toolbar.InsertTool(3, leginon.gui.wx.ToolBar.ID_PAUSE,
			'pause',shortHelpString='Pause before Autosubmit')
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
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def addTargetTools(self):
		# add example target at top
		self.addExampleTargetTool()
		super(Panel, self).addTargetTools()

	def addExampleTargetTool(self):
		self.imagepanel.addTargetTool('example', wx.GREEN, shape='<>', target=True)
		self.imagepanel.selectiontool.setDisplayed('example', True)

	def addOtherTools(self):
		self.toolbar.InsertSeparator(10)
		self.toolbar.InsertTool(11, leginon.gui.wx.ToolBar.ID_ALIGN,
			'alignpresets', shortHelpString='Transfer targets')
		self.toolbar.InsertTool(12, leginon.gui.wx.ToolBar.ID_FIND_SQUARES,
			'squarefinder',shortHelpString='Find Squares')
		self.imagepanel.addTargetTool('Blobs', wx.Colour(0, 255, 255), shape='o')
		self.imagepanel.selectiontool.setDisplayed('Blobs', True)
		self.imagepanel.addTypeTool('Filtered', display=True, settings=True)
		self.imagepanel.addTypeTool('Thresholded', display=True, settings=True)

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
		self.toolbar.Bind(wx.EVT_TOOL, self.onPauseTool,
											id=leginon.gui.wx.ToolBar.ID_PAUSE)

		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)
		self.addOtherBindings()

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)

	def addOtherBindings(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onTransferTargetsButton,
											id=leginon.gui.wx.ToolBar.ID_ALIGN)
		self.toolbar.Bind(wx.EVT_TOOL, self.onFindSquaresButton,
											id=leginon.gui.wx.ToolBar.ID_FIND_SQUARES)

	def onSettingsTool(self, evt):
		dialog = self.SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPauseTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		threading.Thread(target=self.node.guiPauseBeforeSubmit).start()

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)
		threading.Thread(target=self._onSubmitTool, args=(evt,)).start()

	def _onSubmitTool(self, evt):
		self.node.submitTargets()

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)

	def _enable_on_tile_loaded(self):
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
				self._enable_on_tile_loaded()
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
		if evt.name == 'Filtered':
			dialog = LPFSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'acquisition':
			dialog = TargetSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'Thresholded':
			dialog = BlobSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

	def onTransferTargetsButton(self, evt):
		if not self.node.getMosaicName():
			threading.Thread(target=self.node.logger.error, args=['Need to load mosaic to use this.']).start()
			return
		dialog = leginon.gui.wx.MosaicAligner.AlignDialog(self, self.node)
		dialog.ShowModal()
		dialog.Destroy()

	def onFindSquaresButton(self, evt):
		xys = self.imagepanel.shapetool.fitted_shape_points
		threading.Thread(target=self.node.guiTargetMask, args=[xys,]).start()
		threading.Thread(target=self.node.autoTargetFinder).start()

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

class LPFSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return LPFScrolledSettings(self,self.scrsize,False)

class LPFScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['lpf'] = {}
		self.widgets['lpf']['size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Size:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['lpf']['size'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Sigma:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['lpf']['sigma'], (1, 1), (1, 1),
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
		sb1 = wx.StaticBox(self, -1, 'Rough Blob Finding')
		sbsz1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
		sb2 = wx.StaticBox(self, -1, 'Blob Filtering (Set by example targets)')
		sbsz2 = wx.StaticBoxSizer(sb2, wx.VERTICAL)
		self.widgets['threshold'] = FloatEntry(self, -1, min=0, chars=6)
		self.widgets['blobs'] = {}
		self.widgets['blobs']['border'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs']['max'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs']['min size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs']['max size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs']['min mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['blobs']['max mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['blobs']['min stdev'] = FloatEntry(self, -1, chars=6)
		self.widgets['blobs']['max stdev'] = FloatEntry(self, -1, chars=6)
		self.widgets['blobs']['min filter size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs']['max filter size'] = IntEntry(self, -1, min=0, chars=6)

		szrange1 = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min.')
		szrange1.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Max.')
		szrange1.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Finder Blob size:')
		szrange1.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szrange1.Add(self.widgets['blobs']['min size'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange1.Add(self.widgets['blobs']['max size'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		szrange2 = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Filter Blob size:')
		szrange2.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szrange2.Add(self.widgets['blobs']['min filter size'], (0, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange2.Add(self.widgets['blobs']['max filter size'], (0, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Blob mean:')
		szrange2.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szrange2.Add(self.widgets['blobs']['min mean'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange2.Add(self.widgets['blobs']['max mean'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Blob stdev.:')
		szrange2.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER)
		szrange2.Add(self.widgets['blobs']['min stdev'], (2, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange2.Add(self.widgets['blobs']['max stdev'], (2, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Threshold:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['threshold'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Border:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['blobs']['border'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. number of blobs:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['blobs']['max'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(szrange1, (3, 0), (1, 2), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		sz2 = wx.GridBagSizer(5, 5)
		sz2.Add(szrange2, (0, 0), (1, 2), wx.ALIGN_CENTER)
		sz2.AddGrowableCol(1)

		sbsz1.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		sbsz2.Add(sz2, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz1, sbsz2]

class TargetSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return TargetScrolledSettings(self,self.scrsize,False)

class TargetScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb1 = wx.StaticBox(self, -1, 'Target Selection')
		sbsz1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
		self.widgets['target grouping'] = {}
		self.widgets['target grouping']['total targets'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['target grouping']['classes'] = IntEntry(self, -1, min=1, chars=6)
		self.widgets['target multiple'] = IntEntry(self, -1, min=1, max=9, chars=6)
		self.widgets['target grouping']['randomize blobs'] = wx.CheckBox(self, -1, 'Randomize blob selection within groups')
		# row sizers
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Max. number of targets:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['target grouping']['total targets'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Number of target group to sample:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['target grouping']['classes'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(self.createGroupMethodSizer(), (2,0),(1,2),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_LEFT)
		
		tm_sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Cover each square with:')
		tm_sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		tm_sz.Add(self.widgets['target multiple'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'targets')
		tm_sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(tm_sz, (3, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		tm_sz.Add(self.widgets['target grouping']['randomize blobs'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# finalize
		sz.AddGrowableCol(1)
		sbsz1.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		return [sbsz1, ]

	def createGroupMethodSizer(self):
		groupmethods = self.node.getGroupMethodChoices()
		self.widgets['target grouping']['group method'] = Choice(self, -1, choices=groupmethods)
		szgroupmethod = wx.GridBagSizer(5, 5)
		szgroupmethod.Add(wx.StaticText(self, -1, 'Grouping method: '),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szgroupmethod.Add(self.widgets['target grouping']['group method'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		return szgroupmethod

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'General Mosaic Click Target Finder Settings ')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = self.addSettings()
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def createAutoFinderSizer(self):
		sz = wx.GridBagSizer(5, 5)
		self.widgets['autofinder'] = wx.CheckBox(self, -1, 'Enable auto targeting')
		sz.Add(self.widgets['autofinder'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return sz

	def createCheckMethodSizer(self):
		checkmethods = self.node.getCheckMethods()
		self.widgets['check method'] = Choice(self, -1, choices=checkmethods)
		szcheckmethod = wx.GridBagSizer(5, 5)
		szcheckmethod.Add(wx.StaticText(self, -1, '   Check from'),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szcheckmethod.Add(self.widgets['check method'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		return szcheckmethod

	def createSimpleBlobMergeSizer(self):
		sz = wx.GridBagSizer(5, 5)
		self.widgets['simpleblobmerge'] = wx.CheckBox(self, -1, 'Simple blob merging')
		sz.Add(self.widgets['simpleblobmerge'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return sz

	def createSortTargetSizer(self):
		sz = wx.GridBagSizer(5, 5)
		self.widgets['sort target'] = wx.CheckBox(self, -1, 'Sort targets by shortest path')
		sz.Add(self.widgets['sort target'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return sz

	def addSettings(self):
		sortsz = self.createSortTargetSizer()
		autosz = self.createAutoFinderSizer()
		checkmethodsz = self.createCheckMethodSizer()
		simpleblobmergesz = self.createSimpleBlobMergeSizer()
		sz = wx.GridBagSizer(5, 5)
		sz.Add(sortsz, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(autosz, (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(simpleblobmergesz, (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(checkmethodsz, (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		self.Bind(wx.EVT_CHOICE, self.onChooseCheckMethod, self.widgets['check method'])
		return sz

	def onChooseCheckMethod(self, evt):
		item_index = self.widgets['check method'].GetSelection()
		if item_index != wx.NOT_FOUND:
			self.node.uiChooseCheckMethod(self.widgets['check method'].GetString(item_index))

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

