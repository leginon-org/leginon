# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ClickMaskMaker.py,v $
# $Revision: 1.6 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-18 17:15:25 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import Entry,IntEntry
import gui.wx.Node
import gui.wx.ImageAssessor
import gui.wx.TargetPanel
import gui.wx.Settings
import gui.wx.ToolBar
import wx.lib.filebrowsebutton as filebrowse
import gui.wx.Choice

class Panel(gui.wx.ImageAssessor.Panel):
	icon = 'check'
	imagepanelclass = gui.wx.TargetPanel.TargetImagePanel
	def __init__(self, *args, **kwargs):
		gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()

		self.toolbar.AddTool(gui.wx.ToolBar.ID_BEGIN,
													'begin',
													shortHelpString='To Beginning')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PREVIOUS,
													'up',
													shortHelpString='Previous')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_NEXT,
													'down',
													shortHelpString='Next')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_END,
													'end',
													shortHelpString='To End')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SIMULATE_TARGET,
													'simulatetarget',
													shortHelpString='Jump')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLUS, 						'plus',
													shortHelpString='Add Region')
		self.toolbar.AddSeparator()

		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Save')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Clear')

		self.toolbar.Realize()

		self.addImagePanel()

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()
		

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

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onBeginTool,
											id=gui.wx.ToolBar.ID_BEGIN)
		self.toolbar.Bind(wx.EVT_TOOL, self.onNextTool,
											id=gui.wx.ToolBar.ID_NEXT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPreviousTool,
											id=gui.wx.ToolBar.ID_PREVIOUS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEndTool,
											id=gui.wx.ToolBar.ID_END)
		self.toolbar.Bind(wx.EVT_TOOL, self.onJumpTool,
											id=gui.wx.ToolBar.ID_SIMULATE_TARGET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAddTool,
											id=gui.wx.ToolBar.ID_PLUS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onKeepTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRejectTool,
											id=gui.wx.ToolBar.ID_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onAddTool(self, evt):
		self.node.onAdd()


class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.GridBagSizer(5, 10)


		label = wx.StaticText(self, -1, 'Preset Name:')
		self.widgets['preset'] = Entry(self, -1)
		sz.Add(label, (0, 0), (1, 1))
		sz.Add(self.widgets['preset'], (0, 1), (1, 1))

		label = wx.StaticText(self, -1, 'Binning:')
		self.widgets['bin'] = IntEntry(self, -1, min=1, chars=4)
		sz.Add(label, (1, 0), (1, 1))
		sz.Add(self.widgets['bin'], (1, 1), (1, 1))

		label = wx.StaticText(self, -1, 'Mask Run Name:')
		self.widgets['run'] = Entry(self, -1)
		sz.Add(label, (2, 0), (1, 1))
		sz.Add(self.widgets['run'], (2, 1), (1, 1))

		self.widgets['continueon'] = wx.CheckBox(self, -1,'empty-mask-overwrite Not Allowed')
		sz.Add(self.widgets['continueon'], (3, 0), (1, 1))

		label = wx.StaticText(self, -1, 'Mask Run Path:')
		self.widgets['path'] = Entry(self, -1)
		sz.Add(label, (4, 0), (1, 1))
		sz.Add(self.widgets['path'], (4, 1), (1, 1))

		self.widgets['jump filename'] = Entry(self, -1, chars=12)
		label = wx.StaticText(self, -1, 'Image to Jump to:')
		sz.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['jump filename'], (5, 1), (1, 1),
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

