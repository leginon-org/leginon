# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Focuser.py,v $
# $Revision: 1.35 $
# $Name: not supported by cvs2svn $
# $Date: 2005-12-08 00:55:10 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY
from gui.wx.Presets import EditPresetOrder
import gui.wx.Acquisition
import gui.wx.Dialog
import gui.wx.Events
import gui.wx.Icons
import gui.wx.ImageViewer
import gui.wx.ToolBar
import gui.wx.FocusSequence

UpdateImagesEventType = wx.NewEventType()
ManualCheckEventType = wx.NewEventType()
ManualCheckDoneEventType = wx.NewEventType()

EVT_UPDATE_IMAGES = wx.PyEventBinder(UpdateImagesEventType)
EVT_MANUAL_CHECK = wx.PyEventBinder(ManualCheckEventType)
EVT_MANUAL_CHECK_DONE = wx.PyEventBinder(ManualCheckDoneEventType)

class UpdateImagesEvent(wx.PyCommandEvent):
    def __init__(self, source):
        wx.PyCommandEvent.__init__(self, UpdateImagesEventType, source.GetId())
        self.SetEventObject(source)

class ManualCheckEvent(wx.PyCommandEvent):
    def __init__(self, source):
        wx.PyCommandEvent.__init__(self, ManualCheckEventType, source.GetId())
        self.SetEventObject(source)

class ManualCheckDoneEvent(wx.PyCommandEvent):
    def __init__(self, source):
        wx.PyCommandEvent.__init__(self, ManualCheckDoneEventType, source.GetId())
        self.SetEventObject(source)

