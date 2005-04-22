import wx
import numarrayimage

class	Panel(wx.Window):
	def __init__(self, parent, id):
		wx.Window.__init__(self, parent, id)

		self.updatedrawing = False

		width, height = self.GetClientSizeTuple() 
		self.clientwidth = width
		self.clientheight = height

		self.buffer = wx.EmptyBitmap(width, height)
		self.bufferwidth = width
		self.bufferheight = height

		self.sizetimer = wx.Timer(self)

		self.source = None
		self.sourcewidth = 0
		self.sourceheight = 0

		self.blitxdest = 0
		self.blitydest = 0
		self.blitwidth = 0
		self.blitheight = 0
		self.blitxsrc = 0
		self.blitysrc = 0

		self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_TIMER, self.onSizeTimer, self.sizetimer)
		self.Bind(wx.EVT_SIZE, self.onSize)

	def updateSourceGeometry(self):
		updated = False
		if self.source is None:
			sourcewidth = 0
			sourceheight = 0
		else:
			sourcewidth = self.source.shape[1]
			sourceheight = self.source.shape[0]
		if sourcewidth != self.sourcewidth:
			self.sourcewidth = sourcewidth
			updated = True
		if sourceheight != self.sourceheight:
			self.sourceheight = sourceheight
			updated = True
		updated = updated or self.updateBlitGeometry()
		return updated

	def updateClientGeometry(self):
		updated = False
		clientwidth, clientheight = self.GetClientSizeTuple() 
		if clientwidth != self.clientwidth:
			self.clientwidth = clientwidth
		if clientheight != self.clientheight:
			self.clientheight = clientheight
		updated = updated or self.updateBlitGeometry()
		return updated

	def updateBufferGeometry(self):
		updated = False
		bufferwidth = self.buffer.GetWidth()
		bufferheight = self.buffer.GetHeight()
		if bufferwidth != self.bufferwidth:
			self.bufferwidth = bufferwidth
			updated = True
		if bufferheight != self.bufferheight:
			self.bufferheight = bufferheight
			updated = True
		updated = updated or self.updateBlitGeometry()
		return updated

	def updateBlitGeometry(self):
		updated = False
		offsetx = int(round((self.clientwidth - self.sourcewidth)/2.0))
		offsety = int(round((self.clientheight - self.sourceheight)/2.0))
		blitxdest = max(0, offsetx)
		blitydest = max(0, offsety)
		if blitxdest != self.blitxdest:
			self.blitxdest = blitxdest
			updated = True
		if blitydest != self.blitydest:
			self.blitydest = blitydest
			updated = True
		blitwidth = min(self.bufferwidth, self.sourcewidth)
		blitheight = min(self.bufferheight, self.sourceheight)
		if blitwidth != self.blitwidth:
			self.blitwidth = blitwidth
			updated = True
		if blitheight != self.blitheight:
			self.blitheight = blitheight
			updated = True
		return updated

	def setNumarray(self, array):
		self.source = array
		self.updateSourceGeometry()
		self.updateDrawing()
		self.Refresh()

	def onEraseBackground(self, evt):
		pass

	def updateDrawing(self):
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)

		dc.Clear()

		if self.source is None:
			return

		if self.blitheight < 1 or self.blitwidth < 1:
			bitmap = wx.EmptyBitmap(self.blitwidth, self.blitheight)
		else:
			bitmap = numarrayimage.numarray2wxBitmap(
																self.source[:self.blitheight, :self.blitwidth])
		bitmapdc = wx.MemoryDC()
		bitmapdc.SelectObject(bitmap)

		dc.Blit(self.blitxdest, self.blitydest, self.blitwidth, self.blitheight,
						bitmapdc,
						0, 0)

		bitmapdc.SelectObject(wx.NullBitmap)

		dc.SelectObject(wx.NullBitmap)

	def onPaint(self, dc):
		if self.updatedrawing:
			self.updateDrawing()
			self.updatedrawing = False
		dc = wx.PaintDC(self) 
		memorydc = wx.MemoryDC()
		memorydc.SelectObject(self.buffer)
		regioniterator = wx.RegionIterator(self.GetUpdateRegion())
		while(regioniterator):
			rect = regioniterator.GetRect()
			dc.Blit(rect.x, rect.y, rect.width, rect.height, memorydc, rect.x, rect.y)
			regioniterator.Next()
		memorydc.SelectObject(wx.NullBitmap)

	def onSizeTimer(self, evt):
		width, height = self.GetClientSizeTuple() 
		self.buffer = wx.EmptyBitmap(width, height)
		self.updateClientGeometry()
		self.updateBufferGeometry()
		self.updatedrawing = True
		self.Refresh()

	def onSize(self, evt):
		width, height = self.GetClientSizeTuple() 
		self.buffer = wx.EmptyBitmap(width, height)

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.Clear()
		dc.SelectObject(wx.NullBitmap)

		self.updateBufferGeometry()
		self.updateClientGeometry()
		self.sizetimer.Start(100, True)
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

