import wx
import gui.wx.Acquisition
import gui.wx.Camera
import gui.wx.Settings
import gui.wx.ToolBar
from gui.wx.Entry import Entry, FloatEntry, IntEntry
from gui.wx.Presets import EditPresetOrder
import gui.wx.tomography.TomographyViewer as TomoViewer

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
    def initialize(self):
        szs = gui.wx.Acquisition.SettingsDialog.initialize(self)

        self.widgets['tilt min'] = FloatEntry(self, -1,
                                               allownone=False,
                                               chars=7,
                                               value='0.0')
        self.widgets['tilt max'] = FloatEntry(self, -1,
                                               allownone=False,
                                               chars=7,
                                               value='0.0')
        self.widgets['tilt start'] = FloatEntry(self, -1,
                                                 allownone=False,
                                                 chars=7,
                                                 value='0.0')
        self.widgets['tilt step'] = FloatEntry(self, -1,
                                                allownone=False,
                                                chars=7,
                                                value='0.0')

        tiltsz = wx.GridBagSizer(5, 10)
        label = wx.StaticText(self, -1, 'Min.:')
        tiltsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        tiltsz.Add(self.widgets['tilt min'], (0, 1), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'Max.:')
        tiltsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        tiltsz.Add(self.widgets['tilt max'], (0, 3), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'degree(s)')
        tiltsz.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'Start:')
        tiltsz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        tiltsz.Add(self.widgets['tilt start'], (1, 1), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'Step:')
        tiltsz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        tiltsz.Add(self.widgets['tilt step'], (1, 3), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'degree(s)')
        tiltsz.Add(label, (1, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        tiltsb = wx.StaticBox(self, -1, 'Tilt')
        tiltsbsz = wx.StaticBoxSizer(tiltsb, wx.VERTICAL)
        tiltsbsz.Add(tiltsz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.widgets['cosine exposure'] = wx.CheckBox(self, -1, 'Cosine')

        self.widgets['thickness value'] = FloatEntry(self, -1,
                                                      min=0.0,
                                                      allownone=False,
                                                      chars=7,
                                                      value='100.0')
        expsz = wx.GridBagSizer(5, 10)
        expsz.Add(self.widgets['cosine exposure'], (0, 0), (1, 3),
                    wx.ALIGN_CENTER)
        label = wx.StaticText(self, -1, 'Thickness')
        expsz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        expsz.Add(self.widgets['thickness value'], (1, 1), (1, 1),
                    wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'nm')
        expsz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        expsz.AddGrowableCol(0)

        expsb = wx.StaticBox(self, -1, 'Exposure')
        expsbsz = wx.StaticBoxSizer(expsb, wx.VERTICAL)
        expsbsz.Add(expsz, 0, wx.EXPAND|wx.ALL, 5)

        presets = self.node.presetsclient.getPresetNames()
        self.widgets['registration preset order'] = EditPresetOrder(self, -1)
        self.widgets['registration preset order'].storder.SetLabel('Registration Presets Order')
        self.widgets['registration preset order'].setChoices(presets)

        self.widgets['run buffer cycle'] = wx.CheckBox(self, -1, 'Run buffer cycle before collection')
        self.widgets['align zero loss peak'] = wx.CheckBox(self, -1, 'Align zero loss peak after collection')

        miscsz = wx.GridBagSizer(5, 10)
        miscsz.Add(self.widgets['registration preset order'],
                   #(0, 0), (1, 2), wx.ALIGN_CENTER)
                   (0, 0), (1, 1), wx.ALIGN_CENTER)
        miscsz.Add(self.widgets['run buffer cycle'],
                   (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        miscsz.Add(self.widgets['align zero loss peak'],
                   (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        miscsz.AddGrowableCol(0)

        miscsb = wx.StaticBox(self, -1, 'Misc.')
        miscsbsz = wx.StaticBoxSizer(miscsb, wx.VERTICAL)
        miscsbsz.Add(miscsz, 0, wx.EXPAND|wx.ALL, 5)

        sz = wx.GridBagSizer(10, 10)
        sz.Add(tiltsbsz, (0, 0), (1, 1), wx.EXPAND)
        sz.Add(expsbsz, (1, 0), (1, 1), wx.EXPAND)
        sz.Add(miscsbsz, (0, 1), (2, 1), wx.EXPAND)

        return szs + [sz]

class Panel(gui.wx.Acquisition.Panel):
    settingsdialogclass = SettingsDialog
    def __init__(self, parent, name):
        gui.wx.Acquisition.Panel.__init__(self, parent, -1)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_BROWSE_IMAGES, False)

    def addImagePanel(self):
        self.viewer = TomoViewer.Viewer(self, -1)
        self.szmain.Add(self.viewer, (1, 0), (1, 1), wx.EXPAND)

