# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/FocusSequence.py,v $
# $Revision: 1.14 $
# $Name: not supported by cvs2svn $
# $Date: 2006-04-24 21:48:25 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import math
import wx
import gui.wx.Choice
import gui.wx.Dialog
import gui.wx.Entry
import gui.wx.ListBox
import gui.wx.Presets

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

class EditListBox(gui.wx.ListBox.EditListBox):
    def __init__(self, parent, id, label, choices, **kwargs):
        gui.wx.ListBox.EditListBox.__init__(self, parent, id, label, choices,
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

        result = gui.wx.ListBox.EditListBox.onInsert(self, evt)

        n = self.listbox.FindString(string)
        self.dialog.insertDefaultSetting(n, string)

        return result

    def onSelect(self, evt):
        name = evt.GetString()
        self.dialog.select(name)
        return gui.wx.ListBox.EditListBox.onSelect(self, evt)

    def onDelete(self, evt):
        result = gui.wx.ListBox.EditListBox.onDelete(self, evt)
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
        return gui.wx.ListBox.EditListBox.onUp(self, evt)

    def onDown(self, evt):
        self.dialog.move(1)
        return gui.wx.ListBox.EditListBox.onDown(self, evt)

class Dialog(gui.wx.Dialog.Dialog):
    def __init__(self, parent, title, settings, **kwargs):
        self.settings = settings
        self.current_setting = None
        gui.wx.Dialog.Dialog.__init__(self, parent, title, **kwargs)

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
        setting['tilt'] = math.radians(self.tilt_entry.GetValue())
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
        choice = self.reset_choice.GetStringSelection()
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
        self.reset_choice.SetStringSelection(choice)

    def setSetting(self, setting):
        ## fix only necessary if you already have settings saved before
        ## switch was added (None is read from DB instead of bool value)
        #self.switch_checkbox.SetValue(bool(setting['switch']))
        self.switch_checkbox.SetValue(setting['switch'])
        self.preset_choice.SetStringSelection(setting['preset name'])
        self.focus_method_choice.SetStringSelection(setting['focus method'])
        #self.tilt_entry.SetValue(0.0)
        self.tilt_entry.SetValue(math.degrees(setting['tilt']))
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
            self.reset_choice,
        ]

        [widget.Enable(enable) for widget in widgets]
        [label.Enable(enable) for label in self.labels]

    def onInitialize(self):
        self.labels = []

        self.focus_sequence = EditListBox(self, -1, 'Focus sequence', None)
        self.focus_sequence.setValues([s['name'] for s in self.settings.sequence])

        self.switch_checkbox = wx.CheckBox(self, -1, 'Enabled')
        preset_names = self.settings.preset_names
        self.preset_choice = gui.wx.Presets.PresetChoice(self, -1)
        self.preset_choice.setChoices(preset_names)

        self.focus_method_choice = gui.wx.Choice.Choice(self, -1, choices=self.settings.focus_methods)

        self.reset_choice = gui.wx.Choice.Choice(self, -1, choices=self.settings.reset_types)

        ## auto focus only
        self.correction_type_choice = gui.wx.Choice.Choice(self, -1, choices=self.settings.correction_types)
        self.tilt_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6) 
        self.correlation_type_choice = gui.wx.Choice.Choice(self, -1,
                                        choices=self.settings.correlation_types)
        self.fit_limit_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6)
        self.delta_min_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6)
        self.delta_max_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6)
        self.check_drift_checkbox = wx.CheckBox(self, -1,
                                           'Check for drift greater than')
        self.drift_threshold_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6)
        self.correct_astig_checkbox = wx.CheckBox(self, -1,
                                      'Correct astigmatism for defocus between')
        self.stig_defocus_min_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6)
        self.stig_defocus_max_entry = gui.wx.Entry.FloatEntry(self, -1, chars=6)

        drift_sizer = wx.GridBagSizer(3, 3)
        drift_sizer.Add(self.check_drift_checkbox, (0, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        drift_sizer.Add(self.drift_threshold_entry, (0, 1), (1, 1),
                        wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'm/s')
        self.labels.append(label)
        drift_sizer.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        stig_sizer = wx.GridBagSizer(3, 3)
        stig_sizer.Add(self.correct_astig_checkbox, (0, 0), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL)
        stig_sizer.Add(self.stig_defocus_min_entry, (0, 1), (1, 1),
                       wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'and')
        self.labels.append(label)
        stig_sizer.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
        stig_sizer.Add(self.stig_defocus_max_entry, (0, 3), (1, 1),
                       wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'meters')
        self.labels.append(label)
        stig_sizer.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        ##

        sizer = self.sz

        sizer.Add(self.focus_sequence, (0, 0), (9, 1),
                    wx.EXPAND|wx.ALL, 5)

        label = wx.StaticText(self, -1, 'Preset:')
        self.labels.append(label)
        sizer.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Focus method:')
        self.labels.append(label)
        sizer.Add(label, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Reset defocus:')
        self.labels.append(label)
        sizer.Add(label, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        ## these are auto only
        label = wx.StaticText(self, -1, 'Tilt:')
        self.labels.append(label)
        sizer.Add(label, (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Image registration:')
        self.labels.append(label)
        sizer.Add(label, (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Fit limit:')
        self.labels.append(label)
        sizer.Add(label, (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Min. change:')
        self.labels.append(label)
        sizer.Add(label, (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Max. change:')
        self.labels.append(label)
        sizer.Add(label, (8, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Correction type:')
        self.labels.append(label)
        sizer.Add(label, (9, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        ##

        sizer.Add(self.switch_checkbox, (0, 1), (1, 1), wx.EXPAND)
        sizer.Add(self.preset_choice, (1, 2), (1, 1), wx.EXPAND)
        sizer.Add(self.focus_method_choice, (2, 2), (1, 1), wx.EXPAND)
        sizer.Add(self.reset_choice, (3, 2), (1, 1), wx.EXPAND)

        ## These are auto only
        sizer.Add(self.tilt_entry, (4, 2), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'degrees')
        self.labels.append(label)
        sizer.Add(label, (4, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.correlation_type_choice, (5, 2), (1, 1), wx.EXPAND)
        label = wx.StaticText(self, -1, 'correlation')
        self.labels.append(label)
        sizer.Add(label, (5, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.fit_limit_entry, (6, 2), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
        sizer.Add(self.delta_min_entry, (7, 2), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
        sizer.Add(self.delta_max_entry, (8, 2), (1, 1),
                       wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
        sizer.Add(self.correction_type_choice, (9, 2), (1, 1), wx.EXPAND)

        sizer.Add(stig_sizer, (10, 1), (1, 3), wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(drift_sizer, (12, 1), (1, 3), wx.ALIGN_CENTER_VERTICAL)
        ##

        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        [sizer.AddGrowableRow(i) for i in range(13)]

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

if __name__ == '__main__':
    preset_names = ['Grid', 'Square', 'Hole', 'Exposure']
    focus_methods = ['Manual', 'Auto']
    correction_types = ['Defocus', 'Stage Z']
    correlation_types = ['Cross', 'Phase']

    default_setting = {
        'switch': True,
        'preset name': 'Grid',
        'focus method': 'Auto',
        'tilt': 0.01,
        'correlation type': 'Phase',
        'fit limit': 10000,
        'correction type': 'Defocus',
        'stig correction': False,
        'stig defocus min': -4e-6,
        'stig defocus max': -2e-6,
        'check drift': False,
        'drift threshold': 3e-10,
    }

    sequence = [
    {
        'switch': True,
        'name': 'Test 1',
        'preset name': 'Hole',
        'focus method': 'Auto',
        'tilt': 0.01,
        'correlation type': 'Phase',
        'fit limit': 10000,
        'delta min': 0.0,
        'delta max': 1e-3,
        'correction type': 'Defocus',
        'stig correction': False,
        'stig defocus min': -4e-6,
        'stig defocus max': -2e-6,
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

