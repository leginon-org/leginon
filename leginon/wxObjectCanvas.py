from wxPython.wx import *

wxEVT_UPDATE_DRAWING = wxNewEventType()

wxEVT_LEFT_CLICK = wxNewEventType()
wxEVT_RIGHT_CLICK = wxNewEventType()
wxEVT_LEFT_DRAG_START = wxNewEventType()
wxEVT_LEFT_DRAG_END = wxNewEventType()
wxEVT_RIGHT_DRAG_START = wxNewEventType()
wxEVT_RIGHT_DRAG_END = wxNewEventType()
wxEVT_RAISE = wxNewEventType()
wxEVT_LOWER = wxNewEventType()

class UpdateDrawingEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_UPDATE_DRAWING)

class LeftClickEvent(wxPyEvent):
	def __init__(self, shapeobject, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_CLICK)
		self.shapeobject = shapeobject
		self.x = x
		self.y = y

class RightClickEvent(wxPyEvent):
	def __init__(self, shapeobject, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_CLICK)
		self.shapeobject = shapeobject
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

class RaiseEvent(wxPyEvent):
	def __init__(self, shapeobject, top=False):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RAISE)
		self.shapeobject = shapeobject
		self.top = top

class LowerEvent(wxPyEvent):
	def __init__(self, shapeobject, bottom=False):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LOWER)
		self.shapeobject = shapeobject
		self.bottom = bottom

def EVT_UPDATE_DRAWING(window, function):
	window.Connect(-1, -1, wxEVT_UPDATE_DRAWING, function)

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

def EVT_RAISE(window, function):
	window.Connect(-1, -1, wxEVT_RAISE, function)

def EVT_LOWER(window, function):
	window.Connect(-1, -1, wxEVT_LOWER, function)

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

		EVT_UPDATE_DRAWING(self, self.OnUpdateDrawing)
		EVT_LEFT_CLICK(self, self.OnLeftClick)
		EVT_RIGHT_CLICK(self, self.OnRightClick)
		EVT_LEFT_DRAG_START(self, self.OnLeftDragStart)
		EVT_LEFT_DRAG_END(self, self.OnLeftDragEnd)
		EVT_RIGHT_DRAG_START(self, self.OnRightDragStart)
		EVT_RIGHT_DRAG_END(self, self.OnRightDragEnd)
		EVT_RAISE(self, self.OnRaise)
		EVT_LOWER(self, self.OnLower)

	def ProcessEvent(self, evt):
		wxEvtHandler.ProcessEvent(self, evt)
		if evt.GetSkipped():
			handler = self.GetNextHandler()
			if handler is not None:
				handler.ProcessEvent(evt)

	def OnUpdateDrawing(self, evt):
		evt.Skip()

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

	def OnRaise(self, evt):
		evt.Skip()

	def OnLower(self, evt):
		evt.Skip()

