import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry, IntEntry
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Reference

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Reference.ScrolledSettings):
	def createIntervalEntry(self, start_position):
		return self.createIntervalCountEntry(start_position)

	def createIntervalCountEntry(self, start_position):
		self.widgets['interval count'] = IntEntry(self, -1, min=0, allownone=False, chars=8, value='1')
		szintervalcount = wx.GridBagSizer(5, 5)
		szintervalcount.Add(wx.StaticText(self, -1, 'If fewer than'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szintervalcount.Add(self.widgets['interval count'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szintervalcount.Add(wx.StaticText(self, -1, 'images are sent here before, ignore request'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(szintervalcount, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

class ReferenceCounterPanel(leginon.gui.wx.Reference.ReferencePanel):
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Reference.ReferencePanel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EXTRACT, 'clock', shortHelpString='Reset Counter')

	def onNodeInitialized(self):
		leginon.gui.wx.Reference.ReferencePanel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetCounterTool,
											id=leginon.gui.wx.ToolBar.ID_EXTRACT)

	def _SettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return SettingsDialog(parent)
	
	def onResetCounterTool(self, evt):
		threading.Thread(target=self.node.uiResetCounter).start()


