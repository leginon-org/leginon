# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
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
import leginon.gui.wx.ToolBar
import threading
from leginon.gui.wx.Presets import PresetChoice

class Panel(leginon.gui.wx.ClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		leginon.gui.wx.ClickTargetFinder.Panel.initialize(self)

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

	def addOtherTools(self):
		self.toolbar.InsertSeparator(10)
		self.toolbar.InsertTool(11, leginon.gui.wx.ToolBar.ID_FIND_SQUARES,
			'squarefinder',shortHelpString='Find Squares')
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

		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, False)

	def addOtherBindings(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onFindSquaresButton,
											id=leginon.gui.wx.ToolBar.ID_FIND_SQUARES)

	def onSubmitTool(self, evt):
		threading.Thread(target=self._onSubmitTool, args=(evt,)).start()

	def _onSubmitTool(self, evt):
		leginon.gui.wx.ClickTargetFinder.Panel.onSubmitTool(self, evt)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

	def onTilesButton(self, evt):
		choices = self.node.getMosaicNames()
		dialog = TilesDialog(self, choices)
		result = dialog.ShowModal()
		if result == wx.ID_OK:
			selection = dialog.cmosaic.GetStringSelection()
			if selection:
				self.node.loadMosaicTiles(selection)
		elif result == wx.ID_RESET:
			self.node.clearTiles()
		dialog.Destroy()

	def onMosaicButton(self, evt):
		dialog = MosaicSettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onRefreshTargetsButton(self, evt):
		self.node.displayDatabaseTargets()

	def onShowPositionButton(self, evt):
		self.node.refreshCurrentPosition()

	def onImageSettings(self, evt):
		if evt.name == 'Filtered':
			dialog = LPFSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'Thresholded':
			dialog = BlobSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

	def onFindSquaresButton(self, evt):
		#self.node.findSquares()
		threading.Thread(target=self.node.findSquares).start()

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
		sb = wx.StaticBox(self, -1, 'Blob Finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
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

		szrange = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min.')
		szrange.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Max.')
		szrange.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Blob size:')
		szrange.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['blobs']['min size'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['blobs']['max size'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Blob mean:')
		szrange.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['blobs']['min mean'], (2, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['blobs']['max mean'], (2, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Blob stdev.:')
		szrange.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER)
		szrange.Add(self.widgets['blobs']['min stdev'], (3, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szrange.Add(self.widgets['blobs']['max stdev'], (3, 2), (1, 1),
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
		sz.Add(szrange, (3, 0), (1, 2), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

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

