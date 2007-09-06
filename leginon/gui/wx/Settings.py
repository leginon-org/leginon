# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Settings.py,v $
# $Revision: 1.28 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-06 20:47:12 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Choice import Choice
import gui.wx.Camera
import gui.wx.Entry
import gui.wx.Presets
import wx.lib.filebrowsebutton as filebrowse
import gui.wx.Rings
import gui.wx.TargetTemplate
import gui.wx.Instrument

class SettingsError(Exception):
	pass

attributes = {
	wx.CheckBox: ('GetValue', 'SetValue', wx.EVT_CHECKBOX),
	wx.Choice: ('GetStringSelection', 'SetStringSelection', wx.EVT_CHOICE),
	Choice: ('GetStringSelection', 'SetStringSelection', wx.EVT_CHOICE),
	gui.wx.Entry.Entry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Entry.IntEntry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Entry.FloatEntry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Entry.FloatSequenceEntry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Presets.PresetChoice:
		('GetStringSelection', 'SetStringSelection',
			gui.wx.Presets.EVT_PRESET_CHOICE),
	gui.wx.Presets.PresetOrder:
		('getValues', 'setValues', gui.wx.Presets.EVT_PRESET_ORDER_CHANGED),
	gui.wx.Presets.EditPresetOrder:
		('getValues', 'setValues', gui.wx.Presets.EVT_PRESET_ORDER_CHANGED),
	gui.wx.Camera.CameraPanel:
		('getConfiguration', 'setConfiguration',
			gui.wx.Camera.EVT_CONFIGURATION_CHANGED),
	filebrowse.FileBrowseButton: ('GetValue', 'SetValue', None),
	gui.wx.Rings.Panel: ('getRings', 'setRings', gui.wx.Rings.EVT_RINGS_UPDATED),
	gui.wx.TargetTemplate.Panel: ('getTemplate', 'setTemplate',
																gui.wx.TargetTemplate.EVT_TEMPLATE_UPDATED),
	gui.wx.Instrument.SelectionPanel: ('GetValue', 'SetValue', None),
}

class Dialog(wx.Dialog):
	def __init__(self, parent, title=None):
		self.node = parent.node

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

		self.growrows = None
		sz = self.initialize()

		szmain = wx.GridBagSizer(5, 5)
		for i, s in enumerate(sz):
			szmain.Add(s, (i, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
			if self.growrows is not None and self.growrows[i] is True:
				szmain.AddGrowableRow(i)
		szmain.Add(szbuttons, (i+1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)
		szmain.AddGrowableCol(0)

		self.getNodeSettings()

		# set values
		self.SetSizerAndFit(szmain)
		self.SetAutoLayout(True)

		self.szmain = szmain

		self.Bind(wx.EVT_BUTTON, self.onSet, self.bok)
		self.Bind(wx.EVT_BUTTON, self.onSet, self.bapply)

		# work around event prop.
		self.Bind(gui.wx.Events.EVT_TEM_CHANGE, self.onPropagateEvent)
		self.Bind(gui.wx.Events.EVT_CCDCAMERA_CHANGE, self.onPropagateEvent)

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
		return []

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

