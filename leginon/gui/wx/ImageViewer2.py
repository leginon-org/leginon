import math
import numextension
import wx

def getColorMap():
	b = [0] * 512 + range(256) + [255] * 512 + range(255, -1, -1)
	g = b[512:] + b[:512]
	r = g[512:] + g[:512]
	return zip(r, g, b)

colormap = getColorMap()

def wxBitmapFromNumarray(n, min=None, max=None, color=False):
	if min is None or max is None:
		min, max = numextension.minmax(n)
	wximage = wx.EmptyImage(n.shape[1], n.shape[0])
	if color:
		wximage.SetData(numextension.rgbstring(n, float(min), float(max), colormap))
	else:
		wximage.SetData(numextension.rgbstring(n, float(min), float(max)))
	return wx.BitmapFromImage(wximage)

class BufferedWindow(wx.Window):
	def __init__(self, parent, id):
		wx.Window.__init__(self, parent, id)

		self.onSize(None)

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)

	def onEraseBackground(self, evt):
		pass

	def _updateDrawing(self, dc):
		pass

	def updateDrawing(self):
		dc = wx.MemoryDC()
		dc.SelectObject(self._buffer)
		self._updateDrawing(dc)
		dc.SelectObject(wx.NullBitmap)

	def _onPaintRegion(self, dc, x, y, width, height, memorydc):
		dc.Blit(x, y, width, height, memorydc, x, y)

	def _onPaint(self, dc):
		memorydc = wx.MemoryDC()
		memorydc.SelectObject(self._buffer)
		regioniterator = wx.RegionIterator(self.GetUpdateRegion())
		while(regioniterator):
			rect = regioniterator.GetRect()
			self._onPaintRegion(dc, rect.x, rect.y, rect.width, rect.height, memorydc)
			regioniterator.Next()
		memorydc.SelectObject(wx.NullBitmap)

	def onPaint(self, evt):
		dc = wx.PaintDC(self) 
		dc.SetDeviceOrigin(0, 0)
		self._onPaint(dc)

	def _onSize(self, evt):
		self._clientwidth, self._clientheight = self.GetClientSizeTuple() 
		# TODO: set buffer size in steps
		self._buffer = wx.EmptyBitmap(self._clientwidth, self._clientheight) 

	def onSize(self, evt):
		self._onSize(evt)
		self.updateDrawing()
		if evt is not None:
			evt.Skip()

class BitmapWindow(BufferedWindow):
	def __init__(self, parent, id):
		self._xbitmap = 0
		self._ybitmap = 0
		self._bitmapwidth = 0
		self._bitmapheight = 0

		self._bitmap = None

		self._xblit = 0
		self._yblit = 0
		self._blitwidth = 0
		self._blitheight = 0

		BufferedWindow.__init__(self, parent, id)

	def _updateBlitGeometry(self):
		if self._bitmap is None:
			self._blitwidth = 0
			self._blitheight = 0
		else:
			self._blitwidth = min(self._bitmapwidth - self._xbitmap,
														self._clientwidth)
			self._blitheight = min(self._bitmapheight - self._ybitmap,
															self._clientheight)

	def _setBitmap(self, bitmap):
		self._bitmap = bitmap
		if bitmap is None:
			self._bitmapwidth = 0
			self._bitmapheight = 0
		else:
			self._bitmapwidth = self._bitmap.GetWidth()
			self._bitmapheight = self._bitmap.GetHeight()
		self._updateBlitGeometry()

	def setBitmap(self, bitmap):
		self._setBitmap(bitmap)
		self.updateDrawing()
		self.Refresh()

	def _updateDrawing(self, dc):
		BufferedWindow._updateDrawing(self, dc)

		# TODO: _draw smarter
		dc.Clear()

		if self._bitmap is None:
			return

		if wx.Platform == '__WXGTK__':
			bitmap = self._bitmap.GetSubBitmap((self._xbitmap, self._ybitmap,
																				self._blitwidth, self._blitheight))
			memorydc = wx.MemoryDC()
			memorydc.SelectObject(bitmap)

			dc.Blit(self._xblit, self._yblit,
							self._blitwidth, self._blitheight,
							memorydc,
							0, 0)
		else:
			memorydc = wx.MemoryDC()
			memorydc.SelectObject(self._bitmap)
			dc.Blit(self._xblit, self._yblit,
							self._blitwidth, self._blitheight,
							memorydc,
							self._xbitmap, self._ybitmap)
		memorydc.SelectObject(wx.NullBitmap)

	def _onSize(self, evt):
		BufferedWindow._onSize(self, evt)
		self._updateBlitGeometry()

class ScaledWindow(BitmapWindow):
	def __init__(self, parent, id):
		self._xscale = 1.0
		self._yscale = 1.0
		self._updatedrawing = False
		self._refresh = False

		BitmapWindow.__init__(self, parent, id)

	def _updateBlitGeometry(self):
		BitmapWindow._updateBlitGeometry(self)

	def _setScale(self, x, y):
		updated = False
		if self._xscale != x:
			self._xscale = x
			if self._bitmap is not None:
				updated = True
		if self._yscale != y:
			self._yscale = y
			if self._bitmap is not None:
				updated = True
		if updated:
			self._updatedrawing = True
			self._refresh = True
		self._updateBlitGeometry()

	def setScale(self, x, y):
		self._setScale(x, y)
		if self._updatedrawing:
			self.updateDrawing()
		if self._refresh:
			self.Refresh()
			self._refresh = False

	def getScale(self):
		return (self._xscale, self._yscale)

	def _updateDrawing(self, dc):
		dc.SetUserScale(self._xscale, self._yscale)
		BitmapWindow._updateDrawing(self, dc)
		self._updatedrawing = False

