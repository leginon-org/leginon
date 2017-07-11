import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.ReferenceTimer
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar


class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.ReferenceTimer.ScrolledSettings):
	'''
	def initialize(self):
		sb = wx.StaticBox(self, -1, 'Reference Target')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.sz = wx.GridBagSizer(5, 5)

		position = self.createBypassCheckBox((0, 0))
		position = self.createMoveTypeChoice((position[0],0))
		position = self.createPauseTimeEntry((position[0],0))
		position = self.createIntervalTimeEntry((position[0],0))

		sbsz.Add(self.sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]
	'''
	def insertSizersToSZ(self):
		super(ScrolledSettings, self).insertSizersToSZ()

class ScreenCurrentLoggerPanel(leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel):
	def _SettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return SettingsDialog(parent)
	
	def onNodeInitialized(self):
		super(ScreenCurrentLoggerPanel,self).onNodeInitialized()

	def onTest(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		threading.Thread(target=self.node.onTest).start()
