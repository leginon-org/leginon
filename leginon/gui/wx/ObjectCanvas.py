# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ObjectCanvas.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
from wxPython.wx import *
import math

def magnitude(p1, p2):
	return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

wxEVT_UPDATE_DRAWING = wxNewEventType()

wxEVT_LEFT_CLICK = wxNewEventType()
wxEVT_RIGHT_CLICK = wxNewEventType()
wxEVT_LEFT_DRAG_START = wxNewEventType()
wxEVT_LEFT_DRAG_END = wxNewEventType()
wxEVT_LEFT_DRAG = wxNewEventType()
wxEVT_RIGHT_DRAG_START = wxNewEventType()
wxEVT_RIGHT_DRAG_END = wxNewEventType()
wxEVT_RIGHT_DRAG = wxNewEventType()
wxEVT_RAISE = wxNewEventType()
wxEVT_LOWER = wxNewEventType()
wxEVT_ENTER = wxNewEventType()
wxEVT_LEAVE = wxNewEventType()
wxEVT_SET_CURSOR = wxNewEventType()
wxEVT_START_CONNECTION = wxNewEventType()
wxEVT_END_CONNECTION = wxNewEventType()
wxEVT_CANCEL_CONNECTION = wxNewEventType()
wxEVT_MOVE_CONNECTION = wxNewEventType()
wxEVT_POPUP_MENU = wxNewEventType()

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
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_DRAG_START)
		self.x = x
		self.y = y

class LeftDragEndEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_DRAG_END)

class LeftDragEvent(wxPyEvent):
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEFT_DRAG)
		self.x = x
		self.y = y

class RightDragStartEvent(wxPyEvent):
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_DRAG_START)
		self.x = x
		self.y = y

class RightDragEndEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_DRAG_END)

class RightDragEvent(wxPyEvent):
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_RIGHT_DRAG)
		self.x = x
		self.y = y

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

class EnterEvent(wxPyEvent):
	def __init__(self, fromshapeobject, toshapeobject):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ENTER)
		self.fromshapeobject = fromshapeobject
		self.toshapeobject = toshapeobject

class LeaveEvent(wxPyEvent):
	def __init__(self, fromshapeobject, toshapeobject):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_LEAVE)
		self.fromshapeobject = fromshapeobject
		self.toshapeobject = toshapeobject

class SetCursorEvent(wxPyEvent):
	def __init__(self, cursor):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SET_CURSOR)
		self.cursor = cursor

class StartConnectionEvent(wxPyEvent):
	def __init__(self, connection):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_START_CONNECTION)
		self.connection = connection

class EndConnectionEvent(wxPyEvent):
	def __init__(self, toso):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_END_CONNECTION)
		self.toso = toso

class CancelConnectionEvent(wxPyEvent):
	def __init__(self):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_CANCEL_CONNECTION)

class MoveConnectionEvent(wxPyEvent):
	def __init__(self, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_MOVE_CONNECTION)
		self.x = x
		self.y = y

class PopupMenuEvent(wxPyEvent):
	def __init__(self, shapeobject, x, y):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_POPUP_MENU)
		self.shapeobject = shapeobject
		self.x = x
		self.y = y

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

def EVT_LEFT_DRAG(window, function):
	window.Connect(-1, -1, wxEVT_LEFT_DRAG, function)

def EVT_RIGHT_DRAG_START(window, function):
	window.Connect(-1, -1, wxEVT_RIGHT_DRAG_START, function)

def EVT_RIGHT_DRAG_END(window, function):
	window.Connect(-1, -1, wxEVT_RIGHT_DRAG_END, function)

def EVT_RIGHT_DRAG(window, function):
	window.Connect(-1, -1, wxEVT_RIGHT_DRAG, function)

def EVT_RAISE(window, function):
	window.Connect(-1, -1, wxEVT_RAISE, function)

def EVT_LOWER(window, function):
	window.Connect(-1, -1, wxEVT_LOWER, function)

def EVT_ENTER(window, function):
	window.Connect(-1, -1, wxEVT_ENTER, function)

def EVT_LEAVE(window, function):
	window.Connect(-1, -1, wxEVT_LEAVE, function)

def EVT_SET_CURSOR(window, function):
	window.Connect(-1, -1, wxEVT_SET_CURSOR, function)

def EVT_START_CONNECTION(window, function):
	window.Connect(-1, -1, wxEVT_START_CONNECTION, function)

def EVT_END_CONNECTION(window, function):
	window.Connect(-1, -1, wxEVT_END_CONNECTION, function)

