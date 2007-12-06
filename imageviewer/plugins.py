import wx
import icons
import numpyimage

class Plugin(wx.EvtHandler):
    def __init__(self, imagewindow):
        wx.EvtHandler.__init__(self)
        self.hasalpha = False
        self.background = False
        self.ignoresize = False
        self.imagewindow = imagewindow
        self.region = None
        self.buffered = None
        self.clientregion = None
        self.enabled = True

    def GetId(self):
        return -1

    def draw(self, dc, region):
        raise NotImplementedError

    def clientRegionUpdated(self, clientregion):
        pass

    def onUpdateClientRegion(self, clientregion):
        self.clientregion = clientregion
        return False

class ClearPlugin(Plugin):
    def __init__(self, imagewindow, color=wx.WHITE, style=wx.SOLID):
        self.brush = wx.TheBrushList.FindOrCreateBrush(color, style)
        Plugin.__init__(self, imagewindow)
        self.background = True

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
        Plugin.onUpdateClientRegion(self, clientregion)
        return True

class NumpyPlugin(Plugin):
    def __init__(self, imagewindow):
        Plugin.__init__(self, imagewindow)
        self.region = wx.Region()
        self.array = None
        self.scale = 1.0
        self.rect = self.getRect()
        self.extrema = None
        self.valuerange = None
        self.fitclient = False

    def getRect(self, clientregion=None):
        rect = wx.Rect()

        if self.array is None:
            return rect

        if clientregion is None:
            crect = self.imagewindow.rect
        else:
            crect = clientregion.GetBox()

        if self.fitclient:
            self.scale = min(float(crect.width)/self.array.shape[1],
                             float(crect.height)/self.array.shape[0])

            rect.width = int(round(self.scale*self.array.shape[1]))
            rect.height = int(round(self.scale*self.array.shape[0]))
        else:
            rect.width = int(round(self.scale*self.array.shape[1]))
            rect.height = int(round(self.scale*self.array.shape[0]))

        return rect

    def getNumpy(self):
        return self.array

    def setNumpy(self, array):
        if array is None:
            self.extrema = None
            self.valuerange = None
        else:
            self.extrema = (array.min(), array.max())
            self.valuerange = self.extrema

        self.array = array

        self.rect = self.getRect()
        self.region = wx.Region(*self.rect)

        self.imagewindow.onUpdatePluginRegion(self, copy=False)

    def fitClient(self):
        self.fitclient = True
        self.imagewindow.onUpdatePluginRegion(self)

    def setScale(self, scale):
        if self.fitclient:
            self.fitclient = False
        self.scale = scale
        self.imagewindow.onUpdatePluginRegion(self)

    def setValueRange(self, valuerange):
        self.valuerange = valuerange
        self.imagewindow.onUpdatePluginRegion(self, copy=False)

    def draw(self, dc, region):
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            bitmap = numpyimage.numpy2wxBitmap(
                                      self.array,
                                      r.x - self.rect.x, r.y - self.rect.y,
                                      r.width, r.height,
                                      self.rect.width, self.rect.height,
                                      self.valuerange)
            sourcedc = wx.MemoryDC()
            sourcedc.SelectObject(bitmap)
            dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
            sourcedc.SelectObject(wx.NullBitmap)
            regioniterator.Next()

    def onUpdateClientRegion(self, clientregion):
        Plugin.onUpdateClientRegion(self, clientregion)

        if self.array is None:
            return False

        size = wx.Size(*self.rect.size)
        self.rect = self.getRect(clientregion)
        self.region = wx.Region(*self.rect)

        return size == self.rect.size

    def getXY(self, x, y):
        ix, iy, ih, iw = self.region.GetBox()
        cx, cy, ch, cw = self.clientregion.GetBox()
        x = x + cx - ix
        y = y + cy - iy
        x = int(round(x/self.scale))
        y = int(round(y/self.scale))
        return x, y

    def getXYValue(self, x, y):
        x, y = self.getXY(x, y)
        value = None
        if x >= 0 and y >= 0:
            try:
                value = self.array[y, x]
            except (TypeError, IndexError):
                pass
        return x, y, value

class CrosshairsPlugin(Plugin):
    def __init__(self, imagewindow, plugin,
                    width=2, color=wx.BLUE, style=wx.SOLID):
        self.brush = wx.TheBrushList.FindOrCreateBrush(color, style)
        self.plugin = plugin
        self.width = width
        Plugin.__init__(self, imagewindow)
        self.ignoresize = True
        self.region = self.getRegion()

    def getRegion(self, clientregion=None):
        if self.plugin.region.IsEmpty():
            return wx.Region()
        x, y, width, height = self.plugin.region.GetBox()
        center = (int(round(width/2.0 + x - self.width/2.0)),
                  int(round(height/2.0 + y - self.width/2.0)))
        if clientregion is None:
            crect = self.imagewindow.rect
        else:
            crect = clientregion.GetBox()
        region = wx.Region()
        region.Union(center[0], crect.y, self.width, crect.height)
        region.Union(crect.x, center[1], crect.width, self.width)
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
        Plugin.onUpdateClientRegion(self, clientregion)
        self.region = self.getRegion(clientregion)
        return True

