import wx
from gui.wx.Entry import IntEntry, FloatEntry, EVT_ENTRY
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar

class Panel(gui.wx.Node.Panel):
	icon = 'sine'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Process')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Stop')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.Realize()

		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=gui.wx.ToolBar.ID_STOP)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.node.uiStartLoop()
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, True)

	def onStopTool(self, evt):
		self.node.uiStopLoop()
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)

	def onLoopDone(self):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['wait time'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['iterations'] = IntEntry(self, -1, min=0.0, chars=6)
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.session)

		szwaittime = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Wait Time:')
		szwaittime.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szwaittime.Add(self.widgets['wait time'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		szwaittime.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sziterations = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Iterations:')
		sziterations.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sziterations.Add(self.widgets['iterations'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szwaittime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sziterations, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Loop')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]
