from wxPython.wx import *
import math

def magnitude(p1, p2):
	return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

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
	def __init__(self, so1, so2, text=''):
		self.fromso = so1
		self.toso = so2
		self.text = text

	def setText(self, text):
		self.text = text

	def DrawText(self, dc, x, y):
		if not self.text:
			return
		width, height = dc.GetTextExtent(self.text)
		x -= width/2
		y -= height/2
		oldpen = dc.GetPen()
		dc.SetPen(wxWHITE_PEN)
		dc.DrawRectangle(x, y, width, height)
		dc.SetPen(oldpen)
		dc.DrawText(self.text, x, y)

	def DrawArrow(self, dc, p, direction, size=7):
		oldbrush = dc.GetBrush()
		dc.SetBrush(wxBLACK_BRUSH)
		x, y = p
		if direction == 'n':
			dc.DrawPolygon([(0, 0), (-3, 7), (3, 7)], x, y)
		elif direction == 's':
			dc.DrawPolygon([(0, 0), (-3, -7), (3, -7)], x, y)
		elif direction == 'e':
			dc.DrawPolygon([(0, 0), (-7, -3), (-7, 3)], x, y)
		elif direction == 'w':
			dc.DrawPolygon([(0, 0), (7, -3), (7, 3)], x, y)
		dc.SetBrush(oldbrush)

	def straightLine(self, dc, so1, so2):
		x1, y1 = so1.getCanvasCenter()
		x2, y2 = so2.getCanvasCenter()
		n1, e1, s1, w1 = so1.getFaces()
		n2, e2, s2, w2 = so2.getFaces()

		direction = so1.direction(so2)
		if direction == 'n':
			if abs(x1 - x2) > so1.width + so2.width:
				return False
			p1, p2 = n1, s2
			x = (p2[0] - p1[0])/2 + p1[0]
			p1 = (x, p1[1])
			p2 = (x, p2[1])
			self.DrawArrow(dc, p2, 'n')
		elif direction == 'e':
			if abs(y1 - y2) > so1.height + so2.height:
				return False
			p1, p2 = e1, w2
			y = (p2[1] - p1[1])/2 + p1[1]
			p1 = (p1[0], y)
			p2 = (p2[0], y)
			self.DrawArrow(dc, p2, 'e')
		elif direction == 's':
			if abs(x1 - x2) > so1.width + so2.width:
				return False
			p1, p2 = s1, n2
			x = (p2[0] - p1[0])/2 + p1[0]
			p1 = (x, p1[1])
			p2 = (x, p2[1])
			self.DrawArrow(dc, p2, 's')
		elif direction == 'w':
			if abs(y1 - y2) > so1.height + so2.height:
				return False
			p1, p2 = w1, e2
			y = (p2[1] - p1[1])/2 + p1[1]
			p1 = (p1[0], y)
			p2 = (p2[0], y)
			self.DrawArrow(dc, p2, 'w')
		x1, y1 = p1
		x2, y2 = p2
		dc.DrawLine(x1, y1, x2, y2)

		tx = (x2 - x1)/2 + x1
		ty = (y2 - y1)/2 + y1
		self.DrawText(dc, tx, ty)

	def elbowLine(self, dc, so1, so2):
		arrowsize = 7
		x1, y1 = so1.getCanvasCenter()
		x2, y2 = so2.getCanvasCenter()

		penwidth = dc.GetPen().GetWidth()
		if so1.width > so2.width:
			width = so2.width
		else:
			width = so1.width
		if abs(x1 - x2) < width/2 + arrowsize + penwidth + 1:
			return False
		if so1.height > so2.height:
			height = so2.height
		else:
			height = so1.height
		if abs(y1 - y2) < height/2 + arrowsize + penwidth + 1:
			return False

		n1, e1, s1, w1 = so1.getFaces()
		n2, e2, s2, w2 = so2.getFaces()

		quadrant = so1.quadrant(so2)
		if quadrant == 1:
			if magnitude(n1, w2) < magnitude(e1, s2):
				p1, p2 = n1, w2
				reverse = False
				arrowdirection = 'e'
			else:
				p1, p2 = e1, s2
				reverse = True
				arrowdirection = 'n'
		elif quadrant == 2:
			if magnitude(s1, w2) < magnitude(e1, n2):
				p1, p2 = s1, w2
				reverse = False
				arrowdirection = 'e'
			else:
				p1, p2 = e1, n2
				reverse = True
				arrowdirection = 's'
		elif quadrant == 3:
			if magnitude(s1, e2) < magnitude(w1, n2):
				p1, p2 = s1, e2
				reverse = False
				arrowdirection = 'w'
			else:
				p1, p2 = w1, n2
				reverse = True
				arrowdirection = 's'
		elif quadrant == 4:
			if magnitude(n1, e2) < magnitude(w1, s2):
				p1, p2 = n1, e2
				reverse = False
				arrowdirection = 'w'
			else:
				p1, p2 = w1, s2
				reverse = True
				arrowdirection = 'n'
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
		self.DrawArrow(dc, p2, arrowdirection, arrowsize)

		if magnitude((x1, y1), (mx, my)) > magnitude((mx, my), (x2, y2)):
			tx1, ty1 = x1, y1
			tx2, ty2 = mx, my
		else:
			tx1, ty1 = mx, my
			tx2, ty2 = x2, y2
		tx = (tx2 - tx1)/2 + tx1
		ty = (ty2 - ty1)/2 + ty1
		self.DrawText(dc, tx, ty)

		return True

	def Draw(self, dc):
		if self.elbowLine(dc, self.fromso, self.toso):
			return
		if self.straightLine(dc, self.fromso, self.toso):
			return

