from wxPython.wx import *

wxEVT_LEFT_CLICK = wxNewEventType()
wxEVT_RIGHT_CLICK = wxNewEventType()
wxEVT_LEFT_DRAG_START = wxNewEventType()
wxEVT_LEFT_DRAG_END = wxNewEventType()
wxEVT_RIGHT_DRAG_START = wxNewEventType()
wxEVT_RIGHT_DRAG_END = wxNewEventType()
wxEVT_SELECT = wxNewEventType()
wxEVT_UNSELECT = wxNewEventType()

class LeftClickEvent(wxPyEvent):
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_CLICK)
		self.x = x
		self.y = y

class RightClickEvent(wxPyEvent):
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_CLICK)
		self.x = x
		self.y = y

class LeftDragStartEvent(wxPyEvent):
	def __init__(self, shapeobject, offsetx, offsety):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_DRAG_START)
		self.shapeobject = shapeobject
		self.offsetx = offsetx
		self.offsety = offsety

class LeftDragEndEvent(wxPyEvent):
	def __init__(self, shapeobject, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_DRAG_END)
		self.shapeobject = shapeobject
		self.x = x
		self.y = y

class RightDragStartEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_DRAG_START)

class RightDragEndEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_DRAG_END)

class SelectEvent(wxPyEvent):
	def __init__(self, shapeobject):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SELECT)
		self.shapeobject = shapeobject

class UnselectEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_UNSELECT)

def EVT_LEFT_CLICK(window, function):
	window.Connect(-1, -1, wxEVT_LEFT_CLICK, function)

def EVT_RIGHT_CLICK(window, function):
	window.Connect(-1, -1, wxEVT_RIGHT_CLICK, function)

def EVT_LEFT_DRAG_START(window, function):
	window.Connect(-1, -1, wxEVT_LEFT_DRAG_START, function)

def EVT_LEFT_DRAG_END(window, function):
	window.Connect(-1, -1, wxEVT_LEFT_DRAG_END, function)

def EVT_RIGHT_DRAG_START(window, function):
	window.Connect(-1, -1, wxEVT_RIGHT_DRAG_START, function)

def EVT_RIGHT_DRAG_END(window, function):
	window.Connect(-1, -1, wxEVT_RIGHT_DRAG_END, function)

def EVT_SELECT(window, function):
	window.Connect(-1, -1, wxEVT_SELECT, function)

def EVT_UNSELECT(window, function):
	window.Connect(-1, -1, wxEVT_UNSELECT, function)

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

		self.selected = False

		EVT_LEFT_CLICK(self, self.OnLeftClick)
		EVT_RIGHT_CLICK(self, self.OnRightClick)
		EVT_LEFT_DRAG_START(self, self.OnLeftDragStart)
		EVT_LEFT_DRAG_END(self, self.OnLeftDragEnd)
		EVT_RIGHT_DRAG_START(self, self.OnRightDragStart)
		EVT_RIGHT_DRAG_END(self, self.OnRightDragEnd)
		EVT_SELECT(self, self.OnSelect)
		EVT_UNSELECT(self, self.OnUnselect)

	def ProcessEvent(self, evt):
		wxEvtHandler.ProcessEvent(self, evt)
		if evt.GetSkipped():
			handler = self.GetNextHandler()
			if handler is not None:
				handler.ProcessEvent(evt)

	def OnLeftClick(self, evt):
		evt.Skip()

	def OnRightClick(self, evt):
		evt.Skip()

	def OnLeftDragStart(self, evt):
		evt.Skip()

	def OnLeftDragEnd(self, evt):
		evt.Skip()

	def OnRightDragStart(self, evt):
		evt.Skip()

	def OnRightDragEnd(self, evt):
		evt.Skip()

	def OnSelect(self, evt):
		self.selected = True
		evt.Skip()

	def OnUnselect(self, evt):
		self.selected = False
		evt.Skip()

