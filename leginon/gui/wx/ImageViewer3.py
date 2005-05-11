import wx
import numarrayimage
import gui.wx.ImageViewerEvents as Events
import gui.wx.ImageViewerTools as Tools

class Plugin(wx.EvtHandler):
	def __init__(self, hasalpha=False):
		wx.EvtHandler.__init__(self)
		self.hasalpha = hasalpha

	def GetId(self):
		return -1

	def getRegion(self):
		raise NotImplementedError

	def draw(self, dc, region, offset):
		raise NotImplementedError

class ClearPlugin(Plugin):
	def __init__(self):
		self.color = wx.WHITE
		self.brush = wx.TheBrushList.FindOrCreateBrush(self.color, wx.SOLID)
		Plugin.__init__(self)

	def getRegion(self):
		return None

	def draw(self, dc, region, offset):
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
	def __init__(self):
		Plugin.__init__(self)
		self.array = None
		self.size = wx.Size()
		self.extrema = None
		self.valuerange = None
		self.scale = 1.0
		self.fitpage = False

		self.Bind(wx.EVT_SIZE, self.onSize)

	def _fitToPage(self, width, height):
		widthscale = float(width)/self.array.shape[1]
		heightscale = float(height)/self.array.shape[0]
		if widthscale < heightscale:
			self.size.width = width
			self.size.height = int(round(float(self.array.shape[0])*widthscale))
		elif heightscale < widthscale:
			self.size.width = int(round(float(self.array.shape[1])*heightscale))
			self.size.height = height
		else:
			self.size.width = width
			self.size.height = height

	def fitToPage(self, width, height):
		self.fitpage = True
		region = self.getRegion()

		self._fitToPage(width, height)

		region.UnionRegion(self.getRegion())
		evt = Events.UpdatePluginRegionEvent(self, region)
		self.AddPendingEvent(evt)

	def onSize(self, evt):
		if self.array is not None and self.fitpage:
			width, height = evt.GetSize()
			self._fitToPage(width, height)
		evt.Skip()

	def setScale(self, scale):
		self.fitpage = False
		region = self.getRegion()
		self.scale = scale
		self.size.width = int(round(self.scale*self.array.shape[1]))
		self.size.height = int(round(self.scale*self.array.shape[0]))
		region.UnionRegion(self.getRegion())
		evt = Events.UpdatePluginRegionEvent(self, region)
		self.AddPendingEvent(evt)

	def setNumarray(self, array):
		region = self.getRegion()

		if array is None:
			self.size.width = 0
			self.size.height = 0
			self.extrema = None
			self.valuerange = None
		else:
			self.size.width = int(round(self.scale*array.shape[1]))
			self.size.height = int(round(self.scale*array.shape[0]))
			self.extrema = (array.min(), array.max())
			self.valuerange = self.extrema

		self.array = array

		region.UnionRegion(self.getRegion())
		evt = Events.UpdatePluginRegionEvent(self, region)
		self.AddPendingEvent(evt)

	def setValueRange(self, valuerange):
		self.valuerange = valuerange
		region = self.getRegion()
		evt = Events.UpdatePluginRegionEvent(self, region)
		self.AddPendingEvent(evt)

	def getXYValue(self, x, y):
		if self.array is None:
			return None

		x = int(round(x/self.scale))
		y = int(round(y/self.scale))

		if x < 0 or x >= self.array.shape[1] or y < 0 or y >= self.array.shape[0]:
			value = None
		else:
			value = self.array[y, x]

		return x, y, value

	def getRegion(self):
		if self.array is None:
			return wx.Region()
		else:
			return wx.Region(0, 0, self.size.width, self.size.height)

	def draw(self, dc, region, offset):
		regioniterator = wx.RegionIterator(region)
		while(regioniterator):
			r = regioniterator.GetRect()
			bitmap = numarrayimage.numarray2wxBitmap(
								array,
								r.x + offset.x, r.y + offset.y,
								r.width, r.height,
								self.size.width, self.size.height,
								self.valuerange)
			sourcedc = wx.MemoryDC()
			sourcedc.SelectObject(bitmap)
			dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
			sourcedc.SelectObject(wx.NullBitmap)
			regioniterator.Next()