class ToolTipPlugin(Plugin):
    def __init__(self, imagewindow):
        Plugin.__init__(self, imagewindow)
        self.hasalpha = True
        self.ignoresize = True

        self.bitmap = None

        self.pen = wx.BLACK_PEN
        self.brush = wx.WHITE_BRUSH
        self.font = wx.NORMAL_FONT

        self.rect = wx.Rect()
        self.region = self.getRegion()

        self.offsets = ((15, 5), (1, 1))
        self.border = (3, 3, 3, 3)

        self.setText(None)

    def getRegion(self):
        if self.bitmap is None:
            return wx.Region()

        crect = self.imagewindow.rect

        rect = wx.Rect(*self.rect)

        if rect.x - crect.x < crect.width/2:
            rect.x += self.offsets[0][0]
        else:
            rect.x -= self.rect.width + self.offsets[0][1]

        if rect.y - crect.y < crect.size.height/2:
            rect.y += self.offsets[1][0]
        else:
            rect.y -= self.rect.height + self.offsets[1][1]

        return wx.Region(*rect)

    def _setText(self, text):
        self.text = text
        if self.text is None:
            self.bitmap = None
        else:
            extent = self.imagewindow.GetFullTextExtent(self.text, self.font)
            width, height, descent, leading = extent
            self.rect.width = width + self.border[0] + self.border[2]
            self.rect.height = height + self.border[1] + self.border[3]
            self.updateBitmap()

    def setText(self, text):
        self._setText(text)
        self.imagewindow.onUpdatePluginRegion(self)

    def _setXY(self, xy):
        self.rect.position = xy + self.imagewindow.rect.position

    def setXY(self, xy):
        self._setXY(xy)
        self.imagewindow.onUpdatePluginRegion(self)

    def setXYText(self, xy, text):
        self._setXY(xy)
        self._setText(text)
        self.imagewindow.onUpdatePluginRegion(self)

    def draw(self, dc, region):
        if self.bitmap is None:
            return
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            sourcedc = wx.MemoryDC()
            sourcedc.SelectObject(self.bitmap)
            dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
            sourcedc.SelectObject(wx.NullBitmap)
            regioniterator.Next()

    def updateBitmap(self):
        bitmap = wx.EmptyBitmap(*self.rect.size)
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        dc.SetPen(self.pen)
        dc.SetBrush(self.brush)
        dc.SetFont(self.font)
        dc.DrawRectangle(0, 0, self.rect.width, self.rect.height)
        dc.DrawText(self.text, self.border[0], self.border[1])
        dc.SelectObject(wx.NullBitmap)
        image = bitmap.ConvertToImage()
        image.InitAlpha()
        size = self.rect.width*self.rect.height
        image.SetAlphaData(chr(127)*size)
        self.bitmap = image.ConvertToBitmap()

    def onUpdateClientRegion(self, clientregion):
        self.region = self.getRegion()
        return True

class MagnifierPlugin(Plugin):
    def __init__(self, imagewindow, imageplugin):
        self.imageplugin = imageplugin

        Plugin.__init__(self, imagewindow)
        self.hasalpha = True
        self.ignoresize = True

        self.bitmap = None

        self.pen = wx.BLACK_PEN
        self.brush = wx.WHITE_BRUSH

        self.alpha = 223
        self.border = 1

        self.rect = wx.Rect(0, 0, 196, 196)
        self.scale = min(*self.rect.size)/32
        self.region = self.getRegion()

    def getRegion(self):
        if self.bitmap is None:
            return wx.Region()

        x = self.rect.x + self.imagewindow.rect.x - self.rect.width/2.0
        y = self.rect.y + self.imagewindow.rect.y - self.rect.height/2.0
        x = int(round(x))
        y = int(round(y))
        region = wx.Region(x, y, self.rect.width, self.rect.height)

        return region

    def _setXY(self, xy):
        self.rect.position = xy

    def setXY(self, xy):
        self._setXY(xy)
        self.updateBitmap()
        self.imagewindow.onUpdatePluginRegion(self)

    def draw(self, dc, region):
        if self.bitmap is None:
            return
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            sourcedc = wx.MemoryDC()
            sourcedc.SelectObject(self.bitmap)
            dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
            sourcedc.SelectObject(wx.NullBitmap)
            regioniterator.Next()

    def updateBitmap(self):
        scale = self.scale*self.imageplugin.scale
        x, y = self.imageplugin.getXY(*self.rect.position)
        try:
            b = numpyimage.numpy2wxBitmap(self.imageplugin.array,
                  int(round(x*scale - self.rect.width/2.0)) + self.border,
                  int(round(y*scale - self.rect.width/2.0)) + self.border,
                  self.rect.width - 2*self.border,
                  self.rect.height - 2*self.border,
                  self.imageplugin.array.shape[1]*scale,
                  self.imageplugin.array.shape[0]*scale,
                  self.imageplugin.valuerange)
        except (AttributeError, ValueError):
            self.bitmap = None
            return
        bitmap = wx.EmptyBitmap(*self.rect.size)
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        dc.SetPen(self.pen)
        dc.SetBrush(self.brush)
        dc.DrawRectangle(0, 0, self.rect.width, self.rect.height)
        sourcedc = wx.MemoryDC()
        sourcedc.SelectObject(b)
        dc.Blit(self.border, self.border,
                 self.rect.width - 2*self.border,
                 self.rect.height - 2*self.border,
                 sourcedc, 0, 0)
        sourcedc.SelectObject(wx.NullBitmap)
        dc.SelectObject(wx.NullBitmap)
        image = bitmap.ConvertToImage()
        image.InitAlpha()
        size = self.rect.width*self.rect.height
        image.SetAlphaData(chr(self.alpha)*size)
        self.bitmap = image.ConvertToBitmap()

    def onUpdateClientRegion(self, clientregion):
        self.region = self.getRegion()
        return True

