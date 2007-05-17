import wx
import numarrayimage

def diffRegion(region1, region2):
    equalregion = wx.Region()
    equalregion.UnionRegion(region1)
    equalregion.IntersectRegion(region2)
    minusregion = wx.Region()
    minusregion.UnionRegion(region1)
    minusregion.SubtractRegion(equalregion)
    plusregion = wx.Region()
    plusregion.UnionRegion(region2)
    plusregion.SubtractRegion(equalregion)
    return minusregion, equalregion, plusregion

class Plugin(wx.EvtHandler):
    def __init__(self, imagewindow, hasalpha=False, background=False):
        wx.EvtHandler.__init__(self)
        self.hasalpha = hasalpha
        self.imagewindow = imagewindow
        self.region = None
        self.buffered = None
        self.background = background

    def GetId(self):
        return -1

    def draw(self, dc, region):
        raise NotImplementedError

    def clientRegionUpdated(self, clientregion):
        pass

    def onUpdateClientRegion(self, clientregion):
        return False

class ClearPlugin(Plugin):
    def __init__(self, imagewindow, color=wx.WHITE, style=wx.SOLID):
        self.brush = wx.TheBrushList.FindOrCreateBrush(color, style)
        Plugin.__init__(self, imagewindow, background=True)

    def draw(self, dc, region):
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(self.brush)
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            dc.DrawRectangle(r.x, r.y, r.width, r.height)
            regioniterator.Next()
        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

    def onUpdateClientRegion(self, clientregion):
        return True

class NumarrayPlugin(Plugin):
    def __init__(self, imagewindow):
        Plugin.__init__(self, imagewindow)
        self.region = wx.Region()
        self.array = None
        self.scale = 1.0
        self.size = wx.Size()
        self.offset = self.getOffset()
        self.extrema = None
        self.valuerange = None
        self.fitclient = False

    def getOffset(self, clientregion=None):
        if self.array is None:
            return wx.Point()

        if clientregion is None:
            x, y = self.imagewindow.offset
            width, height = self.imagewindow.size
        else:
            x, y, width, height = clientregion.GetBox()

        offset = wx.Point(0, 0)
        if self.size.width < width:
            offset.x = int(round((width - self.size.width)/2.0))
        if self.size.height < height:
            offset.y = int(round((height - self.size.height)/2.0))

        return offset

    def getSize(self, clientregion=None):
        if self.array is None:
            return wx.Size()

        if self.fitclient:
            if clientregion is None:
                width, height = self.imagewindow.size
            else:
                x, y, width, height = clientregion.GetBox()
            scale = min(float(width)/array.shape[1],
                        float(height)/array.shape[0])
            width = int(round(scale*array.shape[1]))
            height = int(round(scale*array.shape[0]))
        else:
            width = int(round(self.scale*array.shape[1]))
            height = int(round(self.scale*array.shape[0]))
        return wx.Size(width, height)

    def setNumarray(self, array):
        if array is None:
            self.extrema = None
            self.valuerange = None
        else:
            self.extrema = (array.min(), array.max())
            self.valuerange = self.extrema

        self.array = array

        width, height = self.getSize()
        x, y = self.getOffset()
        self.offset = wx.Point(x, y)
        self.region = wx.Region(x, y, width, height)

        self.imagewindow.onUpdatePluginRegion(self)

    def draw(self, dc, region):
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            bitmap = numarrayimage.numarray2wxBitmap(
                                      array,
                                      r.x - self.offset.x, r.y - self.offset.y,
                                      r.width, r.height,
                                      self.size.width, self.size.height,
                                      self.valuerange)
            sourcedc = wx.MemoryDC()
            sourcedc.SelectObject(bitmap)
            dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
            sourcedc.SelectObject(wx.NullBitmap)
            regioniterator.Next()

    def onUpdateClientRegion(self, clientregion):
        if self.array is None:
            return False

        size = self.getSize(clientregion)
        copy = self.size == size
        self.size = size
        self.offset = self.getOffset(clientregion)
        (x, y), (width, height) = self.offset, self.size
        self.region = wx.Region(x, y, width, height)
        return copy

