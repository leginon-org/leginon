# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Acquisition.py,v $
# $Revision: 1.33 $
# $Name: not supported by cvs2svn $
# $Date: 2005-04-01 22:35:55 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import gui.wx.Node
import gui.wx.Settings
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY, IntEntry
from gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import wx
import gui.wx.Events
import gui.wx.ImageViewer
import gui.wx.ToolBar
import threading
from gui.wx.ImageBrowser import ImageBrowserPanel

class Panel(gui.wx.Node.Panel):
	icon = 'acquisition'
	imagepanelclass = gui.wx.ImageViewer.ImagePanel
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Process')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PAUSE,
													'pause',
													shortHelpString='Pause')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ABORT,
													'stop',
													shortHelpString='Abort')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SIMULATE_TARGET,
													'simulatetarget',
													shortHelpString='Simulate Target')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP,
													'simulatetargetloop',
													shortHelpString='Simulate Target Loop')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP_STOP,
													'simulatetargetloopstop',
													shortHelpString='Stop Simulate Target Loop')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_BROWSE_IMAGES,
													'imagebrowser',
													shortHelpString='Browse Images')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)
		self.toolbar.Realize()

		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(gui.wx.Events.EVT_PLAYER, self.onPlayer)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPauseTool,
											id=gui.wx.ToolBar.ID_PAUSE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=gui.wx.ToolBar.ID_ABORT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSimulateTargetTool,
											id=gui.wx.ToolBar.ID_SIMULATE_TARGET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSimulateTargetLoopTool,
											id=gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSimulateTargetLoopStopTool,
											id=gui.wx.ToolBar.ID_SIMULATE_TARGET_LOOP_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onBrowseImagesTool,
											id=gui.wx.ToolBar.ID_BROWSE_IMAGES)

	def onSimulateTargetTool(self, evt):
		threading.Thread(target=self.node.simulateTarget).start()

	def onSimulateTargetLoopTool(self, evt):
		threading.Thread(target=self.node.simulateTargetLoop).start()

	def onSimulateTargetLoopStopTool(self, evt):
		threading.Thread(target=self.node.simulateTargetLoopStop).start()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.play()

	def onPauseTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.pause()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)
		self.node.player.stop()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False) 
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, True) 
			self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)

	def onBrowseImagesTool(self, evt):
		frame = wx.Frame(None, -1, 'Image Browser Test')
		frame.node = self.node
		panel = ImageBrowserPanel(frame)
		frame.Fit()
		#self.SetTopWindow(frame)
		frame.Show()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		# move type
		movetypes = self.node.calclients.keys()
		self.widgets['move type'] = Choice(self, -1, choices=movetypes)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to target'),
										(0, 2), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		# preset order
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset order'] = EditPresetOrder(self, -1)
		self.widgets['preset order'].setChoices(presets)

		# misc. checkboxes
#		self.widgets['correct image'] = wx.CheckBox(self, -1, 'Correct image')
#		self.widgets['display image'] = wx.CheckBox(self, -1, 'Display image')
		self.widgets['save image'] = wx.CheckBox(self, -1, 'Save image to database')
		self.widgets['wait for process'] = wx.CheckBox(self, -1,
																				'Wait for a node to process the image')
		self.widgets['wait for rejects'] = wx.CheckBox(self, -1,
																				'Publish and wait for rejected targets')
		self.widgets['adjust for drift'] = wx.CheckBox(self, -1,
																				'Adjust targets for drift')

		# simulate loop settings
		self.widgets['wait time'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['iterations'] = IntEntry(self, -1, min=0.0, chars=6)

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

		szsim = wx.GridBagSizer(5, 5)
		szsim.Add(szwaittime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsim.Add(sziterations, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsim = wx.StaticBox(self, -1, 'Simulated Target Loop')
		sbszsim = wx.StaticBoxSizer(sbsim, wx.VERTICAL)
		sbszsim.Add(szsim, 0, wx.ALIGN_CENTER|wx.ALL, 5)

#		# duplicate target
#		self.widgets['duplicate targets'] = wx.CheckBox(self, -1,
#																				'Duplicate targets with type:')
#		self.widgets['duplicate target type'] = Choice(self, -1,
#																							choices=self.node.duplicatetypes)

#		szduplicate = wx.GridBagSizer(0, 0)
#		szduplicate.Add(self.widgets['duplicate targets'], (0, 0), (1, 1),
#										wx.ALIGN_CENTER_VERTICAL)
#		szduplicate.Add(self.widgets['duplicate target type'], (0, 1), (1, 1),
#										wx.ALIGN_CENTER_VERTICAL)

		# settings sizer
		sz = wx.GridBagSizer(5, 25)
		sz.Add(szmovetype, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpausetime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset order'], (0, 1), (5, 1), wx.ALIGN_CENTER)
#		sz.Add(self.widgets['correct image'], (0, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
#		sz.Add(self.widgets['display image'], (1, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['save image'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['wait for process'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['wait for rejects'], (4, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['adjust for drift'], (5, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sbszsim, (6,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
#		sz.Add(szduplicate, (5, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
#		sz.AddGrowableRow(6)

		sb = wx.StaticBox(self, -1, 'Image Acquisition')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Acquisition Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

