#!/usr/bin/env python
import wx
import events
import icons
import plugins
import tools
import window
from pyami import arraystats
class Viewer(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.imagewindow = window.Window(self, -1)

        clearplugin = plugins.ClearPlugin(self.imagewindow)
        self.imagewindow.addPlugin(clearplugin)

        self.numarrayplugin = plugins.NumpyPlugin(self.imagewindow)
        self.imagewindow.addPlugin(self.numarrayplugin)

        self.crosshairsplugin = plugins.CrosshairsPlugin(self.imagewindow,
                                                 self.numarrayplugin)
        self.imagewindow.addPlugin(self.crosshairsplugin)

        self.magnifierplugin = plugins.MagnifierPlugin(self.imagewindow,
                                                        self.numarrayplugin)
        self.imagewindow.addPlugin(self.magnifierplugin)

        self.tooltipplugin = plugins.ToolTipPlugin(self.imagewindow)
        self.imagewindow.addPlugin(self.tooltipplugin)

        self.targetsplugin = plugins.TargetsPlugin(self.imagewindow,
                                                    self.numarrayplugin,
                                                    wx.RED)
        self.imagewindow.addPlugin(self.targetsplugin)

        self.tools = Tools(self, -1)

        self.sizer = wx.GridBagSizer(0, 0)
        self.sizer.Add(self.tools, (0, 0), (1, 1), wx.EXPAND)
        self.sizer.Add(self.imagewindow, (1, 0), (1, 1),
                        wx.EXPAND|wx.FIXED_MINSIZE)

        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(1)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)

        self.tools.infobitmap.Bind(wx.EVT_LEFT_UP, self.onInfoBitmap)
        self.tools.displaybitmap.Bind(wx.EVT_LEFT_UP, self.onDisplayBitmap)
        self.tools.valuescalebitmap.Bind(wx.EVT_LEFT_UP,
                                          self.onValueScaleBitmap)

        self.tools.Bind(events.EVT_DISPLAY_CROSSHAIRS, self.onDisplayCrosshairs)
        self.tools.Bind(events.EVT_DISPLAY_MAGNIFIER, self.onDisplayMagnifier)
        self.tools.Bind(events.EVT_SCALE_SIZE, self.onScaleSize)
        self.tools.Bind(events.EVT_FIT_TO_PAGE, self.onFitToPage)
        self.tools.Bind(events.EVT_SCALE_VALUES, self.onScaleValues)

        self.imagewindow.Bind(wx.EVT_MOTION, self.onMotion)

        self.onDisplayCrosshairs()
        self.onDisplayMagnifier()

    def onMotion(self, evt):
        if self.tools.isShown(self.tools.infotool):
            x, y, value = self.numarrayplugin.getXYValue(evt.m_x, evt.m_y)
            tooltip = '(%d, %d)' % (x, y)
            if value is not None:
                tooltip += ' %g' % value
            self.tooltipplugin.setXYText(wx.Point(evt.m_x, evt.m_y), tooltip)
        if self.tools.displaytool.magnifier:
            self.magnifierplugin.setXY(wx.Point(evt.m_x, evt.m_y))

    def getNumpy(self):
        return self.numarrayplugin.getNumpy()

    def setNumpy(self, array,use_extrema=False):
        if array is None:
            extrema = None
            contrastlimit = None
        else:
            min = array.min()
            max = array.max()
            extrema = (min, max)
            mean = array.mean()
            std = array.std()
            imagemin = mean - 3 * std
            imagemax = mean + 3 * std
            if use_extrema:
						    contrastlimit = extrema
            else:
						    contrastlimit = (imagemin,imagemax)
        self.numarrayplugin.setValueRange(contrastlimit)
        self.numarrayplugin.setNumpy(array)
        self.tools.infotool.setStatistics(array)
        self.tools.valuescalebitmap.updateParameters(extrema=extrema,
                                                      fromrange=contrastlimit)
        self.tools.valuescaletool.setValueRange(extrema,
                                                      valuerange=contrastlimit)

    def onDisplayBitmap(self, evt):
        self.tools.toggleShown(self.tools.displaytool)
        self.sizer.Layout()

    def onInfoBitmap(self, evt):
        shown = self.tools.toggleShown(self.tools.infotool)
        self.imagewindow.enablePlugin(self.tooltipplugin, shown)
        self.sizer.Layout()

    def onValueScaleBitmap(self, evt):
        self.tools.toggleShown(self.tools.valuescaletool)
        self.sizer.Layout()

    def onDisplayCrosshairs(self, evt=None):
        if evt is None:
            display = self.tools.displaytool.crosshairs
        else:
            display = evt.display
        self.imagewindow.enablePlugin(self.crosshairsplugin, display)

    def onDisplayMagnifier(self, evt=None):
        if evt is None:
            display = self.tools.displaytool.magnifier
        else:
            display = evt.display
        self.imagewindow.enablePlugin(self.magnifierplugin, display)

    def onScaleSize(self, evt):
        self.numarrayplugin.setScale(evt.scale)

    def onFitToPage(self, evt):
        self.numarrayplugin.fitClient()

    def onScaleValues(self, evt):
        self.tools.valuescalebitmap.updateParameters(fromrange=evt.valuerange)
        self.numarrayplugin.setValueRange(evt.valuerange)

