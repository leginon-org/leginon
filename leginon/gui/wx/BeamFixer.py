# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Reference.py,v $
# $Revision: 1.4 $
# $Name: not supported by cvs2svn $
# $Date: 2006-08-22 19:22:33 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry
import gui.wx.Reference
import gui.wx.Settings
import gui.wx.ToolBar

class BeamFixerPanel(gui.wx.Reference.ReferencePanel):
	imagepanelclass = gui.wx.ImagePanel.ImagePanel
	def __init__(self, parent, name):
		gui.wx.Reference.ReferencePanel.__init__(self, parent, -1)
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
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onSettingsTool(self, evt):
		dialog = gui.wx.Reference.SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

