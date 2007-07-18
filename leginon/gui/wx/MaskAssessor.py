# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MaskAssessor.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2007-07-18 00:22:42 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import Entry
import gui.wx.Node
import gui.wx.ImageAssessor
import gui.wx.Settings
import gui.wx.ToolBar
import wx.lib.filebrowsebutton as filebrowse
from gui.wx.Choice import Choice

class Panel(gui.wx.ImageAssessor.Panel):
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
		self.toolbar.AddSeparator()

		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play',
													shortHelpString='Save Current Assessment')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP,
													'stop',
													shortHelpString='Reject All Regions')

		self.toolbar.Realize()

		self.addImagePanel()

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

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()


class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

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

		sb = wx.StaticBox(self, -1, 'Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
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

