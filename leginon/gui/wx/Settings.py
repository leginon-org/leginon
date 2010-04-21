# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/Settings.py,v $
# $Revision: 1.29 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-18 22:46:47 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
import wx.lib.scrolledpanel as scrolledpanel
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.Camera
import leginon.gui.wx.Entry
import leginon.gui.wx.Presets
import wx.lib.filebrowsebutton as filebrowse
import leginon.gui.wx.Rings
import leginon.gui.wx.TargetTemplate
import leginon.gui.wx.Instrument

class SettingsError(Exception):
	pass

attributes = {
	wx.CheckBox: ('GetValue', 'SetValue', wx.EVT_CHECKBOX),
	wx.ToggleButton: ('GetValue', 'SetValue', wx.EVT_TOGGLEBUTTON),
	wx.Choice: ('GetStringSelection', 'SetStringSelection', wx.EVT_CHOICE),
	Choice: ('GetStringSelection', 'SetStringSelection', wx.EVT_CHOICE),
	leginon.gui.wx.Entry.Entry: ('GetValue', 'SetValue', leginon.gui.wx.Entry.EVT_ENTRY),
	leginon.gui.wx.Entry.IntEntry: ('GetValue', 'SetValue', leginon.gui.wx.Entry.EVT_ENTRY),
	leginon.gui.wx.Entry.FloatEntry: ('GetValue', 'SetValue', leginon.gui.wx.Entry.EVT_ENTRY),
	leginon.gui.wx.Entry.FloatSequenceEntry: ('GetValue', 'SetValue', leginon.gui.wx.Entry.EVT_ENTRY),
	leginon.gui.wx.Presets.PresetChoice:
		('GetStringSelection', 'SetStringSelection',
			leginon.gui.wx.Presets.EVT_PRESET_CHOICE),
	leginon.gui.wx.Presets.PresetOrder:
		('getValues', 'setValues', leginon.gui.wx.Presets.EVT_PRESET_ORDER_CHANGED),
	leginon.gui.wx.Presets.EditPresetOrder:
		('getValues', 'setValues', leginon.gui.wx.Presets.EVT_PRESET_ORDER_CHANGED),
	leginon.gui.wx.Camera.CameraPanel:
		('getConfiguration', 'setConfiguration',
			leginon.gui.wx.Camera.EVT_CONFIGURATION_CHANGED),
	filebrowse.FileBrowseButton: ('GetValue', 'SetValue', None),
	leginon.gui.wx.Rings.Panel: ('getRings', 'setRings', leginon.gui.wx.Rings.EVT_RINGS_UPDATED),
	leginon.gui.wx.TargetTemplate.Panel: ('getTemplate', 'setTemplate',
																leginon.gui.wx.TargetTemplate.EVT_TEMPLATE_UPDATED),
	leginon.gui.wx.Instrument.SelectionPanel: ('GetValue', 'SetValue', None),
}

