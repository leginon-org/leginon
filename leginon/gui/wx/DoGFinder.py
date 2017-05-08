# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import threading

import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.AutoTargetFinder
import leginon.gui.wx.Rings
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.TargetTemplate
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.AutoTargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		leginon.gui.wx.AutoTargetFinder.Panel.initialize(self)
		self.SettingsDialog = leginon.gui.wx.AutoTargetFinder.SettingsDialog

		self.imagepanel.addTypeTool('DoG', display=False, settings=True)
		self.imagepanel.addTypeTool('Threshold', display=True, settings=True)
		self.imagepanel.addTargetTool('Blobs', wx.Colour(0, 255, 255), target=True, settings=True, shape='o')
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True, exp=True)
		self.imagepanel.addTargetTool('Voronoi', wx.LIGHT_GREY, target=False, settings=False, shape='o')
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.addTargetTool('preview', wx.Colour(255, 128, 255), target=True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('Blobs', False)
		self.imagepanel.selectiontool.setDisplayed('Voronoi', False)
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

		if evt.name == 'DoG':
			dialog = DoGSettingsDialog(self)
		elif evt.name == 'Threshold':
			dialog = ThresholdSettingsDialog(self)
		elif evt.name == 'Blobs':
			dialog = BlobsSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		# modeless display
		dialog.Show(True)

class DoGSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return DoGScrolledSettings(self,self.scrsize,False)

class DoGScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		sbsztemplate = self.createDoGFilterBox()
		sbszlpf = self.createDoGLPFBox()

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbsztemplate, sbszlpf, szbutton]

	def createDoGLPFBox(self):
		sb = wx.StaticBox(self, -1, '')
		sbszlpf = wx.StaticBoxSizer(sb)
		return sbszlpf

	def createDoGFilterBox(self):
		sb = wx.StaticBox(self, -1, 'DoG Filter')
		sbsztemplate = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = wx.GridBagSizer(5, 5)
		newrow,newcol = self.createDoGDiamter(sz, (0,0))
		newrow,newcol = self.createDoGInvertCheckBox(sz, (newrow,0))
		newrow,newcol = self.createDoGKFactorEntry(sz, (newrow,0))
		sbsztemplate.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		return sbsztemplate

	def addToSizer(self,sz, item, start_position, total_length,align=wx.ALIGN_LEFT):
		# sz is changed in-place.  Therefore, must be named such where this function is called.
		sz.Add(item, start_position, total_length,
				  align)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createDoGDiamter(self, sz, start_position):
		# define widget
		self.widgets['dog diameter'] = IntEntry(self, -1, chars=4, min=3)
		# make sizer
		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Hole diameter')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['dog diameter'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'in pixels')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,2)
		return self.addToSizer(sz, szcor, start_position, total_length)

	def createDoGInvertCheckBox(self, sz, start_position):
		self.widgets['dog invert'] = wx.CheckBox(self, -1,
			'invert image, when holes are darker than background')
		return self.addToSizer(sz, self.widgets['dog invert'], (start_position[0],0), (1,2))

	def createDoGKFactorEntry(self, sz, start_position):
		self.widgets['dog k-factor'] = FloatEntry(self, -1, chars=4)
		label = wx.StaticText(self, -1, 'k-factor')
		# add to main
		newrow, newcol = self.addToSizer(sz, label, start_position, (1,1))
		return self.addToSizer(sz, self.widgets['dog k-factor'], (start_position[0],newcol), (1,1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.dogFilter()
		self.panel.imagepanel.showTypeToolDisplays(['DoG'])

class ThresholdSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ThresholdScrolledSettings(self,self.scrsize,False)

class ThresholdScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Threshold')
		sbszthreshold = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['threshold'] = FloatEntry(self, -1, chars=9)

		szthreshold = wx.GridBagSizer(5, 5)
		self.widgets['threshold method'] = Choice(self, -1, choices=(
			"Threshold = mean + A * stdev",
			"Threshold = A"))
		szthreshold.Add(self.widgets['threshold method'], (0,0), (1,2))
		label = wx.StaticText(self, -1, 'A:')
		szthreshold.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szthreshold.Add(self.widgets['threshold'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szthreshold.AddGrowableCol(1)

		sbszthreshold.Add(szthreshold, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszthreshold, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.threshold()
		self.panel.imagepanel.showTypeToolDisplays(['Threshold'])

class BlobsSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return BlobsScrolledSettings(self,self.scrsize,False)

class BlobsScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Blob finding')
		sbszblobs = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['blobs border'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs max'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs max size'] = IntEntry(self, -1, min=0, chars=6)
		self.widgets['blobs min size'] = IntEntry(self, -1, min=0, chars=6)
		#self.widgets['blobs max moment'] = IntEntry(self, -1, min=1, chars=6)

		szblobs = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Border:')
		szblobs.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs border'], (0, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. blobs:')
		szblobs.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs max'], (1, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. blob size:')
		szblobs.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs max size'], (2, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Min. blob size:')
		szblobs.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szblobs.Add(self.widgets['blobs min size'], (3, 1), (1, 1),
			wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		#label = wx.StaticText(self, -1, 'Max. blob moment (elongation):')
		#szblobs.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		#szblobs.Add(self.widgets['blobs max moment'], (4, 1), (1, 1),
		#	wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szblobs.AddGrowableCol(1)

		sbszblobs.Add(szblobs, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszblobs, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.findBlobs()
		self.panel.imagepanel.showTypeToolDisplays(['Blobs'])

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Ice Thickness Threshold')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Focus DoG Thickness')
		sbszftt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Target DoG')
		sbsztt = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['lattice zero thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice hole radius'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus hole'] = Choice(self, -1, choices=self.node.focustypes)
		self.widgets['target template'] = wx.CheckBox(self, -1,
			'Use target template')
		self.widgets['focus template'] = leginon.gui.wx.TargetTemplate.Panel(self,
			'Focus Target DoG', autofill=True)
		self.widgets['acquisition template'] = leginon.gui.wx.TargetTemplate.Panel(self,
			'Acquisition Target DoG', autofill=True)
		self.widgets['focus template thickness'] = wx.CheckBox(self, -1,
			'Use focus template thickness and limit to one focus target')
		self.widgets['focus stats radius'] = IntEntry(self, -1, chars=6)
		self.widgets['focus min mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max stdev thickness'] = FloatEntry(self, -1, chars=6)

		szice = wx.GridBagSizer(5, 5)
		nrow = 0
		label = wx.StaticText(self, -1, 'Stats box size:')
		szice.Add(label, (nrow, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['lattice hole radius'], (nrow, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		nrow += 1
		label = wx.StaticText(self, -1, 'Reference intensity (i0):')
		szice.Add(label, (nrow, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['lattice zero thickness'], (nrow, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		nrow += 1
		label = wx.StaticText(self, -1, 'Minimum mean cutoff:')
		szice.Add(label, (nrow, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (nrow, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		nrow += 1
		label = wx.StaticText(self, -1, 'Maximum mean cutoff:')
		szice.Add(label, (nrow, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (nrow, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		nrow += 1
		label = wx.StaticText(self, -1, 'Maximum stdev. cutoff:')
		szice.Add(label, (nrow, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (nrow, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		nrow += 1
		label = wx.StaticText(self, -1, 'Focus hole selection:')
		szice.Add(label, (nrow, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['focus hole'], (nrow, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		nrow += 1
		szice.Add(self.createFocusOffsetSizer(), (nrow,0), (1,2),
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
		label = wx.StaticText(self, -1, 'Max. std. thickness:')
		szftt.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szftt.Add(self.widgets['focus max stdev thickness'], (4, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szftt.AddGrowableCol(1)

		sbszftt.Add(szftt, 1, wx.EXPAND|wx.ALL, 5)

		sztt = wx.GridBagSizer(5, 5)
		sztt.Add(self.widgets['target template'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztt.Add(sbszftt, (1, 0), (3, 1), wx.ALIGN_CENTER)
		sztt.Add(self.widgets['focus template'], (0, 1), (2, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sztt.Add(self.widgets['acquisition template'], (2, 1), (2, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sztt.AddGrowableCol(1)
		sztt.AddGrowableRow(0)
		sztt.AddGrowableRow(2)

		sbsztt.Add(sztt, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, '&Test targeting')
		self.cice = wx.Button(self, -1, '&Clear targets')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.cice, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.Add(self.bice, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.bice)
		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.cice)

		self.growrows = [False, True, False,]

		return [sbszice, sbsztt, szbutton]

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
		self.panel.imagepanel.hideTypeToolDisplays(['Blobs','DoG','Threshold'])
		self.panel.imagepanel.showTypeToolDisplays(['acquisition','focus','Original'])

	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.clearTargets('Blobs')
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

