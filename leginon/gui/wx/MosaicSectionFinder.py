# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MosaicSectionFinder.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-08 01:10:07 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Settings
import gui.wx.TargetFinder
import gui.wx.TargetPanel
import gui.wx.MosaicClickTargetFinder
import gui.wx.ToolBar
import threading
from gui.wx.Presets import PresetChoice

class Panel(gui.wx.MosaicClickTargetFinder.Panel):
	icon = 'atlastarget'
	def initialize(self):
		gui.wx.MosaicClickTargetFinder.Panel.initialize(self)

	def addOtherTools(self):
#		self.imagepanel = gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTargetTool('region', wx.Color(64,128,255), target=True, settings=True, shape='polygon')
		self.imagepanel.selectiontool.setDisplayed('region', True)

	def onNodeInitialized(self):
		gui.wx.MosaicClickTargetFinder.Panel.onNodeInitialized(self)

		# need this enabled for new auto region target finding
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, True)

	def addOtherBindings(self):
		pass

	def onImageSettings(self, evt):
		gui.wx.MosaicClickTargetFinder.Panel.onImageSettings(self,evt)
		if evt.name == 'region':
			dialog = RegionSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'acquisition':
			dialog = RasterSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()
		elif evt.name == 'focus':
			dialog = FocusSettingsDialog(self)
			dialog.ShowModal()
			dialog.Destroy()

	def onSubmitTool(self, evt):
		'''overriding so that submit button stays enabled'''
		autofind = False
		if self.node.settings['find section options'] == 'Regions from Centers':
			manualacq = self.getTargetPositions('acquisition')
			if len(manualacq) == 0:
				self.node.autoTargetFinder()
				autofind = True
		if not autofind:
			gui.wx.MosaicClickTargetFinder.Panel.onSubmitTool(self, evt)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)


class RegionSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szoptions = wx.GridBagSizer(5, 5)

		self.widgets['autofinder'] = wx.CheckBox(self, -1, 'Enable auto targeting')
		szoptions.Add(self.widgets['autofinder'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		choices = ['Limit by Sections','Sections Only','Tissue only','Regions from Centers']
		self.widgets['find section options'] = Choice(self, -1, choices=choices)
		label = wx.StaticText(self, -1, 'Finding Mode')
		szoptions.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['find section options'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Initial Minimum Region Area (% of tile area)')
		self.widgets['min region area'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['min region area'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Maximum Region Area (% of tile area)')
		self.widgets['max region area'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['max region area'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Vertex Evolution Limit')
		self.widgets['ve limit'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['ve limit'], (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Region Min Threshold')
		self.widgets['min threshold'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['min threshold'], (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Section/Background Threshold')
		self.widgets['max threshold'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['max threshold'], (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Max Ellipse Axis Ratio')
		self.widgets['axis ratio'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['axis ratio'], (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szsections = wx.GridBagSizer(6, 6)

		label = wx.StaticText(self, -1, 'Per-Section Area (% of tile area)')
		self.widgets['section area'] = FloatEntry(self, -1, chars=8)
		szsections.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsections.Add(self.widgets['section area'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Maximum Number of Section per Grid')
		self.widgets['max sections'] = IntEntry(self, -1, min=1, chars=4)
		szsections.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsections.Add(self.widgets['max sections'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Per-Section Area Modification Thershold (% of current)')
		self.widgets['adjust section area'] = FloatEntry(self, -1, chars=8)
		szsections.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsections.Add(self.widgets['adjust section area'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szbutton = wx.GridBagSizer(7, 7)
		self.bclear = wx.Button(self, -1, 'Clear Regions')
		szbutton.Add(self.bclear, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton.Add(self.btest, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		return [szoptions, szsections, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.findRegions).start()
		
	def onClearButton(self, evt):
		self.setNodeSettings()
		self.node.clearRegions()

class RasterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szoptions = wx.GridBagSizer(5, 5)

		## auto raster
		self.widgets['raster preset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['raster preset'].setChoices(presets)
		self.widgets['raster overlap'] = FloatEntry(self, -1, chars=8)
		movetypes = self.node.calclients.keys()
		self.widgets['raster movetype'] = Choice(self, -1, choices=movetypes)
		self.autobut = wx.Button(self, -1, 'Calculate spacing and angle using the following parameters:')

		sb = wx.StaticBox(self, -1, 'Spacing/Angle Calculator')
		sbszauto = wx.StaticBoxSizer(sb, wx.VERTICAL)
		szauto = wx.GridBagSizer(5, 5)
		szauto.Add(self.autobut, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Raster Preset')
		szauto.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster preset'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Overlap percent')
		szauto.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster overlap'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Move Type')
		szauto.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster movetype'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszauto.Add(szauto, 1, wx.EXPAND|wx.ALL,5)

		self.Bind(wx.EVT_BUTTON, self.onAutoButton, self.autobut)
		## end of auto raster

		szoptions.Add(sbszauto, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
			
		label = wx.StaticText(self, -1, 'Raster Spacing')
		self.widgets['raster spacing'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster spacing'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Raster Angle')
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=8)
		szoptions.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szoptions.Add(self.widgets['raster angle'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szbutton = wx.GridBagSizer(5, 5)

		self.bclear = wx.Button(self, -1, 'Clear Targets')
		szbutton.Add(self.bclear, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton.Add(self.btest, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [szoptions, szbutton]

	def onAutoButton(self, evt):
		self.setNodeSettings()
		s,a = self.node.autoSpacingAngle()
		self.widgets['raster spacing'].SetValue(s)
		self.widgets['raster angle'].SetValue(a)

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.makeRaster).start()

	def onClearButton(self, evt):
		self.setNodeSettings()
		self.node.clearTargets('acquisition')

class FocusSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.makeFocusTarget).start()



if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Mosaic Section Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

