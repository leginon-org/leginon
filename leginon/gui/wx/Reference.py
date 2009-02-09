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
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import threading

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		sb = wx.StaticBox(self, -1, 'Reference Target')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		move_types = self.node.calibration_clients.keys()
		move_types.sort()
		self.widgets['move type'] = Choice(self, -1, choices=move_types)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to the reference target'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before performing request'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.widgets['interval time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
		szintervaltime = wx.GridBagSizer(5, 5)
		szintervaltime.Add(wx.StaticText(self, -1, 'If request performed less than'), (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szintervaltime.Add(self.widgets['interval time'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szintervaltime.Add(wx.StaticText(self, -1, 'seconds ago, ignore request'), (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szmovetype, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpausetime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szintervaltime, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class ReferencePanel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Test')

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onTest,
											id=gui.wx.ToolBar.ID_PLAY)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onTest(self, evt):
		threading.Thread(target=self.node.execute).start()

class MeasureDosePanel(ReferencePanel):
	icon = 'dose'

