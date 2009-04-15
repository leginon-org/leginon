# -*- coding: iso-8859-1 -*-
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/DoseCalibrator.py,v $
# $Revision: 1.12 $
# $Name: not supported by cvs2svn $
# $Date: 2006-06-08 00:17:06 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator
import gui.wx.Settings
import gui.wx.ToolBar

class Panel(gui.wx.Calibrator.Panel):
    icon = 'dose'
    def initialize(self):
        gui.wx.Calibrator.Panel.initialize(self)
        self.dialog = None
        self.toolbar.Realize()
        self.toolbar.DeleteTool(gui.wx.ToolBar.ID_ABORT)

    def onCalibrateTool(self, evt):
        self.dialog = DoseCalibrationDialog(self)
        self.dialog.ShowModal()
        self.dialog.Destroy()
        self.dialog = None

class DoseCalibrationDialog(gui.wx.Settings.Dialog):
    def initialize(self):
        return DoseScrolledSettings(self,self.scrsize,False)

class DoseScrolledSettings(gui.wx.Settings.ScrolledDialog):
    def initialize(self):
        gui.wx.Settings.ScrolledDialog.initialize(self)
        sb = wx.StaticBox(self, -1, 'Main Screen')
        sbszscreen = wx.StaticBoxSizer(sb, wx.VERTICAL)
        sb = wx.StaticBox(self, -1, 'Dose Measurement')
        sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
        sb = wx.StaticBox(self, -1, 'Camera Sensitivity')
        sbszcam = wx.StaticBoxSizer(sb, wx.VERTICAL)

        self.bscreenup = wx.Button(self, -1, 'Up')
        self.bscreendown = wx.Button(self, -1, 'Down')

        szscreen = wx.GridBagSizer(5, 5)
        szscreen.Add(self.bscreenup, (0, 0), (1, 1), wx.ALIGN_CENTER)
        szscreen.Add(self.bscreendown, (0, 1), (1, 1), wx.ALIGN_CENTER)
        szscreen.AddGrowableCol(0)
        szscreen.AddGrowableCol(1)

        sbszscreen.Add(szscreen, 0, wx.EXPAND|wx.ALL, 5)

        self.stbeamcurrent = wx.StaticText(self, -1, '')
        self.stscreenmag = wx.StaticText(self, -1, '')
        self.stdoserate = wx.StaticText(self, -1, '')
        self.widgets['beam diameter'] = FloatEntry(self, -1, chars=6)
        self.widgets['scale factor'] = FloatEntry(self, -1, chars=6)
        self.bmeasuredose = wx.Button(self, -1, 'Measure Dose')

        sz = wx.GridBagSizer(5, 5)

        label = wx.StaticText(self, -1, 'Beam current:')
        sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.stbeamcurrent, (0, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label = wx.StaticText(self, -1, 'amps')
        sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        label = wx.StaticText(self, -1, 'Screen magnification:')
        sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.stscreenmag, (1, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

        label = wx.StaticText(self, -1, 'Dose rate:')
        sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.stdoserate, (2, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label = wx.StaticText(self, -1, 'e/A^2/s')
        sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        label = wx.StaticText(self, -1, 'Beam diameter:')
        sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['beam diameter'], (3, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
        label = wx.StaticText(self, -1, 'meters')
        sz.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        label = wx.StaticText(self, -1, 'Screen to beam current scale factor:')
        sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['scale factor'], (4, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

        sz.Add(self.bmeasuredose, (5, 0), (1, 3),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        sz.AddGrowableCol(1)

        sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)

        self.szdose = sz

        self.sensitivity = FloatEntry(self, -1, chars=6)
        self.setsensitivity = wx.Button(self, -1, 'Save')
        self.bcalibratesensitivity = wx.Button(self, -1, 'Calibrate')

        szcam = wx.GridBagSizer(5, 5)
        szcam.Add(self.bcalibratesensitivity, (0, 0), (1, 4),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)
        szcam.AddGrowableCol(0)
        label = wx.StaticText(self, -1, 'Sensitivity:')
        szcam.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        szcam.Add(self.sensitivity, (1, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label = wx.StaticText(self, -1, 'counts/e')
        szcam.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        szcam.Add(self.setsensitivity, (1, 3), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

        sbszcam.Add(szcam, 1, wx.EXPAND|wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.onScreenUpButton, self.bscreenup)
        self.Bind(wx.EVT_BUTTON, self.onScreenDownButton, self.bscreendown)
        self.Bind(wx.EVT_BUTTON, self.onMeasureDoseButton, self.bmeasuredose)
        self.Bind(wx.EVT_BUTTON, self.onSetSensitivityButton, self.setsensitivity)
        self.Bind(wx.EVT_BUTTON, self.onCalibrateSensitivityButton,
                            self.bcalibratesensitivity)

        return [sbszscreen, sbsz, sbszcam]

    def onScreenUpButton(self, evt):
        threading.Thread(target=self.node.screenUp).start()
        #self.node.screenUp()

    def onScreenDownButton(self, evt):
        threading.Thread(target=self.node.screenDown).start()
        #self.node.screenDown()

    def _setDoseResults(self, results):
        try:
            self.stbeamcurrent.SetLabel('%.5g' % results['beam current'])
            self.stscreenmag.SetLabel(str(results['screen magnification']))
            self.stdoserate.SetLabel('%.5g' % (results['dose rate']/1e20))
        except KeyError:
            self.stbeamcurrent.SetLabel('')
            self.stscreenmag.SetLabel('')
            self.stdoserate.SetLabel('')
        self.dialog.szmain.Layout()
        self.Fit()

    def onMeasureDoseButton(self, evt):
        threading.Thread(target=self.node.uiMeasureDoseRate).start()
        #self.node.uiMeasureDoseRate()
        #self._setDoseResults(self.node.results)

    def _setSensitivityResults(self, results):
        if results is None:
            self.sensitivity.SetValue(0)
        else:
            self.sensitivity.SetValue(results)
        self.dialog.szmain.Layout()
        self.Fit()

    def onSetSensitivityButton(self, evt):
        self.node.onSetSensitivity(self.sensitivity.GetValue())

    def onCalibrateSensitivityButton(self, evt):
        threading.Thread(target=self.node.uiCalibrateCamera).start()
        #self.node.uiCalibrateCamera()
        #self._setSensitivityResults(self.node.sens)

if __name__ == '__main__':
    class App(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'Dose Calibration Test')
            panel = Panel(frame, 'Test')
            frame.Fit()
            self.SetTopWindow(frame)
            frame.Show()
            return True

    app = App(0)
    app.MainLoop()

