from wxPython.wx import *
import math

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

class wxShapeObject(wxShapeObjectEvtHandler):
	def __init__(self, width, height):
		wxShapeObjectEvtHandler.__init__(self)
		self.width = width
		self.height = height
		self.parent = None

		self.text = {}

		self.shapeobjects = []
		self.positions = {}
		self.connections = []

	def getPosition(self):
		if self.parent is not None:
			return self.parent.getChildPosition(self)
		else:
			return (0, 0)

	def setPosition(self, x, y):
		if self.parent is not None:
			self.parent.setChildPosition(self, x, y)

	def getCanvasPosition(self):
		if self.parent is not None:
			return self.parent.getChildCanvasPosition(self)
		else:
			return (0, 0)

	def getChildPosition(self, so):
		if so in self.positions:
			return self.positions[so]
		else:
			raise ValueError('No position for shape object')

	def setChildPosition(self, so, x, y):
		self.positions[so] = (x, y)

	def getChildCanvasPosition(self, so):
		childx, childy = self.getChildPosition(so)
		x, y = self.getCanvasPosition()
		return (childx + x, childy + y)

	def getCanvasOffset(self):
		x, y = self.getPosition()
		cx, cy = self.getCanvasPosition()
		return (cx - x, cy - y)

	def setParent(self, parent):
		self.parent = parent

	def getParent(self):
		return self.parent

	def UpdateDrawing(self):
		self.ProcessEvent(UpdateDrawingEvent())

	#def addShapeObject(self, so, x=0, y=0):
	def addShapeObject(self, so, x, y):
		if so not in self.shapeobjects:
			so.setParent(self)
			self.shapeobjects.insert(0, so)
			self.positions[so] = (x, y)
			so.SetNextHandler(self)
			self.UpdateDrawing()

	def removeShapeObject(self, so):
		if so in self.shapeobjects:
			so.setParent(None)
			self.shapeobjects.remove(so)
			del self.positions[so]
			# delete handler?
			self.UpdateDrawing()

	def addConnection(self, connection):
		if connection not in self.connections:
			self.connections.append(connection)
			self.UpdateDrawing()

	def removeConnection(self, connection):
		if connection in self.connections:
			self.connections.remove(connection)
			self.UpdateDrawing()

	def getShapeObjectFromXY(self, x, y):
		for shapeobject in self.shapeobjects:
			ccx, ccy = self.getChildCanvasPosition(shapeobject)
			if inside(ccx, ccy, shapeobject.width, shapeobject.height, x, y):
				return shapeobject.getShapeObjectFromXY(x, y)
		return self

	def getContainingShapeObject(self, shapeobject):
		x, y = shapeobject.getCanvasPosition()
		w = shapeobject.width
		h = shapeobject.height
		for so in self.shapeobjects:
			ccx, ccy = self.getChildCanvasPosition(so)
			if inside(ccx, ccy, so.width, so.height, x, y, w, h):
				if so != shapeobject:
					return so.getContainingShapeObject(shapeobject)
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
		for text in self.text:
			x, y = self.getCanvasPosition()
			tx, ty = self.text[text]
			dc.DrawText(text, x + tx, y + ty)

		for i in range(len(self.shapeobjects) - 1, -1, -1):
			so = self.shapeobjects[i]
			so.Draw(dc)

		for i in range(len(self.connections) - 1, -1, -1):
			connection = self.connections[i]
			self.DrawConnection(dc, connection)

	def getCanvasCenter(self):
		x, y = self.getCanvasPosition()
		return (x + self.width/2, y + self.height/2)

	def DrawArrow(self, dc, p, direction, size=7):
		x, y = p
		if direction == 'n':
			dc.DrawPolygon([(0, 0), (-3, 7), (3, 7)], x, y)
		elif direction == 's':
			dc.DrawPolygon([(0, 0), (-3, -7), (3, -7)], x, y)
		elif direction == 'e':
			dc.DrawPolygon([(0, 0), (-7, -3), (-7, 3)], x, y)
		elif direction == 'w':
			dc.DrawPolygon([(0, 0), (7, -3), (7, 3)], x, y)

	def magnitude(self, p1, p2):
		return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

	def elbowLine(self, dc, so1, so2):
		x1, y1 = so1.getCanvasCenter()
		x2, y2 = so2.getCanvasCenter()
		n1 = (x1, y1 - so1.height/2)
		e1 = (x1 + so1.width/2, y1)
		s1 = (x1, y1 + so1.height/2)
		w1 = (x1 - so1.width/2, y1)
		n2 = (x2, y2 - so2.height/2)
		e2 = (x2 + so2.width/2, y2)
		s2 = (x2, y2 + so2.height/2)
		w2 = (x2 - so2.width/2, y2)

		if x1 > x2:
			# III and IV quadrants
			if y1 > y2:
				# IV quadrant
				if self.magnitude(n1, e2) < self.magnitude(w1, s2):
					p1, p2 = n1, e2
					reverse = False
					self.DrawArrow(dc, p2, 'w')
				else:
					p1, p2 = w1, s2
					reverse = True
					self.DrawArrow(dc, p2, 'n')
			else:
				# III quadrant
				if self.magnitude(s1, e2) < self.magnitude(w1, n2):
					p1, p2 = s1, e2
					reverse = False
					self.DrawArrow(dc, p2, 'w')
				else:
					p1, p2 = w1, n2
					reverse = True
					self.DrawArrow(dc, p2, 's')
		else:
			# I and II quadrants
			if y1 > y2:
				# I quadrant
				if self.magnitude(n1, w2) < self.magnitude(e1, s2):
					p1, p2 = n1, w2
					reverse = False
					self.DrawArrow(dc, p2, 'e')
				else:
					p1, p2 = e1, s2
					reverse = True
					self.DrawArrow(dc, p2, 'n')
			else:
				# II quadrant
				if self.magnitude(s1, w2) < self.magnitude(e1, n2):
					p1, p2 = s1, w2
					reverse = False
					self.DrawArrow(dc, p2, 'e')
				else:
					p1, p2 = e1, n2
					reverse = True
					self.DrawArrow(dc, p2, 's')
		x1, y1 = p1
		x2, y2 = p2
		if reverse:
			mx = x2
			my = y1
		else:
			mx = x1
			my = y2
		dc.DrawLine(x1, y1, mx, my)
		dc.DrawLine(mx, my, x2, y2)

	def DrawLine(self, dc, so1, so2):
		oldbrush = dc.GetBrush()
		dc.SetBrush(wxBLACK_BRUSH)
		self.elbowLine(dc, so1, so2)
		dc.SetBrush(oldbrush)

	def DrawConnection(self, dc, connection):
		self.DrawLine(dc, self, connection)

	def crookedLine(self, dc, shapeobject1, shapeobject2, offset=0):
		x1, y1 = shapeobject1.getCanvasPosition()
		x2, y2 = shapeobject2.getCanvasPosition()
		x1 += shapeobject1.width/2
		y1 += shapeobject1.height/2
		x2 += shapeobject2.width/2
		y2 += shapeobject2.height/2

		try:
			slope = float(y2 - y1)/float(x2 - x1)
		except ZeroDivisionError:
			# good enough
			slope = 1

		if slope >= -1 and slope < 1:
			if x1 > x2:
				y1 += offset
				y2 += offset
				x1 -= shapeobject1.width/2
				x2 += shapeobject2.width/2
				dc.DrawPolygon([(0, 0), (7, -3), (7, 3)], x2, y2)
				mx = x2 + (x1 - x2)/2 + offset
			else:
				y1 -= offset
				y2 -= offset
				x1 += shapeobject1.width/2
				x2 -= shapeobject2.width/2
				dc.DrawPolygon([(0, 0), (-7, -3), (-7, 3)], x2, y2)
				mx = x2 + (x1 - x2)/2 - offset
			dc.DrawLine(x1, y1, mx, y1)
			dc.DrawLine(mx, y1, mx, y2)
			dc.DrawLine(mx, y2, x2, y2)
		else:
			if y1 > y2:
				x1 += offset
				x2 += offset
				y1 -= shapeobject1.height/2
				y2 += shapeobject2.height/2
				dc.DrawPolygon([(0, 0), (-3, 7), (3, 7)], x2, y2)
				my = y2 + (y1 - y2)/2 + offset
			else:
				x1 -= offset
				x2 -= offset
				y1 += shapeobject1.height/2
				y2 -= shapeobject2.height/2
				dc.DrawPolygon([(0, 0), (-3, -7), (3, -7)], x2, y2)
				my = y2 + (y1 - y2)/2 - offset
			dc.DrawLine(x1, y1, x1, my)
			dc.DrawLine(x1, my, x2, my)
			dc.DrawLine(x2, my, x2, y2)
		
