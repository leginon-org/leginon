# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx
import wx.lib.filebrowsebutton as filebrowse

import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.Rings
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry
import leginon.gui.wx.TargetTemplate
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.TargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		leginon.gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = SettingsDialog

		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Original', True)
		self.imagepanel.addTypeTool('Edge', display=True, settings=True)
		self.imagepanel.addTypeTool('Template', display=True, settings=True)
		self.imagepanel.addTypeTool('Threshold', display=True, settings=True)
		self.imagepanel.addTargetTool('Blobs', wx.Color(0, 255, 255), shape='o', settings=True)
		self.imagepanel.addTargetTool('Lattice', wx.Color(255, 0, 255), settings=True)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True)
		self.imagepanel.addTargetTool('preview', wx.Color(255, 128, 255), target=True)
		self.imagepanel.addTargetTool('done', wx.RED)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('done', True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)
		self.imagepanel.selectiontool.setDisplayed('preview', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'Edge':
			dialog = EdgeSettingsDialog(self)
		elif evt.name == 'Template':
			dialog = TemplateSettingsDialog(self)
		elif evt.name == 'Threshold':
			dialog = ThresholdSettingsDialog(self)
		elif evt.name == 'Blobs':
			dialog = BlobsSettingsDialog(self)
		elif evt.name == 'Lattice':
			dialog = LatticeSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)
		elif evt.name == 'focus':
			dialog = FinalSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()


class OriginalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return OriginalScrolledSettings(self,self.scrsize,False)

class OriginalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Original Image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['image filename'] = filebrowse.FileBrowseButton(self, -1)
		self.widgets['image filename'].SetMinSize((500,50))
		self.dialog.bok.SetLabel('&Load')


		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class TemplateSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return TemplateScrolledSettings(self,self.scrsize,False)

class TemplateScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Low Pass Filter (Phase Correlation)')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['template lpf'] = {}
		self.widgets['template lpf']['sigma'] = FloatEntry(self, -1,
																												min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['template lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

		sb = wx.StaticBox(self, -1, 'Template Correlation')
		sbsztemplate = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['template rings'] = leginon.gui.wx.Rings.Panel(self)
		self.widgets['template type'] = Choice(self, -1, choices=self.node.cortypes)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['template type'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sztemplate = wx.GridBagSizer(5, 5)
		sztemplate.Add(szcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztemplate.Add(self.widgets['template rings'], (1, 0), (1, 1),
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sbsztemplate.Add(sztemplate, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbsztemplate, sbszlpf, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.correlateTemplate()

class EdgeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return EdgeScrolledSettings(self,self.scrsize,False)

class EdgeScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['edge lpf'] = {}
		self.widgets['edge lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['edge lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

#		self.widgets['edge'] = wx.CheckBox(self, -1, 'Use edge finding')
#		self.widgets['edge type'] = Choice(self, -1, choices=self.node.filtertypes)
#		self.widgets['edge log size'] = IntEntry(self, -1, min=1, chars=4)
#		self.widgets['edge log sigma'] = FloatEntry(self, -1, min=0.0, chars=4)
#		self.widgets['edge absolute'] = wx.CheckBox(self, -1,
#																					'Take absolute value of edge values')
		sb = wx.StaticBox(self, -1, 'Edge Finding')
		sbszedge = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['edge threshold'] = FloatEntry(self, -1, chars=9)

		szedge = wx.GridBagSizer(5, 5)
#		szedge.Add(self.widgets['edge'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
#		label = wx.StaticText(self, -1, 'Type:')
#		szedge.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		szedge.Add(self.widgets['edge type'], (1, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
#		label = wx.StaticText(self, -1, 'LoG Size:')
#		szedge.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		szedge.Add(self.widgets['edge log size'], (2, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
#		label = wx.StaticText(self, -1, 'LoG Sigma:')
#		szedge.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		szedge.Add(self.widgets['edge log sigma'], (3, 1), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
#		szedge.Add(self.widgets['edge absolute'], (4, 0), (1, 2),
#								wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Threshold:')
		szedge.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedge.Add(self.widgets['edge threshold'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szedge.AddGrowableCol(1)

		sbszedge.Add(szedge, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlpf, sbszedge, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.findEdges()

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
		label = wx.StaticText(self, -1, 'Threshold:')
		szthreshold.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szthreshold.Add(self.widgets['threshold'], (0, 1), (1, 1),
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

class LatticeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return LatticeScrolledSettings(self,self.scrsize,False)

class LatticeScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Lattice Fitting')
		sbszlattice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Hole Statistics')
		sbszstats = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['lattice spacing'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice tolerance'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice hole radius'] = FloatEntry(self, -1, chars=6)
		self.widgets['lattice zero thickness'] = FloatEntry(self, -1, chars=6)

		szlattice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Spacing:')
		szlattice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlattice.Add(self.widgets['lattice spacing'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Tolerance:')
		szlattice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlattice.Add(self.widgets['lattice tolerance'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlattice.AddGrowableCol(1)

		sbszlattice.Add(szlattice, 1, wx.EXPAND|wx.ALL, 5)

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

		szbutton = wx.GridBagSizer(5, 5)
		self.btest = wx.Button(self, -1, 'Caculate lattice and stats')
		szbutton.Add(self.btest, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlattice, sbszstats, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.fitLattice()

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

		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus hole'] = Choice(self, -1, choices=self.node.focustypes)
		self.widgets['target template'] = wx.CheckBox(self, -1,
																									'Use target template')
		self.widgets['focus template'] = leginon.gui.wx.TargetTemplate.Panel(self,
			'Focus Target Template', autofill=True)
		self.widgets['acquisition template'] = leginon.gui.wx.TargetTemplate.Panel(self,
			'Acquisition Target Template', autofill=True)
		self.widgets['focus template thickness'] = wx.CheckBox(self, -1,
																								'Use focus template thickness')
		self.widgets['focus stats radius'] = IntEntry(self, -1, chars=6)
		self.widgets['focus min mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max mean thickness'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus max stdev thickness'] = FloatEntry(self, -1, chars=6)

		szice = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min. mean:')
		szice.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice min mean'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. mean:')
		szice.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max mean'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Max. stdev.:')
		szice.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['ice max std'], (2, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Focus hole selection:')
		szice.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szice.Add(self.widgets['focus hole'], (3, 1), (1, 1),
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
		sztt.Add(self.widgets['target template'], (0, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		sztt.Add(sbszftt, (1, 0), (2, 1), wx.ALIGN_CENTER)
		sztt.Add(self.widgets['focus template'], (1, 1), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sztt.Add(self.widgets['acquisition template'], (2, 1), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sbsztt.Add(sztt, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, '&Test targeting')
		self.cice = wx.Button(self, -1, '&Clear targets')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.cice, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.Add(self.bice, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)
		
		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.bice)
		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.cice)
		return [sbszice, sbsztt, szbutton]

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.ice).start()

	def onClearButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.clearTargets('acquisition')
		self.node.clearTargets('focus')

class SettingsDialog(leginon.gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.TargetFinder.ScrolledSettings):
	def initialize(self):
		tfsd = leginon.gui.wx.TargetFinder.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Hole Finder Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['skip'] = wx.CheckBox(self, -1,
																	'Skip automated hole finder')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['skip'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return tfsd + [sbsz]


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