def EVT_CANCEL_CONNECTION(window, function):
	window.Connect(-1, -1, wxEVT_CANCEL_CONNECTION, function)

def EVT_MOVE_CONNECTION(window, function):
	window.Connect(-1, -1, wxEVT_MOVE_CONNECTION, function)

def EVT_POPUP_MENU(window, function):
	window.Connect(-1, -1, wxEVT_POPUP_MENU, function)

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
		EVT_LEFT_DRAG(self, self.OnLeftDrag)
		EVT_RIGHT_DRAG_START(self, self.OnRightDragStart)
		EVT_RIGHT_DRAG_END(self, self.OnRightDragEnd)
		EVT_RIGHT_DRAG(self, self.OnRightDrag)
		EVT_RAISE(self, self.OnRaise)
		EVT_LOWER(self, self.OnLower)
		EVT_MOTION(self, self.OnMotion)
		EVT_ENTER(self, self.OnEnter)
		EVT_LEAVE(self, self.OnLeave)
		EVT_SET_CURSOR(self, self.OnSetCursor)
		EVT_START_CONNECTION(self, self.OnStartConnection)
		EVT_END_CONNECTION(self, self.OnEndConnection)
		EVT_CANCEL_CONNECTION(self, self.OnCancelConnection)
		EVT_MOVE_CONNECTION(self, self.OnMoveConnection)
		EVT_POPUP_MENU(self, self.OnPopupMenu)

		self.updatedrawing = True

	def setUpdateDrawing(self, updatedrawing):
		self.updatedrawing = updatedrawing

	def ProcessEvent(self, evt):
		wxEvtHandler.ProcessEvent(self, evt)
		if evt.GetSkipped():
			handler = self.GetNextHandler()
			if handler is not None:
				handler.ProcessEvent(evt)

	def OnUpdateDrawing(self, evt):
		if self.updatedrawing:
			evt.Skip()

	def OnLeftClick(self, evt):
		evt.Skip()

	def OnRightClick(self, evt):
		evt.Skip()

	def OnLeftDragStart(self, evt):
		evt.Skip()

	def OnLeftDragEnd(self, evt):
		evt.Skip()

	def OnLeftEnd(self, evt):
		evt.Skip()

	def OnRightDragStart(self, evt):
		evt.Skip()

	def OnRightDragEnd(self, evt):
		evt.Skip()

	def OnRightDrag(self, evt):
		evt.Skip()

	def OnRaise(self, evt):
		evt.Skip()

	def OnLower(self, evt):
		evt.Skip()

	def OnMotion(self, evt):
		evt.Skip()

	def OnEnter(self, evt):
		evt.Skip()

	def OnLeave(self, evt):
		evt.Skip()

	def OnSetCursor(self, evt):
		evt.Skip()

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

	def OnMoveConnection(self, evt):
		evt.Skip()

	def OnPopupMenu(self, evt):
		evt.Skip()

