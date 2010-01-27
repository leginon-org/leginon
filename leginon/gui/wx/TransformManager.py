# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx

from leginon.gui.wx.Entry import FloatEntry, IntEntry
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.Camera
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.Instrument

class Panel(leginon.gui.wx.Node.Panel, leginon.gui.wx.Instrument.SelectionMixin):
	icon = 'driftmanager'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

		# settings
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
#		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE_DRIFT,
#													'ruler',
#													shortHelpString='Measure Drift')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_DECLARE_DRIFT,
													'declare',
													shortHelpString='Declare Drift')
#		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CHECK_DRIFT,
#													'play',
#													shortHelpString='Check Drift')
#		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT_DRIFT,
#													'stop',
#													shortHelpString='Abort Drift Check')
		self.toolbar.Realize()

		# image
		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255,0,0))
		self.imagepanel.addTargetTool('Target', wx.Color(255,128,0))

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onDeclareDriftTool,
											id=leginon.gui.wx.ToolBar.ID_DECLARE_DRIFT)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onDeclareDriftTool(self, evt):
		self.node.uiDeclareDrift()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Transform Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['min mag'] = IntEntry(self, -1, min=1, chars=9)
		#self.instrumentselection = leginon.gui.wx.Instrument.SelectionPanel(self, passive=True)
		#self.panel.setInstrumentSelection(self.instrumentselection)
		#self.widgets['camera settings'] = leginon.gui.wx.Camera.CameraPanel(self)
		#self.widgets['camera settings'].setSize(self.node.instrument.camerasize)

		regtypes = self.node.getRegistrationTypes()
		self.widgets['registration'] = Choice(self, -1, choices=regtypes)

		szminmag = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Minimum Magnification')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['min mag'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Register images using')
		szminmag.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['registration'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(szminmag, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(self.instrumentselection, (1, 0), (1, 1), wx.EXPAND)
		#sz.Add(self.widgets['camera settings'], (2, 0), (1, 1), wx.EXPAND)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Transform Manager Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

