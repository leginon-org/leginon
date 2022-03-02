# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import wx.lib.filebrowsebutton as filebrowse
import threading

import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.AutoTargetFinder
import leginon.gui.wx.Rings
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry
import leginon.gui.wx.TargetTemplate
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.AutoTargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		leginon.gui.wx.AutoTargetFinder.Panel.initialize(self)
		self.SettingsDialog = leginon.gui.wx.AutoTargetFinder.SettingsDialog

		self.imagepanel.addTargetTool('Hole', wx.Colour(0, 255, 255), target=True, settings=True, shape='o')
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True, exp=True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.addTargetTool('preview', wx.Colour(255, 128, 255), target=True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('Hole', False)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = leginon.gui.wx.AutoTargetFinder.OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		elif evt.name == 'Hole':
			dialog = self._LatticeSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		# modeless display
		dialog.Show(True)

	def _LatticeSettingsDialog(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return LatticeSettingsDialog(parent)
	
class LatticeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return LatticeScrolledSettings(self,self.scrsize,False)

	def onShow(self):
		self.panel.imagepanel.showTypeToolDisplays(['Original'])
		
class LatticeScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		return self.__initialize()

	def __initialize(self):
		sbszstats = self.createStatsBoxSizer()
		szbutton = self.createTestSizer()
		return [sbszstats, szbutton]

	def createStatsBoxSizer(self):
		sb = wx.StaticBox(self, -1, 'Hole Statistics')
		sbszstats = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['lattice hole radius'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['lattice zero thickness'] = FloatEntry(self, -1, chars=6)

		szstats = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Radius:')
		szstats.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['lattice hole radius'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Reference Intensity:')
		szstats.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['lattice zero thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szstats.AddGrowableCol(1)

		sbszstats.Add(szstats, 1, wx.EXPAND|wx.ALL, 5)
		return sbszstats

	def createTestSizer(self):
		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)
		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		return szbutton

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.findHoles()
		self.panel.imagepanel.hideTypeToolDisplays(['acquisition','focus'])
		self.panel.imagepanel.showTypeToolDisplays(['Hole'])

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Ice Thickness Threshold')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Focus Template Thickness')
		sbszftt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Target Template')
		sbsztt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Acquisition Target Sampling')
		sbszsm = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice min std'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus hole'] = Choice(self, -1, choices=self.node.focustypes)
		self.widgets['target template'] = wx.CheckBox(self, -1,
			'Use target template')
		self.widgets['filter ice on convolved'] = wx.CheckBox(self, -1,
			'Apply ice thickness threshold on template-convolved acquisiton targets')
		self.widgets['focus template'] = leginon.gui.wx.TargetTemplate.Panel(self,
			'Focus Target Template', autofill=True)
		self.widgets['acquisition template'] = leginon.gui.wx.TargetTemplate.Panel(self,
			'Acquisition Target Template', autofill=True)
		self.widgets['focus template thickness'] = wx.CheckBox(self, -1,
			'Use focus template thickness and limit to one focus target')
		self.widgets['focus stats radius'] = IntEntry(self, -1, chars=6)
		self.widgets['focus min mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus min stdev thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max stdev thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['sampling targets'] = wx.CheckBox(self, -1,
			'Use subset of the acquisition targets')
		self.widgets['max sampling'] = IntEntry(self, -1, chars=6)

		szice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min. mean:')
		szice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean:')
		szice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. stdev.:')
		szice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min std'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Focus hole selection:')
		szice.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['focus hole'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szice.Add(self.createFocusOffsetSizer(), (5,0), (1,2),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szice.AddGrowableCol(1)

		sbszice.Add(szice, 1, wx.EXPAND|wx.ALL, 5)

		szftt = wx.GridBagSizer(5, 5)
		szftt.Add(self.widgets['focus template thickness'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Stats. radius:')
		szftt.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus stats radius'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. mean thickness:')
		szftt.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus min mean thickness'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean thickness:')
		szftt.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus max mean thickness'], (3, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. std. thickness:')
		szftt.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus min stdev thickness'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. std. thickness:')
		szftt.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus max stdev thickness'], (5, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szftt.AddGrowableCol(1)

		sbszftt.Add(szftt, 1, wx.EXPAND|wx.ALL, 5)

		sztt = wx.GridBagSizer(5, 5)
		sztt.Add(self.widgets['target template'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztt.Add(self.widgets['filter ice on convolved'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztt.Add(sbszftt, (2, 0), (4, 1), wx.ALIGN_CENTER)
		sztt.Add(self.widgets['focus template'], (0, 1), (3, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sztt.Add(self.widgets['acquisition template'], (3, 1), (2, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sztt.AddGrowableCol(1)
		sztt.AddGrowableRow(0)
		sztt.AddGrowableRow(5)

		sbsztt.Add(sztt, 1, wx.EXPAND|wx.ALL, 5)

		szsm = wx.GridBagSizer(5, 5)
		szsm.Add(self.widgets['sampling targets'], (0, 0), (1, 2),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_LEFT)
		label = wx.StaticText(self, -1, 'Sample Maximal of ')
		szsm.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsm.Add(self.widgets['max sampling'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szsm.AddGrowableCol(0)
		sbszsm.Add(szsm, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, '&Test targeting')
		self.cice = wx.Button(self, -1, '&Clear targets')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.cice, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.Add(self.bice, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)
		
		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.bice)
		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.cice)

		self.growrows = [False, True, False, False,]

		return [sbszice, sbsztt, sbszsm, szbutton]

	def createFocusOffsetSizer(self):
		# set widgets
		self.widgets['focus offset row'] = IntEntry(self, -1, chars=4)
		self.widgets['focus offset col'] = IntEntry(self, -1, chars=4)
		# make sizer
		sz_offset = wx.BoxSizer(wx.HORIZONTAL)
		sz_offset.Add(wx.StaticText(self, -1, 'Focus offset x:'),0,wx.ALIGN_CENTER_VERTICAL)
		sz_offset.Add(self.widgets['focus offset col'])
		sz_offset.AddSpacer(10)
		sz_offset.Add(wx.StaticText(self, -1, 'y:'),0,wx.ALIGN_CENTER_VERTICAL)
		sz_offset.Add(self.widgets['focus offset row'])
		return sz_offset

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.ice).start()
		self.panel.imagepanel.hideTypeToolDisplays(['Blobs','Template','Threshold'])
		self.panel.imagepanel.showTypeToolDisplays(['acquisition','focus','Original'])

	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.clearTargets('Hole')
		self.node.clearTargets('acquisition')
		self.node.clearTargets('focus')



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