class wxShapeObject(wxShapeObjectEvtHandler):
	def __init__(self, width, height, color=wxBLACK, style=wxSOLID):
		wxShapeObjectEvtHandler.__init__(self)
		self.width = width
		self.height = height
		self.color = color
		self.style = style
		self.parent = None

		#self.text = {}

		self.shapeobjects = []
		self.positions = {}

		self.inputconnectionpoints = []
		self.outputconnectionpoints = []

		self.connection = None

		self.popupmenu = wxMenu()
		self.popupmenu.Append(201, 'Raise')
		self.popupmenu.Append(202, 'Lower')
		EVT_MENU(self.popupmenu, 201, self.OnMenuRaise)
		EVT_MENU(self.popupmenu, 202, self.OnMenuLower)

	def getPosition(self):
		if self.parent is not None:
			return self.parent.getChildPosition(self)
		else:
			return (0, 0)

	def setPosition(self, x, y):
		if self.parent is not None:
			self.parent.setChildPosition(self, x, y)

	def getSize(self):
		return self.width, self.height

	def setSize(self, width=None, height=None):
		if width is None or width < 0:
			setwidth = False
		else:
			setwidth = True
		if height is None or height < 0:
			setheight = False
		else:
			setheight = True

		if not setwidth and not setheight:
			return

		for so in self.shapeobjects:
			if not isinstance(so, wxConnectionPointObject):
				x, y = self.getChildPosition(so)
				w, h = so.getSize()
				if setwidth and x is not None and w is not None and x + w > width:
					setwidth = False
				if setheight and y is not None and h is not None and y + h > height:
					setheight = False

		if setwidth:
			self.width = width
		if setheight:
			self.height = height

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

	def delete(self):
		for so in self.shapeobjects:
			so.delete()
		if self.parent is not None:
			self.parent.removeShapeObject(self)

	def UpdateDrawing(self):
		self.ProcessEvent(UpdateDrawingEvent())

	def SetCursor(self, cursor):
		self.ProcessEvent(SetCursorEvent(cursor))

	def addShapeObject(self, so, x=0, y=0, draw=True):
		if so not in self.shapeobjects:
			parent = so.getParent()
			if parent is not None:
				parent.removeShapeObject(so)
			so.setParent(self)
			self.shapeobjects.insert(0, so)
			self.positions[so] = (x, y)
			so.SetNextHandler(self)
			if draw:
				self.UpdateDrawing()

	def removeShapeObject(self, so, draw=True):
		if so in self.shapeobjects:
			so.setParent(None)
			self.shapeobjects.remove(so)
			del self.positions[so]
			# delete handler?
			if draw:
				self.UpdateDrawing()

	def addInputConnectionPoint(self, cpo):
		if cpo not in self.inputconnectionpoints:
			self.inputconnectionpoints.append(cpo)
			self.addShapeObject(cpo)

	def removeInputConnectionPoint(self, cpo):
		if cpo in self.inputconnectionpoints:
			self.inputconnectionpoints.remove(cpo)
			self.removeShapeObject(cpo)

	def addOutputConnectionPoint(self, cpo):
		if cpo not in self.outputconnectionpoints:
			self.outputconnectionpoints.append(cpo)
			self.addShapeObject(cpo)

	def removeOutputConnectionPoint(self, cpo):
		if cpo in self.connectoutputs:
			self.outputconnectionpoints.remove(cpo)
			self.removeShapeObject(cpo)

	def removeConnections(self):
		removeconnectionpoints = []
		for so in self.shapeobjects:
			if isinstance(so, wxConnectionPointObject):
				removeconnectionpoints.append(so)

		for cpo in removeconnectionpoints:
			if cpo in self.inputconnectionpoints:
				self.inputconnectionpoints.remove(cpo)
			if cpo in self.outputconnectionpoints:
				self.outputconnectionpoints.remove(cpo)
			cpo.removeConnections()
			cpo.delete()

	def getShapeObjectFromXY(self, x, y, width=None, height=None):
		for shapeobject in self.shapeobjects:
			xyobject = shapeobject.getShapeObjectFromXY(x, y, width, height)
			if xyobject is not None:
				return xyobject

		cpx, cpy = self.getCanvasPosition()
		if inside(cpx, cpy, self.width, self.height, x, y, width, height):
			return self
		else:
			return None

	def getContainingShapeObject(self, shapeobject=None):
		if shapeobject is None:
			if self.parent is None:
				return None
			else:
				return self.parent.getContainingShapeObject(self)

		containing = self.getContainingChild(shapeobject)
		if containing is not None:
			return containing
		else:
			if self.parent is None:
				return None
			else:
				return self.parent.getContainingShapeObject(shapeobject)

	def getContainingChild(self, shapeobject):
		if shapeobject == self:
			return None

		for child in self.shapeobjects:
			childobject = child.getContainingChild(shapeobject)
			if childobject is not None:
				return childobject

		x, y = shapeobject.getCanvasPosition()
		width = shapeobject.width
		height = shapeobject.height

		cpx, cpy = self.getCanvasPosition()
		if inside(cpx, cpy, self.width, self.height, x, y, width, height):
			return self
		else:
			return None

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

#	def DrawText(self, dc):
#		dc.SetFont(wxSWISS_FONT)
#		for text in self.text:
#			x, y = self.getCanvasPosition()
#			tx, ty = self.text[text]
#			dc.DrawText(text, x + tx + 1, y + ty + 1)

	def Draw(self, dc):
		pen = dc.GetPen()
		dc.SetPen(wxPen(self.color, 1, self.style))

		#self.DrawText(dc)

		for i in range(len(self.shapeobjects) - 1, -1, -1):
			so = self.shapeobjects[i]
			if isinstance(so, wxConnectionObject):
				if so.getTempTo() is not None:
					so.Draw(dc)
			else:
				so.Draw(dc)

		dc.SetPen(pen)

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
		x, y = so.getCanvasCenter()
		return self._direction(x, y)

	def _direction(self, x2, y2):
		# \ n /
		#  \ /
		# w \ e
		#  / \
		# / s \
		x1, y1 = self.getCanvasCenter()

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

