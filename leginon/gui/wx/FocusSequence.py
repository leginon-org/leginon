# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import math
import wx

import leginon.gui.wx.Choice
import leginon.gui.wx.Dialog
import leginon.gui.wx.Entry
import leginon.gui.wx.ListBox
import leginon.gui.wx.Presets

class DialogSettings(object):
	def __init__(self, preset_names,
					   focus_methods,
					   correction_types,
					   correlation_types,
					   default_setting,
					   sequence):
		self.preset_names = preset_names
		self.focus_methods = focus_methods
		self.correction_types = correction_types
		self.correlation_types = correlation_types
		self.default_setting = default_setting
		self.sequence = sequence
		self.reset_types = ['Default', 'Always', 'Never']

class EditListBox(leginon.gui.wx.ListBox.EditListBox):
	def __init__(self, parent, id, label, choices, **kwargs):
		leginon.gui.wx.ListBox.EditListBox.__init__(self, parent, id, label, choices,
											**kwargs)
		self.dialog = parent

	def onInsert(self, evt):
		try:
			string = self.textentry.GetValue()
		except ValueError:
			return
		
		n = self.listbox.FindString(string)
		if n != wx.NOT_FOUND:
			return

		result = leginon.gui.wx.ListBox.EditListBox.onInsert(self, evt)

		n = self.listbox.FindString(string)
		self.dialog.insertDefaultSetting(n, string)

		return result

	def onSelect(self, evt):
		name = evt.GetString()
		self.dialog.select(name)
		return leginon.gui.wx.ListBox.EditListBox.onSelect(self, evt)

	def onDelete(self, evt):
		result = leginon.gui.wx.ListBox.EditListBox.onDelete(self, evt)
		self.dialog.removeCurrent()
		name = self.getSelected()
		if name is None:
			self.dialog.setDefaultSetting()
			self.dialog.enableSetting(False)
		else:
			self.dialog.select(name)
		return result

	def onUp(self, evt):
		self.dialog.move(-1)
		return leginon.gui.wx.ListBox.EditListBox.onUp(self, evt)

	def onDown(self, evt):
		self.dialog.move(1)
		return leginon.gui.wx.ListBox.EditListBox.onDown(self, evt)

class Dialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, title, settings, **kwargs):
		self.settings = settings
		self.current_setting = None
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, title, **kwargs)

	def move(self, direction):
		if self.current_setting is None:
			pass
		i = self.settings.sequence.index(self.current_setting)
		del self.settings.sequence[i]
		self.settings.sequence.insert(i + direction, self.current_setting)

	def removeCurrent(self):
		self.settings.sequence.remove(self.current_setting)

	def saveCurrent(self):
		setting = self.getSetting()
		if self.current_setting is not None:
			self.current_setting.update(setting)

	def select(self, name):
		self.saveCurrent()
		i, setting = self.getSettingByName(name)
		self.current_setting = setting
		self.setSetting(setting)
		self.enableSetting(True)
		self.onFocusMethodChoice()

	def getSettingByName(self, name):
		for i, setting in enumerate(self.settings.sequence):
			if setting['name'] == name:
				return i, setting
		raise ValueError

	def getSetting(self):
		setting = {}
		setting['switch'] = self.switch_checkbox.GetValue()
		setting['preset name'] = self.preset_choice.GetStringSelection()
		setting['focus method'] = self.focus_method_choice.GetStringSelection()
		setting['tilt'] = self.tilt_entry.GetValue()
		if setting['focus method'] == 'Stage Tilt':
			setting['tilt'] = math.radians(setting['tilt'])
		setting['correlation type'] = \
			self.correlation_type_choice.GetStringSelection()
		setting['fit limit'] = self.fit_limit_entry.GetValue()
		setting['delta min'] = self.delta_min_entry.GetValue()
		setting['delta max'] = self.delta_max_entry.GetValue()
		setting['correction type'] = \
			self.correction_type_choice.GetStringSelection()
		setting['stig correction'] = self.correct_astig_checkbox.GetValue()
		setting['stig defocus min'] = self.stig_defocus_min_entry.GetValue()
		setting['stig defocus max'] = self.stig_defocus_max_entry.GetValue()
		setting['check drift'] = self.check_drift_checkbox.GetValue()
		setting['drift threshold'] = self.drift_threshold_entry.GetValue()
		setting['reset defocus'] = self.getResetSetting()

		return setting

	def getResetSetting(self):
