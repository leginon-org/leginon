# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/FFTMaker.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import gui.wx.FFTMaker
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.ImagePanel

class Panel(gui.wx.FFTMaker.Panel):
	imagepanelclass = gui.wx.ImagePanel.ImagePanel
	icon = 'fftmaker'
	def __init__(self, *args, **kwargs):
		gui.wx.Node.Panel.__init__(self, *args, **kwargs)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()


class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'ACE')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Images in Database')
		sbszdb = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Analyze CTF')
		self.widgets['label'] = Entry(self, -1)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['process'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Find images in this session with label:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['label'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sbszdb.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz,sbszdb]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'FFT Maker Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

