import wx
import numarrayimage
import numextension

class	Panel(wx.Window):
	def __init__(self, parent, id):
		wx.Window.__init__(self, parent, id)

		clientwidth, clientheight = self.GetClientSizeTuple()
		self.buffer = wx.EmptyBitmap(clientwidth, clientheight)

		self.bitmapregion = None

		self.source = None
		self.extrema = None

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_SIZE, self.onSize)

	def setNumarray(self, array):
		self.source = array
		if self.source is None:
			self.extrema = None
		else:
			self.extrema = numextension.minmax(self.source)

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.Clear()

		if self.source is None:
			dc.SelectObject(wx.NullBitmap)
			self.Refresh()
			return

		bufferwidth = self.buffer.GetWidth()
		bufferheight = self.buffer.GetHeight()
		bufferregion = wx.Region(0, 0, bufferwidth, bufferheight)

		bitmapwidth, bitmapheight = self.source.shape[1], self.source.shape[0]
		bitmapx = max(0, int(round((bufferwidth - bitmapwidth)/2.0)))
		bitmapy = max(0, int(round((bufferheight - bitmapheight)/2.0)))
		bitmapregion = wx.Region(bitmapx, bitmapy, bitmapwidth, bitmapheight)

		sourceregion = wx.Region(*bitmapregion.GetBox())
		sourceregion.IntersectRegion(bufferregion)

		regioniterator = wx.RegionIterator(sourceregion)
		while(regioniterator):
			r = regioniterator.GetRect()
			x = r.x - bitmapx
			y = r.y - bitmapy
			array = self.source[y:y + r.height, x:x + r.width]
			bitmap = numarrayimage.numarray2wxBitmap(array, self.extrema)
			sourcedc = wx.MemoryDC()
			sourcedc.SelectObject(bitmap)
			dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
			sourcedc.SelectObject(wx.NullBitmap)
			regioniterator.Next()

		self.bitmapregion = sourceregion

		dc.SelectObject(wx.NullBitmap)

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
		clientwidth, clientheight = evt.GetSize()
		clientregion = wx.Region(0, 0, clientwidth, clientheight)
		if clientregion.IsEmpty():
			self.buffer = wx.EmptyBitmap(0, 0)
			return
		buffer = wx.EmptyBitmap(clientwidth, clientheight)

		if self.source is None:
			self.buffer = buffer
			return

		bufferwidth = self.buffer.GetWidth()
		bufferheight = self.buffer.GetHeight()
		bufferregion = wx.Region(0, 0, bufferwidth, bufferheight)

		if clientregion == bufferregion:
			return

		bitmapwidth, bitmapheight = self.source.shape[1], self.source.shape[0]
		bitmapx = max(0, int(round((clientwidth - bitmapwidth)/2.0)))
		bitmapy = max(0, int(round((clientheight - bitmapheight)/2.0)))
		bitmapregion = wx.Region(bitmapx, bitmapy, bitmapwidth, bitmapheight)

		copyregion = wx.Region(*self.bitmapregion.GetBox())
		x1, y1, width1, height1 = self.bitmapregion.GetBox()
		x2, y2, width2, height2 = bitmapregion.GetBox()
		xoffset = x2 - x1
		yoffset = y2 - y1
		copyregion.Offset(xoffset, yoffset)
		copyregion.IntersectRegion(clientregion)

		dc = wx.MemoryDC()
		dc.SelectObject(buffer)
		dc.Clear()

		regioniterator = wx.RegionIterator(copyregion)
		copydc = wx.MemoryDC()
		copydc.SelectObject(self.buffer)
		while(regioniterator):
			r = regioniterator.GetRect()
			dc.Blit(r.x, r.y, r.width, r.height, copydc, r.x - xoffset, r.y - yoffset)
			regioniterator.Next()
		copydc.SelectObject(wx.NullBitmap)

		sourceregion = wx.Region(*bitmapregion.GetBox())
		sourceregion.IntersectRegion(clientregion)
		sourceregion.SubtractRegion(copyregion)

		regioniterator = wx.RegionIterator(sourceregion)
		while(regioniterator):
			r = regioniterator.GetRect()
			x = r.x - bitmapx
			y = r.y - bitmapy
			array = self.source[y:y + r.height, x:x + r.width]
			bitmap = numarrayimage.numarray2wxBitmap(array, self.extrema)
			sourcedc = wx.MemoryDC()
			sourcedc.SelectObject(bitmap)
			dc.Blit(r.x, r.y, r.width, r.height, sourcedc, 0, 0)
			sourcedc.SelectObject(wx.NullBitmap)
			regioniterator.Next()

		dc.SelectObject(wx.NullBitmap)

		self.buffer = buffer

		self.bitmapregion = copyregion
		self.bitmapregion.UnionRegion(sourceregion)

		if xoffset != 0 or yoffset != 0:
			self.Refresh()

		evt.Skip()

if __name__ == '__main__':
	import sys
	import Mrc

	filename = sys.argv[1]

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			self.panel = Panel(frame, -1)

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.SetSize((750, 750))
			frame.Show(True)
			return True

	app = MyApp(0)

	array = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
	app.panel.setNumarray(array)
	app.MainLoop()