class Tools(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        infobitmap = icons.icon('info')
        displaybitmap = icons.icon('display')

        self.infobitmap = wx.StaticBitmap(self, -1, infobitmap)
        self.displaybitmap = wx.StaticBitmap(self, -1, displaybitmap)
        self.sizescaler = tools.SizeScaler(self, -1)
        self.valuescalebitmap = tools.ValueScaleBitmap(self, -1)

        self.infobitmap.SetToolTipString('Info')
        self.displaybitmap.SetToolTipString('Display')

        self.infotool = tools.Information(self, -1)
        self.displaytool = tools.Display(self, -1)
        self.valuescaletool = tools.ValueScaler(self, -1)

        bitmapsizer = wx.GridBagSizer(0, 10)
        bitmapsizer.Add(self.infobitmap, (0, 0), (1, 1), wx.ALIGN_CENTER)
        bitmapsizer.Add(self.displaybitmap, (0, 1), (1, 1), wx.ALIGN_CENTER)

        self.sizer = wx.GridBagSizer(0, 5)
        self.sizer.SetEmptyCellSize((0, 0))

        self.sizer.Add(bitmapsizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
        self.sizer.Add(self.sizescaler, (0, 1), (1, 1), wx.ALIGN_CENTER)
        self.sizer.Add(self.valuescalebitmap, (0, 2), (1, 1), wx.ALIGN_CENTER)
        self.sizer.Add(wx.StaticLine(self, -1), (1, 0), (1, 3), wx.EXPAND)
        self.sizer.Add(self.infotool, (2, 0), (1, 3), wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1), (3, 0), (1, 3), wx.EXPAND)
        self.sizer.Add(self.displaytool, (4, 0), (1, 3), wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1), (5, 0), (1, 3), wx.EXPAND)
        self.sizer.Add(self.valuescaletool, (6, 0), (1, 3), wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self, -1), (7, 0), (1, 3), wx.EXPAND)

        self.showTool(self.infotool, False)
        self.showTool(self.displaytool, False)
        self.showTool(self.valuescaletool, False)

        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableCol(2)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)

    def showTool(self, tool, show=True):
        self.sizer.Show(tool, show)
        gbpos = self.sizer.GetItemPosition(tool)
        self.sizer.Show(gbpos.GetRow() + 1, show)

    def isShown(self, tool):
        return self.sizer.IsShown(tool)

    def toggleShown(self, tool):
        show = not self.sizer.IsShown(tool)
        self.showTool(tool, show)
        return show

if __name__ == '__main__':
    import sys
    from pyami import mrc

    filename = sys.argv[1]

    class MyApp(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'Image Viewer')
            self.panel = Viewer(frame, -1)
            frame.SetSize((750, 750))
            self.SetTopWindow(frame)
            frame.Show(True)
            return True

    app = MyApp(0)

    array = mrc.read(filename)
    app.panel.setNumpy(array)
    import random
    random.seed()
    targets = []
    for i in range(1):
        x = int(random.random()*array.shape[1])
        y = int(random.random()*array.shape[0])
        targets.append((x, y))
    app.panel.targetsplugin.addTargets(targets)
    app.MainLoop()
