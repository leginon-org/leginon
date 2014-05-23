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
import leginon.gui.wx.Events

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
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Reacquire')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
#		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CHECK_DRIFT,
#													'play',
#													shortHelpString='Check Drift')
#		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT_DRIFT,
#													'stop',
#													shortHelpString='Abort Drift Check')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

		# image
		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Colour(255,0,0))
		self.imagepanel.addTargetTool('Target', wx.Colour(255,128,0))

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
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)

		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onDeclareDriftTool(self, evt):
		self.node.uiDeclareDrift()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.play()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.stop()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Transform Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.szmain = wx.GridBagSizer(5, 5)

		newrow,newcol = self.createMinMagEntry((0,0))
		newrow,newcol = self.createRegistrationSelector((newrow,0))
		newrow,newcol = self.createPauseTimeEntry((newrow,0))

		sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		return [sbsz]

	def createMinMagEntry(self,start_position):
		# define widget
		self.widgets['min mag'] = IntEntry(self, -1, min=1, chars=9)
		# make sizer
		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Minimum Magnification')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['min mag'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		# add to main
		total_length = (1,1)
		self.szmain.Add(szminmag, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createRegistrationSelector(self,start_position):
		# define widget
		regtypes = self.node.getRegistrationTypes()
		self.widgets['registration'] = Choice(self, -1, choices=regtypes)
		# make sizer
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Register images using')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['registration'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szmain.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createPauseTimeEntry(self,start_position):
		# define widget
		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		# make sizer
		sz = wx.GridBagSizer(5, 5)
		sz.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'seconds before reacquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szmain.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

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

