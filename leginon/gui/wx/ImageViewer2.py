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
		self._bitmaprect = wx.Rect(0, 0, 0, 0)
		self._bitmap = None
		self._blitrect = wx.Rect(0, 0, 0, 0)
		BufferedWindow.__init__(self, parent, id)

	def _updateBlitGeometry(self):
		if self._bitmap is None:
			self._blitrect.width = 0
			self._blitrect.height = 0
		else:
			self._blitrect.width = min(self._bitmaprect.width - self._bitmaprect.x,
																	self._clientwidth)
			self._blitrect.height = min(self._bitmaprect.height - self._bitmaprect.y,
																	self._clientheight)

	def _setBitmap(self, bitmap):
		self._bitmap = bitmap
		if bitmap is None:
			self._bitmaprect.width = 0
			self._bitmaprect.height = 0
		else:
			self._bitmaprect.width = self._bitmap.GetWidth()
			self._bitmaprect.height = self._bitmap.GetHeight()
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
			bitmap = self._bitmap.GetSubBitmap((self._bitmaprect.x,
																					self._bitmaprect.y,
																					self._blitrect.width,
																					self._blitrect.height))
			memorydc = wx.MemoryDC()
			memorydc.SelectObject(bitmap)

			dc.Blit(self._blitrect.x, self._blitrect.y,
							self._blitrect.width, self._blitrect.height,
							memorydc,
							0, 0)
		else:
			memorydc = wx.MemoryDC()
			memorydc.SelectObject(self._bitmap)
			dc.Blit(self._blitrect.x, self._blitrect.y,
							self._blitrect.width, self._blitrect.height,
							memorydc,
							self._bitmaprect.x, self._bitmaprect.y)
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
		if self._bitmap is None:
			self._blitrect.width = 0
			self._blitrect.height = 0
		else:
			self._blitrect.width = min(self._bitmaprect.width - self._bitmaprect.x,
																	int(self._clientwidth/self._xscale + 1))
			self._blitrect.height = min(self._bitmaprect.height - self._bitmaprect.y,
																	int(self._clientheight/self._yscale + 1))

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
		bitmapwidthscaled = self._bitmaprect.width*self._xscale
		if self._bitmap is None or bitmapwidthscaled >= self._clientwidth:
			xcentered = 0
		else:
			xcentered = (self._clientwidth - bitmapwidthscaled)/(2.0*self._xscale)

		bitmapheightscaled = self._bitmaprect.height*self._yscale
		if self._bitmap is None or bitmapheightscaled >= self._clientheight:
			ycentered = 0
		else:
			ycentered = (self._clientheight - bitmapheightscaled)/(2.0*self._yscale)

		if self._blitrect.x != xcentered:
			self._blitrect.x = xcentered
			self._refresh = True

		if self._blitrect.y != ycentered:
			self._blitrect.y = ycentered
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
		CenteredWindow.__init__(self, parent, id)

	def clientToImage(self, x, y):
		x /= self._xscale
		y /= self._yscale
		x -= self._blitrect.x
		y -= self._blitrect.y
		x += self._bitmaprect.x
		y += self._bitmaprect.y
		return x, y

	def imageToClient(self, x, y):
		x -= self._bitmaprect.x
		y -= self._bitmaprect.y
		x += self._blitrect.x
		y += self._blitrect.y
		x *= self._xscale
		y *= self._yscale
		return x, y

	def _setScale(self, x, y, center=None):
		if center is None:
			center = (self._clientwidth/2.0, self._clientheight/2.0)
		center = self.clientToImage(*center)
		CenteredWindow._setScale(self, x, y)
		self._setOffset(*center)

	def _setOffset(self, x, y):
		x -= self._clientwidth/(2.0*self._xscale)
		y -= self._clientheight/(2.0*self._yscale)
		x = min(x, self._bitmaprect.width - self._clientwidth/self._xscale
																			- self._blitrect.x*2)
		y = min(y, self._bitmaprect.height - self._clientheight/self._yscale
																				- self._blitrect.y*2)
		x = max(x, 0)
		y = max(y, 0)
		x = int(round(x))
		y = int(round(y))
		if self._bitmaprect.x != x:
			self._bitmaprect.x = x
			self._updatedrawing = True
			self._refresh = True
		if self._bitmaprect.y != y:
			self._bitmaprect.y = y
			self._updatedrawing = True
			self._refresh = True

	def setScale(self, x, y, center=None):
		self._setScale(x, y, center)
		if self._updatedrawing:
			self.updateDrawing()
		if self._refresh:
			self.Refresh()
			self._refresh = False

	def _onSize(self, evt):
		CenteredWindow._onSize(self, evt)
		x = min(self._bitmaprect.x, self._bitmaprect.width - self._clientwidth/self._xscale)
		y = min(self._bitmaprect.y, self._bitmaprect.height - self._clientheight/self._yscale)
		x = max(x, 0)
		y = max(y, 0)
		x = int(round(x))
		y = int(round(y))
		if self._bitmaprect.x != x:
			self._blitrect.width += self._bitmaprect.x - x
			self._bitmaprect.x = x
			self._updatedrawing = True
			self._refresh = True
		if self._bitmaprect.y != y:
			self._blitrect.height += self._bitmaprect.y - y
			self._bitmaprect.y = y
			self._updatedrawing = True
			self._refresh = True

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
			xrange = min(self._bitmaprect.widthscaled, self._bitmaprect.width)
			yrange = min(self._bitmaprect.heightscaled, self._bitmaprect.height)
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

	scale = 2.0

	def onLeftUp(evt):
		eventobject = evt.GetEventObject()
		xscale, yscale = eventobject.getScale()
		eventobject.setScale(xscale*scale, yscale*scale)

	def onRightUp(evt):
		eventobject = evt.GetEventObject()
		xscale, yscale = eventobject.getScale()
		eventobject.setScale(xscale/scale, yscale/scale)
		#eventobject.setScale(xscale/scale, yscale/scale, (evt.m_x, evt.m_y))

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
			self.panel = CenteredWindow(frame, -1)
			#self.panel = OffsetWindow(frame, -1)

			self.panel.Bind(wx.EVT_LEFT_UP, onLeftUp)
			self.panel.Bind(wx.EVT_RIGHT_UP, onRightUp)

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