class GridPlugin(Plugin):
    def __init__(self, imagewindow, color=wx.WHITE, style=wx.SOLID):
        self.spacing = 32
        self.pen = wx.ThePenList.FindOrCreatePen(wx.RED, 1, wx.SOLID)
        self.brush = wx.TheBrushList.FindOrCreateBrush(color, style)
        Plugin.__init__(self, imagewindow, hasalpha=True, background=True)

    def draw(self, dc, region):
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
 
            dc.SetPen(self.pen)
            start = (r.x - 1) + self.spacing - (r.x - 1) % self.spacing
            stop = r.x + r.width
            for i in range(start, stop, self.spacing):
                dc.DrawLine(i, r.y, i, r.y + r.height)
            start = (r.y - 1) + self.spacing - (r.y - 1) % self.spacing
            stop = r.y + r.height
            for i in range(start, stop, self.spacing):
                dc.DrawLine(r.x, i, r.x + r.width, i)
            dc.SetPen(wx.NullPen)

            regioniterator.Next()

    def onUpdateClientRegion(self, clientregion):
        #return True
        return False

class CrosshairsPlugin(Plugin):
    def __init__(self, imagewindow, plugin,
                    width=1, color=wx.BLUE, style=wx.SOLID):
        self.brush = wx.TheBrushList.FindOrCreateBrush(color, style)
        self.plugin = plugin
        self.width = width
        Plugin.__init__(self, imagewindow)
        self.region = self.getRegion()

    def getRegion(self, clientregion=None):
        if self.plugin.region.IsEmpty():
            return wx.Region()
        x, y, width, height = self.plugin.region.GetBox()
        center = (int(round(width/2.0 + x - self.width/2.0)),
                  int(round(height/2.0 + y - self.width/2.0)))
        if clientregion is None:
            x, y = self.imagewindow.offset
            width, height = self.imagewindow.size
        else:
            x, y, width, height = clientregion.GetBox()
        region = wx.Region()
        region.Union(center[0], y, self.width, height)
        region.Union(x, center[1], width, self.width)
        return region

    def draw(self, dc, region):
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(self.brush)
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            dc.DrawRectangle(r.x, r.y, r.width, r.height)
            regioniterator.Next()
        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

    def onUpdateClientRegion(self, clientregion):
        self.region = self.getRegion(clientregion)
        return True

