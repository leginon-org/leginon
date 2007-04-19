# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ClickTargetTransformer.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2007-04-19 18:41:34 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import Entry
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.Choice
import gui.wx.ClickTargetFinder
from gui.wx.Presets import PresetChoice

class Panel(gui.wx.ClickTargetFinder.Panel):
	icon = 'check'
	imagepanelclass = gui.wx.ImageViewer.TargetImagePanel
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

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
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Transform')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Clear')

		self.toolbar.Realize()

		self.addImagePanel()

		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)

		self.imagepanel.addTypeTool('Ancestor', display=True)
		self.imagepanel.selectiontool.setDisplayed('Ancestor', True)

		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)

		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, display=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, display=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('transformed', wx.RED, display=True)
		self.imagepanel.selectiontool.setDisplayed('transformed', True)

		self.imagepanel.setTargets('acquisition', [])
		self.imagepanel.setTargets('focus', [])

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
		self.toolbar.Bind(wx.EVT_TOOL, self.onTransformTool,
											id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onClearTool,
											id=gui.wx.ToolBar.ID_STOP)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		self.setNodeSettings()
		dialog.Destroy()

	def onTransformTool(self, evt):
		self.node.onTransform()

	def onClearTool(self, evt):
		self.node.onClear()

	def onBeginTool(self, evt):
		self.node.onBegin()

	def onNextTool(self, evt):
		self.node.onNext()

	def onPreviousTool(self, evt):
		self.node.onPrevious()

	def onEndTool(self, evt):
		self.node.onEnd()

	def onJumpTool(self, evt):
		self.node.onJump()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		sz = wx.GridBagSizer(5, 10)

		#self.widgets['image directory'] = filebrowse.FileBrowseButton(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		label = wx.StaticText(self, -1, 'Transform From:')
		self.widgets['child preset'] = PresetChoice(self, -1)
		self.widgets['child preset'].setChoices(presets)
		sz.Add(label, (0, 0), (1, 1))
		sz.Add(self.widgets['child preset'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Transform To:')
		self.widgets['ancestor preset'] = PresetChoice(self, -1)
		self.widgets['ancestor preset'].setChoices(presets)
		sz.Add(label, (1, 0), (1, 1))
		sz.Add(self.widgets['ancestor preset'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.widgets['jump filename'] = Entry(self, -1, chars=12)
		label = wx.StaticText(self, -1, 'Image to Jump to:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['jump filename'], (2, 1), (1, 1),
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sb = wx.StaticBox(self, -1, 'Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz,]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'ClickTargetTransferor Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