class CenteredWindow(ScaledWindow):
	def __init__(self, parent, id):
		self._xcentered = 0
		self._ycentered = 0
		ScaledWindow.__init__(self, parent, id)

	def _updateBlitGeometry(self):
		ScaledWindow._updateBlitGeometry(self)
		bitmapwidthscaled = self._bitmapwidth*self._xscale
		if self._bitmap is None or bitmapwidthscaled >= self._clientwidth:
			xcentered = 0
		else:
			xcentered = (self._clientwidth - bitmapwidthscaled)/(2.0*self._xscale)

		bitmapheightscaled = self._bitmapheight*self._yscale
		if self._bitmap is None or bitmapheightscaled >= self._clientheight:
			ycentered = 0
		else:
			ycentered = (self._clientheight - bitmapheightscaled)/(2.0*self._yscale)

		if self._xblit != xcentered:
			self._xblit = xcentered
			self._refresh = True

		if self._yblit != ycentered:
			self._yblit = ycentered
			self._refresh = True

	def _onSize(self, evt):
		ScaledWindow._onSize(self, evt)
		if self._refresh:
			# GTK requests a paint of the full area on size
			if wx.Platform != '__WXGTK__':
				self.Refresh()
			self._refresh = False

class OffsetWindow(CenteredWindow):
	def __init__(self, parent, id):
		self._xoffset = 0
		self._yoffset = 0
		ScaledWindow.__init__(self, parent, id)

	def _updateBlitGeometry(self):
		CenteredWindow._updateBlitGeometry(self)
		self._xbitmap = int(round(self._xoffset/self._xscale))
		self._ybitmap = int(round(self._yoffset/self._yscale))

	def clientToImage(self, x, y):
		x /= self._xscale
		y /= self._yscale
		x -= self._xblit*self._xscale
		y -= self._yblit*self._yscale
		x += self._xbitmap
		y += self._ybitmap
		return x, y

	def imageToClient(self, x, y):
		x -= self._xbitmap
		y -= self._ybitmap
		x += self._xblit*self._xscale
		y += self._yblit*self._yscale
		x *= self._xscale
		y *= self._yscale
		return x, y

	def _setScale(self, x, y, center=None):
		'''
		if center is None:
			center = (self._clientwidth/2.0, self._clientheight/2.0)
		center = self.clientToImage(*center)
		'''
		CenteredWindow._setScale(self, x, y)

	def setScale(self, x, y, center=None):
		self._setScale(x, y, center)
		if self._updatedrawing:
			self.updateDrawing()
		if self._refresh:
			self.Refresh()
			self._refresh = False

class ScrolledWindow(OffsetWindow):
	def __init__(self, parent, id):
		self._xscroll = 0
		self._yscroll = 0
		OffsetWindow.__init__(self, parent, id)

	def updateScrollbars(self, position=None):
		if position is None:
			xposition = self.GetScrollPos(wx.HORIZONTAL)
			yposition = self.GetScrollPos(wx.VERTICAL)
		else:
			xposition, yposition = position
		xthumbsize = min(int(self._clientwidth/self._xscale), self._clientwidth)
		ythumbsize = min(int(self._clientheight/self._yscale), self._clientheight)
		if self._bitmap is None:
			xrange, yrange = 0, 0
		else:
			xrange = min(self._bitmapwidthscaled, self._bitmapwidth)
			yrange = min(self._bitmapheightscaled, self._bitmapheight)
		self.SetScrollbar(wx.HORIZONTAL, xposition, xthumbsize, xrange)
		self.SetScrollbar(wx.VERTICAL, yposition, ythumbsize, yrange)
		self._xscroll = self.GetScrollPos(wx.HORIZONTAL)
		self._yscroll = self.GetScrollPos(wx.VERTICAL)

	def _onSize(self, evt):
		self.updateScrollbars()
		OffsetWindow._onSize(self, x, y)

if __name__ == '__main__':
	import sys
	import Mrc
	import numarray

	def wxBitmapFromMRC(filename, min=None, max=None, color=False):
		n = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
		return wxBitmapFromNumarray(n, min, max, color)

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			#self.panel = BufferedWindow(frame, -1)
			#self.panel = BitmapWindow(frame, -1)
			#self.panel = ScaledWindow(frame, -1)
			#self.panel = CenteredWindow(frame, -1)
			self.panel = OffsetWindow(frame, -1)

			self.panel.Bind(wx.EVT_LEFT_UP,
		#lambda e: self.panel.setScale(*(tuple(map(lambda s: s*2.0, self.panel.getScale()))))
		lambda e: self.panel.setScale(*(tuple(map(lambda s: s*2.0, self.panel.getScale()))) + ((e.m_x, e.m_y),))
			)

			self.panel.Bind(wx.EVT_RIGHT_UP,
		lambda e: self.panel.setScale(*map(lambda s: s/2.0, self.panel.getScale())))

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		import numarray
		n = numarray.zeros((2048, 2048))
		n[:1024, :1024] = numarray.ones((1024, 1024))
		n[1024:, 1024:] = numarray.ones((1024, 1024))
		app.panel.setBitmap(wxBitmapFromNumarray(n))
	else:
		app.panel.setBitmap(wxBitmapFromMRC(filename, color=True))
	app.MainLoop()

