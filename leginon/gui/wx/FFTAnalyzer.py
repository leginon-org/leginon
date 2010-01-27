# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx

from pyami import plot

from leginon.gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import leginon.gui.wx.FFTMaker
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.ImagePanel

class Panel(leginon.gui.wx.FFTMaker.Panel):
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	plotpanelclass = plot.PlotPanel
	icon = 'fftmaker'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.FFTMaker.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
			'refresh', shortHelpString='Refresh')

		#self.szmain.Layout()

	def addImagePanel(self):
		sz = wx.GridBagSizer(5,5)
		# image
		self.imagepanel = self.imagepanelclass(self, -1,imagesize=(320,320))
		self.imagepanel.scale = (1/2.0,1/2.0)
		print dir(self.imagepanel.toolsizer)
		self.imagepanel.scaleImage()
		self.imagepanel.addTypeTool('Power', display=True)
		self.imagepanel.selectiontool.setDisplayed('Power', True)
		sz.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 3)
		# plot
		self.plotpanel = self.plotpanelclass(self, -1)
		sz.Add(self.plotpanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)
		self.szmain.Add(sz, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def setPlot(self,*args):
		self.plotpanel.plot(*args)
		self.plotpanel.Refresh()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTool,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onRefreshTool(self, evt):
		self.plotpanel.clear()
		self.plotpanel.Refresh()

	def onPlayTool(self, evt):
		self.node.onStartPostProcess()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, True)

	def onStopTool(self, evt):
		self.node.onStopPostProcess()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_STOP, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

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

