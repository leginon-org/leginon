# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MosaicClickTargetFinder.py,v $
# $Revision: 1.33 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-10 01:01:38 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Settings
import gui.wx.TargetFinder
import gui.wx.ClickTargetFinder
import gui.wx.ToolBar
import threading
from gui.wx.Presets import PresetChoice

class Panel(gui.wx.ClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		gui.wx.ClickTargetFinder.Panel.initialize(self)

		self.toolbar.InsertSeparator(4)

		self.toolbar.InsertTool(5, gui.wx.ToolBar.ID_TILES,
													'tiles',
													shortHelpString='Tiles')
		self.toolbar.InsertTool(6, gui.wx.ToolBar.ID_MOSAIC,
													'atlasmaker',
													shortHelpString='Mosaic')
		self.toolbar.InsertSeparator(7)
		self.toolbar.InsertTool(8, gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh')
		self.toolbar.InsertTool(9, gui.wx.ToolBar.ID_CURRENT_POSITION,
													'currentposition',
													shortHelpString='Show Position')
		self.toolbar.InsertSeparator(10)
		self.toolbar.InsertTool(11, gui.wx.ToolBar.ID_FIND_SQUARES,
													'squarefinder',
													shortHelpString='Find Squares')

		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

		self.imagepanel.addTypeTool('Filtered', display=True, settings=True)
		self.imagepanel.addTypeTool('Thresholded', display=True, settings=True)

	def onNodeInitialized(self):
		gui.wx.ClickTargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTilesButton,
											id=gui.wx.ToolBar.ID_TILES)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMosaicButton,
											id=gui.wx.ToolBar.ID_MOSAIC)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTargetsButton,
											id=gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onShowPositionButton,
											id=gui.wx.ToolBar.ID_CURRENT_POSITION)
		self.toolbar.Bind(wx.EVT_TOOL, self.onFindSquaresButton,
											id=gui.wx.ToolBar.ID_FIND_SQUARES)

		self.Bind(gui.wx.ImageViewer.EVT_SETTINGS, self.onImageSettings)
		# need this enabled for new auto region target finding
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, False)

	def onSubmitTool(self, evt):
		threading.Thread(target=self._onSubmitTool, args=(evt,)).start()

	def _onSubmitTool(self, evt):
		'''overriding so that submit button stays enabled'''
		autofind = False
		if self.node.settings['find section options'] == 'Regions from Centers':
			manualacq = self.getTargetPositions('acquisition')
			if len(manualacq) == 0:
				self.node.autoTargetFinder()
				autofind = True
		if not autofind:
			gui.wx.ClickTargetFinder.Panel.onSubmitTool(self, evt)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

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
		elif evt.name == 'region':
			dialog = RegionSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'acquisition':
			dialog = RasterSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'focus':
			dialog = FocusSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

	def onFindSquaresButton(self, evt):
		#self.node.findSquares()
		threading.Thread(target=self.node.findRegions).start()

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

class MosaicSettingsDialog(gui.wx.Settings.Dialog):
	def __init__(self, parent):
		gui.wx.Settings.Dialog.__init__(self, parent, 'Mosaic Settings')

	def initialize(self):
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

		sb = wx.StaticBox(self, -1, 'Mosaics')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		self.bcreate.Enable(self.node.mosaic.hasTiles())
		self.bsave.Enable(self.node.hasMosaicImage())

		self.Bind(wx.EVT_BUTTON, self.onCreateButton, self.bcreate)
		self.Bind(wx.EVT_BUTTON, self.onSaveButton, self.bsave)

		return [sbsz]

	def onCreateButton(self, evt):
		self.setNodeSettings()
		self.node.createMosaicImage()
		self.bsave.Enable(self.node.hasMosaicImage())

	def onSaveButton(self, evt):
		self.node.publishMosaicImage()

class LPFSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
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

		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class RegionSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szoptions = wx.GridBagSizer(5, 5)

		self.widgets['autofinder'] = wx.CheckBox(self, -1, 'Enable auto targeting')
		szoptions.Add(self.widgets['autofinder'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		choices = ['Limit by Sections','Sections Only','Tissue only','Regions from Centers']
		self.widgets['find section options'] = Choice(self, -1, choices=choices)
		label = wx.StaticText(self, -1, 'Finding Mode')
		szoptions.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['find section options'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Initial Minimum Region Area (% of tile area)')
		self.widgets['min region area'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['min region area'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Maximum Region Area (% of tile area)')
		self.widgets['max region area'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['max region area'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Vertex Evolution Limit')
		self.widgets['ve limit'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['ve limit'], (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Region Min Threshold')
		self.widgets['min threshold'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['min threshold'], (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Section/Background Threshold')
		self.widgets['max threshold'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['max threshold'], (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Max Ellipse Axis Ratio')
		self.widgets['axis ratio'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['axis ratio'], (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szsections = wx.GridBagSizer(6, 6)

		label = wx.StaticText(self, -1, 'Per-Section Area (% of tile area)')
		self.widgets['section area'] = FloatEntry(self, -1, chars=8)
		szsections.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsections.Add(self.widgets['section area'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Maximum Number of Section per Grid')
		self.widgets['max sections'] = IntEntry(self, -1, min=1, chars=4)
		szsections.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsections.Add(self.widgets['max sections'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Per-Section Area Modification Thershold (% of current)')
		self.widgets['adjust section area'] = FloatEntry(self, -1, chars=8)
		szsections.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsections.Add(self.widgets['adjust section area'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szbutton = wx.GridBagSizer(7, 7)
		self.bclear = wx.Button(self, -1, 'Clear Regions')
		szbutton.Add(self.bclear, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton.Add(self.btest, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		return [szoptions, szsections, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.findRegions).start()
		
	def onClearButton(self, evt):
		self.setNodeSettings()
		self.node.clearRegions()

class RasterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szoptions = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Raster Spacing')
		self.widgets['raster spacing'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster spacing'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Raster Angle')
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster angle'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		## auto raster
		self.autobut = wx.Button(self, -1, 'Calculate spacing and angle using the following parameters:')
		self.Bind(wx.EVT_BUTTON, self.onAutoButton, self.autobut)
		szoptions.Add(self.autobut, (2, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Target Preset')
		self.widgets['targetpreset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['targetpreset'].setChoices(presets)
		szoptions.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['targetpreset'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Overlap percent')
		self.widgets['raster overlap'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster overlap'], (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szbutton = wx.GridBagSizer(6, 5)

		self.bclear = wx.Button(self, -1, 'Clear Targets')
		szbutton.Add(self.bclear, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton.Add(self.btest, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [szoptions, szbutton]

	def onAutoButton(self, evt):
		self.setNodeSettings()
		s,a = self.node.autoSpacingAngle()
		self.widgets['raster spacing'].SetValue(s)
		self.widgets['raster angle'].SetValue(a)

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.makeRaster).start()

	def onClearButton(self, evt):
		self.setNodeSettings()
		self.node.clearTargets('acquisition')

class FocusSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.makeFocusTarget).start()


class BlobSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
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

		sb = wx.StaticBox(self, -1, 'Blob Finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
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