#		choice = self.reset_choice.GetStringSelection()
		choice = None
		if choice == 'Always':
			return True
		elif choice == 'Never':
			return False
		else:
			return None

	def setResetSetting(self, value):
		if value is True:
			choice = 'Always'
		elif value is False:
			choice = 'Never'
		else:
			choice = 'Default'
#		self.reset_choice.SetStringSelection(choice)

	def setSetting(self, setting):
		## FIX CRAP
		for key,value in setting.items():
			if value is None:
				if key in self.settings.default_setting:
					setting[key] = self.settings.default_setting[key]

		self.switch_checkbox.SetValue(setting['switch'])
		self.preset_choice.SetStringSelection(setting['preset name'])
		self.focus_method_choice.SetStringSelection(setting['focus method'])
		#self.tilt_entry.SetValue(0.0)
		if setting['focus method'] == 'Stage Tilt':
			angle = math.degrees(setting['tilt'])
		else:
			angle = setting['tilt']
		self.tilt_entry.SetValue(angle)
		self.correlation_type_choice.SetStringSelection(
													setting['correlation type'])
		self.fit_limit_entry.SetValue(setting['fit limit'])
		self.delta_min_entry.SetValue(setting['delta min'])
		self.delta_max_entry.SetValue(setting['delta max'])
		self.correction_type_choice.SetStringSelection(
													setting['correction type'])
		self.correct_astig_checkbox.SetValue(setting['stig correction'])
		self.stig_defocus_min_entry.SetValue(setting['stig defocus min'])
		self.stig_defocus_max_entry.SetValue(setting['stig defocus max'])
		self.check_drift_checkbox.SetValue(setting['check drift'])
		self.drift_threshold_entry.SetValue(setting['drift threshold'])
		self.setResetSetting(setting['reset defocus'])

	def insertDefaultSetting(self, i, name):
		setting = self.settings.default_setting.copy()
		setting['name'] = name
		self.settings.sequence.insert(i, setting)

	def setDefaultSetting(self):
		self.setSetting(self.settings.default_setting)

	def enableSetting(self, enable):
		return
		widgets = [
			self.switch_checkbox,
			self.preset_choice,
			self.focus_method_choice,
			self.tilt_entry,
			self.correlation_type_choice,
			self.fit_limit_entry,
			self.delta_min_entry,
			self.delta_max_entry,
			self.correction_type_choice,
			self.correct_astig_checkbox,
			self.stig_defocus_min_entry,
			self.stig_defocus_max_entry,
			self.check_drift_checkbox,
			self.drift_threshold_entry,
#			self.reset_choice,
		]

		[widget.Enable(enable) for widget in widgets]

	def onInitialize(self):
		sizer = self.sz

		self.focus_sequence = EditListBox(self, -1, 'Focus sequence', None)
		self.focus_sequence.setValues([s['name'] for s in self.settings.sequence])
		sizer.Add(self.focus_sequence, (0, 0), (2, 1),
					wx.EXPAND|wx.ALL, 5)
		sizer.AddGrowableCol(0)
		self.switch_checkbox = wx.CheckBox(self, -1, 'Enabled')
		sizer.Add(self.switch_checkbox, (0, 1), (1, 1), wx.EXPAND)

		## Frame for widgets that can be enabled by the "Enabled" button
		sbparam = wx.StaticBox(self, -1)
		paramsizer = wx.GridBagSizer(3, 3)

		label = wx.StaticText(self, -1, 'Preset:')
		paramsizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		preset_names = self.settings.preset_names
		self.preset_choice = leginon.gui.wx.Presets.PresetChoice(self, -1)
		self.preset_choice.setChoices(preset_names)
		paramsizer.Add(self.preset_choice, (0, 1), (1, 1), wx.EXPAND)

		label = wx.StaticText(self, -1, 'Focus method:')
		paramsizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.focus_method_choice = leginon.gui.wx.Choice.Choice(self, -1, choices=self.settings.focus_methods)
		self.focus_method_choice.Bind(wx.EVT_CHOICE, self.onFocusMethodChoice)
		paramsizer.Add(self.focus_method_choice, (1, 1), (1, 1), wx.EXPAND)

		### Frame for widgets that are not enabled for manual focusing
		sbauto = wx.StaticBox(self, -1, '(Autofocus Only)')
		autosizer = wx.GridBagSizer(3, 3)
		self.autowidgets = []

		tiltsizer = wx.GridBagSizer(3, 3)
		label = wx.StaticText(self, -1, 'Tilt:')
		tiltsizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(label)
		self.tilt_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6) 
		tiltsizer.Add(self.tilt_entry, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(self.tilt_entry)
		self.tiltlabel = wx.StaticText(self, -1, 'radians')
		tiltsizer.Add(self.tiltlabel, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(self.tiltlabel)
		autosizer.Add(tiltsizer, (0, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Image registration:')
		self.autowidgets.append(label)
		autosizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.correlation_type_choice = leginon.gui.wx.Choice.Choice(self, -1,
										choices=self.settings.correlation_types)
		autosizer.Add(self.correlation_type_choice, (1, 1), (1, 1), wx.EXPAND)
		self.autowidgets.append(self.correlation_type_choice)
		label = wx.StaticText(self, -1, 'correlation')
		self.autowidgets.append(label)
		autosizer.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Fit limit:')
		self.autowidgets.append(label)
		autosizer.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.fit_limit_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6)
		autosizer.Add(self.fit_limit_entry, (2, 1), (1, 1),
					   wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		self.autowidgets.append(self.fit_limit_entry)

		changelimitsizer = wx.GridBagSizer(3, 3)
		self.delta_min_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6, min=0.0)
		label = wx.StaticText(self, -1, 'Correct for delta Defocus/Z between')
		self.autowidgets.append(label)
		changelimitsizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(self.delta_min_entry)
		changelimitsizer.Add(self.delta_min_entry, (0, 1), (1, 1),
					   wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		self.delta_max_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6, min=0.0)
		label = wx.StaticText(self, -1, 'and')
		self.autowidgets.append(label)
		changelimitsizer.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		changelimitsizer.Add(self.delta_max_entry, (0, 3), (1, 1),
					   wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		self.autowidgets.append(self.delta_max_entry)
		label = wx.StaticText(self, -1, 'meters')
		changelimitsizer.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(label)
		autosizer.Add(changelimitsizer, (3, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Correction type:')
		autosizer.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(label)
		self.correction_type_choice = leginon.gui.wx.Choice.Choice(self, -1, choices=self.settings.correction_types)
		autosizer.Add(self.correction_type_choice, (4, 1), (1, 1), wx.EXPAND)
		self.autowidgets.append(self.correction_type_choice)

#		label = wx.StaticText(self, -1, 'Reset defocus:')
#		autosizer.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		self.autowidgets.append(label)
#		self.reset_choice = leginon.gui.wx.Choice.Choice(self, -1, choices=self.settings.reset_types)
#		autosizer.Add(self.reset_choice, (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		self.autowidgets.append(self.reset_choice)

		### Frame for drift related items
		driftsizer = wx.GridBagSizer(3, 3)
		self.check_drift_checkbox = wx.CheckBox(self, -1,
										   'Wait for drift to be less than')
		self.drift_threshold_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6)
		driftsizer.Add(self.check_drift_checkbox, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(self.check_drift_checkbox)
		driftsizer.Add(self.drift_threshold_entry, (0, 1), (1, 1),
						wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		self.autowidgets.append(self.drift_threshold_entry)
		label = wx.StaticText(self, -1, 'm/s')
		self.autowidgets.append(label)
		driftsizer.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		autosizer.Add(driftsizer, (6, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		### Frame for stig related items
		stigsizer = wx.GridBagSizer(3, 3)
		self.correct_astig_checkbox = wx.CheckBox(self, -1,
									  'Correct astigmatism for defocus between')
		self.stig_defocus_min_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6, min=0.0)
		self.stig_defocus_max_entry = leginon.gui.wx.Entry.FloatEntry(self, -1, chars=6, min=0.0)
		stigsizer.Add(self.correct_astig_checkbox, (0, 0), (1, 1),
					   wx.ALIGN_CENTER_VERTICAL)
		self.autowidgets.append(self.correct_astig_checkbox)
		stigsizer.Add(self.stig_defocus_min_entry, (0, 1), (1, 1),
					   wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		self.autowidgets.append(self.stig_defocus_min_entry)
		label = wx.StaticText(self, -1, 'and')
		self.autowidgets.append(label)
		stigsizer.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		stigsizer.Add(self.stig_defocus_max_entry, (0, 3), (1, 1),
					   wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		self.autowidgets.append(self.stig_defocus_max_entry)
		label = wx.StaticText(self, -1, 'meters')
		self.autowidgets.append(label)
		stigsizer.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		autosizer.Add(stigsizer, (7, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)

		self.autowidgets.append(sbauto)
		self.autobox = wx.StaticBoxSizer(sbauto, wx.VERTICAL)
		self.autobox.Add(autosizer, 1, wx.EXPAND|wx.ALL, 5)
		paramsizer.Add(self.autobox, (2,0), (1,3))

		parambox = wx.StaticBoxSizer(sbparam, wx.VERTICAL)
		parambox.Add(paramsizer, 1, wx.EXPAND|wx.ALL, 5)
		sizer.Add(parambox, (1,1), (1,1))

		#sizer.AddGrowableCol(0)
		#sizer.AddGrowableCol(1)
		#[sizer.AddGrowableRow(i) for i in range(13)]

		self.addButton('OK', wx.ID_OK)
		self.addButton('Cancel', wx.ID_CANCEL)

		if self.settings.sequence:
			setting = self.settings.sequence[0]
			self.setSetting(setting)
			self.focus_sequence.setSelected(setting['name'])
		else:
			self.setDefaultSetting()
			self.enableSetting(False)

		# select first one by default
		if self.settings.sequence:
			self.select(self.settings.sequence[0]['name'])


	def onFocusMethodChoice(self, evt=None):
		method = self.focus_method_choice.GetStringSelection()
		if method == 'Stage Tilt':
			self.enableAuto(True)
			# stage tilt focus measurement can not be used to correct defocus
			if self.correction_type_choice.GetStringSelection()=='Defocus':
				self.correction_type_choice.SetStringSelection('Stage Z') 
			self.fit_limit_entry.Disable()
			self.correct_astig_checkbox.SetValue(False)
			self.correct_astig_checkbox.Disable()
			self.stig_defocus_max_entry.Disable()
			self.stig_defocus_min_entry.Disable()
			self.tiltlabel.SetLabel('degrees')
		if method == 'Beam Tilt':
			self.enableAuto(True)
			self.tiltlabel.SetLabel('radians')
		if method == 'Manual':
			self.enableAuto(False)

	def enableAuto(self, enable):
		for widget in self.autowidgets:
			widget.Enable(enable)


if __name__ == '__main__':
	preset_names = ['Grid', 'Square', 'Hole', 'Exposure']
	focus_methods = ['Manual', 'Beam Tilt', 'Stage Tilt']
	correction_types = ['Defocus', 'Stage Z']
	correlation_types = ['Cross', 'Phase']

	default_setting = {
		'switch': True,
		'preset name': 'Grid',
		'focus method': 'Beam Tilt',
		'tilt': 0.01,
		'correlation type': 'Phase',
		'fit limit': 1000,
		'delta min': 0,
		'delta max': 1e-3,
		'correction type': 'Defocus',
		'stig correction': False,
		'stig defocus min': 2e-6,
		'stig defocus max': 4e-6,
		'check drift': False,
		'drift threshold': 3e-10,
	}

	sequence = [
	{
		'switch': True,
		'name': 'Test 1',
		'preset name': 'Hole',
		'focus method': 'Beam Tilt',
		'tilt': 0.01,
		'correlation type': 'Phase',
		'fit limit': 1000,
		'delta min': 0.0,
		'delta max': 1e-3,
		'correction type': 'Defocus',
		'stig correction': False,
		'stig defocus min': 2e-6,
		'stig defocus max': 4e-6,
		'check drift': True,
		'drift threshold': 3e-10,
		'reset defocus': False,
	}
	]

	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Test Frame')
			values = DialogSettings(
					   preset_names,
					   focus_methods,
					   correction_types,
					   correlation_types,
					   default_setting,
					   sequence)
			dialog = Dialog(frame, 'Focus Sequence Test', values)
			self.SetTopWindow(frame)
			frame.Show()
			dialog.ShowModal()
			dialog.Destroy()
			return True

	app = App(0)
	app.MainLoop()

