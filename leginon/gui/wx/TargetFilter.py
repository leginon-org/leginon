# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetPanel

class Panel(leginon.gui.wx.Node.Panel):
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
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)
		self.toolbar.Realize()

		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTargetTool('preview', wx.Color(255, 128, 255))
		self.imagepanel.selectiontool.setDisplayed('preview', True)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, numbers=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, numbers=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
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

	def getTargets(self, typename):
		return self.imagepanel.getTargets(typename)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.node.onSubmitTargets()

	def onStopTool(self, evt):
		self.node.onAbortTargets()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

	def onEnablePlayButton(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)

	def enableSubmitTargets(self):
		evt = leginon.gui.wx.Events.EnablePlayButtonEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onOriginalTarget(self,targetcenter):
		pass

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Target Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1,
																			'Bypass Filter')
		self.widgets['user check'] = wx.CheckBox(self, -1,'Verify filter before submitting')
		targettypes = ['acquisition','preview']
		self.widgets['target type'] = wx.Choice(self, -1, choices=targettypes)
		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['target type'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['user check'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		testbut = wx.Button(self, -1, 'test')
		sz.Add(testbut, (2, 0), (1, 2), wx.ALIGN_RIGHT)
		self.Bind(wx.EVT_BUTTON, self.onTestButton, testbut)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.onTest).start()