class wxConnectionObject(object):
	def __init__(self, shapeobject1, shapeobject2):
		self.shapeobject1 = shapeobject1
		self.shapeobject2 = shapeobject2
		self.forward = True
		self.backward = True

	def same(self, other):
		if (self.shapeobject1 == other.shapeobject1 and
				self.shapeobject2 == other.shapeobject2):
			return True
		if (self.shapeobject2 == other.shapeobject1 and
				self.shapeobject1 == other.shapeobject2):
			return True
		return False

	def connects(self, shapeobject):
		if shapeobject == self.shapeobject1 or shapeobject == self.shapeobject2:
			return True
		return False

	def Draw(self, dc):
		if self.forward and self.backward:
			self.DrawLine(dc, 3)
			self.DrawLine(dc, -3, True)
		elif self.forward:
			self.DrawLine(dc, 0)
		elif self.backward:
			self.DrawLine(dc, 0, True)

	def getCenters(self):
		so1 = self.shapeobject1
		so2 = self.shapeobject2
		x1 = so1.x + so1.xoffset + so1.width/2
		y1 = so1.y + so1.yoffset + so1.height/2
		x2 = so2.x + so2.xoffset + so2.width/2
		y2 = so2.y + so2.yoffset + so2.height/2
		return (x1, y1, x2, y2)

	def DrawLine(self, dc, offset=0, reverse=False):
		x1, y1, x2, y2 = self.getCenters()

		try:
			slope = float(y2 - y1)/float(x2 - x1)
		except ZeroDivisionError:
			# good enough
			slope = 1

		oldbrush = dc.GetBrush()
		dc.SetBrush(wxBLACK_BRUSH)
		if slope >= -1 and slope < 1:
			y1 += offset
			y2 += offset
			if x1 > x2:
				x1 = self.shapeobject1.x
				x2 = self.shapeobject2.x + self.shapeobject2.width - 1
				if reverse:
					dc.DrawPolygon([(0, 0), (-7, -3), (-7, 3)], x1, y1)
				else:
					dc.DrawPolygon([(0, 0), (7, -3), (7, 3)], x2, y2)
			else:
				x1 = self.shapeobject1.x + self.shapeobject1.width
				x2 = self.shapeobject2.x
				if reverse:
					dc.DrawPolygon([(0, 0), (7, -3), (7, 3)], x1, y1)
				else:
					dc.DrawPolygon([(0, 0), (-7, -3), (-7, 3)], x2, y2)
			mx = x2 + (x1 - x2)/2 + offset
			dc.DrawLine(x1, y1, mx, y1)
			dc.DrawLine(mx, y1, mx, y2)
			dc.DrawLine(mx, y2, x2, y2)
		else:
			x1 += offset
			x2 += offset
			if y1 > y2:
				y1 = self.shapeobject1.y
				y2 = self.shapeobject2.y + self.shapeobject2.height - 1
				if reverse:
					dc.DrawPolygon([(0, 0), (-3, -7), (3, -7)], x1, y1)
				else:
					dc.DrawPolygon([(0, 0), (-3, 7), (3, 7)], x2, y2)
			else:
				y1 = self.shapeobject1.y + self.shapeobject1.height
				y2 = self.shapeobject2.y
				if reverse:
					dc.DrawPolygon([(0, 0), (-3, 7), (3, 7)], x1, y1)
				else:
					dc.DrawPolygon([(0, 0), (-3, -7), (3, -7)], x2, y2)
			my = y2 + (y1 - y2)/2 + offset
			dc.DrawLine(x1, y1, x1, my)
			dc.DrawLine(x1, my, x2, my)
			dc.DrawLine(x2, my, x2, y2)
		
#		dc.DrawLine(x1, y1, x2, y2)
		dc.SetBrush(oldbrush)