class TargetsPlugin(Plugin):
    def __init__(self, imagewindow, plugin, color, width=1, style=wx.SOLID):
        Plugin.__init__(self, imagewindow)
        self.hasalpha = True

        self.plugin = plugin

        self.color = color

        self.targets = []
        self.targetoffsets = []

        self.bitmap = self.getTargetBitmap()
        self.bitmapsize = wx.Size(self.bitmap.GetWidth(),
                                  self.bitmap.GetHeight())
        self.region = self.getRegion()

    def addTargets(self, targets):
        self.targets += targets
        self.region = self.getRegion()
        self.imagewindow.onUpdatePluginRegion(self)

    def removeTargets(self, targets):
        for target in targets:
            self.targets.remove(target)
        self.region = self.getRegion()
        self.imagewindow.onUpdatePluginRegion(self)

    def clearTargets(self):
        self.targets = []
        self.region = self.getRegion()
        self.imagewindow.onUpdatePluginRegion(self)

    def getRegion(self, clientregion=None):
        try:
            scale = self.plugin.scale
        except AttributeError:
            scale = 1.0
        px, py, pw, ph = self.plugin.region.GetBox()

        region = wx.Region()

        w, h = self.bitmapsize.width, self.bitmapsize.height
        self.targetoffsets = []
        for i, (x, y) in enumerate(self.targets):
            x = int(round(scale*x))
            y = int(round(scale*y))
            x = x - self.bitmapsize.width/2 + px
            y = y - self.bitmapsize.height/2 + py
            region.Union(x, y, w, h)
            self.targetoffsets.append(wx.Rect(x, y, w, h))

        return region

    def getTargetBitmap(self):
        bitmap = icons.icon('target')
        image = bitmap.ConvertToImage()
        r1, g1, b1 = 0, 0, 0
        r2, g2, b2 = self.color.Red(), self.color.Green(), self.color.Blue()
        image.Replace(r1, g1, b1, r2, g2, b2)
        bitmap = image.ConvertToBitmap()
        return bitmap

    def draw(self, dc, region):
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            for tr in self.targetoffsets:
                if not r.Intersects(tr):
                    continue
                x = r.x - tr.x
                y = r.y - tr.y
                w = min(tr.width - x, r.width)
                h = min(tr.height - y, r.height)
                sourcedc = wx.MemoryDC()
                sourcedc.SelectObject(self.bitmap)
                dc.Blit(r.x, r.y, w, h, sourcedc, x, y)
                sourcedc.SelectObject(wx.NullBitmap)
            regioniterator.Next()

    def onUpdateClientRegion(self, clientregion):
        Plugin.onUpdateClientRegion(self, clientregion)

        self.region = self.getRegion(clientregion)
        return True

class AxesPlugin(Plugin):
    def __init__(self, imagewindow, axes,
                  color=wx.RED, width=1, style=wx.SOLID):
        self.pen = wx.ThePenList.FindOrCreatePen(color, width, style)
        Plugin.__init__(self, imagewindow)
        self._setAxes(*axes)

    def _setAxes(self, xaxis, yaxis):
        penwidth = self.pen.GetWidth()

        x0, x1 = xaxis
        y0 = y1 = -int(round(penwidth/2.0))
        self.xaxis = (x0, y0, x1, y1)

        x0 = x1 = -int(round(penwidth/2.0))
        y0, y1 = yaxis
        self.yaxis = (x0, y0, x1, y1)

        self.region = self.getRegion()

    def getRegion(self, clientregion=None):
        penwidth = self.pen.GetWidth()
        region = wx.Region()
        x = self.xaxis[0]
        y = self.xaxis[1]
        w = self.xaxis[2] - x
        h = penwidth
        region.Union(x, y, w, h)
        x = self.yaxis[0]
        y = self.yaxis[1]
        w = penwidth
        h = self.xaxis[2] - y
        region.Union(x, y, w, h)

        return region

    def draw(self, dc, region):
        dc.SetPen(self.pen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        regioniterator = wx.RegionIterator(region)
        while(regioniterator):
            r = regioniterator.GetRect()
            dc.DrawRectangle(r.x, r.y, r.width, r.height)
            regioniterator.Next()
        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

    def onUpdateClientRegion(self, clientregion):
        Plugin.onUpdateClientRegion(self, clientregion)
        return True

