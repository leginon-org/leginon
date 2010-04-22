import threading
import wx

import leginon.gui.wx.Acquisition
import leginon.gui.wx.Camera
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry
from leginon.gui.wx.Presets import EditPresetOrder
import leginon.gui.wx.tomography.TomographyViewer as TomoViewer
from leginon.gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED

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

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
    def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
    def initialize(self):
        #szs = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
        simusb = wx.StaticBox(self, -1, 'Simulation')
        simusbsz = wx.StaticBoxSizer(simusb, wx.VERTICAL)
        miscsb = wx.StaticBox(self, -1, 'Misc.')
        miscsbsz = wx.StaticBoxSizer(miscsb, wx.VERTICAL)
        modelb = wx.StaticBox(self, -1, 'Model')
        modelbsz = wx.StaticBoxSizer(modelb, wx.VERTICAL)
        optb = wx.StaticBox(self, -1, 'Custom Tilt Axis Model in +/- Directions(d)')
        optbsz = wx.StaticBoxSizer(optb, wx.VERTICAL)

 
        alltiltseries = self.getTiltSeriesChoices()
        self.widgets['simu tilt series'] = wx.Choice(self, -1, choices=alltiltseries)
        simusz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Simulate Data Collection and Prediction of')
        simusz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        simusz.Add(self.widgets['simu tilt series'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        simusbsz.Add(simusz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

        self.widgets['use lpf'] = wx.CheckBox(self, -1, 'Use lpf in peak finding of tilt image correlation')
        self.widgets['use tilt'] = wx.CheckBox(self, -1, 'Use tilt info to stretch images')
        self.widgets['taper size'] = IntEntry(self, -1, min=0, allownone=False, chars=3, value='10')
        tapersz = wx.GridBagSizer(5,5)
        lab = wx.StaticText(self, -1, 'edge tapered upto')
        tapersz.Add(lab, (0,0), (1,1))
        tapersz.Add(self.widgets['taper size'], (0,1), (1,1))
        lab = wx.StaticText(self, -1, '% image length')
        tapersz.Add(lab, (0,2), (1,1))
        miscsz = wx.GridBagSizer(5, 10)
        miscsz.Add(self.widgets['use lpf'], (0, 0), (1, 1), wx.ALIGN_CENTER)
        miscsz.Add(self.widgets['use tilt'], (1, 0), (1, 1), wx.ALIGN_CENTER)
        miscsz.Add(tapersz, (2, 0), (1, 1), wx.ALIGN_CENTER)
        #miscsz.Add(self.widgets['measure defocus'], (5, 0), (1, 1), wx.ALIGN_CENTER)
        miscsz.AddGrowableRow(0)
        miscsz.AddGrowableRow(1)
        miscsz.AddGrowableCol(0)

        miscsbsz.Add(miscsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

        modelmags = self.getMagChoices()
        self.widgets['model mag'] = wx.Choice(self, -1, choices=modelmags)
        self.widgets['phi'] = FloatEntry(self, -1, allownone=False,
            chars=4, value='0.0')
        self.widgets['phi2'] = FloatEntry(self, -1, allownone=False,
            chars=4, value='0.0')
        self.widgets['offset'] = FloatEntry(self, -1, allownone=False,
            chars=6, value='0.0')
        self.widgets['offset2'] = FloatEntry(self, -1, allownone=False,
            chars=6, value='0.0')
        self.widgets['z0 error'] = FloatEntry(self, -1, min=0.0,
            allownone=False, chars=6, value='2e-6')
        self.widgets['fixed model'] = wx.CheckBox(self, -1, 'Keep the tilt axis parameters fixed')
        self.widgets['fit data points'] = IntEntry(self, -1, min=4, allownone=False, chars=5, value='4')

        magsz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Initialize with the model of')
        magsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        magsz.Add(self.widgets['model mag'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        phisz = wx.GridBagSizer(2, 2)
        phisz.AddGrowableCol(0)
        label = wx.StaticText(self, -1, 'Tilt Axis from Y')
        phisz.Add(label, (0, 0), (2, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, '+d')
        phisz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        phisz.Add(self.widgets['phi'],
                   (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, '-d')
        phisz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        phisz.Add(self.widgets['phi2'],
                   (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'degs')
        phisz.Add(label, (0, 3), (2, 1), wx.ALIGN_CENTER_VERTICAL)

        offsetsz = wx.GridBagSizer(2, 2)
        label = wx.StaticText(self, -1, 'Offset:')
        offsetsz.Add(label, (0, 0), (2, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, '+d')
        offsetsz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        offsetsz.Add(self.widgets['offset'],
                   (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'um')
        offsetsz.Add(label, (0, 3), (2, 1), wx.ALIGN_CENTER_VERTICAL)
        label = wx.StaticText(self, -1, '-d')
        offsetsz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        offsetsz.Add(self.widgets['offset2'],
                   (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        optsz = wx.GridBagSizer(5, 10)
        optsz.Add(phisz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        optsz.Add(offsetsz, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        optbsz.Add(optsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)
        optsz.AddGrowableCol(0)
        
        zsz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Allow' )
        zsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        zsz.Add(self.widgets['z0 error'],
                   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'um of z0 jump between models' )
        zsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        fsz = wx.GridBagSizer(5, 5)
        label = wx.StaticText(self, -1, 'Smooth' )
        fsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        fsz.Add(self.widgets['fit data points'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
        label = wx.StaticText(self, -1, 'tilts (>=4) for defocus prediction' )
        fsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

        modelsz = wx.GridBagSizer(5, 5)
        modelsz.Add(magsz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        modelsz.Add(optbsz, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        modelsz.Add(zsz, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        modelsz.Add(self.widgets['fixed model'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
        modelsz.Add(fsz, (4, 0), (1, 1), wx.ALIGN_RIGHT)

        modelbsz.Add(modelsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)
        modelsz.AddGrowableCol(0)

        sz = wx.GridBagSizer(5, 5)
        sz.Add(simusbsz, (0, 0), (1, 2), wx.EXPAND)
        sz.Add(miscsbsz, (1, 0), (1, 1), wx.EXPAND)
        sz.Add(modelbsz, (1, 1), (1, 1), wx.EXPAND)
        sz.AddGrowableRow(0)
        sz.AddGrowableRow(1)
        sz.AddGrowableCol(0)
        sz.AddGrowableCol(1)

        self.Bind(wx.EVT_CHECKBOX, self.onFixedModel, self.widgets['fixed model'])
        return [sz]

    def onFixedModel(self, evt):
        state = evt.IsChecked()
        self.widgets['fit data points'].Enable(state)

    def getTiltSeriesChoices(self):
        try:
          numbers = self.node.getTiltSeriesNumbers()
          choices = [str(int(m)) for m in numbers]
        except:
          choices = ['1']
          raise
        return choices

    def getMagChoices(self):
    		choices = ['saved value for this series','this preset and lower mags', 'only this preset','custom values']
    		try:
					mags = self.node.instrument.tem.Magnifications
    		except:
    			mags = []
    		choices.extend( [str(int(m)) for m in mags])
    		return choices

class Panel(leginon.gui.wx.Acquisition.Panel):
    settingsdialogclass = SettingsDialog
    def __init__(self, *args, **kwargs):
        leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)
        self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_BROWSE_IMAGES, False)
        self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CHECK_DOSE,
                             'dose',
                             shortHelpString='Check dose')
        self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
                             'refresh', shortHelpString='Reset Learning')

        self.toolbar.Bind(wx.EVT_TOOL, self.onResetTiltSeriesList,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)

        self.imagepanel = ImagePanel(self.viewer)

    def addImagePanel(self):
        self.viewer = TomoViewer.Viewer(self, -1)
        self.szmain.Add(self.viewer, (1, 0), (1, 1), wx.EXPAND)

    def onNodeInitialized(self):
        leginon.gui.wx.Acquisition.Panel.onNodeInitialized(self)
        self.toolbar.Bind(wx.EVT_TOOL,
                          self.onCheckDose,
                          id=leginon.gui.wx.ToolBar.ID_CHECK_DOSE)

    def onCheckDose(self, evt):
        threading.Thread(target=self.node.checkDose).start()

    def onResetTiltSeriesList(self, evt):
        self.node.resetTiltSeriesList()

