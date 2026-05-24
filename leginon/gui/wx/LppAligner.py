# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import sys
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry, EVT_ENTRY
from leginon.gui.wx.Presets import EditPresetOrder
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar

UpdateImagesEventType = wx.NewEventType()

EVT_UPDATE_IMAGES = wx.PyEventBinder(UpdateImagesEventType)

class UpdateImagesEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, UpdateImagesEventType, source.GetId())
		self.SetEventObject(source)

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = leginon.gui.wx.TargetPanel.ClickAndTargetImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_BEAMTILT, 'beamtiltget', shortHelp='XTilt From Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_BEAMTILT, 'beamtiltset', shortHelp='XTilt To Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ALIGN, 'beamtilt',
							 shortHelp='Set on-plane on-node')
		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		color = wx.Colour(255, 128, 0)
		self.imagepanel.addTargetTool('Peak', color)
		self.imagepanel.addTypeTool('Compressed', display=True)

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onXTiltFromScope, id=leginon.gui.wx.ToolBar.ID_GET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onXTiltToScope, id=leginon.gui.wx.ToolBar.ID_SET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSetOnPlaneOnNode, id=leginon.gui.wx.ToolBar.ID_ALIGN)
		leginon.gui.wx.Acquisition.Panel.onNodeInitialized(self)

		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onImageClicked(self, evt):
		threading.Thread(target=self.node.navigate, args=(evt.xy,)).start()

	def onXTiltToScope(self, evt):
		threading.Thread(target=self.node.xTiltToScope).start()

	def onXTiltFromScope(self, evt):
		threading.Thread(target=self.node.xTiltFromScope).start()

	def onSetOnPlaneOnNode(self, evt):
		threading.Thread(target=self.node.guiSetOnPlaneOnNode).start()

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'LPP Alignment')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 5)
		self.widgets['xlpp'] = wx.CheckBox(self, -1,'Crossed Lpp is used')
		sizer.Add(self.widgets['xlpp'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['acquire type'] = Choice(self, -1, choices=self.node.acquire_types)
		label = wx.StaticText(self, -1, 'acquire image(s) for:')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['acquire type'], (1, 1), (1, 1), wx.ALIGN_CENTER)

		# view offset
		self.widgets['global view offset'] = FloatEntry(self, -1, allownone=False, chars=6, value='0.0')
		bt_sizer = wx.GridBagSizer(5, 5)
		bt_sizer.Add(self.widgets['global view offset'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		bt_sizer.Add(wx.StaticText(self, -1, ' (scope api unit)'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Parallel Illumination Offset value in view:')
		sizer.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(bt_sizer, (2, 1), (1, 1), wx.ALIGN_CENTER)
		#
		cmpsizer = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Compressed View:')
		cmpsizer.Add(label, (0, 0), (1, 3), wx.ALIGN_LEFT)
		# compression ratio
		self.widgets['compress ratio'] = IntEntry(self, -1, min=1, allownone=False, chars=4, value='8')
		label = wx.StaticText(self, -1, 'Compression ratio:')
		cmpsizer.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		cmpsizer.Add(self.widgets['compress ratio'], (1, 2), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(cmpsizer, (3, 0), (2, 3), wx.ALIGN_CENTER)

		fitsizer = wx.GridBagSizer(5, 4)
		bordersize = 3

		label = wx.StaticText(self, -1, 'List of XL1 defocus from current value to collect')
		fitsizer.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['phase plate defocus sequence'] = Entry(self, -1, chars=25, style=wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		fitsizer.Add(self.widgets['phase plate defocus sequence'], (1,1),(1,4), wx.EXPAND|wx.ALL, bordersize)
		fitsizer.AddGrowableCol(4)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		label = wx.StaticText(self, -1, 'Align with single or multiple off-plane series fitting with this sequence')
		sbsz.Add(label, 0 , wx.ALL|wx.EXPAND|wx.ALIGN_LEFT, 5)
		sbsz.Add(fitsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		return sizers + [sbsz,]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = SettingsDialog(frame,None)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