class CrosshairsPlugin(Plugin):
	def __init__(self, plugin):
		self.size = 1
		self.color = wx.BLUE
		self.brush = wx.TheBrushList.FindOrCreateBrush(self.color, wx.SOLID)
		self.plugin = plugin
		Plugin.__init__(self, hasalpha=True)

	def getRegion(self):
		return None

	def draw(self, dc, region, offset):
		pluginregion = self.plugin.getRegion()
		x, y, width, height = region.GetBox()
		pluginx, pluginy, pluginwidth, pluginheight = pluginregion.GetBox()

		crosshairsregion = wx.Region()
		y = pluginy + (pluginheight - self.size)/2
		crosshairsregion.Union(x, y, width, self.size)
		x = pluginx + (pluginwidth - self.size)/2
		crosshairsregion.Union(x, y, self.size, height)
		crosshairsregion.IntersectRegion(region)

		dc.SetPen(wx.TRANSPARENT_PEN)
		dc.SetBrush(self.brush)
		regioniterator = wx.RegionIterator(crosshairsregion)
		while(regioniterator):
			r = regioniterator.GetRect()
			dc.DrawRectangle(r.x, r.y, r.width, r.height)
			regioniterator.Next()
		dc.SetBrush(wx.NullBrush)
		dc.SetPen(wx.NullPen)

