# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx
import threading

from leginon.gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetPanel

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'fftmaker'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Process')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Stop')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.Realize()

		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableRow(1)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def addImagePanel(self):
		# image
		self.imagepanel = leginon.gui.wx.TargetPanel.FFTTargetImagePanel(self, -1,imagesize=(512,512))
		self.imagepanel.addTypeTool('Power', display=True)
		self.imagepanel.selectiontool.setDisplayed('Power', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_STOP)
		self.addImagePanel()
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_ELLIPSE_FOUND, self.onEllipseFound, self.imagepanel)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.node.onStartPostProcess()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)

	def onStopTool(self, evt):
		self.node.onStopPostProcess()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

	def onNewPixelSize(self, pixelsize,center,hightension):
		idcevt = leginon.gui.wx.ImagePanelTools.ImageNewPixelSizeEvent(self.imagepanel, pixelsize,center,hightension)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
		self.center = center

	def onEllipseFound(self, evt):
		centers = [(self.center['y'],self.center['x']),]
		idcevt = leginon.gui.wx.ImagePanelTools.EllipseNewCenterEvent(self.imagepanel, centers)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
		threading.Thread(target=self.node.estimateAstigmation, args=(evt.params,)).start()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'FFT')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Images in Database')
		sbszdb = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Calculate FFT')
		self.widgets['save'] = wx.CheckBox(self, -1,
																			'Save to the database')
		self.widgets['reduced'] = wx.CheckBox(self, -1,
																			'Truncate FFT to center 1024 pixels')
		self.widgets['mask radius'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['label'] = Entry(self, -1)

		szmaskradius = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mask radius:')
		szmaskradius.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmaskradius.Add(self.widgets['mask radius'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of image width')
		szmaskradius.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['reduced'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['process'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['save'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szmaskradius, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Find images in this session with label:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['label'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sbszdb.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz, sbszdb]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'FFT Maker Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

