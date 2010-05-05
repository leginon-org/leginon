# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx
import wx.lib.filebrowsebutton as filebrowse
import threading

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
		self.imagepanel.addTypeTool('templateA', display=True, settings=True)
		self.imagepanel.addTypeTool('templateB', display=True, settings=True)
		self.imagepanel.addTypeTool('correlation', display=True, settings=False)
		self.imagepanel.addTargetTool('peak', wx.Color(255,128,0), target=True, settings=False, numbers=False)
		self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=True, numbers=True)
		self.imagepanel.selectiontool.setDisplayed('acquisition', True)
		self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=True, numbers=True)
		self.imagepanel.selectiontool.setDisplayed('focus', True)

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onImageSettings(self, evt):
		if evt.name == 'Original':
			dialog = OriginalSettingsDialog(self)
			if dialog.ShowModal() == wx.ID_OK:
				filename = self.node.settings['image filename']
				self.node.readImage(filename)
			dialog.Destroy()
			return

		if evt.name == 'templateA':
			dialog = TemplateASettingsDialog(self)
		if evt.name == 'templateB':
			dialog = TemplateBSettingsDialog(self)
		elif evt.name == 'correlation':
			dialog = CorrelationSettingsDialog(self)
		elif evt.name == 'peak':
			dialog = CorrelationSettingsDialog(self)
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
		sz.Add(self.widgets['image filename'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)
		return [sbsz]

class TemplateASettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return TemplateAScrolledSettings(self,self.scrsize,False)

class TemplateAScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		sbsztemplate = wx.GridBagSizer(5,5)
		lab = wx.StaticText(self, -1, 'Template Size (percent of image)')
		self.widgets['template size'] = IntEntry(self, -1, chars=4)
		sbsztemplate.Add(lab, (0,0), (1,1))
		sbsztemplate.Add(self.widgets['template size'], (0,1), (1,1))

		self.btest = wx.Button(self, -1, 'Make Template A')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onButton, self.btest)

		return [sbsztemplate, szbutton]

	def onButton(self, evt):
		self.dialog.setNodeSettings()
		self.node.makeTemplateA()

class TemplateBSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return TemplateBScrolledSettings(self,self.scrsize,False)

class TemplateBScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		sbsztemplate = wx.GridBagSizer(5,5)
		lab = wx.StaticText(self, -1, 'Test Angle (degrees)')
		self.testangle = FloatEntry(self, -1, allownone=False, chars=5, value='0.0')
		sbsztemplate.Add(lab, (0,0), (1,1))
		sbsztemplate.Add(self.testangle, (0,1), (1,1))
		sbsztemplate.AddGrowableCol(0)

		self.btest = wx.Button(self, -1, 'Make Template B')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.btest, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onButton, self.btest)

		return [sbsztemplate, szbutton]

	def onButton(self, evt):
		self.dialog.setNodeSettings()
		angle = self.testangle.GetValue()
		self.node.makeTemplateB(angle)


class CorrelationSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return CorrelationScrolledSettings(self,self.scrsize,False)

class CorrelationScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['correlation type'] = Choice(self, -1, choices=self.node.cortypes)
		szcor.Add(self.widgets['correlation type'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Correlation Low Pass')
		self.widgets['correlation lpf'] = FloatEntry(self, -1, min=0.0, chars=4)
		szcor.Add(label, (1,0), (1,1))
		szcor.Add(self.widgets['correlation lpf'], (1,1), (1,1))
		self.widgets['rotate'] = wx.CheckBox(self, -1, 'Rotate')
		szcor.Add(self.widgets['rotate'], (2,0), (1,1))

		label = wx.StaticText(self, -1, 'Angle Increment')
		self.widgets['angle increment'] = FloatEntry(self, -1, min=0.0, chars=4)
		szcor.Add(label, (3,0), (1,1))
		szcor.Add(self.widgets['angle increment'], (3,1), (1,1))

		label = wx.StaticText(self, -1, 'SNR Threshold')
		self.widgets['snr threshold'] = FloatEntry(self, -1, min=0.0, chars=4)
		szcor.Add(label, (4,0), (1,1))
		szcor.Add(self.widgets['snr threshold'], (4,1), (1,1))

		self.bcor = wx.Button(self, -1, 'Correlate')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		
		self.Bind(wx.EVT_BUTTON, self.onCorrelate, self.bcor)

		return [szcor, szbutton]

	def onCorrelate(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.correlateRotatingTemplate).start()

class FinalSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return FinalScrolledSettings(self,self.scrsize,False)

class FinalScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)

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
		self.dialog.setNodeSettings()
		self.node.clearTargets('acquisition')
		self.node.clearTargets('focus')

	def onTestButton(self, evt):
		self.dialog.setNodeSettings()
		threading.Thread(target=self.node.makeFinalTargets).start()

class SettingsDialog(leginon.gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.TargetFinder.ScrolledSettings):
	def initialize(self):
		tfsd = leginon.gui.wx.TargetFinder.ScrolledSettings.initialize(self)
		if self.show_basic:
			return tfsd
		else:
			sb = wx.StaticBox(self, -1, 'DTFinder Settings')
			sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

			self.widgets['skip'] = wx.CheckBox(self, -1, 'Skip automated hole finder')
			sz = wx.GridBagSizer(5, 5)
			sz.Add(self.widgets['skip'], (0, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)

			sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

			return tfsd + [sbsz]
