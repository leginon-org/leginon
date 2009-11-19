# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/RasterFinder.py,v $
# $Revision: 1.29 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-27 23:12:21 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.TargetPanel
import gui.wx.ImagePanelTools
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
from gui.wx.Entry import Entry, IntEntry, FloatEntry
from gui.wx.Presets import PresetChoice
from gui.wx.Choice import Choice
import gui.wx.TargetTemplate
import gui.wx.ToolBar
import threading

class Panel(gui.wx.TargetFinder.Panel):
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)
#		self.SettingsDialog = gui.wx.TargetFinder.SettingsDialog
		self.SettingsDialog = SettingsDialog

		self.imagepanel = gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Original', True)
		self.imagepanel.addTargetTool('Raster', wx.Color(0, 255, 255), settings=True)
		
		self.imagepanel.addTargetTool('Polygon Vertices', wx.Color(255,255,0), settings=True, target=True, shape='polygon')
		self.imagepanel.selectiontool.setDisplayed('Polygon Vertices', True)
		self.imagepanel.setTargets('Polygon Vertices', [])
	

	
		self.imagepanel.addTargetTool('Polygon Raster', wx.Color(255,128,0))
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableRow(1)

		self.Bind(gui.wx.ImagePanelTools.EVT_SETTINGS, self.onImageSettings)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'Raster':
			dialog = RasterSettingsDialog(self)
		elif evt.name == 'Polygon Vertices':
			dialog = PolygonSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()

class OriginalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return OriginalScrolledSettings(self,self.scrsize,False)

class OriginalScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Original Image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['image filename'] = filebrowse.FileBrowseButton(self, -1)
		self.widgets['image filename'].SetMinSize((500,50))
		self.dialog.bok.SetLabel('&Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class RasterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return RasterScrolledSettings(self,self.scrsize,False)

class RasterScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Raster')
		sbszraster = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Spacing/Angle Calculator')
		sbszauto = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['raster spacing'] = IntEntry(self, -1, chars=4, min=1)
		self.widgets['raster spacing asymm'] = IntEntry(self, -1, chars=4)
		self.widgets['raster limit'] = IntEntry(self, -1, chars=4, min=1)
		self.widgets['raster limit asymm'] = IntEntry(self, -1, chars=4)
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=4)
		self.widgets['raster center on image'] = wx.CheckBox(self, -1, 'Center on image')
		self.widgets['raster center x'] = IntEntry(self, -1, chars=4)
		self.widgets['raster center y'] = IntEntry(self, -1, chars=4)
		self.widgets['raster symmetric'] = wx.CheckBox(self, -1, '&Symmetric')

		## auto raster
		self.autobut = wx.Button(self, -1, 'Calculate spacing and angle using the following parameters:')
		self.Bind(wx.EVT_BUTTON, self.onAutoButton, self.autobut)
		self.widgets['raster preset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['raster preset'].setChoices(presets)
		self.widgets['raster overlap'] = FloatEntry(self, -1, chars=8)


		szauto = wx.GridBagSizer(5, 5)
		szauto.Add(self.autobut, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Raster Preset')
		szauto.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster preset'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Overlap percent')
		szauto.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster overlap'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		movetypes = self.node.calclients.keys()
		self.widgets['raster movetype'] = Choice(self, -1, choices=movetypes)
		label = wx.StaticText(self, -1, 'Move Type')
		szauto.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szauto.Add(self.widgets['raster movetype'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszauto.Add(szauto, 1, wx.EXPAND|wx.ALL,5)

		szraster = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'XY symmetry:')
		szraster.Add(label, (0,0), (1,1) , wx.ALIGN_CENTER_VERTICAL)

		self.Bind(wx.EVT_CHECKBOX, self.onToggleSymm, self.widgets['raster symmetric'])
		szraster.Add(self.widgets['raster symmetric'], (0,1), (1,2) , wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.widgets['raster symmetric'].SetMinSize((120,30))

		label = wx.StaticText(self, -1, 'Spacing (x,y):')
		szraster.Add(label, (1,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster spacing'], (1,1), (1,1), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szraster.Add(self.widgets['raster spacing asymm'], (1,2), (1,1), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Num points (x,y):')
		szraster.Add(label, (2,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster limit'], (2,1), (1,1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szraster.Add(self.widgets['raster limit asymm'], (2,2), (1,1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szraster.AddGrowableCol(1)

		label = wx.StaticText(self, -1, 'Angle:')
		szraster.Add(label, (3,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster angle'], (3,1), (1,2), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)

		szraster.Add(self.widgets['raster center on image'], (4,0), (1,3), 
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
		self.Bind(wx.EVT_CHECKBOX, self.onCheckBox, self.widgets['raster center on image'])

		label = wx.StaticText(self, -1, 'Center on x,y:')
		szraster.Add(label, (5,0), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster center x'], (5,1), (1,1), wx.ALIGN_CENTER_VERTICAL)
		szraster.Add(self.widgets['raster center y'], (5,2), (1,1), wx.ALIGN_CENTER_VERTICAL)

		if self.widgets['raster center on image'].GetValue():
			self.widgets['raster center x'].Enable(False)
			self.widgets['raster center y'].Enable(False)

		if self.widgets['raster symmetric'].GetValue():
			self.widgets['raster spacing asymm'].Enable(False)
			self.widgets['raster limit asymm'].Enable(False)
			self.widgets['raster spacing asymm'].SetValue(None)
			self.widgets['raster limit asymm'].SetValue(None)
		else:
			self.widgets['raster spacing asymm'].Enable(True)
			self.widgets['raster limit asymm'].Enable(True)		

		sbszraster.Add(szraster, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszauto,sbszraster, szbutton]

	def onToggleSymm(self, evt):
		if self.widgets['raster symmetric'].GetValue():
			self.widgets['raster spacing asymm'].Enable(False)
			self.widgets['raster limit asymm'].Enable(False)
			self.widgets['raster spacing asymm'].SetValue(None)
			self.widgets['raster limit asymm'].SetValue(None)
		else:
			self.widgets['raster spacing asymm'].SetValue(self.widgets['raster spacing'].GetValue())
			self.widgets['raster limit asymm'].SetValue(self.widgets['raster limit'].GetValue())
			self.widgets['raster spacing asymm'].Enable(True)
			self.widgets['raster limit asymm'].Enable(True)			
		return

	def onAutoButton(self, evt):
		self.dialog.setNodeSettings()
		s,a = self.node.autoSpacingAngle()
		if s is not None:
			self.widgets['raster spacing'].SetValue(s)
			self.widgets['raster angle'].SetValue(a)
			self.widgets['raster spacing asymm'].SetValue(s)

	def onCheckBox(self, evt):
		if self.widgets['raster center on image'].GetValue():
			self.widgets['raster center x'].Enable(False)
			self.widgets['raster center y'].Enable(False)
		else:		
			self.widgets['raster center x'].Enable(True)
			self.widgets['raster center y'].Enable(True)

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.createRaster()

class PolygonSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return PolygonScrolledSettings(self,self.scrsize,False)

class PolygonScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Polygon')
		sbszpolygon = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['select polygon'] = wx.CheckBox(self, -1, 'Wait for polygon selection')
		self.widgets['publish polygon'] = wx.CheckBox(self, -1, 'Publish polygon vertices as targets')

		szpolygon = wx.GridBagSizer(5, 5)
		szpolygon.Add(self.widgets['select polygon'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpolygon.Add(self.widgets['publish polygon'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbszpolygon.Add(szpolygon, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszpolygon, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.setPolygon()

class PolygonRasterSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return PolygonRasterScrolledSettings(self,self.scrsize,False)

class PolygonRasterScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Polygon Raster')
		sbszpolygon = wx.StaticBoxSizer(sb, wx.VERTICAL)
		szpolyraster = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'No Settings')
		szpolyraster.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbszpolygon.Add(szpolyraster, 1, wx.EXPAND|wx.ALL, 5)
		return [sbszpolygon,]

class FinalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Ice Analysis')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Focus Targets')
		sbszft = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Acquisition Targets')
		sbszat = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['ice box size'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice thickness'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=8)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=8, min=0.0)
		self.widgets['ice min std'] = FloatEntry(self, -1, chars=8, min=0.0)
		self.widgets['focus convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['focus convolve template'] = \
			gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['focus constant template'] = \
			gui.wx.TargetTemplate.Panel(self, 'Constant Template', targetname='Constant target')
		self.widgets['acquisition convolve'] = wx.CheckBox(self, -1, 'Convolve')
		self.widgets['acquisition convolve template'] = \
			gui.wx.TargetTemplate.Panel(self, 'Convolve Template')
		self.widgets['acquisition constant template'] = \
			gui.wx.TargetTemplate.Panel(self, 'Constant Template', targetname='Constant target')

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
		label = wx.StaticText(self, -1, 'Min. stdev.:')
		szice.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min std'], (5, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szice.AddGrowableCol(1)

		sbszice.Add(szice, 1, wx.EXPAND|wx.ALL, 5)

		szft = wx.GridBagSizer(5, 5)
		szft.Add(self.widgets['focus convolve'], (0, 0), (1, 2),
			wx.ALIGN_CENTER_VERTICAL)
		szft.Add(self.widgets['focus convolve template'], (1, 0), (1, 1),
			wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szft.Add(self.widgets['focus constant template'], (2, 0), (1, 1),
			wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szft.AddGrowableCol(0)

		sbszft.Add(szft, 1, wx.EXPAND|wx.ALL, 5)

		szat = wx.GridBagSizer(5, 5)
		szat.Add(self.widgets['acquisition convolve'], (0, 0), (1, 2),
			wx.ALIGN_CENTER_VERTICAL)
		szat.Add(self.widgets['acquisition convolve template'], (1, 0), (1, 1),
			wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szat.Add(self.widgets['acquisition constant template'], (2, 0), (1, 1),
			wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szat.AddGrowableCol(0)

		sbszat.Add(szat, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, 'Test')
		self.cice = wx.Button(self, -1, '&Clear targets')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.cice, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.Add(self.bice, (0, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		szt = wx.GridBagSizer(5, 5)
		szt.Add(sbszft, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		szt.Add(sbszat, (0, 1), (1, 1), wx.EXPAND|wx.ALL)


		self.Bind(wx.EVT_BUTTON, self.onAnalyzeIceButton, self.bice)
		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.cice)

		return [sbszice, szt, szbutton]

	def onAnalyzeIceButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.ice).start()

	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.clearTargets('acquisition')
		self.node.clearTargets('focus')

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.TargetFinder.ScrolledSettings):
	def initialize(self):
		tfsd = gui.wx.TargetFinder.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Raster Finder Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['skip'] = wx.CheckBox(self, -1, 'Skip automated raster target making')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['skip'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return tfsd + [sbsz]


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Raster Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

