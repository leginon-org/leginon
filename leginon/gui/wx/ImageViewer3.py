import wx
import numarrayimage
import numextension
import gui.wx.ImageViewerEvents as Events
import gui.wx.ImageViewerTools as Tools

class	Window(wx.Window):
	def __init__(self, parent, id):
		wx.Window.__init__(self, parent, id)

		self.ignoresize = False

		clientwidth, clientheight = self.GetClientSize()
		self.buffer = wx.EmptyBitmap(clientwidth, clientheight)

		self.validregion = None

		self.source = None
		self.extrema = None
		self.scaledvaluerange = None

		self.scaledwidth = None
		self.scaledheight = None

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

	def copyBuffer(self, dc, region, offset):
		xoffset, yoffset = offset
		regioniterator = wx.RegionIterator(region)
		copydc = wx.MemoryDC()
		copydc.SelectObject(self.buffer)
		while(regioniterator):
			r = regioniterator.GetRect()
			dc.Blit(r.x, r.y, r.width, r.height, copydc, r.x + xoffset, r.y + yoffset)
			regioniterator.Next()
		copydc.SelectObject(wx.NullBitmap)

	def sourceBuffer(self, dc, region, offset):
		xoffset, yoffset = offset
		regioniterator = wx.RegionIterator(region)
		while(regioniterator):
			r = regioniterator.GetRect()
			bitmap = numarrayimage.numarray2wxBitmap(array,
																					r.x + xoffset, r.y + yoffset,
																					r.width, r.height,
																					self.scaledwidth, self.scaledheight,
																					self.scaledvaluerange)
			sourcedc = wx.MemoryDC()
			sourcedc.SelectObject(bitmap)
			dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
			sourcedc.SelectObject(wx.NullBitmap)
			regioniterator.Next()

	def onScroll(self, x, y):
		clientwidth, clientheight = self.GetClientSize()
		clientregion = wx.Region(0, 0, clientwidth, clientheight)

		if self.scaledwidth > clientwidth:
			dx = x - self.GetScrollPos(wx.HORIZONTAL)
			bitmapx = -x
		else:
			dx = 0
			bitmapx = int(round((clientwidth - self.scaledwidth)/2.0))

		if self.scaledheight > clientheight:
			dy = y - self.GetScrollPos(wx.VERTICAL)
			bitmapy = -y
		else:
			dy = 0
			bitmapy = int(round((clientheight - self.scaledheight)/2.0))

		bitmapregion = wx.Region(bitmapx, bitmapy,
															self.scaledwidth, self.scaledheight)

		self.validregion.Offset(-dx, -dy)

		copyregion = wx.Region()
		copyregion.UnionRegion(clientregion)
		copyregion.IntersectRegion(self.validregion)

		sourceregion = wx.Region()
		sourceregion.UnionRegion(clientregion)
		sourceregion.IntersectRegion(bitmapregion)
		sourceregion.SubtractRegion(copyregion)

		buffer = wx.EmptyBitmap(clientwidth, clientheight)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
		dc.Clear()
		self.copyBuffer(dc, copyregion, (dx, dy))
		self.sourceBuffer(dc, sourceregion, (-bitmapx, -bitmapy))
		dc.SelectObject(wx.NullBitmap)

		self.validregion = wx.Region()
		self.validregion.UnionRegion(copyregion)
		self.validregion.UnionRegion(sourceregion)

		self.buffer = buffer

		self.SetScrollPos(wx.HORIZONTAL, x)
		self.SetScrollPos(wx.VERTICAL, y)

		self.Refresh()

	def onScrollWin(self, orientation, position):
		if orientation == wx.HORIZONTAL:
			x = position
			x = max(0, x)
			x = min(x, self.GetScrollRange(orientation)
									- self.GetScrollThumb(orientation))
			y = self.GetScrollPos(wx.VERTICAL)
		elif orientation == wx.VERTICAL:
			x = self.GetScrollPos(wx.HORIZONTAL)
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

	def setNumarray(self, array):
		if self.source is None:
			widthscale = 1.0
			heightscale = 1.0
		else:
			if self.scaledwidth is None:
				widthscale = 1.0
			else:
				widthscale = self.scaledwidth/self.source.shape[1]
			if self.scaledheight is None:
				heightscale = 1.0
			else:
				heightscale = self.scaledheight/self.source.shape[0]

		self.source = array

		bufferwidth = self.buffer.GetWidth()
		bufferheight = self.buffer.GetHeight()

		if self.source is None:
			self.extrema = None
			self.scaledvaluerange = None
			self.scaledwidth, self.scaledheight = None, None
			self.ignoresize = True
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)
			self.ignoresize = False
			clientwidth, clientheight = self.GetClientSize()
			if bufferwidth != clientwidth or bufferheight != clientheight:
				self.buffer = wx.EmptyBitmap(clientwidth, clientheight)
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.Clear()
			dc.SelectObject(wx.NullBitmap)
			self.Refresh()
			return

		self.extrema = numextension.minmax(self.source)
		self.scaledvaluerange = self.extrema

		clientwidth, clientheight = self.GetClientSize()
		clientregion = wx.Region(0, 0, clientwidth, clientheight)

		if self.scaledwidth is not None:
			scrollx = float(self.GetScrollPos(wx.HORIZONTAL))/self.scaledwidth
		else:
			scrollx = 0
		if self.scaledheight is not None:
			scrolly = float(self.GetScrollPos(wx.VERTICAL))/self.scaledheight
		else:
			scrolly = 0

		self.scaledwidth = int(round(self.source.shape[1]*widthscale))
		self.scaledheight = int(round(self.source.shape[0]*heightscale))

		width, height = self.GetSize()

		self.ignoresize = True

		if self.scaledwidth > width:
			self.SetScrollbar(wx.HORIZONTAL, 0, width, self.scaledwidth, False)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

		clientwidth, clientheight = self.GetClientSize()

		if self.scaledheight > clientheight:
			bitmapy = -int(round(self.scaledheight*scrolly))
			bitmapy = max(bitmapy, clientheight - self.scaledheight)
			self.SetScrollbar(wx.VERTICAL, -bitmapy, clientheight, self.scaledheight)
		else:
			bitmapy = int(round((clientheight - self.scaledheight)/2.0))
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)

		clientwidth, clientheight = self.GetClientSize()

		if self.scaledwidth > clientwidth:
			bitmapx = -int(round(self.scaledwidth*scrollx))
			bitmapx = max(bitmapx, clientwidth - self.scaledwidth)
			self.SetScrollbar(wx.HORIZONTAL, -bitmapx, clientwidth, self.scaledwidth)
		else:
			bitmapx = int(round((clientwidth - self.scaledwidth)/2.0))
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

		self.ignoresize = False

		if bufferwidth != clientwidth or bufferheight != clientheight:
			self.buffer = wx.EmptyBitmap(clientwidth, clientheight)

		bitmapregion = wx.Region(bitmapx, bitmapy,
															self.scaledwidth, self.scaledheight)

		sourceregion = wx.Region()
		sourceregion.UnionRegion(clientregion)
		sourceregion.IntersectRegion(bitmapregion)

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.Clear()
		self.sourceBuffer(dc, sourceregion, (-bitmapx, -bitmapy))
		dc.SelectObject(wx.NullBitmap)

		self.validregion = sourceregion

		self.Refresh()

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

	def onSize(self, evt):
		evt.Skip()

		if self.ignoresize:
			return

		width, height = self.GetSize()

		if self.source is None or width < 1 or height < 1:
			self.ignoresize = True
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)
			self.ignoresize = False
			self.buffer = wx.EmptyBitmap(width, height)
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			dc.Clear()
			dc.SelectObject(wx.NullBitmap)
			return

		self.ignoresize = True

		bufferwidth = self.buffer.GetWidth()
		if self.scaledwidth < bufferwidth:
			x = int(round((bufferwidth - self.scaledwidth)/2.0))
		else:
			x = -self.GetScrollPos(wx.HORIZONTAL)

		bufferheight = self.buffer.GetHeight()
		if self.scaledheight < bufferheight:
			y = int(round((bufferheight - self.scaledheight)/2.0))
		else:
			y = -self.GetScrollPos(wx.VERTICAL)

		if self.scaledwidth > width:
			scrollx = self.GetScrollPos(wx.HORIZONTAL)
			self.SetScrollbar(wx.HORIZONTAL, scrollx, width, self.scaledwidth, False)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

		clientwidth, clientheight = self.GetClientSize()

		if self.scaledheight > clientheight:
			scrolly = max(0, -y)
			scrolly = min(scrolly, self.scaledheight - clientheight)
			bitmapy = -scrolly
			self.SetScrollbar(wx.VERTICAL, scrolly, clientheight, self.scaledheight)
		else:
			bitmapy = int(round((clientheight - self.scaledheight)/2.0))
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)
		dy = y - bitmapy

		clientwidth, clientheight = self.GetClientSize()

		if self.scaledwidth > clientwidth:
			scrollx = max(0, -x)
			scrollx = min(scrollx, self.scaledwidth - clientwidth)
			bitmapx = -scrollx
			self.SetScrollbar(wx.HORIZONTAL, scrollx, clientwidth, self.scaledwidth)
		else:
			bitmapx = int(round((clientwidth - self.scaledwidth)/2.0))
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)
		dx = x - bitmapx

		self.ignoresize = False

		self.validregion.Offset(-dx, -dy)

		clientregion = wx.Region(0, 0, clientwidth, clientheight)
		bitmapregion = wx.Region(bitmapx, bitmapy,
															self.scaledwidth, self.scaledheight)

		copyregion = wx.Region()
		copyregion.UnionRegion(clientregion)
		copyregion.IntersectRegion(self.validregion)

		sourceregion = wx.Region()
		sourceregion.UnionRegion(clientregion)
		sourceregion.IntersectRegion(bitmapregion)
		sourceregion.SubtractRegion(copyregion)

		buffer = wx.EmptyBitmap(clientwidth, clientheight)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
		dc.Clear()
		self.copyBuffer(dc, copyregion, (dx, dy))
		self.sourceBuffer(dc, sourceregion, (-bitmapx, -bitmapy))
		dc.SelectObject(wx.NullBitmap)

		self.validregion = wx.Region()
		self.validregion.UnionRegion(copyregion)
		self.validregion.UnionRegion(sourceregion)

		self.buffer = buffer

		# if the offset has changed paint the entire panel
		if dx != 0 or dy != 0:
			self.Refresh()

	def scaleSize(self, width, height):
		if self.source is None:
			return

		clientwidth, clientheight = self.GetClientSize()
		clientregion = wx.Region(0, 0, clientwidth, clientheight)

		if self.scaledwidth:
			scrollx = float(self.GetScrollPos(wx.HORIZONTAL))/self.scaledwidth
		else:
			scrollx = 0
		if self.scaledheight:
			scrolly = float(self.GetScrollPos(wx.VERTICAL))/self.scaledheight
		else:
			scrolly = 0

		self.scaledwidth = width
		self.scaledheight = height

		width, height = self.GetSize()

		self.ignoresize = True

		if self.scaledwidth > width:
			self.SetScrollbar(wx.HORIZONTAL, 0, width, self.scaledwidth, False)
		else:
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

		clientwidth, clientheight = self.GetClientSize()

		if self.scaledheight > clientheight:
			bitmapy = -int(round(self.scaledheight*scrolly))
			bitmapy = max(bitmapy, clientheight - self.scaledheight)
			self.SetScrollbar(wx.VERTICAL, -bitmapy, clientheight, self.scaledheight)
		else:
			bitmapy = int(round((clientheight - self.scaledheight)/2.0))
			self.SetScrollbar(wx.VERTICAL, 0, 0, 0)

		clientwidth, clientheight = self.GetClientSize()

		if self.scaledwidth > clientwidth:
			bitmapx = -int(round(self.scaledwidth*scrollx))
			bitmapx = max(bitmapx, clientwidth - self.scaledwidth)
			self.SetScrollbar(wx.HORIZONTAL, -bitmapx, clientwidth, self.scaledwidth)
		else:
			bitmapx = int(round((clientwidth - self.scaledwidth)/2.0))
			self.SetScrollbar(wx.HORIZONTAL, 0, 0, 0)

		self.ignoresize = False

		bufferwidth = self.buffer.GetWidth()
		bufferheight = self.buffer.GetHeight()
		if bufferwidth != clientwidth or bufferheight != clientheight:
			self.buffer = wx.EmptyBitmap(clientwidth, clientheight)

		bitmapregion = wx.Region(bitmapx, bitmapy,
															self.scaledwidth, self.scaledheight)

		sourceregion = wx.Region()
		sourceregion.UnionRegion(clientregion)
		sourceregion.IntersectRegion(bitmapregion)

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.Clear()
		self.sourceBuffer(dc, sourceregion, (-bitmapx, -bitmapy))
		dc.SelectObject(wx.NullBitmap)

		self.validregion = sourceregion

		self.Refresh()

	def scaleValues(self, valuerange):
		if self.source is None:
			return

		minvalue, maxvalue = valuerange
		if minvalue < self.extrema[0]:
			minvalue = self.extrema[0]
		if maxvalue > self.extrema[1]:
			maxvalue = self.extrema[1]
		self.scaledvaluerange = (minvalue, maxvalue)

		clientwidth, clientheight = self.GetClientSize()
		clientregion = wx.Region(0, 0, clientwidth, clientheight)

		bufferwidth = self.buffer.GetWidth()
		if self.scaledwidth < bufferwidth:
			bitmapx = int(round((bufferwidth - self.scaledwidth)/2.0))
		else:
			bitmapx = -self.GetScrollPos(wx.HORIZONTAL)

		bufferheight = self.buffer.GetHeight()
		if self.scaledheight < bufferheight:
			bitmapy = int(round((bufferheight - self.scaledheight)/2.0))
		else:
			bitmapy = -self.GetScrollPos(wx.VERTICAL)

		bitmapregion = wx.Region(bitmapx, bitmapy,
															self.scaledwidth, self.scaledheight)

		sourceregion = wx.Region()
		sourceregion.UnionRegion(clientregion)
		sourceregion.IntersectRegion(bitmapregion)

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.Clear()
		self.sourceBuffer(dc, sourceregion, (-bitmapx, -bitmapy))
		dc.SelectObject(wx.NullBitmap)

		self.validregion = sourceregion

		self.Refresh()

	def getValueRange(self):
		return self.extrema, self.scaledvaluerange

	def getSourceSize(self):
		return self.source.shape[1], self.source.shape[0]