class Panel(gui.wx.Acquisition.Panel):
    icon = 'focuser'
    imagepanelclass = gui.wx.ImageViewer.TargetImagePanel
    def __init__(self, parent, name):
        gui.wx.Acquisition.Panel.__init__(self, parent, name)

        self.toolbar.InsertTool(2, gui.wx.ToolBar.ID_FOCUS_SEQUENCE, 'focus_sequence',
                                shortHelpString='Focus Sequence')
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(gui.wx.ToolBar.ID_MANUAL_FOCUS, 'manualfocus',
                             shortHelpString='Manual Focus')
        # correlation image
        self.imagepanel.addTypeTool('Correlation', display=True)
        self.imagepanel.addTargetTool('Peak', wx.Color(255, 128, 0))

        self.szmain.Layout()

    def onNodeInitialized(self):
        self.manualdialog = ManualFocusDialog(self, self.node)
        self.Bind(EVT_MANUAL_CHECK, self.onManualCheck, self)
        self.Bind(EVT_MANUAL_CHECK_DONE, self.onManualCheckDone, self)

        gui.wx.Acquisition.Panel.onNodeInitialized(self)

        self.toolbar.Bind(wx.EVT_TOOL, self.onFocusSequenceTool,
                          id=gui.wx.ToolBar.ID_FOCUS_SEQUENCE)
        self.toolbar.Bind(wx.EVT_TOOL, self.onManualFocusTool,
                          id=gui.wx.ToolBar.ID_MANUAL_FOCUS)

    def onSettingsTool(self, evt):
        dialog = SettingsDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def onFocusSequenceTool(self, evt):
        preset_names = self.node.presetsclient.getPresetNames()
        if not preset_names:
            self.node.logger.error('No presets available for focus settings.')
            return
        focus_methods = self.node.focus_methods
        correction_types = self.node.correction_types.keys()
        correction_types.sort()
        correlation_types = self.node.correlation_types
        default_setting = self.node.default_setting
        sequence = self.node.getFocusSequence()
        dialog_settings = gui.wx.FocusSequence.DialogSettings(
            preset_names,
            focus_methods,
            correction_types,
            correlation_types,
            default_setting,
            sequence)
        title = 'Focus Sequence (%s)' % self.node.name
        dialog = gui.wx.FocusSequence.Dialog(self, title, dialog_settings)
        if dialog.ShowModal() == wx.ID_OK:
            dialog.saveCurrent()
            self.node.setFocusSequence(dialog.settings.sequence)
        dialog.Destroy()

    def onManualFocusTool(self, evt):
        self.node.manualNow()

    def onManualCheck(self, evt):
        #self.manualdialog.MakeModal(True)
        self.manualdialog.Raise()
        self.manualdialog.Show()

    def onManualCheckDone(self, evt):
        self.manualdialog.Show(False)
        #self.manualdialog.MakeModal(False)

    def setManualImage(self, image, typename, stats={}):
        evt = gui.wx.Events.SetImageEvent(image, typename, stats)
        self.manualdialog.GetEventHandler().AddPendingEvent(evt)

    def manualUpdated(self):
        self.manualdialog.manualUpdated()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
    def initialize(self):
        sizers = gui.wx.Acquisition.SettingsDialog.initialize(self)

        sizer = wx.GridBagSizer(5, 5)
        self.widgets['melt time'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=4, value='0.0')
        melt_sizer = wx.GridBagSizer(5, 5)
        melt_sizer.Add(self.widgets['melt time'], (0, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        melt_sizer.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        self.widgets['acquire final'] = \
                wx.CheckBox(self, -1, 'Acquire post-focus image')
        label = wx.StaticText(self, -1, 'Melt time:')
        sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(melt_sizer, (0, 1), (1, 1), wx.ALIGN_CENTER)
        sizer.Add(self.widgets['acquire final'], (1, 0), (1, 2),
                  wx.ALIGN_CENTER)

        sb = wx.StaticBox(self, -1, 'Focusing')
        sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
        sbsz.Add(sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        return sizers + [sbsz]


class ManualFocusSettingsDialog(gui.wx.Dialog.Dialog):
    def onInitialize(self):
        self.maskradius = FloatEntry(self, -1, allownone=False,
                                                                                        chars=6,
                                                                                        value='0.01')

        self.increment = FloatEntry(self, -1, min=0.0,
                                                                                    allownone=False,
                                                                                    chars=6,
                                                                                    value='5e-7')

        label = wx.StaticText(self, -1, 'Mask radius:')
        self.sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        self.sz.Add(self.maskradius, (0, 1), (1, 1),
                                wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, '% of image')
        self.sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        label = wx.StaticText(self, -1, 'Increment:')
        self.sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        self.sz.Add(self.increment, (1, 1), (1, 1),
                                wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'm')
        self.sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        self.addButton('OK', wx.ID_OK)
        self.addButton('Cancel', wx.ID_CANCEL)

class ManualFocusDialog(wx.MiniFrame):
    def __init__(self, parent, node, title='Manual Focus'):
        wx.MiniFrame.__init__(self, parent, -1, title,
                                                    style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)
        self.node = node

        self.toolbar = wx.ToolBar(self, -1)

        bitmap = gui.wx.Icons.icon('settings')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS, bitmap,
                                                    shortHelpString='Settings')

        self.toolbar.AddSeparator()

        bitmap = gui.wx.Icons.icon('play')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY, bitmap,
                                                    shortHelpString='Play')
        bitmap = gui.wx.Icons.icon('pause')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_PAUSE, bitmap,
                                                    shortHelpString='Pause')
        bitmap = gui.wx.Icons.icon('stop')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_STOP, bitmap,
                                                    shortHelpString='Stop')

        self.toolbar.AddSeparator()

        self.parameter = wx.Choice(self.toolbar, -1, choices=['Defocus', 'Stage Z'])
        self.parameter.SetStringSelection('Defocus')
        self.toolbar.AddControl(self.parameter)
        bitmap = gui.wx.Icons.icon('plus')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_PLUS, bitmap,
                                                    shortHelpString='Increment up')
        bitmap = gui.wx.Icons.icon('minus')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_MINUS, bitmap,
                                                    shortHelpString='Increment down')

        self.toolbar.AddSeparator()

        self.value = FloatEntry(self.toolbar, -1, allownone=False, chars=6,
                                                        value='0.0')
        self.toolbar.AddControl(self.value)
        self.toolbar.AddControl(wx.StaticText(self.toolbar, -1, ' m'))
        bitmap = gui.wx.Icons.icon('instrumentset')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_VALUE, bitmap,
                                                    shortHelpString='Set instrument')

        self.toolbar.AddSeparator()

        bitmap = gui.wx.Icons.icon('instrumentsetnew')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_RESET, bitmap,
                                                    shortHelpString='Reset Defocus')

        self.toolbar.AddSeparator()

        bitmap = gui.wx.Icons.icon('instrumentget')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_GET_INSTRUMENT, bitmap,
                                                    shortHelpString='Eucentric from instrument')

        bitmap = gui.wx.Icons.icon('instrumentset')
        self.toolbar.AddTool(gui.wx.ToolBar.ID_SET_INSTRUMENT, bitmap,
                                                    shortHelpString='Eucentric to instrument')

        self.toolbar.Realize()

        self.SetToolBar(self.toolbar)

        self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)
        self.imagepanel.addTypeTool('Image', display=True)
        self.imagepanel.addTypeTool('Power', display=True)
        self.imagepanel.selectiontool.setDisplayed('Power', True)

        self.statusbar = wx.StatusBar(self, -1)
        self.SetStatusBar(self.statusbar)

        self.Fit()

        self.settingsdialog = ManualFocusSettingsDialog(self,
                                                                                                        'Manual Focus Settings',
                                                                                                        'Settings')

        self.Bind(gui.wx.Events.EVT_PLAYER, self.onPlayer)
        self.Bind(wx.EVT_TOOL, self.onSettingsTool, id=gui.wx.ToolBar.ID_SETTINGS)
        self.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
        self.Bind(wx.EVT_TOOL, self.onPauseTool, id=gui.wx.ToolBar.ID_PAUSE)
        self.Bind(wx.EVT_TOOL, self.onStopTool, id=gui.wx.ToolBar.ID_STOP)
        self.Bind(wx.EVT_TOOL, self.onPlusTool, id=gui.wx.ToolBar.ID_PLUS)
        self.Bind(wx.EVT_TOOL, self.onMinusTool, id=gui.wx.ToolBar.ID_MINUS)
        self.Bind(wx.EVT_TOOL, self.onValueTool, id=gui.wx.ToolBar.ID_VALUE)
        self.Bind(wx.EVT_TOOL, self.onResetTool, id=gui.wx.ToolBar.ID_RESET)
        self.Bind(wx.EVT_TOOL, self.onGetInstrumentTool,
                            id=gui.wx.ToolBar.ID_GET_INSTRUMENT)
        self.Bind(wx.EVT_TOOL, self.onSetInstrumentTool,
                            id=gui.wx.ToolBar.ID_SET_INSTRUMENT)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
        self.Bind(gui.wx.Events.EVT_MANUAL_UPDATED, self.onManualUpdated)

    def onSettingsTool(self, evt):
        self.settingsdialog.maskradius.SetValue(self.node.maskradius)
        self.settingsdialog.increment.SetValue(self.node.increment)
        #self.MakeModal(False)
        if self.settingsdialog.ShowModal() == wx.ID_OK:
            self.node.maskradius = self.settingsdialog.maskradius.GetValue()
            self.node.increment = self.settingsdialog.increment.GetValue()
        #self.MakeModal(True)

    def onPlayTool(self, evt):
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
        self.node.manualplayer.play()

    def onPauseTool(self, evt):
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
        self.node.manualplayer.pause()

    def onStopTool(self, evt):
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)
        self.node.manualplayer.stop()

    def onPlayer(self, evt):
        if evt.state == 'play':
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, True)
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, True)
        elif evt.state == 'pause':
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, False) 
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, True)
        elif evt.state == 'stop':
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_PAUSE, True) 
            self.toolbar.EnableTool(gui.wx.ToolBar.ID_STOP, False)

    def _manualEnable(self, enable):
        self.toolbar.Enable(enable)

    def onManualUpdated(self, evt):
        self._manualEnable(True)

    def manualUpdated(self):
        evt = gui.wx.Events.ManualUpdatedEvent()
        self.GetEventHandler().AddPendingEvent(evt)

    def onPlusTool(self, evt):
        self._manualEnable(False)
        par = self.parameter.GetStringSelection()
        threading.Thread(target=self.node.uiFocusUp, args=(par,)).start()

    def onMinusTool(self, evt):
        self._manualEnable(False)
        par = self.parameter.GetStringSelection()
        threading.Thread(target=self.node.uiFocusDown, args=(par,)).start()

    def onValueTool(self, evt):
        self._manualEnable(False)
        value = self.value.GetValue()
        threading.Thread(target=self.node.setFocus, args=(value,)).start()

    def onResetTool(self, evt):
        self._manualEnable(False)
        threading.Thread(target=self.node.uiResetDefocus).start()

    def onGetInstrumentTool(self, evt):
        self._manualEnable(False)
        threading.Thread(target=self.node.uiEucentricFromScope).start()

    def onSetInstrumentTool(self, evt):
        self._manualEnable(False)
        threading.Thread(target=self.node.uiChangeToEucentric).start()

    def onClose(self, evt):
        self.node.manualplayer.stop()

    def onSetImage(self, evt):
        self.imagepanel.setImageType(evt.typename, evt.image)

if __name__ == '__main__':
    class App(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'Focuser Test')
            dialog = ManualFocusDialog(frame)
            frame.Fit()
            self.SetTopWindow(frame)
            frame.Show()
            dialog.Show()
            return True

    app = App(0)
    app.MainLoop()

