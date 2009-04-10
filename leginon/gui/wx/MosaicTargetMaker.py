# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MosaicTargetMaker.py,v $
# $Revision: 1.19 $
# $Name: not supported by cvs2svn $
# $Date: 2004-11-11 19:43:17 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import re
import threading
import wx
from gui.wx.Entry import Entry, FloatEntry
import gui.wx.Node
from gui.wx.Presets import PresetChoice
from gui.wx.Choice import Choice
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.Events

class Panel(gui.wx.Node.Panel):
	icon = 'atlasmaker'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_CALCULATE,
													'calculate',
													shortHelpString='Calculate Atlas')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Publish Atlas')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)

		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(gui.wx.Events.EVT_ATLAS_CALCULATED, self.onAtlasCalculated)
		self.Bind(gui.wx.Events.EVT_ATLAS_PUBLISHED, self.onAtlasPublished)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCalculateAtlasTool,
											id=gui.wx.ToolBar.ID_CALCULATE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPublishAtlasTool,
											id=gui.wx.ToolBar.ID_PLAY)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onAtlasCalculated(self, evt):
		self.toolbar.Enable(True)
		if self.node.publishargs:
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
		else:
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)

	def onAtlasPublished(self, evt):
		self.toolbar.Enable(True)

	def onCalculateAtlasTool(self, evt):
		self.toolbar.Enable(False)
		threading.Thread(target=self.node.calculateAtlas).start()

	def onPublishAtlasTool(self, evt):
		self.toolbar.Enable(False)
		threading.Thread(target=self.node.publishAtlas).start()

	def atlasCalculated(self):
		evt = gui.wx.Events.AtlasCalculatedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def atlasPublished(self):
		evt = gui.wx.Events.AtlasPublishedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Mosaic')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = PresetChoice(self, -1)
		self.widgets['preset'].setChoices(presets)
		self.widgets['label'] = Entry(self, -1, allowspaces=False)
		self.widgets['radius'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['overlap'] = FloatEntry(self, -1, max=100.0, chars=6)
		self.widgets['mosaic center'] = Choice(self, -1, choices=['stage center', 'current position'])

		#szradius = wx.GridBagSizer(5, 5)
		#szradius.Add(self.widgets['radius'], (0, 0), (1, 1),
		#								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		#label = wx.StaticText(self, -1, 'meters')
		#szradius.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szoverlap = wx.GridBagSizer(5, 5)
		szoverlap.Add(self.widgets['overlap'], (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '%')
		szoverlap.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)

		label = wx.StaticText(self, -1, 'Preset:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Label:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['label'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Radius:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(szradius, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['radius'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm')
		sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Overlap:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szoverlap, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['overlap'], (3, 2), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		#label = wx.StaticText(self, -1, '%')
		#sz.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Mosaic Center:')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mosaic center'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)


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

