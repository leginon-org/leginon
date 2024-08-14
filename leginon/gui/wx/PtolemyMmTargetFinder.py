# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx

import leginon.gui.wx.Settings
import leginon.gui.wx.IceTargetFinder
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry

class Panel(leginon.gui.wx.IceTargetFinder.Panel):
	icon = 'holefinder'

	def _LatticeSettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return LatticeSettingsDialog(parent)
	
class LatticeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return LatticeScrolledSettings(self,self.scrsize,False)

	def onShow(self):
		self.panel.imagepanel.showTypeToolDisplays(['Original'])
		
class LatticeScrolledSettings(leginon.gui.wx.IceTargetFinder.LatticeScrolledSettings):
	def __initialize(self):
		sbszcmd = self.createScoreSizer()
		sbszstats = self.createStatsBoxSizer()
		szbutton = self.createTestSizer()
		return [sbszcmd, sbszstats, szbutton]

	def createScoreSizer(self):
		sb = wx.StaticBox(self, -1, 'External hole finding with score')
		sbszcmd = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['score key'] = Entry(self, -1, chars=15)
		self.widgets['score threshold'] = FloatEntry(self, -1,
																		min=-10000.0,
																		allownone=False,
																		chars=8,
																		value='-1000.0')

		szsck = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Script output key to threshold on')
		szsck.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsck.Add(self.widgets['score key'], (1, 0), (1, 2),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szsck.AddGrowableCol(1)

		szt = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min. score to accept')
		szt.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szt.Add(self.widgets['score threshold'], (0, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szt.AddGrowableCol(1)

		sbszcmd.Add(szsck, 1, wx.EXPAND|wx.ALL, 5)
		sbszcmd.Add(szt, 1, wx.EXPAND|wx.ALL, 5)
		return sbszcmd

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.IceTargetFinder.FinalScrolledSettings):
	this = 'ScoreTargetFinder'

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Hole Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