class Viewer(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.imagewindow = Window(self, -1)

		self.scalesizetool = Tools.SizeScaler(self, -1)
		bitmap = Tools.getValueScaleBitmap((0, 255), (0, 255), 256, 16)
		self.scalevaluesbitmap = wx.StaticBitmap(self, -1, bitmap=bitmap)
		self.scalevaluestool = Tools.ValueScaler(self, -1)
		self.scalevaluestool.Show(False)

		self.sizer = wx.GridBagSizer(0, 0)

		self.sizer.Add(self.scalesizetool, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.scalevaluesbitmap, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.sizer.Add(self.scalevaluestool, (1, 0), (1, 2), wx.EXPAND)
		self.sizer.Add(self.imagewindow, (2, 0), (1, 2), wx.EXPAND|wx.FIXED_MINSIZE)

		self.sizer.AddGrowableRow(2)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.sizer.SetEmptyCellSize((0, 0))

		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)

		self.Bind(Events.EVT_SET_NUMARRAY, self.onSetNumarray)
		self.Bind(Events.EVT_SCALE_VALUES, self.onScaleValues)
		self.Bind(Events.EVT_SCALE_SIZE, self.onScaleSize)

		self.scalevaluesbitmap.Bind(wx.EVT_LEFT_UP, self.onScaleValuesBitmap)

	def onScaleValuesBitmap(self, evt):
		self.scalevaluestool.Show(not self.scalevaluestool.IsShown())
		self.sizer.Layout()
		evt.Skip()

	def onSetNumarray(self, evt):
		self.setNumarray(evt.GetNumarray())

	def setNumarray(self, array):
		self.imagewindow.setNumarray(array)
		self.scalevaluestool.setValueRange(*self.imagewindow.getValueRange())
		self.scalesizetool.setSize(*self.imagewindow.getSourceSize())

	def onScaleValues(self, evt):
		valuerange = evt.GetValueRange()
		self.imagewindow.scaleValues(valuerange)
		extrema = self.imagewindow.extrema
		bitmap = Tools.getValueScaleBitmap(extrema, valuerange, 256, 16)
		self.scalevaluesbitmap.SetBitmap(bitmap)

	def onScaleSize(self, evt):
		self.imagewindow.scaleSize(evt.GetWidth(), evt.GetHeight())

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