class wxConnectionObject(object):
	def __init__(self, shapeobject1, shapeobject2):
		self.shapeobject1 = shapeobject1
		self.shapeobject2 = shapeobject2

	def Draw(self, dc):
		x1 = self.shapeobject1.x + self.shapeobject1.width/2
		y1 = self.shapeobject1.y + self.shapeobject1.height/2
		x2 = self.shapeobject2.x + self.shapeobject2.width/2
		y2 = self.shapeobject2.y + self.shapeobject2.height/2

		try:
			slope = float(y2 - y1)/float(x2 - x1)
		except ZeroDivisionError:
			# good enough
			slope = 1

		oldbrush = dc.GetBrush()
		dc.SetBrush(wxBLACK_BRUSH)
		if slope >= -1 and slope < 1:
			if x1 > x2:
				x1 = self.shapeobject1.x
				x2 = self.shapeobject2.x + self.shapeobject2.width - 1
				dc.DrawPolygon([(0, 0), (7, -3), (7, 3)], x2, y2)
			else:
				x1 = self.shapeobject1.x + self.shapeobject1.width
				x2 = self.shapeobject2.x
				dc.DrawPolygon([(0, 0), (-7, -3), (-7, 3)], x2, y2)
			mx = x2 + (x1 - x2)/2
			dc.DrawLine(x1, y1, mx, y1)
			dc.DrawLine(mx, y1, mx, y2)
			dc.DrawLine(mx, y2, x2, y2)
		else:
			if y1 > y2:
				y1 = self.shapeobject1.y
				y2 = self.shapeobject2.y + self.shapeobject2.height - 1
				dc.DrawPolygon([(0, 0), (-3, 7), (3, 7)], x2, y2)
			else:
				y1 = self.shapeobject1.y + self.shapeobject1.height
				y2 = self.shapeobject2.y
				dc.DrawPolygon([(0, 0), (-3, -7), (3, -7)], x2, y2)
			my = y2 + (y1 - y2)/2
			dc.DrawLine(x1, y1, x1, my)
			dc.DrawLine(x1, my, x2, my)
			dc.DrawLine(x2, my, x2, y2)
		
#		dc.DrawLine(x1, y1, x2, y2)
		dc.SetBrush(oldbrush)

class wxShapeObject(wxShapeObjectEvtHandler):
	def __init__(self, x=0, y=0, width=0, height=0):
		wxShapeObjectEvtHandler.__init__(self)
		self.text = []
		self.x = x
		self.y = y
		self.width = width
		self.height = height

	def Draw(self, dc):
		for text, tx, ty in self.text:
			dc.DrawText(text, self.x + tx, self.y + ty)
		if self.selected:
			self.DrawSelected(dc)

	def DrawSelected(self, dc):
		oldbrush = dc.GetBrush()
		oldpen = dc.GetPen()
		dc.SetBrush(wxBrush(wxWHITE, wxTRANSPARENT))
		dc.SetPen(wxPen(wxRED, 1, wxDOT))
		dc.DrawRectangle(self.x - 1, self.y - 1, self.width + 2, self.height + 2)
		dc.SetBrush(oldbrush)
		dc.SetPen(oldpen)

	def addText(self, text, x=0, y=0):
		self.text.append((text, x, y))

class wxRectangleObject(wxShapeObject):
	def __init__(self, x, y, width, height):
		wxShapeObject.__init__(self, x, y, width, height)

	def Draw(self, dc):
		dc.DrawRectangle(self.x, self.y, self.width, self.height)
		wxShapeObject.Draw(self, dc)

