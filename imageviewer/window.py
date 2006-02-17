import wx

class Window(wx.Window):
    def __init__(self, parent, id):
        wx.Window.__init__(self, parent, id)

        self.ignoresize = False

        self.plugins = []
        self.pluginsregion = wx.Region()

        self.rect = wx.Rect()
        self.rect.size = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(*self.rect.size)

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
            clientregion = wx.Region(*self.rect)

        updates = []
        self.pluginsregion = wx.Region()
        for i, plugin in enumerate(self.plugins):
            if not plugin.enabled:
                plugin.region = wx.Region()
                updates.append(False)
            else:
                updates.append(plugin.onUpdateClientRegion(clientregion))
                if plugin.background:
                    plugin.region = wx.Region()
                    plugin.region.UnionRegion(clientregion)
                elif not plugin.ignoresize:
                    self.pluginsregion.UnionRegion(plugin.region)
            plugin.buffered = wx.Region()
            plugin.buffered.UnionRegion(plugin.region)
            plugin.buffered.IntersectRegion(clientregion)

            if not plugin.hasalpha:
                for p in self.plugins[:i]:
                    p.buffered.SubtractRegion(plugin.region)

        return updates

    def updateBufferRegion(self, region):
        if region.IsEmpty():
            return

        dc = wx.MemoryDC()
        dc.SelectObject(self.buffer)
        self.sourceBuffer(dc, region)
        dc.SelectObject(wx.NullBitmap)

        self.Refresh()

    def addPlugin(self, plugin, index=None):
        if plugin in self.plugins:
            raise ValueError

        if index is None:
            self.plugins.append(plugin)
        else:
            self.plugins.insert(index, plugin)

        self.updatePluginRegions()

        buffered = plugin.buffered

        self.updateBufferRegion(buffered)

    def enablePlugin(self, plugin, enable=True):
        if plugin not in self.plugins:
            raise ValueError

        if not enable:
            buffered = plugin.buffered

        plugin.enabled = enable

        self.updatePluginRegions()

        if enable:
            buffered = plugin.buffered

        self.updateBufferRegion(buffered)

    def removePlugin(self, plugin):
        if plugin not in self.plugins:
            raise ValueError

        buffered = plugin.buffered

        self.plugins.remove(plugin)

        self.updatePluginRegions()

        self.updateBufferRegion(buffered)

    def copyBuffer(self, dc, regions):
        origin =  dc.GetDeviceOrigin()

        copydc = wx.MemoryDC()
        copydc.SelectObject(self.buffer)
        copydc.SetDeviceOrigin(-self.rect.x, -self.rect.y)

        for offset, region in regions.items():
            dc.SetDeviceOrigin(*(origin + offset))
            regioniterator = wx.RegionIterator(region)
            while(regioniterator):
                r = regioniterator.GetRect()
                dc.Blit(r.x, r.y, r.width, r.height, copydc, r.x, r.y)
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

        dc.SetDeviceOrigin(*origin)

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

    def getScrollPercentage(self, rect=None):
        if rect is None:
            rect = self.rect
        prect = self.pluginsregion.GetBox()
        try:
            x = (rect.x + rect.width/2.0 - prect.x)/prect.width
        except ZeroDivisionError:
            x = 0.0
        try:
            y = (rect.y + rect.height/2.0 - prect.y)/prect.height
        except ZeroDivisionError:
            y = 0.0
        return x, y

    def updateScrollbars(self, rect=None, percentage=None):
        if rect is None:
            rect = self.rect
        rect = wx.Rect(*rect)

        if percentage is None:
            percentage = self.getScrollPercentage()

        initialclientregion = wx.Region(*self.rect)

        self.updatePluginRegions(clientregion=wx.Region(*rect))
        prect = self.pluginsregion.GetBox()

        offsetx = int(round(prect.width*percentage[0] - rect.width/2.0))
        offsetx = max(offsetx, 0)
        offsetx = min(prect.width - rect.width, offsetx)

        self.ignoresize = True

        if prect.x < offsetx or prect.width - prect.x > offsetx + rect.width:
            self.SetScrollbar(wx.HORIZONTAL, offsetx, rect.width, prect.width)
        else:
            self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

        rect.size = self.GetClientSize()
        self.updatePluginRegions(clientregion=wx.Region(*rect))
        prect = self.pluginsregion.GetBox()

        offsety = int(round(prect.height*percentage[1] - rect.height/2.0))
        offsety = max(offsety, 0)
        offsety = min(prect.height - rect.height, offsety)

        if prect.y < offsety or prect.height - prect.y > offsety + rect.height:
            self.SetScrollbar(wx.VERTICAL, offsety, rect.height, prect.height)
        else:
            self.SetScrollbar(wx.VERTICAL, 0, 0, 0)

        rect.size = self.GetClientSize()
        self.updatePluginRegions(clientregion=wx.Region(*rect))
        prect = self.pluginsregion.GetBox()

        offsetx = int(round(prect.width*percentage[0] - rect.width/2.0))
        offsetx = max(offsetx, 0)
        offsetx = min(prect.width - rect.width, offsetx)

        if prect.x < offsetx or prect.width - prect.x > offsetx + rect.width:
            self.SetScrollbar(wx.HORIZONTAL, offsetx, rect.width, prect.width)
        else:
            self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

        self.ignoresize = False

        rect.size = self.GetClientSize()

        if rect.width > prect.width:
            rect.x = int(round((prect.width - rect.width)/2.0)) + prect.x
        else:
            rect.x = self.GetScrollPos(wx.HORIZONTAL) + prect.x

        if rect.height > prect.height:
            rect.y = int(round((prect.height - rect.height)/2.0)) + prect.y
        else:
            rect.y = self.GetScrollPos(wx.VERTICAL) + prect.y

        self.updatePluginRegions(clientregion=initialclientregion)

        return rect

    def getUpdateRegions(self, updates, regions, bufferedregions):
        copyregions = {}
        sourceregion = wx.Region()
        for i, plugin in enumerate(self.plugins):
            offset  = (plugin.region.GetBox().position
                        - regions[i].GetBox().position)
            if updates[i]:
                copyregion = wx.Region()
                copyregion.UnionRegion(bufferedregions[i])

                for j, p in enumerate(self.plugins[i+1:]):
                    if p.hasalpha:
                        copyregion.SubtractRegion(regions[j + i + 1])
                if plugin.hasalpha:
                    for j in range(len(self.plugins[:i])):
                        copyregion.SubtractRegion(regions[j])

                copyregion.Offset(offset.x, offset.y)

                for p in self.plugins[i+1:]:
                    if p.hasalpha:
                        copyregion.SubtractRegion(p.buffered)
                if plugin.hasalpha:
                    for p in self.plugins[:i]:
                        copyregion.SubtractRegion(p.buffered)

                copyregion.IntersectRegion(plugin.buffered)
                if offset not in copyregions:
                    copyregions[offset] = wx.Region()
                sourceregion.UnionRegion(plugin.buffered)
                sourceregion.SubtractRegion(copyregion)
                copyregion.Offset(-offset.x, -offset.y)
                copyregions[offset].UnionRegion(copyregion)
            else:
                sourceregion.UnionRegion(plugin.buffered)

        return sourceregion, copyregions

    def updateBuffer(self, sourceregion, copyregions, rect):
        buffer = wx.EmptyBitmap(*rect.size)
        dc = wx.MemoryDC()
        dc.SelectObject(buffer)
        dc.SetDeviceOrigin(-rect.x, -rect.y)
        self.copyBuffer(dc, copyregions)
        self.sourceBuffer(dc, sourceregion)
        dc.SelectObject(wx.NullBitmap)
        self.buffer = buffer

    def onUpdatePluginRegion(self, plugin, copy=True):
        regions = [p.region for p in self.plugins]
        bufferedregions = [p.buffered for p in self.plugins]

        updates1 = self.updatePluginRegions()

        rect = self.updateScrollbars()

        updates2 = self.updatePluginRegions(clientregion=wx.Region(*rect))

        updates = [u1 and u1 for u1, u2 in zip(updates1, updates2)]
        if not copy:
            i = self.plugins.index(plugin)
            updates[i] = False

        sourceregion, copyregions = self.getUpdateRegions(updates, regions,
                                                           bufferedregions)

        self.updateBuffer(sourceregion, copyregions, rect)

        self.rect = rect

        self.Refresh()

    def updateClientRegion(self, rect, scrollpercentage=None):
        regions = [plugin.region for plugin in self.plugins]
        bufferedregions = [plugin.buffered for plugin in self.plugins]

        rect = self.updateScrollbars(rect, percentage=scrollpercentage)

        updates = self.updatePluginRegions(clientregion=wx.Region(*rect))

        sourceregion, copyregions = self.getUpdateRegions(updates, regions,
                                                           bufferedregions)

        self.updateBuffer(sourceregion, copyregions, rect)

        self.rect = rect

        self.Refresh()

    def onSize(self, evt):
        evt.Skip()

        if self.ignoresize:
            return

        rect = wx.Rect(*self.rect)
        rect.size = evt.GetSize()
        self.updateClientRegion(rect)

    def onScrollWin(self, orientation, position, relative=False):
        if relative:
            position += self.GetScrollPos(orientation)

        rect = wx.Rect(*self.rect)
        prect = self.pluginsregion.GetBox()

        if orientation == wx.HORIZONTAL:
            rect.x = position + prect.x
        elif orientation == wx.VERTICAL:
            rect.y = position + prect.y

        percentage = self.getScrollPercentage(rect)
        self.updateClientRegion(rect, scrollpercentage=percentage)

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

