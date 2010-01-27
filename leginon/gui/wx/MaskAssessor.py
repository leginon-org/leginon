# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx
import wx.lib.filebrowsebutton as filebrowse

from leginon.gui.wx.Entry import Entry
import leginon.gui.wx.Node
import leginon.gui.wx.ImageAssessor
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Choice import Choice

class Panel(leginon.gui.wx.ImageAssessor.Panel):
	icon = 'check'
	imagepanelclass = leginon.gui.wx.TargetPanel.TargetImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_BEGIN,
													'begin',
													shortHelpString='To Beginning')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PREVIOUS,
													'up',
													shortHelpString='Previous')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_NEXT,
													'down',
													shortHelpString='Next')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_END,
													'end',
													shortHelpString='To End')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET,
													'simulatetarget',
													shortHelpString='Jump')
		self.toolbar.AddSeparator()

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Save Current Assessment')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Reject All Regions')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE,
													'send_queue_out',
													shortHelpString='Keep All')


		self.addImagePanel()

		self.toolbar.Realize()

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onBeginTool,
											id=leginon.gui.wx.ToolBar.ID_BEGIN)
		self.toolbar.Bind(wx.EVT_TOOL, self.onNextTool,
											id=leginon.gui.wx.ToolBar.ID_NEXT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPreviousTool,
											id=leginon.gui.wx.ToolBar.ID_PREVIOUS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEndTool,
											id=leginon.gui.wx.ToolBar.ID_END)
		self.toolbar.Bind(wx.EVT_TOOL, self.onJumpTool,
											id=leginon.gui.wx.ToolBar.ID_SIMULATE_TARGET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onKeepTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRejectTool,
											id=leginon.gui.wx.ToolBar.ID_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onKeepAllTool,
											id=leginon.gui.wx.ToolBar.ID_SUBMIT_QUEUE)
		
	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)

		self.imagepanel.addTypeTool('Mask', display=True)
		self.imagepanel.selectiontool.setDisplayed('Mask', True)

		self.imagepanel.addTargetTool('Regions', wx.Color(0, 255, 255), target=True, display=True)
		self.imagepanel.selectiontool.setDisplayed('Regions', True)
		self.imagepanel.setTargets('Regions', [])

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onKeepAllTool(self, evt):
		self.node.onKeepAll()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.GridBagSizer(5, 10)


		label = wx.StaticText(self, -1, 'Mask Run Name:')
		masknames = self.node.getMaskRunNames()
		self.widgets['mask run'] = Choice(self, -1, choices=masknames)
		sz.Add(label, (0, 0), (1, 1))
		sz.Add(self.widgets['mask run'], (0, 1), (1, 1))

		label = wx.StaticText(self, -1, 'Assessor Run Name:')
		self.widgets['run'] = Entry(self, -1)
		sz.Add(label, (1, 1), (1, 1))
		sz.Add(self.widgets['run'], (1, 2), (1, 1))

		self.widgets['continueon'] = wx.CheckBox(self, -1,'Continue')
		sz.Add(self.widgets['continueon'], (2, 0), (1, 1))

		self.widgets['jump filename'] = Entry(self, -1, chars=12)
		label = wx.StaticText(self, -1, 'Image to Jump to:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['jump filename'], (3, 1), (1, 1),
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz,]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'MaskAssessor Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

