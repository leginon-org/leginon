# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/HoleFinder.py,v $
# $Revision: 1.33 $
# $Name: not supported by cvs2svn $
# $Date: 2005-04-01 22:57:05 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
import gui.wx.Rings
from gui.wx.Choice import Choice
from gui.wx.Entry import Entry, IntEntry, FloatEntry
import gui.wx.TargetTemplate
import gui.wx.ToolBar

class Panel(gui.wx.TargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT,
													'play',
													shortHelpString='Submit Targets')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SUBMIT_QUEUE,
													'send_queue',
													shortHelpString='Submit Queued Targets')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('Original', True)
		self.imagepanel.addTypeTool('Edge', display=True, settings=True)
		self.imagepanel.addTypeTool('Template', display=True, settings=True)
		self.imagepanel.addTypeTool('Threshold', display=True, settings=True)
		self.imagepanel.addTargetTool('Blobs', wx.Color(0, 255, 255),
																settings=True)
		self.imagepanel.addTargetTool('Lattice', wx.Color(255, 0, 255),
																	settings=True)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True,
																	settings=True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True,
																	settings=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.Bind(gui.wx.Events.EVT_SUBMIT_TARGETS, self.onSubmitTargets)
		self.Bind(gui.wx.Events.EVT_TARGETS_SUBMITTED, self.onTargetsSubmitted)

	def onSubmitTargets(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, True)

	def onTargetsSubmitted(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)

	def submitTargets(self):
		evt = gui.wx.Events.SubmitTargetsEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def targetsSubmitted(self):
		evt = gui.wx.Events.TargetsSubmittedEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def getTargetPositions(self, typename):
		return self.imagepanel.getTargetPositions(typename)

	def onNodeInitialized(self):
		gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.Bind(gui.wx.ImageViewer.EVT_SETTINGS, self.onImageSettings)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitTool,
											id=gui.wx.ToolBar.ID_SUBMIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSubmitQueueTool,
											id=gui.wx.ToolBar.ID_SUBMIT_QUEUE)

	def onSubmitTool(self, evt):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SUBMIT, False)
		self.node.submit()

	def onSubmitQueueTool(self, evt):
		self.node.publishQueue()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				if filename:
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


class OriginalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['image filename'] = filebrowse.FileBrowseButton(self, -1)
		self.bok.SetLabel('Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Original Image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class TemplateSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['template lpf'] = {}
		self.widgets['template lpf']['sigma'] = FloatEntry(self, -1,
																												min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['template lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter (Phase Correlation)')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

		self.widgets['template rings'] = gui.wx.Rings.Panel(self)
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

		sb = wx.StaticBox(self, -1, 'Template Correlation')
		sbsztemplate = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsztemplate.Add(sztemplate, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbsztemplate, sbszlpf, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.correlateTemplate()

class EdgeSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['edge lpf'] = {}
		self.widgets['edge lpf']['sigma'] = FloatEntry(self, -1, min=0.0, chars=4)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sigma:')
		szlpf.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szlpf.Add(self.widgets['edge lpf']['sigma'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szlpf.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Low Pass Filter')
		sbszlpf = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlpf.Add(szlpf, 1, wx.EXPAND|wx.ALL, 5)

#		self.widgets['edge'] = wx.CheckBox(self, -1, 'Use edge finding')
#		self.widgets['edge type'] = Choice(self, -1, choices=self.node.filtertypes)
#		self.widgets['edge log size'] = IntEntry(self, -1, min=1, chars=4)
#		self.widgets['edge log sigma'] = FloatEntry(self, -1, min=0.0, chars=4)
#		self.widgets['edge absolute'] = wx.CheckBox(self, -1,
#																					'Take absolute value of edge values')
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

		sb = wx.StaticBox(self, -1, 'Edge Finding')
		sbszedge = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszedge.Add(szedge, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlpf, sbszedge, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.findEdges()

class ThresholdSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['threshold'] = FloatEntry(self, -1, chars=9)

		szthreshold = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Threshold:')
		szthreshold.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szthreshold.Add(self.widgets['threshold'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szthreshold.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Threshold')
		sbszthreshold = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszthreshold.Add(szthreshold, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszthreshold, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.threshold()

class BlobsSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

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

		sb = wx.StaticBox(self, -1, 'Blob finding')
		sbszblobs = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszblobs.Add(szblobs, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszblobs, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.findBlobs()

class LatticeSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

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

		sb = wx.StaticBox(self, -1, 'Lattice Fitting')
		sbszlattice = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszlattice.Add(szlattice, 1, wx.EXPAND|wx.ALL, 5)

		szstats = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Radius:')
		szstats.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['lattice hole radius'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Zero thickness:')
		szstats.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szstats.Add(self.widgets['lattice zero thickness'], (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		szstats.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Hole Statistics')
		sbszstats = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszstats.Add(szstats, 1, wx.EXPAND|wx.ALL, 5)

		self.btest = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)

		return [sbszlattice, sbszstats, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.fitLattice()

class FinalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['ice min mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max mean'] = FloatEntry(self, -1, chars=6)
		self.widgets['ice max std'] = FloatEntry(self, -1, chars=6)
		self.widgets['focus hole'] = Choice(self, -1, choices=self.node.focustypes)
		self.widgets['target template'] = wx.CheckBox(self, -1,
																									'Use target template')
		self.widgets['focus template'] = gui.wx.TargetTemplate.Panel(self,
																									'Focus Target Template')
		self.widgets['acquisition template'] = gui.wx.TargetTemplate.Panel(self,
																									'Acquisition Target Template')
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

		sb = wx.StaticBox(self, -1, 'Ice Thickness Threshold')
		sbszice = wx.StaticBoxSizer(sb, wx.VERTICAL)
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

		sb = wx.StaticBox(self, -1, 'Focus Template Thickness')
		sbszftt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszftt.Add(szftt, 1, wx.EXPAND|wx.ALL, 5)

		sztt = wx.GridBagSizer(5, 5)
		sztt.Add(self.widgets['target template'], (0, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		sztt.Add(sbszftt, (1, 0), (2, 1), wx.ALIGN_CENTER)
		sztt.Add(self.widgets['focus template'], (1, 1), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sztt.Add(self.widgets['acquisition template'], (2, 1), (1, 1),
							wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sb = wx.StaticBox(self, -1, 'Target Template')
		sbsztt = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsztt.Add(sztt, 1, wx.EXPAND|wx.ALL, 5)

		self.bice = wx.Button(self, -1, 'Test')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bice, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.bice)

		return [sbszice, sbsztt, szbutton]

	def onTestButton(self, evt):
		self.setNodeSettings()
		self.node.ice()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)

		self.widgets['user check'] = wx.CheckBox(self, -1,
																	'Allow for user verification of picked holes')
		self.widgets['skip'] = wx.CheckBox(self, -1,
																							'Skip auto picking of holes')
		self.widgets['queue'] = wx.CheckBox(self, -1,
																							'Queue up targets')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['user check'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['skip'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['queue'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Hole finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return tfsbsz + [sbsz]

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