#		dc.DrawLine(x1, y1, x2, y2)
		dc.SetBrush(oldbrush)

	def addText(self, text, x=0, y=0):
		self.text[text] = (x, y)

	def OnLeftClick(self, evt):
		self.ProcessEvent(RaiseEvent(self, True))
		evt.Skip()

	def OnRightClick(self, evt):
		self.ProcessEvent(LowerEvent(self, False))
		evt.Skip()

	def OnLeftDragStart(self, evt):
		self.ProcessEvent(RaiseEvent(self, True))

	def OnRaise(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.raiseShapeObject(evt.shapeobject, evt.top)
			self.ProcessEvent(RaiseEvent(self, False))
		else:
			evt.Skip()

	def OnLower(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.lowerShapeObject(evt.shapeobject, evt.bottom)
		else:
			evt.Skip()

class wxRectangleObject(wxShapeObject):
	def __init__(self, width, height):
		wxShapeObject.__init__(self, width, height)

	def Draw(self, dc):
		x, y = self.getCanvasPosition()
		dc.DrawRectangle(x, y, self.width, self.height)
		wxShapeObject.Draw(self, dc)

class DragInfo(object):
	def __init__(self, shapeobject, xoffset, yoffset):
		self.shapeobject = shapeobject
		self.xoffset = xoffset
		self.yoffset = yoffset

	def setPosition(self, x, y):
		xoffset, yoffset = self.shapeobject.getCanvasOffset()
		x = x - xoffset - self.xoffset
		y = y - yoffset - self.yoffset
		self.shapeobject.setPosition(x, y)

class wxObjectCanvas(wxScrolledWindow):
	def __init__(self, parent, id, master):
		wxScrolledWindow.__init__(self, parent, id)

		self.master = master
		self.master.SetNextHandler(self)
		self.SetVirtualSize((self.master.width, self.master.height))

		self.draginfo = None

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

	def updateParent(self, shapeobject):
		cx, cy = shapeobject.getCanvasPosition()
		w = shapeobject.width
		h = shapeobject.height
		oldparent = shapeobject.getParent()
		newparent = self.master.getContainingShapeObject(shapeobject)
		if oldparent is not None and oldparent != newparent:
			oldparent.removeShapeObject(shapeobject)
			x, y = newparent.getCanvasPosition()
			newparent.addShapeObject(shapeobject, cx - x, cy - y)

	def OnLeftUp(self, evt):
		if self.draginfo is not None:
			self.draginfo.setPosition(evt.m_x, evt.m_y)
			self.updateParent(self.draginfo.shapeobject)
			self.draginfo.shapeobject.ProcessEvent(
									LeftDragEndEvent(self.draginfo.shapeobject, evt.m_x, evt.m_y))
			self.draginfo = None
			self.UpdateDrawing()
		else:
			shapeobject = self.master.getShapeObjectFromXY(evt.m_x, evt.m_y)
			shapeobject.ProcessEvent(LeftClickEvent(shapeobject, evt.m_x, evt.m_y))

	def OnRightUp(self, evt):
		shapeobject = self.master.getShapeObjectFromXY(evt.m_x, evt.m_y)
		shapeobject.ProcessEvent(RightClickEvent(shapeobject, evt.m_x, evt.m_y))

	def OnMotion(self, evt):
		if evt.LeftIsDown():
			if self.draginfo is None:
				shapeobject = self.master.getShapeObjectFromXY(evt.m_x, evt.m_y)
				xoffset, yoffset = shapeobject.getCanvasPosition()
				self.draginfo = DragInfo(shapeobject, evt.m_x - xoffset,
																							evt.m_y - yoffset)
				shapeobject.ProcessEvent(LeftDragStartEvent(shapeobject,
																										evt.m_x, evt.m_y))
			else:	
				self.draginfo.setPosition(evt.m_x, evt.m_y)
				self.UpdateDrawing()

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Test')
			self.SetTopWindow(frame)
			self.master = wxRectangleObject(600, 600)
			self.master.addText('master shape object', 10, 10)
			self.canvas = wxObjectCanvas(frame, -1, self.master)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)

	o1 = wxRectangleObject(400, 400)
	o1.addText('test child object', 10, 10)
	app.master.addShapeObject(o1, 25, 25)

	o2 = wxRectangleObject(200, 200)
	o2.addText('test child child 1 object', 10, 10)
	o1.addShapeObject(o2, 25, 25)

	o3 = wxRectangleObject(50, 50)
	o3.addText('test child child 2 object', 10, 10)
	o1.addShapeObject(o3, 250, 100)

	o2.addConnection(o3)
	o3.addConnection(o2)

	o4 = wxRectangleObject(50, 50)
	o4.addText('foo', 10, 10)
	o2.addShapeObject(o4, 30, 30)

	app.MainLoop()

