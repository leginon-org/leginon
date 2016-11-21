import wx
import threading

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Reference

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Reference.ScrolledSettings):
	def createIntervalEntry(self, start_position):
		return self.createIntervalTimeEntry(start_position)

	def createIntervalTimeEntry(self, start_position):
		self.widgets['interval time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=8, value='0.0')
		szintervaltime = wx.GridBagSizer(5, 5)
		szintervaltime.Add(wx.StaticText(self, -1, 'If request performed less than'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szintervaltime.Add(self.widgets['interval time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szintervaltime.Add(wx.StaticText(self, -1, 'seconds ago, ignore request'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(szintervaltime, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return start_position[0]+1,start_position[1]+1

class ReferenceTimerPanel(leginon.gui.wx.Reference.ReferencePanel):
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Reference.ReferencePanel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EXTRACT, 'clock', shortHelpString='Reset Timer')

	def onNodeInitialized(self):
		leginon.gui.wx.Reference.ReferencePanel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetTimerTool,
											id=leginon.gui.wx.ToolBar.ID_EXTRACT)

	def _SettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return SettingsDialog(parent)
	
	def onResetTimerTool(self, evt):
		threading.Thread(target=self.node.uiResetTimer).start()


class MeasureDosePanel(ReferenceTimerPanel):
	icon = 'dose'