class wxShapeObject(wxShapeObjectEvtHandler):
	def __init__(self, x, y, width, height):
		wxShapeObjectEvtHandler.__init__(self)
		self.x = x
		self.y = y
		self.width = width
		self.height = height

		self.xoffset = 0
		self.yoffset = 0
		self.text = []

		self.shapeobjects = []
		self.connectionobjects = []

	def setOffset(self, x, y):
		self.xoffset = x
		self.yoffset = y

	def UpdateDrawing(self):
		self.ProcessEvent(UpdateDrawingEvent())

	def addShapeObject(self, so):
		if so not in self.shapeobjects:
			self.shapeobjects.append(so)
			so.SetNextHandler(self)
			so.setOffset(self.x + self.xoffset, self.y + self.yoffset)
			self.UpdateDrawing()

	def removeShapeObject(self, so):
		if so in self.shapeobjects:
			self.shapeobjects.remove(so)
			# delete handler?
		remove = []
		for co in self.connectionobjects:
			if co.connects(so):
				remove.append(co)
		for i in remove:
			self.removeConnectionObject(i)
		self.UpdateDrawing()

	def addConnectionObject(self, co):
		for i in self.connectionobjects:
			if co.same(i):
				return
		self.connectionobjects.append(co)
		self.UpdateDrawing()

	def removeConnectionObject(self, co):
		if co in self.connectionobjects:
			self.connectionobjects.remove(co)
			self.UpdateDrawing()

	def getShapeObjectFromXY(self, x, y, w=None, h=None):
		for shapeobject in self.shapeobjects:
			if inside(shapeobject.x + shapeobject.xoffset,
								shapeobject.y + shapeobject.yoffset,
								shapeobject.width, shapeobject.height,
								x, y, w, h):
				return shapeobject.getShapeObjectFromXY(x, y, w, h)
		return self

	def raiseShapeObject(self, shapeobject, top=False):
		index = self.shapeobjects.index(shapeobject)
		if index > 0:
			del self.shapeobjects[index]
			if top:
				self.shapeobjects.insert(0, shapeobject)
			else:
				self.shapeobjects.insert(index - 1, shapeobject)
			self.UpdateDrawing()

	def lowerShapeObject(self, shapeobject, bottom=False):
		index = self.shapeobjects.index(shapeobject)
		if index < len(self.shapeobjects) - 1:
			del self.shapeobjects[index]
			if bottom:
				self.shapeobjects.append(shapeobject)
			else:
				self.shapeobjects.insert(index + 1, shapeobject)
			self.UpdateDrawing()

	def Draw(self, dc):
		for text, tx, ty in self.text:
			dc.DrawText(text, self.x + self.xoffset + tx, self.y + self.yoffset + ty)

		for i in range(len(self.connectionobjects) - 1, -1, -1):
			co = self.connectionobjects[i]
			co.Draw(dc)
		for i in range(len(self.shapeobjects) - 1, -1, -1):
			so = self.shapeobjects[i]
			so.Draw(dc)

	def addText(self, text, x=0, y=0):
		self.text.append((text, x, y))

	def OnLeftClick(self, evt):
		self.ProcessEvent(RaiseEvent(self, True))
		evt.Skip()

	def OnRightClick(self, evt):
		self.ProcessEvent(LowerEvent(self, False))
		evt.Skip()

	def OnRaise(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.raiseShapeObject(evt.shapeobject, evt.top)
		else:
			evt.Skip()

	def OnLower(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.lowerShapeObject(evt.shapeobject, evt.bottom)
		else:
			evt.Skip()

class wxRectangleObject(wxShapeObject):
	def __init__(self, x, y, width, height):
		wxShapeObject.__init__(self, x, y, width, height)

	def Draw(self, dc):
		dc.DrawRectangle(self.x + self.xoffset, self.y + self.yoffset,
											self.width, self.height)
		wxShapeObject.Draw(self, dc)

class wxObjectCanvas(wxScrolledWindow):
	def __init__(self, parent, id, master):
		wxScrolledWindow.__init__(self, parent, id)

		self.master = master
		self.master.SetNextHandler(self)
		self.SetVirtualSize((self.master.width, self.master.height))

		EVT_PAINT(self, self.OnPaint)
		EVT_SIZE(self, self.OnSize)
		EVT_LEFT_UP(self, self.OnLeftUp)
		EVT_RIGHT_UP(self, self.OnRightUp)
		EVT_MOTION(self, self.OnMotion)

		EVT_UPDATE_DRAWING(self, self.OnUpdateDrawing)

		self.OnSize(None)

	def Draw(self, dc):
		dc.BeginDrawing()
		dc.SetBackground(wxWHITE_BRUSH)
		dc.Clear()
		self.master.Draw(dc)
		dc.EndDrawing()

	def UpdateDrawing(self):
		dc = wxBufferedDC(wxClientDC(self), self._buffer)
		self.Draw(dc)

	def OnSize(self, evt):
		width, height = self.GetClientSizeTuple()
		self._buffer = wxEmptyBitmap(width, height)
		self.UpdateDrawing()

	def OnPaint(self, evt):
		dc = wxBufferedPaintDC(self, self._buffer)

	def OnUpdateDrawing(self, evt):
		self.UpdateDrawing()

	def OnLeftUp(self, evt):
		shapeobject = self.master.getShapeObjectFromXY(evt.m_x, evt.m_y)
		shapeobject.ProcessEvent(LeftClickEvent(shapeobject, evt.m_x, evt.m_y))

	def OnRightUp(self, evt):
		shapeobject = self.master.getShapeObjectFromXY(evt.m_x, evt.m_y)
		shapeobject.ProcessEvent(RightClickEvent(shapeobject, evt.m_x, evt.m_y))

	def OnMotion(self, evt):
		pass

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Test')
			self.SetTopWindow(frame)
			self.master = wxRectangleObject(0, 0, 600, 600)
			self.master.addText('master shape object', 10, 10)
			self.canvas = wxObjectCanvas(frame, -1, self.master)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)

	o1 = wxRectangleObject(25, 25, 400, 400)
	o1.addText('test child object', 10, 10)
	app.master.addShapeObject(o1)

	o2 = wxRectangleObject(25, 25, 200, 200)
	o2.addText('test child child 1 object', 10, 10)
	o1.addShapeObject(o2)

	o3 = wxRectangleObject(50, 50, 200, 200)
	o3.addText('test child child 2 object', 10, 10)
	o1.addShapeObject(o3)

	app.MainLoop()

