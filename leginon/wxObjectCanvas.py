from wxPython.wx import *

def inside(x1, y1, w1, h1, x2, y2, w2=None, h2=None):
	if x2 < x1 or y2 < y1:
		return False

	tx = x2
	ty = y2

	if w2 is not None and h2 is not None:
		tx += w2
		ty += h2

	if tx > x1 + w1 or ty > y1 + h1:
		return False

	return True

class wxShapeObjectEvtHandler(wxEvtHandler):
	def __init__(self):
		wxEvtHandler.__init__(self)
		EVT_LEFT_DOWN(self, self.OnLeftDragStart)
		EVT_LEFT_UP(self, self.OnLeftClick)

	def OnLeftDragStart(self, evt):
		pass

	def OnLeftClick(self, evt):
		pass

class wxShapeObject(wxShapeObjectEvtHandler):
	def __init__(self, width=0, height=0):
		wxShapeObjectEvtHandler.__init__(self)
		self.text = []
		self.width = width
		self.height = height

	def Draw(self, dc, x, y):
		for text, tx, ty in self.text:
			dc.DrawText(text, x + tx, y + ty)

	def addText(self, text, x=0, y=0):
		self.text.append((text, x, y))

class wxRectangleObject(wxShapeObject):
	def __init__(self, width, height):
		wxShapeObject.__init__(self, width, height)

	def Draw(self, dc, x, y):
		dc.DrawRectangle(x, y, self.width, self.height)
		wxShapeObject.Draw(self, dc, x, y)

	def OnLeftClick(self, evt):
		print 'foo'

class wxObjectCanvas(wxScrolledWindow):
	def __init__(self, parent, id):
		self.shapeobjects = []

		wxScrolledWindow.__init__(self, parent, id)

		EVT_PAINT(self, self.OnPaint)
		EVT_SIZE(self, self.OnSize)
		EVT_LEFT_UP(self, self.OnLeftClick)
		EVT_MOTION(self, self.OnMotion)
		self.dragobject = None

		self.OnSize(None)

	def addShapeObject(self, so, x, y):
		if (so, x, y) not in self.shapeobjects:
			self.shapeobjects.append((so, x, y))

	def Draw(self, dc):
		dc.BeginDrawing()
		dc.SetBackground(wxWHITE_BRUSH)
		dc.Clear()
		for i in range(len(self.shapeobjects) - 1, -1, -1):
			so, x, y = self.shapeobjects[i]
			so.Draw(dc, x, y)
		dc.EndDrawing()

	def OnSize(self, evt):
		width, height = self.GetClientSizeTuple()
		self._buffer = wxEmptyBitmap(width, height)
		self.UpdateDrawing()

	def OnPaint(self, evt):
		dc = wxBufferedPaintDC(self, self._buffer)

	def UpdateDrawing(self):
		dc = wxBufferedDC(wxClientDC(self), self._buffer)
		self.Draw(dc)

	def getShapeObject(self, x, y):
		for so, sox, soy in self.shapeobjects:
			if inside(sox, soy, so.width, so.height, x, y):
				return (so, sox, soy)
		return None

	def OnLeftClick(self, evt):
		if self.dragobject is not None:
			self.OnLeftDragEnd(evt)
			return
		shapeobjectinfo = self.getShapeObject(evt.m_x, evt.m_y)
		if shapeobjectinfo is not None:
			shapeobjectinfo[0].AddPendingEvent(evt)
			# maybe need a value here
			return

	def OnLeftDragEnd(self, evt):
		if self.dragobject is not None:
			i = self.shapeobjects.index(self.dragobject[:3])
			self.shapeobjects[i] = (self.dragobject[0], evt.m_x + self.dragobject[3],
																									evt.m_y + self.dragobject[4])
			self.dragobject = None
			self.UpdateDrawing()

	def OnLeftDragStart(self, evt):
		dragobject = self.getShapeObject(evt.m_x, evt.m_y)
		if dragobject is not None:
			self.dragobject = dragobject + (dragobject[1] - evt.m_x,
																			dragobject[2] - evt.m_y)

	def OnMotion(self, evt):
		if evt.Dragging():
			if self.dragobject is None:
				self.OnLeftDragStart(evt)
		else:
			if self.dragobject is not None:
				self.OnLeftDragEnd(evt)

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Test')
			self.SetTopWindow(frame)
			self.canvas = wxObjectCanvas(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	ro1 = wxRectangleObject(100, 100)
	ro1.addText('Foo', 10, 10)
	app.canvas.addShapeObject(ro1, 100, 100)
	ro2 = wxRectangleObject(100, 100)
	ro2.addText('Bar', 10, 10)
	app.canvas.addShapeObject(ro2, 300, 100)
	ro3 = wxRectangleObject(100, 100)
	ro3.addText('Foo Bar', 10, 10)
	app.canvas.addShapeObject(ro3, 100, 300)
	app.MainLoop()

