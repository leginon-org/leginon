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
		self.drawn = None
		self.buffered = None
		self.background = background

	def GetId(self):
		return -1

	def draw(self, dc, region, offset):
		raise NotImplementedError

	def clientRegionUpdated(self, clientregion):
		pass

	def onUpdateClientRegion(self, clientregion):
		return wx.Point(0, 0)

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

	def setNumarray(self, array):
		if array is None:
			self.size = wx.Size()

			self.extrema = None
			self.valuerange = None
		else:
			width = int(round(self.scale*array.shape[1]))
			height = int(round(self.scale*array.shape[0]))
			self.size = wx.Size(width, height)

			self.extrema = (array.min(), array.max())
			self.valuerange = self.extrema

		self.array = array

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

		offset = self.offset
		self.offset = self.getOffset(clientregion)

		if offset != self.offset:
			x, y = self.offset
			width, height = self.size
			self.region = wx.Region(x, y, width, height)
			return self.offset - offset
		else:
			return False

class	Window(wx.Window):
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
			plugin.drawn = wx.Region()
			plugin.drawn.UnionRegion(plugin.region)

			if not plugin.hasalpha:
				for p in self.plugins[:i]:
					p.drawn.SubtractRegion(plugin.region)

		for plugin in self.plugins:
			plugin.buffered = wx.Region()
			plugin.buffered.UnionRegion(plugin.drawn)
			plugin.buffered.IntersectRegion(clientregion)

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
		for offset, region in regions.items():
			x, y = offset
			regioniterator = wx.RegionIterator(region)
			while(regioniterator):
				r = regioniterator.GetRect()
				dc.Blit(r.x + x, r.y + y, r.width, r.height, copydc, r.x, r.y)
				regioniterator.Next()
			#dc.SetPen(wx.TRANSPARENT_PEN)
			#dc.SetBrush(wx.GREEN_BRUSH)
			#regioniterator = wx.RegionIterator(region)
			#while(regioniterator):
			#	r = regioniterator.GetRect()
			#	dc.DrawRectangle(r.x, r.y, r.width, r.height)
			#	regioniterator.Next()
			#dc.SetBrush(wx.NullBrush)
			#dc.SetPen(wx.NullPen)
		copydc.SelectObject(wx.NullBitmap)

	def sourceBuffer(self, dc, sourceregion=None):
		for plugin in self.plugins:
			region = wx.Region()
			region.UnionRegion(plugin.buffered)
			if sourceregion is not None:
				region.IntersectRegion(sourceregion)
			if not region.IsEmpty():
				plugin.draw(dc, region)
				#dc.SetPen(wx.TRANSPARENT_PEN)
				#dc.SetBrush(wx.RED_BRUSH)
				#regioniterator = wx.RegionIterator(region)
				#while(regioniterator):
				#	r = regioniterator.GetRect()
				#	dc.DrawRectangle(r.x, r.y, r.width, r.height)
				#	regioniterator.Next()
				#dc.SetBrush(wx.NullBrush)
				#dc.SetPen(wx.NullPen)

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

	def onUpdatePluginRegion(self, plugin):
		regions1 = [plugin.buffered for plugin in self.plugins]

		self.updatePluginRegions()

		regions2 = [plugin.buffered for plugin in self.plugins]

		diff = [diffRegion(r1, r2) for r1, r2 in zip(regions1, regions2)]

		copyregion = wx.Region()
		sourceregion = wx.Region()
		for i, (minus, equal, plus) in enumerate(diff):
			sourceregion.UnionRegion(minus)
			if plugin is self.plugins[i]:
				sourceregion.UnionRegion(equal)
			else:
				copyregion.UnionRegion(equal)
			sourceregion.UnionRegion(plus)

		buffer = wx.EmptyBitmap(self.size.width, self.size.height)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
		self.copyBuffer(dc, {wx.Point(0, 0): copyregion})
		self.sourceBuffer(dc, sourceregion)
		dc.SelectObject(wx.NullBitmap)

		self.buffer = buffer

		self.Refresh()

	def updateScrollbars(self, offset=None, size=None):
		if offset is None:
			offset = self.offset
		if size is None:
			size = self.GetSize()

		x, y = offset
		width, height = size
		clientregion = wx.Region(x, y, width, height)
		initialclientregion = clientregion
		self.updatePluginRegions(clientregion=clientregion)
		[p.onUpdateClientRegion(clientregion) for p in self.plugins]
		x, y, w, h = self.pluginsregion.GetBox()

		self.ignoresize = True

		if x < offset.x or w - x > offset.x + size.width:
			self.SetScrollbar(wx.HORIZONTAL, offset.x, size.width, w - x, False)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0, False)

		size = self.GetClientSize()

		x, y = offset
		width, height = size
		clientregion = wx.Region(x, y, width, height)
		self.updatePluginRegions(clientregion=clientregion)
		[p.onUpdateClientRegion(clientregion) for p in self.plugins]
		x, y, w, h = self.pluginsregion.GetBox()

		if y < offset.y or h - y > offset.x + size.height:
			self.SetScrollbar(wx.VERTICAL, offset.y, size.height, h - y)
		else:
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)

		size = self.GetClientSize()

		x, y = offset
		width, height = size
		clientregion = wx.Region(x, y, width, height)
		self.updatePluginRegions(clientregion=clientregion)
		[p.onUpdateClientRegion(clientregion) for p in self.plugins]
		x, y, w, h = self.pluginsregion.GetBox()

		if x < offset.x or w - x > offset.x + size.width:
			self.SetScrollbar(wx.HORIZONTAL, offset.x, size.width, w - x)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

		size = self.GetClientSize()

		self.updatePluginRegions(clientregion=initialclientregion)

		self.ignoresize = False

		return size

	def updateClientRegion(self, offset=None, size=None):
		if offset is None:
			offset = self.offset
		if size is None:
			size = self.size

		x, y = offset
		width, height = size
		clientregion = wx.Region(x, y, width, height)

		regions1 = [plugin.buffered for plugin in self.plugins]

		size = self.updateScrollbars(offset=offset, size=size)

		width, height = size
		clientregion = wx.Region(x, y, width, height)

		updates = [p.onUpdateClientRegion(clientregion) for p in self.plugins]

		self.updatePluginRegions(clientregion=clientregion)

		regions2 = [plugin.buffered for plugin in self.plugins]

		diff = [diffRegion(r1, r2) for r1, r2 in zip(regions1, regions2)]

		copyregions = {}
		sourceregion = wx.Region()
		for i, (minus, equal, plus) in enumerate(diff):
			if isinstance(updates[i], wx.Point):
				if updates[i] not in copyregions:
					copyregions[updates[i]] = wx.Region()
				if updates[i] != wx.Point(0, 0):
					x, y = updates[i]
					equal = wx.Region()
					equal.UnionRegion(regions2[i])
					equal.Offset(-x, -y)
					equal.IntersectRegion(regions1[i])
					plus = wx.Region()
					plus.UnionRegion(regions2[i])
					equal.Offset(x, y)
					plus.SubtractRegion(equal)
					equal.Offset(-x, -y)
				copyregions[updates[i]].UnionRegion(equal)
			else:
				sourceregion.UnionRegion(equal)
			sourceregion.UnionRegion(plus)

		buffer = wx.EmptyBitmap(size.width, size.height)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
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

class Viewer(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.imagewindow = Window(self, -1)

		clearplugin = ClearPlugin(self.imagewindow)
		self.imagewindow.addPlugin(clearplugin)

		self.numarrayplugin = NumarrayPlugin(self.imagewindow)
		self.imagewindow.addPlugin(self.numarrayplugin)

		self.sizer = wx.GridBagSizer(0, 0)

		self.sizer.Add(self.imagewindow, (0, 0), (1, 1), wx.EXPAND|wx.FIXED_MINSIZE)

		self.sizer.AddGrowableRow(0)
		self.sizer.AddGrowableCol(0)

		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)

	def setNumarray(self, array):
		self.numarrayplugin.setNumarray(array)

if __name__ == '__main__':
	import sys
	import Mrc

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

	array = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
	app.panel.setNumarray(array)
	app.MainLoop()

