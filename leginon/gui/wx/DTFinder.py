# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx
import gui.wx.TargetPanel
import gui.wx.Settings
import gui.wx.TargetFinder
import wx.lib.filebrowsebutton as filebrowse
import gui.wx.Rings
from gui.wx.Choice import Choice
from gui.wx.Entry import Entry, IntEntry, FloatEntry
import gui.wx.TargetTemplate
import gui.wx.ToolBar
import threading

class Panel(gui.wx.TargetFinder.Panel):
	icon = 'holefinder'
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)
		self.SettingsDialog = SettingsDialog

		self.imagepanel = gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('original', display=True, settings=True)
		self.imagepanel.selectiontool.setDisplayed('original', True)
		self.imagepanel.addTypeTool('template', display=True, settings=True)
		self.imagepanel.addTypeTool('correlation', display=True, settings=False)
		self.imagepanel.addTargetTool('peak', wx.Color(255,128,0), target=True, settings=False, numbers=False)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def onImageSettings(self, evt):
		if evt.name == 'original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'template':
			dialog = TemplateSettingsDialog(self)
		elif evt.name == 'correlation':
			dialog = CorrelationSettingsDialog(self)
		elif evt.name == 'peak':
			dialog = CorrelationSettingsDialog(self)
		elif evt.name == 'acquisition':
			dialog = FinalSettingsDialog(self)

		dialog.ShowModal()
		dialog.Destroy()


class OriginalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Original Image')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['image filename'] = filebrowse.FileBrowseButton(self, -1)
		self.widgets['image filename'].SetMinSize((500,50))
		self.bok.SetLabel('&Load')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		return [sbsz]

class TemplateSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		sbsztemplate = wx.GridBagSizer(5,5)
		lab = wx.StaticText(self, -1, 'Template Size')
		self.widgets['template size'] = IntEntry(self, -1, chars=4)
		sbsztemplate.Add(lab, (0,0), (1,1))
		sbsztemplate.Add(self.widgets['template size'], (0,1), (1,1))

		self.btest = wx.Button(self, -1, 'Make Template')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onButton, self.btest)

		return [sbsztemplate, szbutton]

	def onButton(self, evt):
		self.setNodeSettings()
		self.node.makeTemplate()

class CorrelationSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['template type'] = Choice(self, -1, choices=self.node.cortypes)
		szcor.Add(self.widgets['template type'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.bcor = wx.Button(self, -1, 'Correlate')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		
		self.Bind(wx.EVT_BUTTON, self.onCorrelate, self.bcor)

		return [szcor, szbutton]

	def onCorrelate(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.correlateTemplate).start()

class FinalSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.btest = wx.Button(self, -1, 'Make Targets')
		self.bclear = wx.Button(self, -1, 'Clear targets')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		szbutton.Add(self.bclear, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(1)
		
		self.Bind(wx.EVT_BUTTON, self.onTestButton, self.btest)
		self.Bind(wx.EVT_BUTTON, self.onClearButton, self.bclear)

		self.growrows = [False, True, False,]

		return [szbutton]

	def onClearButton(self, evt):
		self.setNodeSettings()
		self.node.clearTargets('acquisition')

	def onTestButton(self, evt):
		self.setNodeSettings()
		threading.Thread(target=self.node.makeAcquisitionTargets).start()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsd = gui.wx.TargetFinder.SettingsDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'DTFinder Settings')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['skip'] = wx.CheckBox(self, -1, 'Skip automated hole finder')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['skip'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return tfsd + [sbsz]