class	Window(wx.Window):
	def __init__(self, parent, id):
		wx.Window.__init__(self, parent, id)

		self.ignoresize = False

		self.plugins = []

		self.offset = wx.Point(0, 0)
		self.pluginregion = wx.Region()

		self.size = self.GetClientSize()
		self.buffer = wx.EmptyBitmap(self.size.width, self.size.height)

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_SCROLLWIN_TOP, self.onScrollWinTop)
		self.Bind(wx.EVT_SCROLLWIN_BOTTOM, self.onScrollWinBottom)
		self.Bind(wx.EVT_SCROLLWIN_LINEUP, self.onScrollWinLineUp)
		self.Bind(wx.EVT_SCROLLWIN_LINEDOWN, self.onScrollWinLineDown)
		self.Bind(wx.EVT_SCROLLWIN_PAGEUP, self.onScrollWinPageUp)
		self.Bind(wx.EVT_SCROLLWIN_PAGEDOWN, self.onScrollWinPageDown)
		self.Bind(wx.EVT_SCROLLWIN_THUMBTRACK, self.onScrollWinThumbTrack)

		self.Bind(Events.EVT_UPDATE_PLUGIN_REGION, self.onUpdatePluginRegion)

	def copyBuffer(self, dc, region, offset=(0, 0)):
		x, y = offset
		regioniterator = wx.RegionIterator(region)
		copydc = wx.MemoryDC()
		copydc.SelectObject(self.buffer)
		while(regioniterator):
			r = regioniterator.GetRect()
			dc.Blit(r.x, r.y, r.width, r.height, copydc, r.x + x, r.y + y)
			regioniterator.Next()
		copydc.SelectObject(wx.NullBitmap)

	def sourceBuffer(self, dc, sourceregion):
		backgroundregion = wx.Region()
		backgroundregion.UnionRegion(sourceregion)

		self.plugins.reverse()
		plugins = []
		for plugin in self.plugins:
			region = wx.Region()
			region.UnionRegion(backgroundregion)
			pluginregion = plugin.getRegion()
			if pluginregion is not None:
				pluginregion.Offset(-self.offset.x, -self.offset.y)
				region.IntersectRegion(pluginregion)
			plugins.append((plugin, region))
			if not plugin.hasalpha:
				backgroundregion.SubtractRegion(region)
		self.plugins.reverse()

		for plugin, region in plugins:
			plugin.draw(dc, region, self.offset)

	def offsetClientRegion(self, x=None, y=None):
		if x is None:
			dx = 0
		else:
			dx = x - self.offset.x
		if y is None:
			dy = 0
		else:
			dy = y - self.offset.y

		copyregion = wx.Region(-dx, -dy, self.size.width, self.size.height)
		copyregion.Intersect(0, 0, self.size.width, self.size.height)

		sourceregion = wx.Region(0, 0, self.size.width, self.size.height)
		sourceregion.SubtractRegion(copyregion)

		self.offset.x += dx
		self.offset.y += dy

		buffer = wx.EmptyBitmap(self.size.width, self.size.height)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
		self.copyBuffer(dc, copyregion, offset=(dx, dy))
		self.sourceBuffer(dc, sourceregion)
		dc.SelectObject(wx.NullBitmap)

		self.buffer = buffer

		self.Refresh()

	def onScroll(self, x=None, y=None):
		if x is not None:
			self.SetScrollPos(wx.HORIZONTAL, x)
		if y is not None:
			self.SetScrollPos(wx.VERTICAL, y)

		self.offsetClientRegion(x, y)

	def onScrollWin(self, orientation, position):
		if orientation == wx.HORIZONTAL:
			x = position
			x = max(0, x)
			x = min(x, self.GetScrollRange(orientation)
									- self.GetScrollThumb(orientation))
			y = None
		elif orientation == wx.VERTICAL:
			x = None
			y = position
			y = max(0, y)
			y = min(y, self.GetScrollRange(orientation)
									- self.GetScrollThumb(orientation))
		self.onScroll(x, y)

	def onScrollWinTop(self, evt):
		orientation = evt.GetOrientation()
		position = 0
		self.onScrollWin(orientation, position)

	def onScrollWinBottom(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollRange(orientation)
		position -= self.GetScrollThumb(orientation)
		self.onScrollWin(orientation, position)

	def onScrollWinLineUp(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation)
		position -= 1
		self.onScrollWin(orientation, position)

	def onScrollWinLineDown(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation)
		position += 1
		self.onScrollWin(orientation, position)

	def onScrollWinPageUp(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation)
		position -= self.GetScrollThumb(orientation)
		self.onScrollWin(orientation, position)

	def onScrollWinPageDown(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation)
		position += self.GetScrollThumb(orientation)
		self.onScrollWin(orientation, position)

	def onScrollWinThumbTrack(self, evt):
		orientation = evt.GetOrientation()
		position = evt.GetPosition()
		self.onScrollWin(orientation, position)

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

	def getPluginRegion(self):
		region = wx.Region()
		for plugin in self.plugins:
			pluginregion = plugin.getRegion()
			if pluginregion is not None:
				region.UnionRegion(pluginregion)
		return region

	def onUpdatePluginRegion(self, evt):
		x0, y0, width0, height0 = self.pluginregion.GetBox()
		self.pluginregion = self.getPluginRegion()
		x, y, width, height = self.pluginregion.GetBox()

		if width0 == width and height0 == height:
			region = evt.GetRegion()
			sourceregion = wx.Region(0, 0, self.size.width, self.size.height)
			region.Offset(-self.offset.x, -self.offset.y)
			sourceregion.IntersectRegion(region)
			region.Offset(self.offset.x, self.offset.y)
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			self.sourceBuffer(dc, sourceregion)
			dc.SelectObject(wx.NullBitmap)
			self.Refresh()
			return

		clientwidth, clientheight = self.GetSize()

		if width0:
			xscale = float(width)/width0
			scrollx = int(round(self.GetScrollPos(wx.HORIZONTAL)*xscale))
		else:
			scrollx = 0
		if height0:
			yscale = float(height)/height0
			scrolly = int(round(self.GetScrollPos(wx.VERTICAL)*yscale))
		else:
			scrolly = 0

		self.ignoresize = True

		if width > clientwidth:
			self.SetScrollbar(wx.HORIZONTAL, 0, clientwidth, width, False)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0, False)

		clientwidth, clientheight = self.GetClientSize()

		if height > clientheight:
			y = max(0, scrolly)
			y = min(scrolly, height - clientheight)
			self.SetScrollbar(wx.VERTICAL, y, clientheight, height)
		else:
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)
			y = int(round((height - clientheight)/2.0))

		clientwidth, clientheight = self.GetClientSize()

		if width > clientwidth:
			x = max(0, scrollx)
			x = min(scrollx, width - clientwidth)
			self.SetScrollbar(wx.HORIZONTAL, x, clientwidth, width)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)
			x = int(round((width - clientwidth)/2.0))

		self.ignoresize = False

		self.offset.x = x
		self.offset.y = y

		clientregion = wx.Region(0, 0, self.size.width, self.size.height)

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		self.sourceBuffer(dc, clientregion)
		dc.SelectObject(wx.NullBitmap)

		self.Refresh()

	def resizeClientRegion(self):
		x, y, width, height = self.pluginregion.GetBox()

		clientwidth, clientheight = self.GetSize()

		self.ignoresize = True

		if width > clientwidth:
			scrollx = self.GetScrollPos(wx.HORIZONTAL)
			self.SetScrollbar(wx.HORIZONTAL, scrollx, clientwidth, width, False)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0, False)

		clientwidth, clientheight = self.GetClientSize()

		if height > clientheight:
			scrolly = max(0, self.offset.y)
			scrolly = min(scrolly, height - clientheight)
			self.SetScrollbar(wx.VERTICAL, scrolly, clientheight, height)
			dy = scrolly - self.offset.y
		else:
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)
			dy = int(round((height - clientheight)/2.0)) - self.offset.y

		clientwidth, clientheight = self.GetClientSize()

		if width > clientwidth:
			scrollx = max(0, self.offset.x)
			scrollx = min(scrollx, width - clientwidth)
			self.SetScrollbar(wx.HORIZONTAL, scrollx, clientwidth, width)
			dx = scrollx - self.offset.x
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)
			dx = int(round((width - clientwidth)/2.0)) - self.offset.x

		self.ignoresize = False

		self.offset.x += dx
		self.offset.y += dy

		copyregion = wx.Region(-dx, -dy, self.size.width, self.size.height)
		self.size = self.GetClientSize()
		copyregion.Intersect(0, 0, self.size.width, self.size.height)

		sourceregion = wx.Region(0, 0, self.size.width, self.size.height)
		sourceregion.SubtractRegion(copyregion)

		buffer = wx.EmptyBitmap(clientwidth, clientheight)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
		self.copyBuffer(dc, copyregion, offset=(dx, dy))
		self.sourceBuffer(dc, sourceregion)
		dc.SelectObject(wx.NullBitmap)

		self.buffer = buffer

		if dx != 0 or dy != 0:
			self.Refresh()

	def onSize(self, evt):
		evt.Skip()

		if self.ignoresize:
			return

		self.resizeClientRegion()