class Window(wx.Window):
    def __init__(self, parent, id):
        wx.Window.__init__(self, parent, id)

        self.ignoresize = False

        self.plugins = []
        self.pluginsregion = wx.Region()

        self.offset = wx.Point(0, 0)
        self.size = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(self.size.width, self.size.height)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.Bind(wx.EVT_PAINT, self.onPaint)

        self.Bind(wx.EVT_SIZE, self.onSize)

        self.Bind(wx.EVT_SCROLLWIN_LINEUP, self.onScrollWinLineUp)
        self.Bind(wx.EVT_SCROLLWIN_LINEDOWN, self.onScrollWinLineDown)
        self.Bind(wx.EVT_SCROLLWIN_PAGEUP, self.onScrollWinPageUp)
        self.Bind(wx.EVT_SCROLLWIN_PAGEDOWN, self.onScrollWinPageDown)
        self.Bind(wx.EVT_SCROLLWIN_TOP, self.onScrollWinTop)
        self.Bind(wx.EVT_SCROLLWIN_BOTTOM, self.onScrollWinBottom)
        self.Bind(wx.EVT_SCROLLWIN_THUMBTRACK, self.onScrollWinThumbTrack)

    def updatePluginRegions(self, clientregion=None):
        if clientregion is None:
            x, y, = self.offset
            width, height = self.size
            clientregion = wx.Region(x, y, width, height)

        self.pluginsregion = wx.Region()

        for i, plugin in enumerate(self.plugins):
            if plugin.background:
                plugin.region = wx.Region()
                plugin.region.UnionRegion(clientregion)
            else:
                self.pluginsregion.UnionRegion(plugin.region)
            plugin.buffered = wx.Region()
            plugin.buffered.UnionRegion(plugin.region)
            plugin.buffered.IntersectRegion(clientregion)

            if not plugin.hasalpha:
                for p in self.plugins[:i]:
                    p.buffered.SubtractRegion(plugin.region)

    def addPlugin(self, plugin):
        self.plugins.append(plugin)

        self.updatePluginRegions()

        if not plugin.buffered.IsEmpty():
            dc = wx.MemoryDC()
            dc.SelectObject(self.buffer)
            self.sourceBuffer(dc, plugin.buffered)
            dc.SelectObject(wx.NullBitmap)

            self.Refresh()

    def copyBuffer(self, dc, regions):
        copydc = wx.MemoryDC()
        copydc.SelectObject(self.buffer)
        copydc.SetDeviceOrigin(-self.offset.x, -self.offset.y)
        for offset, region in regions.items():
            regioniterator = wx.RegionIterator(region)
            while(regioniterator):
                r = regioniterator.GetRect()
                dc.Blit(r.x + offset.x, r.y + offset.y, r.width, r.height,
                        copydc, r.x, r.y)
                regioniterator.Next()
            '''
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.GREEN_BRUSH)
            regioniterator = wx.RegionIterator(region)
            while(regioniterator):
                r = regioniterator.GetRect()
                dc.DrawRectangle(r.x, r.y, r.width, r.height)
                regioniterator.Next()
            dc.SetBrush(wx.NullBrush)
            dc.SetPen(wx.NullPen)
            '''
        copydc.SelectObject(wx.NullBitmap)

    def sourceBuffer(self, dc, sourceregion=None):
        for plugin in self.plugins:
            region = wx.Region()
            region.UnionRegion(plugin.buffered)
            if sourceregion is not None:
                region.IntersectRegion(sourceregion)
            if not region.IsEmpty():
                plugin.draw(dc, region)
                '''
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.SetBrush(wx.RED_BRUSH)
                regioniterator = wx.RegionIterator(region)
                while(regioniterator):
                    r = regioniterator.GetRect()
                    dc.DrawRectangle(r.x, r.y, r.width, r.height)
                    regioniterator.Next()
                dc.SetBrush(wx.NullBrush)
                dc.SetPen(wx.NullPen)
                '''

    def onEraseBackground(self, evt):
        pass

    def onPaint(self, dc):
        dc = wx.PaintDC(self)
        memorydc = wx.MemoryDC()
        memorydc.SelectObject(self.buffer)
        regioniterator = wx.RegionIterator(self.GetUpdateRegion())
        while(regioniterator):
            r = regioniterator.GetRect()
            dc.Blit(r.x, r.y, r.width, r.height, memorydc, r.x, r.y)
            regioniterator.Next()
        memorydc.SelectObject(wx.NullBitmap)

    def updateScrollbars(self, offset=None, size=None):
        if offset is None:
            offset = self.offset
        if size is None:
            size = self.GetSize()

        x, y = self.offset
        width, height = self.size
        initialclientregion = wx.Region(x, y, width, height)

        x, y = offset
        width, height = size
        clientregion = wx.Region(x, y, width, height)
        [p.onUpdateClientRegion(clientregion) for p in self.plugins]
        self.updatePluginRegions(clientregion=clientregion)
        x, y, w, h = self.pluginsregion.GetBox()

        self.ignoresize = True

        if x < offset.x or w - x > offset.x + size.width:
            self.SetScrollbar(wx.HORIZONTAL, offset.x, size.width, w - x)
        else:
            self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

        size = self.GetClientSize()

        x, y = offset
        width, height = size
        clientregion = wx.Region(x, y, width, height)
        [p.onUpdateClientRegion(clientregion) for p in self.plugins]
        self.updatePluginRegions(clientregion=clientregion)
        x, y, w, h = self.pluginsregion.GetBox()

        if y < offset.y or h - y > offset.y + size.height:
            self.SetScrollbar(wx.VERTICAL, offset.y, size.height, h - y)
        else:
            self.SetScrollbar(wx.VERTICAL, 0, 0, 0)

        size = self.GetClientSize()

        x, y = offset
        width, height = size
        clientregion = wx.Region(x, y, width, height)
        [p.onUpdateClientRegion(clientregion) for p in self.plugins]
        self.updatePluginRegions(clientregion=clientregion)
        x, y, w, h = self.pluginsregion.GetBox()

        if x < offset.x or w - x > offset.x + size.width:
            self.SetScrollbar(wx.HORIZONTAL, offset.x, size.width, w - x)
        else:
            self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

        size = self.GetClientSize()

        [p.onUpdateClientRegion(initialclientregion) for p in self.plugins]
        self.updatePluginRegions(clientregion=initialclientregion)

        self.ignoresize = False

        x = self.GetScrollPos(wx.HORIZONTAL)
        y = self.GetScrollPos(wx.VERTICAL)
        offset = wx.Point(x, y)
        return offset, size

    def onUpdatePluginRegion(self, plugin):
        # ...
        self.updateClientRegion()

    def updateClientRegion(self, offset=None, size=None):
        # TODO: alpha updates
        if offset is None:
            offset = self.offset
        if size is None:
            size = self.size

        regions = [plugin.region for plugin in self.plugins]
        bufferedregions = [plugin.buffered for plugin in self.plugins]

        offset, size = self.updateScrollbars(offset=offset, size=size)

        x, y = offset
        width, height = size
        clientregion = wx.Region(x, y, width, height)

        updates = [p.onUpdateClientRegion(clientregion) for p in self.plugins]
        self.updatePluginRegions(clientregion=clientregion)

        copyregions = {}
        sourceregion = wx.Region()
        for i, plugin in enumerate(self.plugins):
            x1, y1, w1, h1 = regions[i].GetBox()
            x2, y2, w2, h2 = plugin.region.GetBox()
            doffset = wx.Point(x2 - x1, y2 - y1)
            if updates[i]:
                copyregion = wx.Region()
                copyregion.UnionRegion(bufferedregions[i])
                copyregion.Offset(doffset.x, doffset.y)
                copyregion.IntersectRegion(plugin.buffered)
                if doffset not in copyregions:
                    copyregions[doffset] = wx.Region()
                sourceregion.UnionRegion(plugin.buffered)
                sourceregion.SubtractRegion(copyregion)
                copyregion.Offset(-doffset.x, -doffset.y)
                copyregions[doffset].UnionRegion(copyregion)
            else:
                sourceregion.UnionRegion(plugin.buffered)

        buffer = wx.EmptyBitmap(size.width, size.height)

        dc = wx.MemoryDC()
        dc.SelectObject(buffer)
        dc.SetDeviceOrigin(-offset.x, -offset.y)
        self.copyBuffer(dc, copyregions)
        self.sourceBuffer(dc, sourceregion)
        dc.SelectObject(wx.NullBitmap)

        self.offset = offset
        self.size = size
        self.buffer = buffer

        self.Refresh()

    def onSize(self, evt):
        evt.Skip()

        if self.ignoresize:
            return

        self.updateClientRegion(size=evt.GetSize())

    def onScrollWin(self, orientation, position, relative=False):
        x, y = self.offset
        if orientation == wx.HORIZONTAL:
            if relative:
                x += position
            else:
                x = position
            x = max(0, x)
            x = min(x, self.GetScrollRange(orientation)
                        - self.GetScrollThumb(orientation))
        elif orientation == wx.VERTICAL:
            if relative:
                y += position
            else:
                y = position
            y = max(0, y)
            y = min(y, self.GetScrollRange(orientation)
                        - self.GetScrollThumb(orientation))
        self.updateClientRegion(offset=wx.Point(x, y))

    def onScrollWinLineUp(self, evt):
        orientation = evt.GetOrientation()
        position = -1
        self.onScrollWin(orientation, position, relative=True)

    def onScrollWinLineDown(self, evt):
        orientation = evt.GetOrientation()
        position = 1
        self.onScrollWin(orientation, position, relative=True)

    def onScrollWinPageUp(self, evt):
        orientation = evt.GetOrientation()
        position = -self.GetScrollThumb(orientation)
        self.onScrollWin(orientation, position, relative=True)

    def onScrollWinPageDown(self, evt):
        orientation = evt.GetOrientation()
        position = self.GetScrollThumb(orientation)
        self.onScrollWin(orientation, position, relative=True)

    def onScrollWinTop(self, evt):
        orientation = evt.GetOrientation()
        position = 0
        self.onScrollWin(orientation, position)

    def onScrollWinBottom(self, evt):
        orientation = evt.GetOrientation()
        position = self.GetScrollRange(orientation)
        self.onScrollWin(orientation, position)

    def onScrollWinThumbTrack(self, evt):
        orientation = evt.GetOrientation()
        position = evt.GetPosition()
        self.onScrollWin(orientation, position)

class Viewer(wx.Panel):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)

        self.imagewindow = Window(self, -1)

        clearplugin = ClearPlugin(self.imagewindow)
        self.imagewindow.addPlugin(clearplugin)

        self.numarrayplugin = NumarrayPlugin(self.imagewindow)
        self.imagewindow.addPlugin(self.numarrayplugin)

        self.crosshairsplugin = CrosshairsPlugin(self.imagewindow,
                                                 self.numarrayplugin)
        self.imagewindow.addPlugin(self.crosshairsplugin)

        self.sizer = wx.GridBagSizer(0, 0)

        self.sizer.Add(self.imagewindow, (0, 0), (1, 1),
                       wx.EXPAND|wx.FIXED_MINSIZE)

        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(0)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)

    def setNumarray(self, array):
        self.numarrayplugin.setNumarray(array)

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
    app.panel.setNumarray(array)
    app.MainLoop()