class ScrolledDialog(scrolledpanel.ScrolledPanel):
	def __init__(self, parent, size=(200,200),scrolling=False,show_basic=False):
		self.node = parent.node
		self.panel = parent.GetParent()
		self.dialog = parent
		self.show_basic = show_basic
		scrolledpanel.ScrolledPanel.__init__(self,parent,size=size,style=wx.TAB_TRAVERSAL)
		if scrolling:
			self.SetupScrolling(scroll_x=True, scroll_y=True)
		else:
			self.SetupScrolling(scroll_x=False, scroll_y=False)

		self.widgets = {}

		self.growrows = None
		sz = self.initialize()
		szsp = wx.GridBagSizer(5, 5)
		for i, s in enumerate(sz):
			szsp.Add(s, (i, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
			if self.growrows is not None and self.growrows[i] is True:
				szsp.AddGrowableRow(i)
		szsp.Layout()
		if scrolling:
			self.SetSizer(szsp)
		else:
			self.SetSizerAndFit(szsp)
		self.Layout()
		virtualsize = self.GetVirtualSize()
		self.Fit()
		parent.widgets = self.widgets

	def initialize(self):
		return []
###
#	ScrolledDialog is placed inside Dialog for SettingsDialog so that
#	it can be fit on 12" laptop.  As a result, some of the functions are
#	only availabe at dialog lever and another level called scrsettings
#	is included as a child of the dialog where settings sizers are difined.
###
class Dialog(wx.Dialog):
	def __init__(self, parent, title=None,show_basic=False):
		self.node = parent.node
		self.show_basic = show_basic
		self.panel = parent

		if title is None:
			title = '%s Settings' % self.node.name
		wx.Dialog.__init__(self, parent, -1, title,
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

		self.widgets = {}

		# buttons
		self.bok = wx.Button(self, wx.ID_OK, '&OK')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.bapply = wx.Button(self, wx.ID_APPLY, '&Apply')
		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(self.bok, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bapply, (0, 2), (1, 1), wx.ALIGN_CENTER)
		if self.show_basic:
			self.ball = wx.Button(self, -1, '&Advanced')
			szbuttons.Add(self.ball, (0, 3), (1, 1), wx.ALIGN_CENTER)
			self.settingsdialogclass = self.__class__

		self.growrows = None

		szmain = wx.GridBagSizer(5, 5)
		# leave some room around the display but not expand if on large screen
		display = wx.DisplaySize()
		self.scrsize = (min(1050,display[0])-150,min(900,display[1])-150)
		self.scrsettings = self.initialize()
		szmain.Add(self.scrsettings, (0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 10)
		szmain.Add(szbuttons, (1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)
		szmain.AddGrowableCol(0)

		self.getNodeSettings()

		# set values
		self.SetSizerAndFit(szmain)
#		self.SetAutoLayout(True)

		self.szmain = szmain

		self.Bind(wx.EVT_BUTTON, self.onSet, self.bok)
		self.Bind(wx.EVT_BUTTON, self.onSet, self.bapply)
		if self.show_basic:
			self.Bind(wx.EVT_BUTTON, self.onSetAll, self.ball)

		# work around event prop.
		self.Bind(leginon.gui.wx.Events.EVT_TEM_CHANGE, self.onPropagateEvent)
		self.Bind(leginon.gui.wx.Events.EVT_CCDCAMERA_CHANGE, self.onPropagateEvent)

		self.bindSettings(self.widgets)

	def Show(self, show):
		if show:
			self.getNodeSettings()
		return wx.Dialog.Show(self, show)

	def ShowModal(self):
		self.getNodeSettings()
		return wx.Dialog.ShowModal(self)

	def bindSettings(self, widgets):
		for widget in widgets.values():
			if widget.__class__ is dict:
				self.bindSettings(widget)
			elif attributes[widget.__class__][2] is not None:
				self.Bind(attributes[widget.__class__][2], self.onModified)

	def initialize(self):
		scr = ScrolledDialog(self,self.scrsize,False,self.show_basic)
		return scr

	def onModified(self, evt):
		if self.getSettings(self.widgets) == self.settings:
			self.bapply.Enable(False)
		else:
			self.bapply.Enable(True)
		evt.Skip()

	def onSet(self, evt):
		try:
			self.setNodeSettings()
			evt.Skip()
		except SettingsError:
			dialog = wx.MessageDialog(self, str(e), 'Settings Error',
				wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

	def onSetAll(self, evt):
		self.onSet(evt)
		dialog = self.settingsdialogclass(self,show_basic=False)
		dialog.ShowModal()
		dialog.Destroy()
		self.getNodeSettings()

	def getSettings(self, widgets):
		settings = {}
		for key, widget in widgets.items():
			if widget.__class__ is dict:
				settings[key] = self.getSettings(widget)
			else:
				settings[key] = getattr(widget, attributes[widget.__class__][0])()
		return settings

	def setSettings(self, widgets, sd):
		for key, widget in widgets.items():
			if widget.__class__ is dict:
				self.setSettings(widget, sd[key])
			else:
				try:
					if key not in sd or sd[key] is None:
						widgetvalue = getattr(widget, attributes[widget.__class__][0])()
						sd[key] = widgetvalue
					else:
						try:
							getattr(widget, attributes[widget.__class__][1])(sd[key])
						except ValueError:
							widgetvalue = getattr(widget, attributes[widget.__class__][0])()
							sd[key] = widgetvalue
				except ValueError:
					raise ValueError('Invalid value %s for widget "%s"' % (sd[key], key))

	def setNodeSettings(self):
		node = self.GetParent().node
		if node is None:
			return
		settings = self.getSettings(self.widgets)
		if settings != self.settings:
			node = self.GetParent().node
			if node is None:
				d = {}
			else:
				d = node.getSettings()
			d.update(settings)
			node.setSettings(d)
			self.settings = settings
			self.bapply.Enable(False)

	def getNodeSettings(self):
		node = self.GetParent().node
		if node is None:
			return

		nodesettings = node.getSettings()
		self.setSettings(self.widgets, nodesettings)
		self.settings = self.getSettings(self.widgets)
		## check if setting the widgets caused values to change during validation
		## if values changed, send them back to node.settings
		if self.settings != nodesettings:
			nodesettings.update(self.settings)
			node.setSettings(nodesettings)

		self.bapply.Enable(False)

	def onPropagateEvent(self, evt):
		self.GetParent().GetEventHandler().AddPendingEvent(evt)