class Viewer(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.imagewindow = Window(self, -1)

		clearplugin = ClearPlugin()
		clearplugin.SetNextHandler(self.imagewindow)
		clearplugin.SetNextHandler(self.imagewindow)
		self.imagewindow.PushEventHandler(clearplugin)
		self.imagewindow.plugins.append(clearplugin)

		self.numarrayplugin = NumarrayPlugin()
		self.numarrayplugin.SetNextHandler(self.imagewindow)
		self.imagewindow.PushEventHandler(self.numarrayplugin)
		self.imagewindow.plugins.append(self.numarrayplugin)

		crosshairsplugin = CrosshairsPlugin(self.numarrayplugin)
		crosshairsplugin.SetNextHandler(self.imagewindow)
		self.imagewindow.PushEventHandler(crosshairsplugin)
		self.imagewindow.plugins.append(crosshairsplugin)

		self.informationbutton = wx.Button(self, -1, 'Information')
		self.displaybutton = wx.Button(self, -1, 'Display')
		self.scalesizetool = Tools.SizeScaler(self, -1)
		self.scalevaluesbitmap = Tools.ValueScaleBitmap(self, -1)

		self.informationtool = Tools.Information(self, -1)
		self.informationtool.Show(False)
		self.displaytool = Tools.Display(self, -1)
		self.displaytool.Show(False)
		self.scalevaluestool = Tools.ValueScaler(self, -1)
		self.scalevaluestool.Show(False)

		self.sizer = wx.GridBagSizer(0, 0)

		self.sizer.Add(self.informationbutton, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.displaybutton, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.scalesizetool, (0, 2), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.scalevaluesbitmap, (0, 3), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.informationtool, (1, 0), (1, 4), wx.EXPAND)
		self.sizer.Add(self.displaytool, (2, 0), (1, 4), wx.EXPAND)
		self.sizer.Add(self.scalevaluestool, (3, 0), (1, 4), wx.EXPAND)
		self.sizer.Add(self.imagewindow, (4, 0), (1, 4), wx.EXPAND|wx.FIXED_MINSIZE)

		self.sizer.AddGrowableRow(4)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)
		self.sizer.AddGrowableCol(2)
		self.sizer.AddGrowableCol(3)

		self.sizer.SetEmptyCellSize((0, 0))

		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)

		self.informationbutton.Bind(wx.EVT_BUTTON, self.onInformationButton)
		self.displaybutton.Bind(wx.EVT_BUTTON, self.onDisplayButton)
		self.scalevaluesbitmap.Bind(wx.EVT_LEFT_UP, self.onScaleValuesBitmap)

		self.Bind(Events.EVT_SCALE_VALUES, self.onScaleValues)
		self.Bind(Events.EVT_SCALE_SIZE, self.onScaleSize)
		self.Bind(Events.EVT_FIT_TO_PAGE, self.onFitToPage)
		self.Bind(Events.EVT_DISPLAY_CROSSHAIRS, self.onDisplayCrosshairs)

	def onImageWindowMotion(self, evt):
		x, y = evt.m_x, evt.m_y
		x += self.imagewindow.offset.x
		y += self.imagewindow.offset.y
		x, y, value = self.numarrayplugin.getXYValue(x, y)
		self.informationtool.setValue(x, y, value)
		evt.Skip()

	def onInformationButton(self, evt):
		self.informationtool.Show(not self.informationtool.IsShown())
		if self.informationtool.IsShown():
			self.imagewindow.Bind(wx.EVT_MOTION, self.onImageWindowMotion)
		else:
			self.imagewindow.Unbind(wx.EVT_MOTION)
		self.sizer.Layout()

	def onDisplayButton(self, evt):
		self.displaytool.Show(not self.displaytool.IsShown())
		self.sizer.Layout()
		evt.Skip()

	def onScaleValuesBitmap(self, evt):
		self.scalevaluestool.Show(not self.scalevaluestool.IsShown())
		self.sizer.Layout()
		evt.Skip()

	def setNumarray(self, array):
		self.numarrayplugin.setNumarray(array)
		self.informationtool.setStatistics(array)
		self.scalevaluestool.setValueRange(self.numarrayplugin.extrema,
																				self.numarrayplugin.valuerange)
		self.scalevaluesbitmap.updateParameters(self.numarrayplugin.extrema,
																						self.numarrayplugin.valuerange)

	def onScaleValues(self, evt):
		valuerange = evt.GetValueRange()
		self.numarrayplugin.setValueRange(valuerange)
		self.scalevaluesbitmap.updateParameters(self.numarrayplugin.extrema,
																						self.numarrayplugin.valuerange)

	def onScaleSize(self, evt):
		self.numarrayplugin.setScale(evt.GetScale())

	def onFitToPage(self, evt):
		width, height = self.imagewindow.GetClientSize()
		self.numarrayplugin.fitToPage(width, height)

	def onDisplayCrosshairs(self, evt):
		self.imagewindow.enablePlugin(self.crosshairsplugin, evt.display)

if __name__ == '__main__':
	import sys
	import Mrc

	filename = sys.argv[1]

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.panel = Viewer(frame, -1)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)

	array = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
	app.panel.setNumarray(array)
	app.MainLoop()

