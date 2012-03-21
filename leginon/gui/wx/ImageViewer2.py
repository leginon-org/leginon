import math
from pyami import arraystats
import wx
import time

def getColorMap():
	b = [0] * 512 + range(256) + [255] * 512 + range(255, -1, -1)
	g = b[512:] + b[:512]
	r = g[512:] + g[:512]
	return zip(r, g, b)

colormap = getColorMap()

def wxBitmapFromNumarray(n, min=None, max=None, color=False):
	if min is None or max is None:
		min = arraystats.min(n)
		max = arraystats.max(n)
	wximage = wx.EmptyImage(n.shape[1], n.shape[0])
	if color:
		wximage.SetData(numextension.rgbstring(n, float(min), float(max), colormap))
	else:
		wximage.SetData(numextension.rgbstring(n, float(min), float(max)))
	return wx.BitmapFromImage(wximage)

class BufferedWindow(wx.Window):
	def __init__(self, parent, id):
		wx.Window.__init__(self, parent, id)

		self._clientwidth, self._clientheight = self.GetClientSizeTuple() 
		self._buffer = wx.EmptyBitmap(self._clientwidth, self._clientheight)

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
		self._fit = False
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
		self._fit = False
		self._setScale(x, y)
		if self._updatedrawing:
			self.updateDrawing()
		if self._refresh:
			self.Refresh()
			self._refresh = False

	def setFit(self, fit):
		self._fit = fit

	def getScale(self):
		return (self._xscale, self._yscale)

	def _updateDrawing(self, dc):
		dc.SetUserScale(self._xscale, self._yscale)
		BitmapWindow._updateDrawing(self, dc)
		self._updatedrawing = False

	def _setBitmap(self, bitmap):
		BitmapWindow._setBitmap(self, bitmap)
		if self._fit:
			self.fit()

	def _onSize(self, evt):
		BitmapWindow._onSize(self, evt)
		if self._fit:
			self.fit()

	def fit(self):
		try:
			x = float(self._clientwidth)/self._bitmaprect.width
			y = float(self._clientheight)/self._bitmaprect.height
			scale = min(x, y)
			self._setScale(scale, scale)
		except ZeroDivisionError:
			return False
		return True

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
		CenteredWindow.__init__(self, parent, id)

	def clientToBitmap(self, x, y):
		x /= self._xscale
		y /= self._yscale
		x -= self._blitrect.x
		y -= self._blitrect.y
		x += self._bitmaprect.x
		y += self._bitmaprect.y
		return x, y

	def bitmapToClient(self, x, y):
		x -= self._bitmaprect.x
		y -= self._bitmaprect.y
		x += self._blitrect.x
		y += self._blitrect.y
		x *= self._xscale
		y *= self._yscale
		return x, y

	def centerOffset(self, x, y):
		x -= self._clientwidth/(2.0*self._xscale)
		y -= self._clientheight/(2.0*self._yscale)
		self.setOffset(x, y)

	def _setOffset(self, x, y):
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

		return x, y

	def setOffset(self, x, y):
		self._setOffset(x, y)
		if self._updatedrawing:
			self.updateDrawing()
		if self._refresh:
			self.Refresh()
			self._refresh = False

	def _updateBlitGeometry(self):
		CenteredWindow._updateBlitGeometry(self)
		x = min(self._bitmaprect.x,
						self._bitmaprect.width - self._clientwidth/self._xscale)
		y = min(self._bitmaprect.y,
						self._bitmaprect.height - self._clientheight/self._yscale)
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
		OffsetWindow.__init__(self, parent, id)
		self.Bind(wx.EVT_SCROLLWIN_TOP, self.onScrollWinTop)
		self.Bind(wx.EVT_SCROLLWIN_BOTTOM, self.onScrollWinBottom)
		self.Bind(wx.EVT_SCROLLWIN_LINEUP, self.onScrollWinLineUp)
		self.Bind(wx.EVT_SCROLLWIN_LINEDOWN, self.onScrollWinLineDown)
		self.Bind(wx.EVT_SCROLLWIN_PAGEUP, self.onScrollWinPageUp)
		self.Bind(wx.EVT_SCROLLWIN_PAGEDOWN, self.onScrollWinPageDown)
		self.Bind(wx.EVT_SCROLLWIN_THUMBTRACK, self.onScrollWinThumbTrack)

	def onScrollWinTop(self, evt):
		orientation = evt.GetOrientation()
		position = 0
		self.onScrollWin(orientation, position)

	def onScrollWinBottom(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollRange(orientation)
		self.onScrollWin(orientation, position)

	def onScrollWinLineUp(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation) - 1
		self.onScrollWin(orientation, position)

	def onScrollWinLineDown(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation) + 1
		self.onScrollWin(orientation, position)

	def onScrollWinPageUp(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation) - self.GetScrollThumb(orientation)
		self.onScrollWin(orientation, position)

	def onScrollWinPageDown(self, evt):
		orientation = evt.GetOrientation()
		position = self.GetScrollPos(orientation) + self.GetScrollThumb(orientation)
		self.onScrollWin(orientation, position)

	def onScrollWinThumbTrack(self, evt):
		orientation = evt.GetOrientation()
		position = evt.GetPosition()
		self.onScrollWin(orientation, position)

	def onScrollWin(self, orientation, position):
		if orientation == wx.HORIZONTAL:
			x = position
			y = self.GetScrollPos(wx.VERTICAL)
		elif orientation == wx.VERTICAL:
			x = self.GetScrollPos(wx.HORIZONTAL)
			y = position
		wx.CallAfter(self.setOffset, x, y)

	def _setOffset(self, x, y):
		x, y = OffsetWindow._setOffset(self, x, y)
		self.SetScrollPos(wx.HORIZONTAL, x)
		self.SetScrollPos(wx.VERTICAL, y)

	def updateScrollbars(self):
		xposition = self.GetScrollPos(wx.HORIZONTAL)
		yposition = self.GetScrollPos(wx.VERTICAL)
		xthumbsize = min(int(self._clientwidth/self._xscale), self._clientwidth)
		ythumbsize = min(int(self._clientheight/self._yscale), self._clientheight)
		if self._bitmap is None:
			xrange, yrange = 0, 0
		else:
			bitmapwidthscaled = self._bitmaprect.width*self._xscale
			bitmapheightscaled = self._bitmaprect.height*self._yscale
			xrange = min(bitmapwidthscaled, self._bitmaprect.width)
			yrange = min(bitmapheightscaled, self._bitmaprect.height)
		self.SetScrollbar(wx.HORIZONTAL, xposition, xthumbsize, xrange)
		self.SetScrollbar(wx.VERTICAL, yposition, ythumbsize, yrange)

	def _setBitmap(self, bitmap):
		OffsetWindow._setBitmap(self, bitmap)
		self.updateScrollbars()

	def _setScale(self, x, y):
		OffsetWindow._setScale(self, x, y)
		self.updateScrollbars()

	def _onSize(self, evt):
		OffsetWindow._onSize(self, evt)
		self.updateScrollbars()

if __name__ == '__main__':
	import sys
	from pyami import mrc

	def wxBitmapFromMRC(filename, min=None, max=None, color=False):
		n = mrc.read(filename)
		return wxBitmapFromNumarray(n, min, max, color)

	def onLeftUp(evt):
		eventobject = evt.GetEventObject()
		offset = eventobject.clientToBitmap(evt.GetX(), evt.GetY())
		wx.CallAfter(eventobject.centerOffset, *offset)

	def onRightUp(evt):
		pass

	def onMouseWheel(evt):
		eventobject = evt.GetEventObject()
		xscale, yscale = eventobject.getScale()
		scale = 2.0**(evt.GetWheelRotation()/evt.GetWheelDelta())
		wx.CallAfter(eventobject.setScale, xscale*scale, yscale*scale)

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
			#self.panel = OffsetWindow(frame, -1)
			self.panel = ScrolledWindow(frame, -1)

			self.panel.Bind(wx.EVT_LEFT_UP, onLeftUp)
			self.panel.Bind(wx.EVT_RIGHT_UP, onRightUp)
			self.panel.Bind(wx.EVT_MOUSEWHEEL, onMouseWheel)

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		import numpy
		n = numpy.zeros((2048, 2048))
		n[:1024, :1024] = numpy.ones((1024, 1024))
		n[1024:, 1024:] = numpy.ones((1024, 1024))
		app.panel.setBitmap(wxBitmapFromNumarray(n))
	else:
		app.panel.setBitmap(wxBitmapFromMRC(filename, color=True))
	app.MainLoop()

