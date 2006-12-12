import threading
import wx
import gui.wx.Acquisition
import gui.wx.Camera
import gui.wx.Settings
import gui.wx.ToolBar
from gui.wx.Entry import Entry, FloatEntry, IntEntry
from gui.wx.Presets import EditPresetOrder
import gui.wx.tomography.TomographyViewer as TomoViewer

class ImagePanel(object):
    def __init__(self, viewer):
        self.viewer = viewer

    def setImage(self, image):
        pass

    def setTargets(self, type_name, targets):
        #if type_name == 'Peak':
        #    self.viewer.setXCShift(targets[0], center=False)
        pass

    def setImageType(self, type_name, image):
        #if type_name == 'Image':
        #    self.viewer.addImage(image)
        #elif type_name == 'Correlation':
        #    self.viewer.setXC(image)
        pass

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
        self.widgets['equally sloped'] = wx.CheckBox(self, -1, 'Use equally sloped (symmetric) angles, power of 2 angles in 180 degree range:')
        self.widgets['equally sloped n'] = IntEntry(self, -1, min=2, allownone=False, chars=5, value='8')

        tiltsz = wx.GridBagSizer(5, 10)

        label = wx.StaticText(self, -1, 'Min.')
        tiltsz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
        label = wx.StaticText(self, -1, 'Max.')
        tiltsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
        label = wx.StaticText(self, -1, 'Start')
        tiltsz.Add(label, (0, 3), (1, 1), wx.ALIGN_CENTER)
        label = wx.StaticText(self, -1, 'Step')
        tiltsz.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER)

        label = wx.StaticText(self, -1, 'Parameters')
        tiltsz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        tiltsz.Add(self.widgets['tilt min'], (1, 1), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        tiltsz.Add(self.widgets['tilt max'], (1, 2), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        tiltsz.Add(self.widgets['tilt start'], (1, 3), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        tiltsz.Add(self.widgets['tilt step'], (1, 4), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'degree(s)')
        tiltsz.Add(label, (1, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        tiltsz.Add(self.widgets['equally sloped'], (2, 0), (1, 4),
                    wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        tiltsz.Add(self.widgets['equally sloped n'], (2, 4), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

        tiltsz.AddGrowableCol(0)

        tiltsb = wx.StaticBox(self, -1, 'Tilt')
        tiltsbsz = wx.StaticBoxSizer(tiltsb, wx.VERTICAL)
        tiltsbsz.Add(tiltsz, 0, wx.EXPAND|wx.ALL, 5)

        self.widgets['dose'] = FloatEntry(self, -1, min=0.0,
                                                    allownone=False,
                                                    chars=7,
                                                    value='200.0')
        self.widgets['min exposure'] = FloatEntry(self, -1, min=0.0,
                                                            allownone=False,
                                                            chars=5,
                                                            value='0.25')
        self.widgets['max exposure'] = FloatEntry(self, -1, min=0.0,
                                                            allownone=False,
                                                            chars=5,
                                                            value='2.0')

        expsz = wx.GridBagSizer(5, 10)
        label = wx.StaticText(self, -1, 'Total dose')
        expsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        expsz.Add(self.widgets['dose'], (0, 1), (1, 2),
                    wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
        #text = u'e\N{SUPERSCRIPT MINUS}/\N{ANGSTROM SIGN}\N{SUPERSCRIPT TWO}'
        #label = wx.StaticText(self, -1, text)
        label = wx.StaticText(self, -1, 'e-/A^2')
        expsz.Add(label, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        label = wx.StaticText(self, -1, 'Min.')
        expsz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER)
        label = wx.StaticText(self, -1, 'Max.')
        expsz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER)

        label = wx.StaticText(self, -1, 'Exposure time')
        expsz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        expsz.Add(self.widgets['min exposure'], (2, 1), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        expsz.Add(self.widgets['max exposure'], (2, 2), (1, 1),
                    wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'seconds')
        expsz.Add(label, (2, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        expsz.AddGrowableCol(0)
        expsz.AddGrowableRow(0)
        expsz.AddGrowableRow(2)

        expsb = wx.StaticBox(self, -1, 'Exposure')
        expsbsz = wx.StaticBoxSizer(expsb, wx.VERTICAL)
        expsbsz.Add(expsz, 1, wx.EXPAND|wx.ALL, 5)

        self.widgets['run buffer cycle'] = wx.CheckBox(self, -1, 'Run buffer cycle')
        self.widgets['align zero loss peak'] = wx.CheckBox(self, -1, 'Align zero loss peak')
        self.widgets['measure dose'] = wx.CheckBox(self, -1, 'Measure dose')

        bcsz = wx.GridBagSizer(5, 10)
        bcsz.Add(self.widgets['run buffer cycle'],
                   (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        bcsz.Add(self.widgets['align zero loss peak'],
                   (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        bcsz.Add(self.widgets['measure dose'],
                   (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        bcsz.AddGrowableRow(0)
        bcsz.AddGrowableRow(1)
        bcsz.AddGrowableRow(2)
        bcsz.AddGrowableCol(0)

        bcsb = wx.StaticBox(self, -1, 'Before Collection')
        bcsbsz = wx.StaticBoxSizer(bcsb, wx.VERTICAL)
        bcsbsz.Add(bcsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

        self.widgets['integer'] = wx.CheckBox(self, -1, 'Scale by')
        self.widgets['intscale'] = FloatEntry(self, -1, min=0.0,
                                                            allownone=False,
                                                            chars=5,
                                                            value='10.0')
        self.widgets['mean threshold'] = FloatEntry(self, -1, min=0.0,
                                                            allownone=False,
                                                            chars=5,
                                                            value='100.0')
        self.widgets['collection threshold'] = FloatEntry(self, -1, min=0.0,
                                                            allownone=False,
                                                            chars=5,
                                                            value='90.0')
        self.widgets['tilt pause time'] = FloatEntry(self, -1, min=0.0,
                                                            allownone=False,
                                                            chars=5,
                                                            value='1.0')
        self.widgets['measure defocus'] = wx.CheckBox(self, -1, 'Measure defocus')


        intsz = wx.GridBagSizer(5, 5)
        intsz.Add(self.widgets['integer'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        intsz.Add(self.widgets['intscale'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, 'to convert to integer')
        intsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        mtsz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Consider images with less than')
        mtsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        mtsz.Add(self.widgets['mean threshold'],
                   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'counts as obstructed')
        mtsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        ctsz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Abort series if one half has collected less than')
        ctsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        ctsz.Add(self.widgets['collection threshold'],
                   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'percent of images')
        ctsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        tptsz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Pause')
        tptsz.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        tptsz.Add(self.widgets['tilt pause time'],
                   (0, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'seconds before each tilt image.')
        tptsz.Add(label, (0, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        miscsz = wx.GridBagSizer(5, 10)
        miscsz.Add(intsz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        miscsz.Add(mtsz, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        miscsz.Add(ctsz, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        miscsz.Add(tptsz, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        miscsz.Add(self.widgets['measure defocus'], (4, 0), (1, 1), wx.ALIGN_CENTER)
        miscsz.AddGrowableRow(0)
        miscsz.AddGrowableRow(1)
        miscsz.AddGrowableRow(2)
        miscsz.AddGrowableCol(0)

        miscsb = wx.StaticBox(self, -1, 'Misc.')
        miscsbsz = wx.StaticBoxSizer(miscsb, wx.VERTICAL)
        miscsbsz.Add(miscsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

        sz = wx.GridBagSizer(10, 10)
        sz.Add(tiltsbsz, (0, 0), (1, 2), wx.EXPAND)
        sz.Add(expsbsz, (1, 0), (1, 1), wx.EXPAND)
        sz.Add(bcsbsz, (1, 1), (1, 1), wx.EXPAND)
        sz.Add(miscsbsz, (2, 0), (1, 2), wx.EXPAND)
        sz.AddGrowableRow(0)
        sz.AddGrowableRow(1)
        sz.AddGrowableCol(0)
        sz.AddGrowableCol(1)

        return szs + [sz]

class Panel(gui.wx.Acquisition.Panel):
    settingsdialogclass = SettingsDialog
    def __init__(self, parent, name):
        gui.wx.Acquisition.Panel.__init__(self, parent, -1)
        self.toolbar.EnableTool(gui.wx.ToolBar.ID_BROWSE_IMAGES, False)
        self.toolbar.AddTool(gui.wx.ToolBar.ID_CHECK_DOSE,
                             'dose',
                             shortHelpString='Check dose')
        self.imagepanel = ImagePanel(self.viewer)

    def addImagePanel(self):
        self.viewer = TomoViewer.Viewer(self, -1)
        self.szmain.Add(self.viewer, (1, 0), (1, 1), wx.EXPAND)

    def onNodeInitialized(self):
        gui.wx.Acquisition.Panel.onNodeInitialized(self)
        self.toolbar.Bind(wx.EVT_TOOL,
                          self.onCheckDose,
                          id=gui.wx.ToolBar.ID_CHECK_DOSE)

    def onCheckDose(self, evt):
        threading.Thread(target=self.node.checkDose).start()

