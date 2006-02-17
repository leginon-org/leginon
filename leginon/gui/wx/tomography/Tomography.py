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

        tomogramsbsz = self.mAddTomogram()

        presets = self.node.presetsclient.getPresetNames()
        self.widgets['registration preset order'] = EditPresetOrder(self, -1)
        self.widgets['registration preset order'].setChoices(presets)

        #self.widgets['xcf bin'] = IntEntry(self, -1,
        #                                    values=[1, 2, 4, 8],
        #                                    allownone=False,
        #                                    chars=1,
        #                                    value='1')
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
        #label = wx.StaticText(self, -1, 'XCF binning')
        #iscsz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        #iscsz.Add(self.widgets['xcf bin'], (2, 1), (1, 1),
        #           wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
        miscsz.AddGrowableCol(0)

        miscsb = wx.StaticBox(self, -1, 'Misc.')
        miscsbsz = wx.StaticBoxSizer(miscsb, wx.VERTICAL)
        miscsbsz.Add(miscsz, 0, wx.EXPAND|wx.ALL, 5)

        sz = wx.GridBagSizer(10, 10)
        sz.Add(tomogramsbsz, (0, 0), (1, 1), wx.EXPAND)
        sz.Add(miscsbsz, (0, 1), (1, 1), wx.EXPAND)
        sz.Add(tiltsbsz, (1, 0), (1, 1), wx.EXPAND)
        sz.Add(expsbsz, (1, 1), (1, 1), wx.EXPAND)

        return szs + [sz]

    def mAddTomogram(self):
        self.widgets['unsigned data'] = wx.CheckBox(self, -1, 
            'Unsigned', style = wx.ALIGN_RIGHT)
        self.widgets['cryo data'] = wx.CheckBox(self, -1, 
            'Cryo', style = wx.ALIGN_RIGHT)
        self.widgets['label'] = Entry(self, -1, chars=24)
        self.widgets['description'] = Entry(self, -1, style=wx.TE_MULTILINE)

        pDataType = wx.StaticText(self, -1, 'Data Type:')
        pFileName = wx.StaticText(self, -1, 'File Name:')
        pLabel = wx.StaticText(self, -1, 'Description:')

        pSizer = wx.GridBagSizer(vgap=5, hgap=10)
        alignment = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT
        pSizer.Add(pDataType, (0, 0), (1, 1), alignment)
        pSizer.Add(pFileName, (1, 0), (1, 1), alignment)
        pSizer.Add(pLabel, (2, 0), (1, 2), alignment)

        alignment = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT
        pSizer.Add(self.widgets['unsigned data'], (0, 1), (1, 1), alignment)
        pSizer.Add(self.widgets['cryo data'], (0, 2), (1, 1), alignment)

        alignment = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.FIXED_MINSIZE
        pSizer.Add(self.widgets['label'], (1, 1), (1, 2), alignment)
        pSizer.Add(self.widgets['description'], (3, 0), (1, 3), wx.EXPAND)
        pSizer.AddGrowableCol(0)
        pSizer.AddGrowableRow(3)

        tomogramsb = wx.StaticBox(self, -1, 'Tomogram')
        tomogramsbsz = wx.StaticBoxSizer(tomogramsb, wx.VERTICAL)
        tomogramsbsz.Add(pSizer, 1, wx.EXPAND|wx.ALL, 5)
        return tomogramsbsz

class Panel(gui.wx.Acquisition.Panel):
    settingsdialogclass = SettingsDialog
    def __init__(self, parent, name):
        gui.wx.Acquisition.Panel.__init__(self, parent, -1)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_BROWSE_IMAGES, False)

    def addImagePanel(self):
        self.viewer = TomoViewer.Viewer(self, -1)
        self.szmain.Add(self.viewer, (1, 0), (1, 1), wx.EXPAND)

