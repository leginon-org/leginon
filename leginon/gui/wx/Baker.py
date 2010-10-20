import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
from leginon.gui.wx.Presets import PresetChoice
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		sb = wx.StaticBox(self, -1, 'Baker')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		aftersb = wx.StaticBox(self, -1, 'After baking')
		aftersbsz = wx.StaticBoxSizer(aftersb, wx.VERTICAL)
		aftersz = wx.BoxSizer(wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Baking')
		self.widgets['preset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'].setChoices(presets)
		self.widgets['total bake time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		self.widgets['manual aperture'] = wx.CheckBox(self, -1, 'Wait for user before continue to next task')
		self.widgets['emission off'] = wx.CheckBox(self, -1, 'Turn emission off when done')
		sz_bypass = wx.GridBagSizer(0, 0)
		sz_bypass.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_preset = wx.GridBagSizer(5, 5)
		sz_preset.Add(wx.StaticText(self, -1, 'Use'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_preset.Add(self.widgets['preset'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_preset.Add(wx.StaticText(self, -1, 'to set the scope parameters'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_time = wx.GridBagSizer(5, 5)
		sz_time.Add(wx.StaticText(self, -1, 'Take'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_time.Add(self.widgets['total bake time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz_time.Add(wx.StaticText(self, -1, 'seconds to move to the saved position'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		aftersz.Add(self.widgets['manual aperture'])
		aftersz.Add(self.widgets['emission off'])
		aftersbsz.Add(aftersz, wx.ALIGN_CENTER|wx.ALL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sz_bypass, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_preset, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sz_time, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(aftersbsz, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'bread'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_XY, 'xy',
													shortHelpString='Save stage X,Y as end point')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Start')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlay,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSaveXY,
											id=leginon.gui.wx.ToolBar.ID_RESET_XY)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlay(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		threading.Thread(target=self.node.onPlay).start()

	def onPlayer(self, evt):
		print 'got evt',evt
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

	def onStopTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.stop()

	def onDone(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

	def onSaveXY(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.node.fromScope()
