# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx
import threading

import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetFilter
from leginon.gui.wx.Entry import IntEntry, FloatEntry
from leginon.gui.wx.Presets import PresetChoice
from leginon.gui.wx.Choice import Choice

class Panel(leginon.gui.wx.TargetFilter.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Submit')
		self.Bind(leginon.gui.wx.Events.EVT_ENABLE_PLAY_BUTTON, self.onEnablePlayButton)
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Stop')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GRID, 'grid', shortHelpString='Default offset')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EXTRACT, 'extractgrid', shortHelpString='Alternative offset')
		self.toolbar.Bind(wx.EVT_TOOL, self.onToggleDefaultOffset, id=leginon.gui.wx.ToolBar.ID_GRID)
		self.toolbar.Bind(wx.EVT_TOOL, self.onToggleAlternateOffset, id=leginon.gui.wx.ToolBar.ID_EXTRACT)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)
		self.toolbar.Realize()

		self.imagepanel = leginon.gui.wx.TargetPanel.EllipseTargetImagePanel(self, -1)
		self.imagepanel.addTargetTool('preview', target=True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)
		self.imagepanel.addTargetTool('acquisition', target=True, area=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', numbers=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('meter')
		self.imagepanel.selectiontool.setDisplayed('meter', True)
		self.imagepanel.addTargetTool('original', numbers=True)
		self.imagepanel.selectiontool.setDisplayed('original', True)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_ELLIPSE_FOUND, self.onEllipseFound, self.imagepanel)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_STOP)
		self.imagepanel.imagevector = self.node.getDefaultImageVector()
		
	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onToggleDefaultOffset(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_GRID, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_EXTRACT, True)
		self.node.setToggleOffset(False)

	def onToggleAlternateOffset(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_GRID, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_EXTRACT, False)
		self.node.setToggleOffset(True)

	def setDefaultOffset(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_GRID, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_EXTRACT, True)
		
	def setAlternateOffset(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_GRID, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_EXTRACT, False)

	def onEllipseFound(self, evt):
		threading.Thread(target=self.node.autoRasterEllipse, args=(evt.params,)).start()

	def onOriginalTarget(self, centers):
		idcevt = leginon.gui.wx.ImagePanelTools.EllipseNewCenterEvent(self.imagepanel, centers)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sbr = wx.StaticBox(self, -1, 'Target Raster')
		sbszr = wx.StaticBoxSizer(sbr, wx.VERTICAL)
		sbcalc = wx.StaticBox(self, -1, 'Spacing/Angle Calculator')
		sbszcalc = wx.StaticBoxSizer(sbcalc, wx.VERTICAL)
		sblimit = wx.StaticBox(self, -1, 'Limiting Ellipse')
		sbszlimit = wx.StaticBoxSizer(sblimit, wx.VERTICAL)

		sz = wx.GridBagSizer(5, 10)

		self.widgets['bypass'] = wx.CheckBox(self, -1,'Bypass Filter')
		targettypes = ['acquisition','preview']
		self.widgets['target type'] = wx.Choice(self, -1, choices=targettypes)
		self.widgets['user check'] = wx.CheckBox(self, -1,'Verify filter before submitting')

		self.widgets['raster spacing'] = FloatEntry(self, -1, min=0, chars=6)
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=8)
		self.widgets['raster offset'] = wx.CheckBox(self, -1,'offset by half an image every other row')
		self.widgets['ellipse angle'] = FloatEntry(self, -1, chars=6)
		self.widgets['ellipse a'] = FloatEntry(self, -1, min=0, chars=6)
		self.widgets['ellipse b'] = FloatEntry(self, -1, min=0, chars=6)

		movetypes = self.node.calclients.keys()
		self.widgets['raster movetype'] = Choice(self, -1, choices=movetypes)
		self.autobut = wx.Button(self, -1, 'Calculate spacing and angle using the following parameters:')
		self.Bind(wx.EVT_BUTTON, self.onAutoButton, self.autobut)
		self.widgets['raster preset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['raster preset'].setChoices(presets)
		self.widgets['raster overlap'] = FloatEntry(self, -1, chars=8)

		## filter
		sztype = wx.GridBagSizer(0,5)
		sztype.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Convoluting Target Type')
		sztype.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztype.Add(self.widgets['target type'], (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztype.Add(self.widgets['user check'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztype.AddGrowableCol(0)
		sz.Add(sztype, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		## auto raster calculator
		szcalc = wx.GridBagSizer(5,5)
		sztype.AddGrowableCol(0)
		szcalc.Add(self.autobut, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Preset for raster')
		szcalc.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalc.Add(self.widgets['raster preset'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Overlap Percent')
		szcalc.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalc.Add(self.widgets['raster overlap'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Move Type')
		szcalc.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalc.Add(self.widgets['raster movetype'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbszcalc.Add(szcalc, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sz.Add(sbszcalc, (1, 0), (1, 2), wx.EXPAND)

		## raster
		szr = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Spacing')
		szr.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szr.Add(self.widgets['raster spacing'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'pixels in parent image')
		szr.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Angle')
		szr.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szr.Add(self.widgets['raster angle'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'degrees')
		szr.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szr.Add(self.widgets['raster offset'], (2, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		## raster limiting ellipse
		szlimit = wx.GridBagSizer(0,5)
		label = wx.StaticText(self, -1, 'Angle to a-axis')
		szlimit.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlimit.Add(self.widgets['ellipse angle'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'degrees')
		szlimit.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, '2 * a-axis')
		szlimit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlimit.Add(self.widgets['ellipse a'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'raster spacings')
		szlimit.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, '2 * b-axis')
		szlimit.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlimit.Add(self.widgets['ellipse b'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'raster spacings')
		szlimit.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbszlimit.Add(szlimit, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		szr.Add(sbszlimit, (3, 0), (1, 3), wx.EXPAND)

		sbszr.Add(szr, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		sz.Add(sbszr, (2, 0), (1, 2), wx.EXPAND)

		#test button
		testbut = wx.Button(self, -1, 'test')
		sz.Add(testbut, (3, 0), (1, 2), wx.ALIGN_RIGHT)
		self.Bind(wx.EVT_BUTTON, self.onTestButton, testbut)

		#sb = wx.StaticBox(self, -1, 'Target Filter')
		#sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		#sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sz]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.onTest).start()

	def onAutoButton(self, evt):
		self.dialog.setNodeSettings()
		s,a, p2 = self.node.autoSpacingAngle()
		self.widgets['raster spacing'].SetValue(s)
		self.widgets['raster angle'].SetValue(a)
		self.panel.imagepanel.imagevector = p2
		self.dialog.setNodeSettings()