class wxShapeObject(wxShapeObjectEvtHandler):
	def __init__(self, width, height):
		wxShapeObjectEvtHandler.__init__(self)
		self.width = width
		self.height = height
		self.parent = None

		self.text = {}

		self.shapeobjects = []
		self.positions = {}
		self.connectionobjects = []

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

	def addShapeObject(self, so, x=0, y=0):
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

	def addConnectionObject(self, connectionobject):
		if connectionobject not in self.connectionobjects:
			self.connectionobjects.append(connectionobject)
			self.UpdateDrawing()

	def removeConnectionObject(self, connectionobject):
		if connectionobject in self.connectionobjects:
			self.connectionobjects.remove(connectionobject)
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
			dc.DrawText(text, x + tx + 1, y + ty + 1)

		for i in range(len(self.shapeobjects) - 1, -1, -1):
			so = self.shapeobjects[i]
			so.Draw(dc)

		for i in range(len(self.connectionobjects) - 1, -1, -1):
			connectionobject = self.connectionobjects[i]
			connectionobject.Draw(dc)

	def getCanvasCenter(self):
		x, y = self.getCanvasPosition()
		return (x + self.width/2, y + self.height/2)

	def getFaces(self):
		x, y = self.getCanvasCenter()
		n = (x, y - self.height/2)
		e = (x + self.width/2, y)
		s = (x, y + self.height/2)
		w = (x - self.width/2, y)
		return (n, e, s, w)

	def direction(self, so):
		# \ n /
		#  \ /
		# w \ e
		#  / \
		# / s \
		x1, y1 = self.getCanvasCenter()
		x2, y2 = so.getCanvasCenter()

		try:
			slope = float(y2 - y1)/float(x2 - x1)
		except ZeroDivisionError:
			# good enough
			slope = 1.0

		if slope >= -1 and slope < 1:
			# east or west
			if x1 > x2:
				# west
				return 'w'
			else:
				# east
				return 'e'
		else:
			# north or south
			if y1 > y2:
				# north
				return 'n'
			else:
				# south
				return 's'

	def quadrant(self, so):
		#  IV | I
		# --------
		# III | II
		x1, y1 = self.getCanvasCenter()
		x2, y2 = so.getCanvasCenter()
		if x1 < x2:
			# I and II quadrants
			if y1 > y2:
				# I quadrant
				return 1
			else:
				# II quadrant
				return 2
		else:
			# III and IV quadrants
			if y1 < y2:
				# III quadrant
				return 3
			else:
				# IV quadrant
				return 4

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

	c1 = wxConnectionObject(o2, o3, 'Connection 1')
	c2 = wxConnectionObject(o3, o2)
	o1.addConnectionObject(c1)
	o1.addConnectionObject(c2)

	o4 = wxRectangleObject(50, 50)
	o4.addText('foo', 10, 10)
	o2.addShapeObject(o4, 30, 30)

	app.MainLoop()

