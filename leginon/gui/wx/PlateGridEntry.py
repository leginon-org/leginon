# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

from leginon.gui.wx.Entry import Entry, FloatEntry
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.Node
import leginon.gui.wx.GridEntry
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Settings

import threading
import wx

class Panel(leginon.gui.wx.GridEntry.GridSelectionPanel):
	#icon = 'robot'
	def setDefaultGridSelection(self):
		self.default_gridlabel = '--Not-specified--'

	def addNew(self):
		self.createNewGridFromPlate((2,0))
		self.createNewPlateSelector((4,0))

	def runNew(self):
		self.node.onBadEMGridName('No Grid')

	def createNewGridFromPlate(self,start_position):
		sb = wx.StaticBox(self, -1, 'New Grid Batch')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		szgrid = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Select a Grid Format (r x c:skips):')
		szgrid.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.cgridformat = wx.Choice(self, -1)
		self.cgridformat.Enable(False)
		szgrid.Add(self.cgridformat, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Select a plate in the project')
		szgrid.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.cplate = wx.Choice(self, -1)
		self.cplate.Enable(False)

		szgrid.Add(self.cplate, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.savenewgrid = wx.Button(self, wx.ID_APPLY)

		szgrid.Add(self.savenewgrid, (2, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		szgrid.AddGrowableCol(1)
		sbsz.Add(szgrid, 0, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbsz, start_position, (1, 1), wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_VERTICAL)

	def createNewPlateSelector(self,start_position):
		sb = wx.StaticBox(self, -1, 'New Prep Plate')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		szplate = wx.GridBagSizer(5, 5)
		# plate format
		label = wx.StaticText(self, -1, 'Plate Format:')
		szplate.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.cplateformat = wx.Choice(self, -1)
		self.cplateformat.Enable(False)
		szplate.Add(self.cplateformat, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# plate name
		label = wx.StaticText(self, -1, 'New Plate Name:')
		szplate.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.newplate = Entry(self, -1)
		szplate.Add(self.newplate, (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.savenewplate = wx.Button(self, wx.ID_SAVE)

		szplate.Add(self.savenewplate, (2, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		szplate.AddGrowableCol(1)
		sbsz.Add(szplate, 0, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbsz, start_position, (1, 1), wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_VERTICAL)

	def onNodeInitialized(self):
		super(Panel,self).onNodeInitialized()

		self.Bind(wx.EVT_BUTTON, self.onSaveNewGrids, self.savenewgrid)
		self.Bind(wx.EVT_CHOICE, self.onGridFormatChoice, self.cgridformat)
		self.Bind(wx.EVT_CHOICE, self.onPlateChoice, self.cplate)
		self.Bind(wx.EVT_CHOICE, self.onPlateFormatChoice, self.cplateformat)
		self.Bind(wx.EVT_BUTTON, self.onSaveNewPlate, self.savenewplate)
		self.refreshNewGrids()
		self.refreshPlates()

	def onSaveNewGrids(self,evt=None):
		self.cplate.Update()
		plate = self.cplate.GetStringSelection()
		if plate is None or plate == '':
			self.node.onBadEMGridName('No Plate')
			return
		if plate == '--New Plate as Below--':
			# save the new plate entry and then update the value
			status = self.onSaveNewPlate()
			if status is False:
				return
			plate = self.cplate.GetStringSelection()
		self.cgridformat.Update()
		gformat = self.cgridformat.GetStringSelection()
		if gformat is None or gformat == '':
			self.node.onBadEMGridName('No Grid Format')
			return
		else:
			self.node.publishNewEMGrids(gformat, plate)
		self.refreshGrids()

	def onGridFormatChoice(self, evt=None):
		if evt is None:
			formatlabel = self.cgridformat.GetStringSelection()
		else:
			formatlabel = evt.GetString()
		settings = self.node.getSettings()
		settings['grid format name'] = formatlabel
		self.node.setSettings(settings)
		self.newplate.Enable(False)

	def onPlateFormatChoice(self, evt=None):
		if evt is None:
			formatlabel = self.cplateformat.GetStringSelection()
		else:
			formatlabel = evt.GetString()
		settings = self.node.getSettings()
		settings['plate format name'] = formatlabel
		self.node.setSettings(settings)
		self.newplate.Enable(True)

	def setGridFormatSelection(self,choices):
		if choices:
			self.cgridformat.Clear()
			self.cgridformat.AppendItems(choices)
			if self.node.settings['grid format name']:
				n = self.cgridformat.FindString(self.node.settings['grid format name'])
			else:
				n = wx.NOT_FOUND
			if n == wx.NOT_FOUND:
				self.cgridformat.SetSelection(0)
			else:
				self.cgridformat.SetSelection(n)
			self.cgridformat.Enable(True)
			self.onGridFormatChoice()

	def setPlateFormatSelection(self,choices):
		if choices:
			self.cplateformat.Clear()
			self.cplateformat.AppendItems(choices)
			if self.node.settings['plate format name']:
				n = self.cplateformat.FindString(self.node.settings['plate format name'])
			else:
				n = wx.NOT_FOUND
			if n == wx.NOT_FOUND:
				self.cplateformat.SetSelection(0)
			else:
				self.cplateformat.SetSelection(n)
			self.cplateformat.Enable(True)
			self.onPlateFormatChoice()

	def onSaveNewPlate(self,evt=None):
		choices = self.node.getPlateNames()
		self.newplate.Update()
		newplate = self.newplate.GetValue()
		if newplate is None or newplate == '':
			self.node.onBadPlateName('No Plate Name')
			return False
		elif newplate in choices:
			self.node.onBadPlateName('Plate Name Exists')
			return False
		choices = self.node.getPlateFormats()
		self.cplateformat.Update()
		pformat = self.cplateformat.GetStringSelection()
		if pformat is None or pformat == '':
			self.node.onBadPlateName('No Plate Format')
			return False
		else:
			self.node.publishNewPlate(newplate,pformat)
		self.refreshPlates()

	def onPlateChoice(self, evt=None):
		if evt is None:
			platelabel = self.cplate.GetStringSelection()
		else:
			platelabel = evt.GetString()
		settings = self.node.getSettings()
		settings['plate name'] = platelabel
		self.node.setSettings(settings)
		if platelabel != '--New Plate as Below--':
			self.newplate.Enable(False)
		else:
			self.newplate.Enable(True)

	def setPlateSelection(self,choices):
		if choices:
			self.cplate.Clear()
			self.cplate.AppendItems(choices)
			if self.node.settings['plate name']:
				n = self.cplate.FindString(self.node.settings['plate name'])
			else:
				n = wx.NOT_FOUND
			if n == wx.NOT_FOUND:
				self.cplate.SetSelection(0)
			else:
				self.cplate.SetSelection(n)
			self.cplate.Enable(True)
			self.onPlateChoice()

	def onRefreshGridsButton(self, evt):
		self.refreshGrids()
		self.refreshNewGrids()
		self.refreshPlates()

	def refreshNewGrids(self):
		choices = self.node.getGridFormats()
		self.setGridFormatSelection(choices)		

	def refreshPlates(self):
		choices = self.node.getPlateNames()
		choices.insert(0,'--New Plate as Below--')
		self.setPlateSelection(choices)		
		choices = self.node.getPlateFormats()
		self.setPlateFormatSelection(choices)		

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Grid Entry')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'No Settings')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

