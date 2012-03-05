# WVN 10/5/11 - gui.wx.RasterFCFinder based on gui.wx.RasterFinder
#  (and later re-written to inherit from that class).

import wx
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry
import threading

import leginon.gui.wx.RasterFinder

class Panel(leginon.gui.wx.RasterFinder.Panel):
	def _FinalSettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return FinalSettingsDialog(parent)
	
class OriginalSettingsDialog(leginon.gui.wx.RasterFinder.OriginalSettingsDialog):
	pass

class RasterSettingsDialog(leginon.gui.wx.RasterFinder.RasterSettingsDialog):
	pass

class PolygonSettingsDialog(leginon.gui.wx.RasterFinder.PolygonSettingsDialog):
	pass

class PolygonRasterSettingsDialog(leginon.gui.wx.RasterFinder.PolygonRasterSettingsDialog):
	pass

class FinalSettingsDialog(leginon.gui.wx.RasterFinder.FinalSettingsDialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.RasterFinder.FinalScrolledSettings):
	def FocusFilterSettingsPanel(self):
		# WVN 20/5/07 - new focus stuff
		self.widgets['focus center x'] = FloatEntry(self, -1, chars=4)
		self.widgets['focus center y'] = FloatEntry(self, -1, chars=4)
		self.widgets['focus radius'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus box size'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus min mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus max mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus min std'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus max std'] = FloatEntry(self, -1, chars=8)
		szft = wx.GridBagSizer(5, 5)

		# WVN 20/5/07 new stuff
		label = wx.StaticText(self, -1, 'Center on x,y:')
		szft.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus center x'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus center y'], (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Radius:')
		szft.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus radius'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Box size:')
		szft.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus box size'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Min. mean:')
		szft.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus min mean'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Max. mean:')
		szft.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus max mean'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Min. stdev.:')
		szft.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus min std'], (5, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szft.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus max std'], (6, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		szft.AddGrowableCol(0)

		return szft

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Raster FC Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