#	def addText(self, text, x=0, y=0):
#		self.text[text] = (x, y)
#
#	def removeText(self, text):
#		del self.text[text]

	def setCursor(self, evtx, evty):
		thresh = 5
		x, y = self.getCanvasPosition()
		x = evtx - x
		y = evty - y
		if inside(0, 0, thresh, thresh, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENWSE))
		elif inside(self.width - thresh, 0, thresh, thresh, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENESW))
		elif inside(self.width - thresh, self.height - thresh,
								thresh, thresh, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENWSE))
		elif inside(0, self.height - thresh, thresh, thresh, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENESW))
		elif inside(0, 0, self.width, thresh, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENS))
		elif inside(self.width - thresh, 0, thresh, self.height, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZEWE))
		elif inside(0, self.height - thresh, self.width, thresh, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENS))
		elif inside(0, 0, thresh, self.height, x, y):
			self.SetCursor(wxStockCursor(wxCURSOR_SIZEWE))
		else:
			self.SetCursor(wxSTANDARD_CURSOR)

	def setDragInfo(self, evtx, evty):
		self.draginfo = {}
		self.draginfo['start'] = self.getPosition()
		self.draginfo['last'] = (evtx, evty)
		thresh = 5
		x, y = self.getCanvasPosition()
		x = evtx - x
		y = evty - y
		w, h = self.getSize()
		if inside(0, 0, thresh, thresh, x, y):
			self.draginfo['type'] = 'nw'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENWSE))
		elif inside(w - thresh, 0, thresh, thresh, x, y):
			self.draginfo['type'] = 'ne'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENESW))
		elif inside(w - thresh, h - thresh,
								thresh, thresh, x, y):
			self.draginfo['type'] = 'se'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENWSE))
		elif inside(0, h - thresh, thresh, thresh, x, y):
			self.draginfo['type'] = 'sw'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENESW))
		elif inside(0, 0, w, thresh, x, y):
			self.draginfo['type'] = 'n'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENS))
		elif inside(w - thresh, 0, thresh, h, x, y):
			self.draginfo['type'] = 'e'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZEWE))
		elif inside(0, h - thresh, w, thresh, x, y):
			self.draginfo['type'] = 's'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZENS))
		elif inside(0, 0, thresh, h, x, y):
			self.draginfo['type'] = 'w'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZEWE))
		else:
			self.draginfo['type'] = 'move'
			self.SetCursor(wxStockCursor(wxCURSOR_SIZING))

	def OnLeftDrag(self, evt):
		evtx, evty = evt.x, evt.y
		px, py = self.getPosition()
		lastx, lasty = self.draginfo['last']
		self.draginfo['last'] = (evtx, evty)

		w, h = self.getSize()
		dt = self.draginfo['type']
		if dt == 'move':
			self.setPosition(evtx - lastx + px, evty - lasty + py)
		else:
			self.style = wxDOT
			if dt == 'nw':
				self.setPosition(px + (evtx - lastx), py + (evty - lasty))
				self.setSize(w - evtx + lastx, h - evty + lasty)
			elif dt == 'ne':
				self.setPosition(px, py + (evty - lasty))
				self.setSize(w + evtx - lastx, h - evty + lasty)
			elif dt == 'se':
				self.setSize(w + evtx - lastx, h + evty - lasty)
			elif dt == 'sw':
				self.setPosition(px + (evtx - lastx), py)
				self.setSize(w - evtx + lastx, h + evty - lasty)
			elif dt == 'n':
				self.setPosition(px, py + (evty - lasty))
				self.setSize(None, h - evty + lasty)
			elif dt == 'e':
				self.setSize(w + evtx - lastx, None)
			elif dt == 's':
				self.setSize(None, h + evty - lasty)
			elif dt == 'w':
				self.setPosition(px + (evtx - lastx), py)
				self.setSize(w - evtx + lastx, None)
		self.UpdateDrawing()

	def OnLeftDragStart(self, evt):
		self.ProcessEvent(RaiseEvent(self, True))
		self.setDragInfo(evt.x, evt.y)

	def OnLeftDragEnd(self, evt):
		containingobject = self.getContainingShapeObject()
		if containingobject is None:
			x, y = self.draginfo['start']
			self.setPosition(x, y)
		elif containingobject != self.parent:
			try:
				x, y = self.getCanvasPosition()
				cox, coy = containingobject.getCanvasPosition()
				containingobject.addShapeObject(self, x - cox, y - coy)
			except TypeError:
				x, y = self.draginfo['start']
				self.setPosition(x, y)
		self.SetCursor(wxSTANDARD_CURSOR)
		self.style = wxSOLID
		self.draginfo = None
		self.UpdateDrawing()

	def OnMotion(self, evt):
		if evt.LeftIsDown():
			if self.draginfo is None:
				self.ProcessEvent(LeftDragStartEvent(evt.GetX(), evt.GetY()))
			else:
				self.ProcessEvent(LeftDragEvent(evt.GetX(), evt.GetY()))
		else:
			if self.draginfo is None:
				self.setCursor(evt.GetX(), evt.GetY())
			else:
				self.ProcessEvent(LeftDragEndEvent())
		self.ProcessEvent(MoveConnectionEvent(evt.GetX(), evt.GetY()))

	def OnLeave(self, evt):
		self.SetCursor(wxSTANDARD_CURSOR)
		if self.draginfo is not None:
			self.draginfo = None

	def OnLeftClick(self, evt):
		if self.draginfo is not None:
			self.ProcessEvent(LeftDragEndEvent())

	def OnRightClick(self, evt):
		if self.connection is not None:
			self.cancelConnection()
		elif self.popupmenu is not None:
			self.ProcessEvent(PopupMenuEvent(self, evt.x, evt.y))

	def OnRaise(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.raiseShapeObject(evt.shapeobject, evt.top)
			self.ProcessEvent(RaiseEvent(self, True))
		evt.Skip()

	def OnLower(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.lowerShapeObject(evt.shapeobject, evt.bottom)
		evt.Skip()

	def OnMenuRaise(self, evt):
		self.ProcessEvent(RaiseEvent(self, True))

	def OnMenuLower(self, evt):
		self.ProcessEvent(LowerEvent(self, False))

	def OnStartConnection(self, evt):
		self.connection = evt.connection
		#self.addConnectionObject(self.connection)
		self.addShapeObject(self.connection)

	def OnEndConnection(self, evt):
		if self.connection is not None:
			self.connection.setToShapeObject(evt.toso)
			self.connection = None
			self.UpdateDrawing()

	def OnCancelConnection(self, evt):
		self.cancelConnection()

	def OnMoveConnection(self, evt):
		if self.connection is not None:
			self.connection.setTempTo((evt.x, evt.y))
			self.UpdateDrawing()
		evt.Skip()

	def cancelConnection(self):
		if self.connection is not None:
			#self.removeConnectionObject(self.connection)
			self.removeShapeObject(self.connection)
			self.connection = None
			self.UpdateDrawing()

class wxConnectionObject(wxShapeObject):
	def __init__(self, so1, so2, color=wxBLACK, style=wxSOLID):
		wxShapeObject.__init__(self, None, None, color, style)
		self.parent = None
		self.fromso = None
		self.toso = None
		self.tempto = None
		self.setFromShapeObject(so1)
		self.setToShapeObject(so2)
		self.color = color
		self.style = style
		self.drawn = False

	def delete(self):
		self.setFromShapeObject(None)
		self.setToShapeObject(None)
		wxShapeObject.delete(self)

	def OnLower(self, evt):
		if evt.shapeobject in self.shapeobjects:
			self.lowerShapeObject(evt.shapeobject, evt.bottom)
		evt.Skip()

	def getShapeObjectFromXY(self, x, y, width=None, height=None):
		for shapeobject in self.shapeobjects:
			xyobject = shapeobject.getShapeObjectFromXY(x, y, width, height)
			if xyobject is not None:
				return xyobject
		return None

	def getContainingShapeObject(self, shapeobject=None):
		if shapeobject is None:
			if self.parent is None:
				return None
			else:
				return self.parent.getContainingShapeObject(self)

		containing = self.getContainingChild(shapeobject)
		if containing is not None:
			return containing
		else:
			if self.parent is None:
				return None
			else:
				return self.parent.getContainingShapeObject(shapeobject)

	def getContainingChild(self, shapeobject):
		if shapeobject == self:
			return None

		for child in self.shapeobjects:
			childobject = child.getContainingChild(shapeobject)
			if childobject is not None:
				return childobject

		x, y = shapeobject.getCanvasPosition()
		width = shapeobject.width
		height = shapeobject.height

		return None

	def getFromShapeObject(self):
		return self.fromso

	def setFromShapeObject(self, so):
		if self.fromso is not None:
			self.fromso.removeConnectionOutput(self)
		self.fromso = so
		if self.fromso is not None:
			self.fromso.addConnectionOutput(self)

	def getToShapeObject(self):
		return self.toso

	def setToShapeObject(self, so):
		if self.tempto is not None:
			self.tempto = None
		if self.toso is not None:
			self.toso.removeConnectionInput(self)
		self.toso = so
		if self.toso is not None:
			self.toso.addConnectionInput(self)

	def getTempTo(self):
		return self.tempto

	def setTempTo(self, position):
		self.tempto = position

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

	def crookedLine(self, dc, so1, so2):
		x1, y1 = so1.getCanvasCenter()
		x2, y2 = so2.getCanvasCenter()
		n1, e1, s1, w1 = so1.getFaces()
		n2, e2, s2, w2 = so2.getFaces()

		direction = so1.direction(so2)
		if direction == 'n':
			x1, y1 = n1
			x2, y2 = s2
			my = (y1 - y2)/2 + y2
			l1 = (x1, y1, x1, my)
			l2 = (x1, my, x2, my)
			l3 = (x2, my, x2, y2)
			tx = (x2 - x1)/2 + x1
			ty = my
			angle = 180
			self.DrawArrow(dc, (x2, y2), 'n')
		elif direction == 'e':
			x1, y1 = e1
			x2, y2 = w2
			mx = (x2 - x1)/2 + x1
			l1 = (x1, y1, mx, y1)
			l2 = (mx, y1, mx, y2)
			l3 = (mx, y2, x2, y2)
			tx = mx
			ty = (y2 - y1)/2 + y1
			angle = 90
			self.DrawArrow(dc, (x2, y2), 'e')
		elif direction == 's':
			x1, y1 = s1
			x2, y2 = n2
			my = (y2 - y1)/2 + y1
			l1 = (x1, y1, x1, my)
			l2 = (x1, my, x2, my)
			l3 = (x2, my, x2, y2)
			tx = (x2 - x1)/2 + x1
			ty = my
			angle = 0
			self.DrawArrow(dc, (x2, y2), 's')
		elif direction == 'w':
			x1, y1 = w1
			x2, y2 = e2
			mx = (x1 - x2)/2 + x2
			l1 = (x1, y1, mx, y1)
			l2 = (mx, y1, mx, y2)
			l3 = (mx, y2, x2, y2)
			tx = mx
			ty = (y2 - y1)/2 + y1
			angle = -90
			self.DrawArrow(dc, (x2, y2), 'w')
		apply(dc.DrawLine, l1)
		apply(dc.DrawLine, l2)
		apply(dc.DrawLine, l3)
		return x1, y1, x2, y2

	def _crookedLine(self, dc, so1, x2, y2):
		x1, y1 = so1.getCanvasCenter()
		n1, e1, s1, w1 = so1.getFaces()
		direction = so1._direction(x2, y2)
		if direction == 'n':
			x1, y1 = n1
			my = (y1 - y2)/2 + y2
			l1 = (x1, y1, x1, my)
			l2 = (x1, my, x2, my)
			l3 = (x2, my, x2, y2)
			tx = (x2 - x1)/2 + x1
			ty = my
			angle = 180
			self.DrawArrow(dc, (x2, y2), 'n')
		elif direction == 'e':
			x1, y1 = e1
			mx = (x2 - x1)/2 + x1
			l1 = (x1, y1, mx, y1)
			l2 = (mx, y1, mx, y2)
			l3 = (mx, y2, x2, y2)
			tx = mx
			ty = (y2 - y1)/2 + y1
			angle = 90
			self.DrawArrow(dc, (x2, y2), 'e')
		elif direction == 's':
			x1, y1 = s1
			my = (y2 - y1)/2 + y1
			l1 = (x1, y1, x1, my)
			l2 = (x1, my, x2, my)
			l3 = (x2, my, x2, y2)
			tx = (x2 - x1)/2 + x1
			ty = my
			angle = 0
			self.DrawArrow(dc, (x2, y2), 's')
		elif direction == 'w':
			x1, y1 = w1
			mx = (x1 - x2)/2 + x2
			l1 = (x1, y1, mx, y1)
			l2 = (mx, y1, mx, y2)
			l3 = (mx, y2, x2, y2)
			tx = mx
			ty = (y2 - y1)/2 + y1
			angle = -90
			self.DrawArrow(dc, (x2, y2), 'w')
		apply(dc.DrawLine, l1)
		apply(dc.DrawLine, l2)
		apply(dc.DrawLine, l3)
		return x1, y1

	def Draw(self, dc):
		pen = dc.GetPen()
		dc.SetPen(wxPen(self.color, 1, self.style))
		if self.fromso is not None:
			if self.tempto is not None:
				x, y = self.tempto
				self._crookedLine(dc, self.fromso, x, y)
			elif self.toso is not None:
				self.crookedLine(dc, self.fromso, self.toso)
		dc.SetPen(pen)
		wxShapeObject.Draw(self, dc)

class wxTextObject(wxShapeObject):
	def __init__(self, text, color=wxBLACK):
		self.text = text
		width = -1
		height = -1
		wxShapeObject.__init__(self, width, height, color)
		self.draginfo = None

	def Draw(self, dc):
		dc.SetFont(wxSWISS_FONT)
		self.width, self.height = dc.GetTextExtent(self.text)
		pen = dc.GetPen()
		dc.SetPen(wxPen(self.color, 1, self.style))
		x, y = self.getCanvasPosition()
		dc.DrawText(self.text, x, y)
		dc.SetPen(pen)
		wxShapeObject.Draw(self, dc)

class wxRectangleObject(wxShapeObject):
	def __init__(self, width, height, color=wxBLACK):
		wxShapeObject.__init__(self, width, height, color)

		self.draginfo = None

	def Draw(self, dc):
		pen = dc.GetPen()
		dc.SetPen(wxPen(self.color, 1, self.style))
		x, y = self.getCanvasPosition()
		dc.DrawRectangle(x, y, self.width, self.height)
		dc.SetPen(pen)
		wxShapeObject.Draw(self, dc)

	def setSize(self, width=None, height=None):
		wxShapeObject.setSize(self, width, height)
		self.positionConnectionInputs()
		self.positionConnectionOutputs()

	def addInputConnectionPoint(self, cpo):
		wxShapeObject.addInputConnectionPoint(self, cpo)
		self.positionConnectionInputs()

	def removeInputConnectionPoint(self, cpo):
		wxShapeObject.removeInputConnectionPoint(self, cpo)
		self.positionConnectionInputs()

	def addOutputConnectionPoint(self, cpo):
		wxShapeObject.addOutputConnectionPoint(self, cpo)
		self.positionConnectionOutputs()

	def removeOutputConnectionPoint(self, cpo):
		wxShapeObject.removeOutputConnectionPoint(self, cpo)
		self.positionConnectionOutputs()

	def positionConnectionInputs(self):
		# need to account for running out of room
		nconnectionpoints = len(self.inputconnectionpoints)
		#spacings = range(0, self.width, self.width/(nconnectionpoints + 1))
		spacings = range(0, self.height, self.height/(nconnectionpoints + 1))
		for i in range(nconnectionpoints):
			ci = self.inputconnectionpoints[i]
			#self.setChildPosition(ci, spacings[i + 1] - ci.width/2, -ci.height/2)
			self.setChildPosition(ci, -ci.width/2, spacings[i + 1] - ci.height/2)

	def positionConnectionOutputs(self):
		# need to account for running out of room
		nconnectionpoints = len(self.outputconnectionpoints)
		#spacings = range(0, self.width, self.width/(nconnectionpoints + 1))
		spacings = range(0, self.height, self.height/(nconnectionpoints + 1))
		for i in range(nconnectionpoints):
			co = self.outputconnectionpoints[i]
			#self.setChildPosition(co, spacings[i + 1] - co.width/2,
			#											-co.height/2 + self.height - 1)
			self.setChildPosition(co,
														-co.width/2 + self.width - 1,
														spacings[i + 1] - co.height/2)

	def arrangeShapeObjects(self, shapeobjects, resize=True):
		buffer = 25
		maxwidth = buffer*2
		y = buffer
		n = int(math.ceil(math.sqrt(len(shapeobjects))))
		while shapeobjects:
			x = buffer
			maxheight = 0
			for i in range(n):
				try:
					so = shapeobjects[0]
				except IndexError:
					break
				del shapeobjects[0]
				so.setPosition(x, y)
				width, height = so.getSize()
				x += width + buffer
				if height > maxheight:
					maxheight = height
			if x > maxwidth:
				maxwidth = x
			y += maxheight + buffer
		size = (maxwidth, y)
		if resize:
			apply(self.setSize, size)
		self.UpdateDrawing()
		return size

class wxRoundedRectangleObject(wxRectangleObject):
	def __init__(self, width, height, color=wxBLACK):
		wxRectangleObject.__init__(self, width, height, color)

		self.edgeradius = 5

	def Draw(self, dc):
		pen = dc.GetPen()
		dc.SetPen(wxPen(self.color, 1, self.style))
		x, y = self.getCanvasPosition()
		dc.DrawRoundedRectangle(x, y, self.width, self.height, self.edgeradius)
		dc.SetPen(pen)
		wxShapeObject.Draw(self, dc)

class wxConnectionPointObject(wxRectangleObject):
	def __init__(self, color=wxBLACK):
		wxRectangleObject.__init__(self, 7, 7, color)
		self.connectioninputs = []
		self.connectionoutputs = []

	def addConnectionInput(self, connection):
		if connection not in self.connectioninputs:
			self.connectioninputs.append(connection)
		else:
			raise ValueError('Connection already exists')

	def removeConnectionInput(self, connection):
		try:
			self.connectioninputs.remove(connection)
		except ValueError:
			raise ValueError('No such connection to remove')

	def addConnectionOutput(self, connection):
		if connection not in self.connectionoutputs:
			self.connectionoutputs.append(connection)
		else:
			raise ValueError('Connection already exists')

	def removeConnectionOutput(self, connection):
		try:
			self.connectionoutputs.remove(connection)
		except ValueError:
			raise ValueError('No such connection to remove')

	def removeConnections(self):
		wxRectangleObject.removeConnections(self)
		for connection in self.connectioninputs + self.connectionoutputs:
			connection.delete()

	def OnMotion(self, evt):
		self.ProcessEvent(MoveConnectionEvent(evt.GetX(), evt.GetY()))

	def OnLeftClick(self, evt):
		self.ProcessEvent(EndConnectionEvent(self))

	def Draw(self, dc):
		wxRectangleObject.Draw(self, dc)
		for connection in self.connectioninputs:
			if not connection.drawn:
				fromso = connection.getFromShapeObject()
				if fromso is not None:
					connection.Draw(dc)
					connection.drawn = True
			else:
				connection.drawn = False
		for connection in self.connectionoutputs:
			toso = connection.getToShapeObject()
			if not connection.drawn:
				if toso is not None:
					connection.Draw(dc)
					connection.drawn = True
			else:
				connection.drawn = False

class wxObjectCanvas(wxScrolledWindow):
	def __init__(self, parent, id, master):
		wxScrolledWindow.__init__(self, parent, id)

		self.master = master
		self.master.SetNextHandler(self)
		self.SetSize((self.master.width, self.master.height))
		self.SetScrollRate(1, 1)

		self.draginfo = None
		self.lastshapeobject = None

		EVT_PAINT(self, self.OnPaint)
		EVT_SIZE(self, self.OnSize)
		EVT_LEFT_UP(self, self.OnLeftUp)
		EVT_RIGHT_UP(self, self.OnRightUp)
		EVT_MOTION(self, self.OnMotion)

		EVT_UPDATE_DRAWING(self, self.OnUpdateDrawing)
		EVT_SET_CURSOR(self, self.OnSetCursor)
		EVT_POPUP_MENU(self, self.OnPopupMenu)

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
		self.master.setSize(width, height)
		self._buffer = wxEmptyBitmap(width, height)
		self.UpdateDrawing()

	def OnPaint(self, evt):
		dc = wxBufferedPaintDC(self, self._buffer)

	def OnUpdateDrawing(self, evt):
		self.UpdateDrawing()

	def OnSetCursor(self, evt):
		self.SetCursor(evt.cursor)

	def OnLeftUp(self, evt):
		shapeobject = self.master.getShapeObjectFromXY(evt.GetX(), evt.GetY())
		if shapeobject is not None:
			shapeobject.ProcessEvent(LeftClickEvent(shapeobject, evt.GetX(), evt.GetY()))

	def OnRightUp(self, evt):
		shapeobject = self.master.getShapeObjectFromXY(evt.GetX(), evt.GetY())
		if shapeobject is not None:
			shapeobject.ProcessEvent(RightClickEvent(shapeobject, evt.GetX(), evt.GetY()))

	def OnMotion(self, evt):
		if self.lastshapeobject is None or self.lastshapeobject.draginfo is None:
			shapeobject = self.master.getShapeObjectFromXY(evt.GetX(), evt.GetY())
			if shapeobject != self.lastshapeobject:
				if self.lastshapeobject is not None:
					self.lastshapeobject.ProcessEvent(LeaveEvent(self.lastshapeobject, shapeobject))
				if shapeobject is not None:
					shapeobject.ProcessEvent(EnterEvent(self.lastshapeobject, shapeobject))
			self.lastshapeobject = shapeobject

		if self.lastshapeobject is not None:
			self.lastshapeobject.ProcessEvent(evt)

		#self.UpdateDrawing()

	def OnPopupMenu(self, evt):
		self.PopupMenu(evt.shapeobject.popupmenu, (evt.x, evt.y))

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
#	o1.addConnectionObject(c1)
#	o1.addConnectionObject(c2)

	o4 = wxRectangleObject(50, 50)
	o4.addText('foo', 10, 10)
	o2.addShapeObject(o4, 30, 30)

	app.MainLoop()

