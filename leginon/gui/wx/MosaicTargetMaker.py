# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import re
import threading
import wx

from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry
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
		dialog = SettingsDialog(self, show_basic=True)
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
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Image Acquisition')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.szmain = wx.GridBagSizer(5, 5)

		if self.show_basic:
			self.addBasicSettings()
		else:
			self.addSettings()
		sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		return [sbsz]

	def addBasicSettings(self):
		newrow,newcol = self.createPresetSelector((0,0))
		newrow,newcol = self.createAlphaTiltEntry((newrow,0))

	def createPresetSelector(self, start_position):
		sz = wx.GridBagSizer(5, 10)
		# preset
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = PresetChoice(self, -1)
		self.widgets['preset'].setChoices(presets)
		label = wx.StaticText(self, -1, 'Preset:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		# atlas label
		self.widgets['label'] = Entry(self, -1, allowspaces=False)
		label = wx.StaticText(self, -1, 'Label:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['label'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		# radius
		self.widgets['radius'] = FloatEntry(self, -1, min=0.0, chars=6)
		label = wx.StaticText(self, -1, 'Radius:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(szradius, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['radius'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm')
		sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		'''
		# atlas max size
		self.widgets['max size'] = IntEntry(self, -1)
		label = wx.StaticText(self, -1, 'Max size:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max size'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		# atlas max size
		self.widgets['max targets'] = IntEntry(self, -1)
		label = wx.StaticText(self, -1, 'Max targets:')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max targets'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		'''

		# add to main
		total_length = (3,2)
		self.szmain.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createAlphaTiltEntry(self,start_position):
		# define widget
		self.widgets['alpha tilt'] = FloatEntry(self, -1, min=-80.0, allownone=True, max=80.0, chars=5, value='0.0')
		# make sizer
		sz = wx.GridBagSizer(5, 5)
		sz.Add(wx.StaticText(self, -1, 'Collect atlas at'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['alpha tilt'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'degree tilt'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szmain.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def addSettings(self):
		newrow,newcol = self.createPresetSelector((0,0))
		newrow,newcol = self.createAlphaTiltEntry((newrow,0))
		newrow,newcol = self.createAdvancedSizer((newrow,0))

	def createAdvancedSizer(self, start_position):
		self.widgets['max size'] = IntEntry(self, -1, chars=6)
		self.widgets['max targets'] = IntEntry(self, -1, chars=6)
		self.widgets['overlap'] = FloatEntry(self, -1, max=100.0, chars=6)
		self.widgets['mosaic center'] = Choice(self, -1, choices=['stage center', 'current position'])
		self.widgets['ignore request'] = wx.CheckBox(self, -1, 'Ignore Request to Make Targets from Others')
		self.widgets['use spiral path'] = wx.CheckBox(self, -1, 'Spiral from center')

		#szradius = wx.GridBagSizer(5, 5)
		#szradius.Add(self.widgets['radius'], (0, 0), (1, 1),
		#								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		#label = wx.StaticText(self, -1, 'meters')
		#szradius.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)
		label = wx.StaticText(self, -1, 'Max size:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max size'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Max targets:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max targets'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Overlap:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['overlap'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '%')
		sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Mosaic Center:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mosaic center'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['use spiral path'], (4, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		sz.Add(self.widgets['ignore request'], (5, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(1)
		# add to main
		total_length = (1,1)
		self.szmain.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

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

