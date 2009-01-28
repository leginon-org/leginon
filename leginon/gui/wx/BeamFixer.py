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

class BeamFixerPanel(gui.wx.Reference.ReferencePanel, gui.wx.Instrument.SelectionMixin):
	imagepanelclass = gui.wx.ImagePanel.ImagePanel
	def __init__(self, parent, name):
		gui.wx.Reference.ReferencePanel.__init__(self, parent, -1)
		gui.wx.Instrument.SelectionMixin.__init__(self)
		self.addImagePanel()
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		gui.wx.Reference.ReferencePanel.onNodeInitialized(self)
		gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)

	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.Reference.SettingsDialog):
	def initialize(self):
		refsizers = gui.wx.Reference.SettingsDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Beam Fixer')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		# override preset
		overridebox = wx.StaticBox(self, -1, "Override Preset")
		overridesz = wx.StaticBoxSizer(overridebox, wx.VERTICAL)
		self.widgets['override preset'] = wx.CheckBox(self, -1,
																								'Override Preset')
		self.widgets['instruments'] = gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.GetParent().setInstrumentSelection(self.widgets['instruments'])
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['override preset'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['instruments'], (1, 0), (1, 1), wx.EXPAND)
		sz.Add(self.widgets['camera settings'], (2, 0), (1, 1), wx.EXPAND)
		overridesz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sbsz.Add(overridesz)

		return refsizers + [sbsz]
