# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from wxPython.wx import *
#wxInitAllImageHandlers()

class Grid(object):
	def __init__(self, parent, position, number, callback):
		self.number = number
		self.callback = callback
		bitmap = wxImage('grid.png', wxBITMAP_TYPE_PNG).ConvertToBitmap()
		bitmapsize = (bitmap.GetWidth(), bitmap.GetHeight())
		bitmapoffset = (bitmapsize[0]/2, bitmapsize[1]/2)

		bitmapposition = (position[0] - bitmapoffset[0],
											position[1] - bitmapoffset[1])
		self.bitmap = wxStaticBitmap(parent, -1, bitmap, bitmapposition, bitmapsize)

		labelposition = (position[0] - 14, position[1] - 16)
		self.label = wxStaticText(parent, -1, str(self.number),
																		labelposition)
		font = self.label.GetFont()
		font.SetPointSize(6)
		self.label.SetFont(font)
		self.label.SetBackgroundColour(wxWHITE)

		EVT_LEFT_UP(self.bitmap, self.onLeftUp)

	def makeBitmap(self):
		mask = wxEmptyBitmap(11, 11)
		dc = wxMemoryDC()
		dc.SelectObject(mask)
		dc.SetPen(wxWHITE_PEN)
		dc.DrawEllipse(0, 0, 11, 11)
		dc.SelectObject(wxNullBitmap)

		bitmap = wxEmptyBitmap(11, 11)
		bitmap.SetMask(wxMaskColour(mask, wxBLACK))
		return bitmap

	def onLeftUp(self, evt):
		self.callback(self.number)

	def setOrder(self, order):
		order.sort()
		label = ''
		if order:
			label += '[' + str(order[0])
			if len(order) > 1:
				label += ',...'
			label += ']'
		self.label.SetLabel(str(self.number) + ' ' + label)

class GridTrayPanel(wxPanel):
	def __init__(self, parent, callback=None):
		wxPanel.__init__(self, parent, -1)
		self.callback = callback

		gridtraybitmap = wxImage('robotgridtray.png',
												wxBITMAP_TYPE_PNG).ConvertToBitmap()
		self.gridtraybitmap = wxStaticBitmap(self, -1, gridtraybitmap,
									size=(gridtraybitmap.GetWidth(), gridtraybitmap.GetHeight()))

		self.delta = (-31, 31)
		self.offset = (416, 63)
		self.ngrids = (12, 8)

		self.queue = []
		self.grids = []
		for i in range(self.ngrids[0]):
			for j in range(self.ngrids[1]):
				position = (self.offset[0] + i*self.delta[0],
										self.offset[1] + j*self.delta[1])
				number = i*self.ngrids[1] + j + 1
				self.grids.append(Grid(self.gridtraybitmap, position, number,
																self.gridCallback))

	def gridCallback(self, number):
		if callable(self.callback):
			self.callback(self.queue + [number])

	def set(self, queue):
		self.queue = queue
		mapping = {}

		for grid in self.grids:
			grid.setOrder([])

		for i, gridnumber in enumerate(queue):
			try:
				mapping[gridnumber - 1].append(i + 1)
			except KeyError:
				mapping[gridnumber - 1] = [i + 1]

		for gridnumber, order in mapping.items():
			self.grids[gridnumber].setOrder(order)

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Grid Tray')
			self.SetTopWindow(frame)
			self.panel = GridTrayPanel(frame)
			self.panel.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.panel.set([1,4,5,53,32,87,7,5,2,2,4,53,5,6,7,8])
	app.MainLoop()

