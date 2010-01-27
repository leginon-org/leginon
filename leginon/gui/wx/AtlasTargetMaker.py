# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx

from leginon.gui.wx.Entry import Entry, FloatEntry
import leginon.gui.wx.Node
from leginon.gui.wx.Presets import PresetChoice
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Events

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'atlasmaker'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CALCULATE,
													'calculate',
													shortHelpString='Calculate Atlas')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Publish Atlas')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)

		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(leginon.gui.wx.Events.EVT_ATLAS_CALCULATED, self.onAtlasCalculated)
		self.Bind(leginon.gui.wx.Events.EVT_ATLAS_PUBLISHED, self.onAtlasPublished)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCalculateAtlasTool,
											id=leginon.gui.wx.ToolBar.ID_CALCULATE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPublishAtlasTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onAtlasCalculated(self, evt):
		self.toolbar.Enable(True)
		if self.node.publishargs:
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		else:
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)

	def onAtlasPublished(self, evt):
		self.toolbar.Enable(True)

	def onCalculateAtlasTool(self, evt):
		self.toolbar.Enable(False)
		threading.Thread(target=self.node.calculateAtlas).start()

	def onPublishAtlasTool(self, evt):
		self.toolbar.Enable(False)
		threading.Thread(target=self.node.publishAtlas).start()

	def atlasCalculated(self):
		evt = leginon.gui.wx.Events.AtlasCalculatedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def atlasPublished(self):
		evt = leginon.gui.wx.Events.AtlasPublishedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Atlas')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = PresetChoice(self, -1)
		self.widgets['preset'].setChoices(presets)
		#self.widgets['label'] = Entry(self, -1)
		self.widgets['center'] = {}
		self.widgets['center']['x'] = FloatEntry(self, -1, chars=6)
		self.widgets['center']['y'] = FloatEntry(self, -1, chars=6)
		self.widgets['size'] = {}
		self.widgets['size']['x'] = FloatEntry(self, -1, chars=6)
		self.widgets['size']['y'] = FloatEntry(self, -1, chars=6)

		gsz = wx.GridBagSizer(5, 10)
		label = wx.StaticText(self, -1, 'x')
		gsz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'y')
		gsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Center:')
		gsz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		gsz.Add(self.widgets['center']['x'], (1, 1), (1, 1), wx.ALIGN_CENTER)
		gsz.Add(self.widgets['center']['y'], (1, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'm')
		gsz.Add(label, (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Size:')
		gsz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		gsz.Add(self.widgets['size']['x'], (2, 1), (1, 1), wx.ALIGN_CENTER)
		gsz.Add(self.widgets['size']['y'], (2, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'm')
		gsz.Add(label, (2, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		gsz.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 10)

		label = wx.StaticText(self, -1, 'Preset:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		#label = wx.StaticText(self, -1, 'Label:')
		#sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(self.widgets['label'], (1, 1), (1, 1),
		#				wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		#sz.Add(gsz, (2, 0), (1, 3), wx.ALIGN_CENTER|wx.EXPAND)
		sz.Add(gsz, (1, 0), (1, 3), wx.ALIGN_CENTER|wx.EXPAND)

		sz.AddGrowableCol(1)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Target Maker Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