class wxObjectCanvas(wxScrolledWindow):
	def __init__(self, parent, id):
		self.shapeobjects = []
		self.connectionobjects = []

		wxScrolledWindow.__init__(self, parent, id)

		self.dragobject = None
		self.selected = None

		EVT_PAINT(self, self.OnPaint)
		EVT_SIZE(self, self.OnSize)
		EVT_LEFT_UP(self, self.OnLeftUp)
		EVT_RIGHT_UP(self, self.OnRightUp)
		EVT_MOTION(self, self.OnMotion)

		EVT_LEFT_CLICK(self, self.OnLeftClick)
		EVT_RIGHT_CLICK(self, self.OnRightClick)
		EVT_LEFT_DRAG_START(self, self.OnLeftDragStart)
		EVT_LEFT_DRAG_END(self, self.OnLeftDragEnd)
		EVT_RIGHT_DRAG_START(self, self.OnRightDragStart)
		EVT_RIGHT_DRAG_END(self, self.OnRightDragEnd)
		EVT_SELECT(self, self.OnSelect)
		EVT_UNSELECT(self, self.OnUnselect)

		self.OnSize(None)

	def addShapeObject(self, so):
		if so not in self.shapeobjects:
			self.shapeobjects.append(so)
			so.SetNextHandler(self)

	def addConnectionObject(self, co):
		if co not in self.connectionobjects:
			self.connectionobjects.append(co)

	def Draw(self, dc):
		dc.BeginDrawing()
		dc.SetBackground(wxWHITE_BRUSH)
		dc.Clear()
		for i in range(len(self.connectionobjects) - 1, -1, -1):
			co = self.connectionobjects[i]
			co.Draw(dc)
		for i in range(len(self.shapeobjects) - 1, -1, -1):
			so = self.shapeobjects[i]
			so.Draw(dc)
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

	def getShapeObjectFromXY(self, x, y):
		for so in self.shapeobjects:
			if inside(so.x, so.y, so.width, so.height, x, y):
				return so
		return None

	def orderShapeObject(self, index, shapeobject):
		so = self.shapeobjects.pop(self.shapeobjects.index(shapeobject))
		self.shapeobjects.insert(index, so)

	def selectShapeObject(self, shapeobject):
		shapeobject.ProcessEvent(SelectEvent(shapeobject))

	def unselectShapeObject(self):
		if self.selected is not None:
			self.selected.ProcessEvent(UnselectEvent())

	def OnLeftUp(self, evt):
		shapeobject = self.getShapeObjectFromXY(evt.m_x, evt.m_y)
		if self.dragobject is not None:
			self.dragobject[0].ProcessEvent(LeftDragEndEvent(self.dragobject[0],
																				evt.m_x + self.dragobject[1],
																				evt.m_y + self.dragobject[2]))
			self.dragobject = None
		elif shapeobject is not None:
			shapeobject.ProcessEvent(LeftClickEvent(evt.m_x, evt.m_y))

	def OnRightUp(self, evt):
		shapeobject = self.getShapeObjectFromXY(evt.m_x, evt.m_y)
		if shapeobject is not None:
			shapeobject.ProcessEvent(RightClickEvent(evt.m_x, evt.m_y))

	def OnMotion(self, evt):
		if self.dragobject is None and evt.LeftIsDown():
			shapeobject = self.getShapeObjectFromXY(evt.m_x, evt.m_y)
			if shapeobject is not None:
				offsetx = shapeobject.x - evt.m_x
				offsety = shapeobject.y - evt.m_y
				shapeobject.ProcessEvent(LeftDragStartEvent(shapeobject,
																										offsetx, offsety))

	def OnLeftClick(self, evt):
		shapeobject = self.getShapeObjectFromXY(evt.x, evt.y)
		if shapeobject is not None:
			self.selectShapeObject(shapeobject)

	def OnRightClick(self, evt):
		shapeobject = self.getShapeObjectFromXY(evt.x, evt.y)
		if shapeobject == self.selected:
			self.unselectShapeObject()

	def OnLeftDragStart(self, evt):
		self.dragobject = (evt.shapeobject, evt.offsetx, evt.offsety)

	def OnLeftDragEnd(self, evt):
		evt.shapeobject.x = evt.x
		evt.shapeobject.y = evt.y
		self.UpdateDrawing()

	def OnRightDragStart(self, evt):
		print 'wxObjectCanvas', evt.__class__

	def OnRightDragEnd(self, evt):
		print 'wxObjectCanvas', evt.__class__

	def OnSelect(self, evt):
		if self.selected != evt.shapeobject:
			self.unselectShapeObject()
		self.orderShapeObject(0, evt.shapeobject)
		self.selected = evt.shapeobject
		self.UpdateDrawing()

	def OnUnselect(self, evt):
		self.selected = None
		self.UpdateDrawing()

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
	ro1 = wxRectangleObject(100, 100, 100, 100)
	ro1.addText('Foo', 10, 10)
	app.canvas.addShapeObject(ro1)
	ro2 = wxRectangleObject(300, 100, 100, 100)
	ro2.addText('Bar', 10, 10)
	app.canvas.addShapeObject(ro2)
	ro3 = wxRectangleObject(100, 300, 100, 100)
	ro3.addText('Foo Bar', 10, 10)
	app.canvas.addShapeObject(ro3)
	app.canvas.addConnectionObject(wxConnectionObject(ro3, ro2))
	app.canvas.addConnectionObject(wxConnectionObject(ro1, ro2))
	app.canvas.addConnectionObject(wxConnectionObject(ro3, ro1))
	app.MainLoop()

