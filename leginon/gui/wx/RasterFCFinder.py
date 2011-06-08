# WVN 10/5/11 - gui.wx.RasterFCFinder based on gui.wx.RasterFinder
#  (and later re-written to inherit from that class).

import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
from gui.wx.Entry import Entry, IntEntry, FloatEntry
import gui.wx.TargetTemplate
import gui.wx.ToolBar
import threading

# WVN 12/8/07
import gui.wx.RasterFinder

class Panel(gui.wx.RasterFinder.Panel):
	def initialize(self):
		# WVN 12/8/07 - This code is identical to RasterFinder.Panel
		# but needs to be repeated, probably for scope reasons
		# (so the code can see the RasterFCFinder "versions" of
		# the classes in RasterFCFinder.py).
		gui.wx.TargetFinder.Panel.initialize(self)


		self.SettingsDialog = gui.wx.TargetFinder.SettingsDialog

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Original', True)
		self.imagepanel.addTargetTool('Raster', wx.Color(0, 255, 255),
																	settings=True)
		# WVN 19/1/08 - change borrowed from Leginon v.1.4.1 RasterFinder
		# self.imagepanel.addTargetTool('Polygon Vertices', wx.Color(255,0,0),
		#															settings=True, target=True)
		self.imagepanel.addTargetTool('Polygon Vertices', wx.Color(255,255,0),
																	settings=True, target=True)
		self.imagepanel.selectiontool.setDisplayed('Polygon Vertices', True)
		self.imagepanel.setTargets('Polygon Vertices', [])
		self.imagepanel.addTargetTool('Polygon Raster', wx.Color(255,128,0),
																	settings=False)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True,
																	settings=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True,
																	settings=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		# WVN 19/1/08 - change borrowed from Leginon v.1.4.1 RasterFinder
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('done', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableRow(1)

		self.Bind(gui.wx.ImageViewer.EVT_SETTINGS, self.onImageSettings)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				if filename:
					self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'Raster':
			dialog = RasterSettingsDialog(self)
		elif evt.name == 'Polygon Vertices':
			dialog = PolygonSettingsDialog(self)
		elif evt.name == 'Polygon Raster':
			dialog = PolygonRasterSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()

class OriginalSettingsDialog(gui.wx.RasterFinder.OriginalSettingsDialog):
	pass

class RasterSettingsDialog(gui.wx.RasterFinder.RasterSettingsDialog):
	pass

class PolygonSettingsDialog(gui.wx.RasterFinder.PolygonSettingsDialog):
	pass

class PolygonRasterSettingsDialog(gui.wx.RasterFinder.PolygonRasterSettingsDialog):
	pass

class FinalSettingsDialog(gui.wx.RasterFinder.FinalSettingsDialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['ice box size'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice thickness'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=8)

		# WVN 20/5/07 - new focus stuff
                self.widgets['focus center x'] = FloatEntry(self, -1, chars=4)
                self.widgets['focus center y'] = FloatEntry(self, -1, chars=4)
		self.widgets['focus radius'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus box size'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus min mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus max mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus min std'] = FloatEntry(self, -1, chars=8)
		self.widgets['focus max std'] = FloatEntry(self, -1, chars=8)

		self.widgets['acquisition convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['acquisition convolve template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['acquisition constant template'] = \
							gui.wx.TargetTemplate.Panel(self, 'Constant Template',
																					targetname='Constant target')

		szice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Box size:')
		szice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice box size'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Reference Intensity:')
		szice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. mean:')
		szice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean:')
		szice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szice.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szice.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Ice Analysis')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszice.Add(szice, 1, wx.EXPAND|wx.ALL, 5)

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

		sb = wx.StaticBox(self, -1, 'Focus Targets')
		sbszft = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszft.Add(szft, 1, wx.EXPAND|wx.ALL, 5)

		szat = wx.GridBagSizer(5, 5)
		szat.Add(self.widgets['acquisition convolve'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		szat.Add(self.widgets['acquisition convolve template'], (1, 0), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szat.Add(self.widgets['acquisition constant template'], (2, 0), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szat.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Acquisition Targets')
		sbszat = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszat.Add(szat, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, 'Analyze Ice')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bice, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		szt = wx.GridBagSizer(5, 5)
		szt.Add(sbszft, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		szt.Add(sbszat, (0, 1), (1, 1), wx.EXPAND|wx.ALL)

		self.Bind(wx.EVT_BUTTON, self.onAnalyzeIceButton, self.bice)

		return [sbszice, szt, szbutton]


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

