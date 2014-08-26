# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx
import threading
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.MosaicClickTargetFinder
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Presets import PresetChoice

class Panel(leginon.gui.wx.MosaicClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		leginon.gui.wx.MosaicClickTargetFinder.Panel.initialize(self)

	def addOtherTools(self):
		self.imagepanel.addTargetTool('well', wx.Colour(64,128,255), target=True, settings=True, shape='o')

	def onNodeInitialized(self):
		leginon.gui.wx.MosaicClickTargetFinder.Panel.onNodeInitialized(self)

		# need this enabled for new auto region target finding
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, True)
		self.imagepanel.selectiontool.setDisplayed('well', True)

	def addOtherBindings(self):
		pass

	def onImageSettings(self, evt):
		'''
		Handle event of clicking Settings Tools for the image panel.
		'''
		if not self.node.hasValidEMGrid():
			return
		if evt.name == 'well':
			dialog = SpotIDNameSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

	def onSubmitTool(self, evt):
		'''overriding so that submit button stays enabled'''
		autofind = False
		if not autofind:
			leginon.gui.wx.MosaicClickTargetFinder.Panel.onSubmitTool(self, evt)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SUBMIT, True)

class SpotIDNameSettingsDialog(leginon.gui.wx.Settings.Dialog):

	def onSet(self,evt):
		rasterspots = self.scr_dialog.getSpotGridValues()
		# validate values
		is_valid = self.node.validateSpotRegister(rasterspots)
		if not is_valid:
			# do not save nor exit
			return
		args = (rasterspots,)
		t = threading.Thread(target=self.node.guiSetSpotTargets,args=args)
		t.start()
		super(SpotIDNameSettingsDialog,self).onSet(evt)

	def initialize(self):
		self.scr_dialog = SpotIDNameScrolledSettings(self,self.scrsize,False)
		return self.scr_dialog

class SpotIDNameScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		#szoptions = wx.GridBagSizer(5, 5)

		#self.widgets['autofinder'] = wx.CheckBox(self, -1, 'Enable auto targeting')
		#szoptions.Add(self.widgets['autofinder'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		gridformat = self.node.getGridFormat()
		szedit = self.addSpotGrid(gridformat)

		szbutton = wx.GridBagSizer(7, 7)
		self.bclear = wx.Button(self, -1, 'Clear')
		szbutton.Add(self.bclear, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton.Add(self.btest, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		# settings sizer
		sz = wx.GridBagSizer(5, 10)
		#sz.Add(szoptions, (0, 0), (1, 2))
		sz.Add(szedit, (1, 0), (10, 10))
		sz.Add(szbutton, (11, 0), (1, 2))
		return [sz]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		mythread = threading.Thread(target=self.node.findSpotIDNames)
		mythread.start()
		# wait for thread to finish before setting values
		mythread.join()
		self.setSpotGridValues()
		
	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		t = threading.Thread(target=self.node.clearSpotTargets)
		t.start()
		# wait for thread to finish before setting values
		t.join()
		self.setSpotGridValues()

	def addSpotGrid(self,gridformat):
		'''
		SpotGrid is an editable wx.grid.Grid displaying the spots
		registered at each gridformat raster cell.
		'''
		import wx.grid
		self.grid = wx.grid.Grid(self, -1)
		self.grid.SetDefaultColSize(40)
		self.grid.CreateGrid(gridformat['rows'], gridformat['cols'])

		for coord in gridformat['skips']:
			self.grid.SetCellBackgroundColour(coord[0]-1,coord[1]-1,wx.Colour(100,100,0))
		try:
			# only available for newer wxpython
			self.grid.HideColLabels()
		except:
			pass
		self.setSpotGridValues()

		return self.grid

	def setSpotGridValues(self):
		'''
		Set values in the spotgrid based on current node values.
		'''
		# clear the grid first so that those are now blank
		# would not left with the old value
		self.grid.ClearGrid()
		spotregister = self.node.guiGetSpotRegister()
		for key in spotregister:
			r = key[0]
			c = key[1]
			self.grid.SetCellValue(r,c,spotregister[key])
		self.grid.ForceRefresh()

	def getSpotGridValues(self):
		cols = self.grid.GetNumberCols()
		rows = self.grid.GetNumberRows()
		spotregister = {}
		for c in range(cols):
			for r in range(rows):
				spotregister[(r,c)] = self.grid.GetCellValue(r,c)
		return spotregister

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Section Target Finder Test')
			dialog = Panel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

