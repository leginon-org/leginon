#!/usr/bin/env python

import cStringIO
import Mrc
import math
import Numeric
from wxPython.wx import *
from wxPython.lib.buttons import wxGenBitmapToggleButton
from NumericImage import NumericImage

wxInitAllImageHandlers()

class ImageTool(object):
	def __init__(self, imagepanel, sizer, bitmap, tooltip='', cursor=None,
								untoggle=False):
		self.sizer = sizer
		self.imagepanel = imagepanel
		self.cursor = cursor
		self.button = wxGenBitmapToggleButton(self.imagepanel, -1, bitmap,
                                          size=(24, 24))
		self.untoggle = untoggle
		self.button.SetBezelWidth(1)
		if tooltip:
			self.button.SetToolTip(wxToolTip(tooltip))
		self.sizer.Add(self.button, 0, wxALL, 3)
		EVT_BUTTON(self.imagepanel, self.button.GetId(), self.OnButton)

	def OnButton(self, evt):
		if self.button.GetToggle():
			if self.untoggle:
				self.untoggle = False
				self.imagepanel.UntoggleTools()
				self.untoggle = True
			if self.cursor is not None:
				self.imagepanel.panel.SetCursor(self.cursor)
			self.OnToggle(True)
		else:
			self.imagepanel.panel.SetCursor(self.imagepanel.defaultcursor)
			self.OnToggle(False)

	def OnToggle(self, value):
		pass

	def getToolBitmap(self, filename):
		wximage = wxImage('icons/' + filename)
		bitmap = wxBitmapFromImage(wximage)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		return bitmap

	def OnLeftClick(self, evt):
		pass

	def OnRightClick(self, evt):
		pass

	def OnLeftDoubleClick(self, evt):
		pass

	def OnRightDoubleClick(self, evt):
		pass

	def OnMotion(self, evt, dc):
		pass

	def getToolTipString(self, x, y, value):
		return ''

class ValueTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = self.getToolBitmap('valuetool.bmp')
		tooltip = 'Toggle Show Value'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(True)

	def valueString(self, x, y, value):
		return '(%d, %d) %s' % (x, y, str(value))

	def getToolTipString(self, x, y, value):
		if self.button.GetToggle():
			return self.valueString(x, y, value)
		else:
			return ''

class RulerTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = self.getToolBitmap('rulertool.bmp')
		tooltip = 'Toggle Ruler Tool'
		cursor = wxCROSS_CURSOR
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.start = None

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.start = self.imagepanel.view2image((evt.m_x, evt.m_y))

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.start = None
			self.imagepanel.UpdateDrawing()

	def OnToggle(self, value):
		if not value:
			self.start = None

	def DrawRuler(self, dc, x, y):
		dc.SetPen(wxPen(wxRED, 1))
		x0, y0 = self.imagepanel.image2view(self.start)
		x0 -= self.imagepanel.offset[0]
		y0 -= self.imagepanel.offset[1]
		dc.DrawLine(x0, y0, x, y)

	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and self.start is not None:
			x = evt.m_x - self.imagepanel.offset[0]
			y = evt.m_y - self.imagepanel.offset[1]
			self.DrawRuler(dc, x, y)

	def getToolTipString(self, x, y, value):
		if self.button.GetToggle() and self.start is not None:
			x0, y0 = self.start
			return 'From (%d, %d) x=%d y=%d %.2f' % (x0, y0, x - x0, y - y0,
																								math.sqrt((x-x0)**2+(y-y0)**2))
		else:
			return ''

class ZoomTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = self.getToolBitmap('zoomtool.bmp')
		tooltip = 'Toggle Zoom Tool'
		cursor = wxStockCursor(wxCURSOR_MAGNIFIER)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.label = wxStaticText(self.imagepanel, -1, '')
		self.updateLabel()
		self.sizer.Add(self.label, 0, wxALIGN_CENTER_VERTICAL | wxALL, 3)

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.zoomIn(evt.m_x, evt.m_y)

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.zoomOut(evt.m_x, evt.m_y)

	def updateLabel(self):
		xscale, yscale = self.imagepanel.getScale()
		self.label.SetLabel('Zoom: ' + str(xscale) + 'x')
		width, height = self.label.GetSizeTuple()
		self.sizer.SetItemMinSize(self.label, width, height)
		self.sizer.Layout()

	def zoomIn(self, x, y):
		xscale, yscale = self.imagepanel.getScale()
		center = self.imagepanel.view2image((x, y))
		self.imagepanel.setScale((xscale*2, yscale*2))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()
		self.updateLabel()

	def zoomOut(self, x, y):
		xscale, yscale = self.imagepanel.getScale()
		center = self.imagepanel.view2image((x, y))
		self.imagepanel.setScale((xscale/2, yscale/2))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()
		self.updateLabel()

class ImagePanel(wxPanel):
	def __init__(self, parent, id, imagesize=(512, 512)):
		self.numericimage = None
		self.bitmap = None
		self.buffer = None
		self.motionbuffer = None
		self.imagesize = imagesize
		self.scale = (1.0, 1.0)
		self.offset = (0, 0)

		wxPanel.__init__(self, parent, id)

		self.sizer = wxBoxSizer(wxVERTICAL)
		self.SetAutoLayout(true)
		self.SetSizer(self.sizer)

		self.toolsizer = wxBoxSizer(wxHORIZONTAL)
		self.sizer.Add(self.toolsizer)
		self.tools = []

		height, width = self.imagesize
		self.initPanel()

		self.Fit()

		EVT_LEFT_UP(self.panel, self.OnLeftUp)
		EVT_RIGHT_UP(self.panel, self.OnRightUp)
		EVT_LEFT_DCLICK(self.panel, self.OnLeftDoubleClick)
		EVT_RIGHT_DCLICK(self.panel, self.OnRightDoubleClick)
		EVT_PAINT(self.panel, self.OnPaint)
		EVT_SIZE(self.panel, self.OnSize)
		EVT_MOTION(self.panel, self.OnMotion)
		EVT_LEAVE_WINDOW(self.panel, self.OnLeave)

		self.addTool(ValueTool(self, self.toolsizer))
		self.addTool(RulerTool(self, self.toolsizer))
		self.addTool(ZoomTool(self, self.toolsizer))

	def addTool(self, tool):
		self.tools.append(tool)

	def initPanel(self):
		self.panel = wxScrolledWindow(self, -1, size=self.imagesize)
		self.panel.SetScrollRate(1,1)
		self.defaultcursor = wxCROSS_CURSOR
		self.panel.SetCursor(self.defaultcursor)
		self.sizer.Add(self.panel)
		width, height = self.panel.GetSizeTuple()
		self.sizer.SetItemMinSize(self.panel, width, height)

	# image set functions

	def setBitmap(self):
		if self.numericimage is None:
			self.bitmap = None
			return

		image = NumericImage(self.numericimage)
		image.update_image()
		wximage = image.wxImage()

		if self.smallScale():
			xscale, yscale = self.getScale()
			width, height = wximage.GetWidth()*xscale, wximage.GetHeight()*yscale
			self.bitmap = wxBitmapFromImage(wximage.Scale(width, height))
		else:
			self.bitmap = wxBitmapFromImage(wximage)

	def setBuffers(self):
		if self.bitmap is None:
			self.buffer = None
			self.motionbuffer = None
		else:
			width, height = self.bitmap.GetWidth(), self.bitmap.GetHeight()
			self.buffer = wxEmptyBitmap(width, height)
			self.motionbuffer = wxEmptyBitmap(width, height)

	def setVirtualSize(self):
		if self.bitmap is not None:
			width, height = self.bitmap.GetWidth(), self.bitmap.GetHeight()
			if self.smallScale():
				virtualsize = (width - 1, height - 1)
			else:
				xscale, yscale = self.getScale()
				virtualsize = ((width - 1) * xscale, (height - 1) * yscale)
			self.panel.SetVirtualSize(virtualsize)
		else:
			self.panel.SetVirtualSize((0, 0))

		if self.biggerView():
			xsize, ysize = self.panel.GetVirtualSize()
			xclientsize, yclientsize = self.panel.GetClientSize()
			self.offset = ((xclientsize - xsize)/2, (yclientsize - ysize)/2)
		else:
			self.offset = (0, 0)

	def setNumericImage(self, numericimage, scroll=False):
		self.numericimage = numericimage
		self.setBitmap()
		self.setBuffers()
		self.setVirtualSize()
		if not scroll:
			self.panel.Scroll(0, 0)
		self.UpdateDrawing()

	def clearImage(self):
		self.setNumericImage(None)

	def setImageFromMrcString(self, imagestring, scroll=False):
		self.setNumericImage(Mrc.mrcstr_to_numeric(imagestring), scroll)

	# scaling functions

	def getScale(self):
		return self.scale

	def smallScale(self, scale=None):
		if scale is None:
			scale = self.getScale()
		if scale[0] < 1.0 or scale[1] < 1.0:
			return True
		else:
			return False

	def setScale(self, scale):
		for n in scale:
			# from one test
			if n > 512.0 or n < 0.002:
				return
		oldscale = self.getScale()
		self.scale = scale
		if self.smallScale() or self.smallScale(oldscale):
			self.setBitmap()
			self.setBuffers()

		self.setVirtualSize()
		if self.biggerView():
			self.panel.Refresh()
		#self.UpdateDrawing()

	# utility functions

	def getValue(self, x, y):
		try:
			return self.numericimage[y, x]
		except (IndexError, AttributeError), e:
			return None

	def getClientCenter(self):
		center = self.panel.GetClientSize()
		return (center[0]/2, center[1]/2)

	def biggerView(self):
		size = self.panel.GetVirtualSize()
		clientsize = self.panel.GetClientSize()
		if size[0] < clientsize[0] or size[1] < clientsize[1]:
			return True
		else:
			return False

	def center(self, center):
		x, y = center
		xcenter, ycenter = self.getClientCenter()
		xscale, yscale = self.getScale()
		self.panel.Scroll(x * xscale - xcenter, y * yscale - ycenter)

	def view2image(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		xoffset, yoffset = self.offset
		return (int(round((viewoffset[0] + xy[0] - xoffset) / scale[0])),
						int(round((viewoffset[1] + xy[1] - yoffset) / scale[1])))

	def image2view(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		xoffset, yoffset = self.offset
		return (int(round(((xy[0]) * scale[0]) - viewoffset[0] + xoffset)),
						int(round(((xy[1]) * scale[1]) - viewoffset[1] + yoffset)))

	# tool utility functions

	def UntoggleTools(self):
		for tool in self.tools:
			if tool.untoggle:
				tool.button.SetToggle(False)

	# eventhandlers

	def getMotionBufferDC(self):
		dc = wxMemoryDC()
		dc.SelectObject(self.motionbuffer)
		dc.BeginDrawing()
		dc.Clear()

		fromdc = wxMemoryDC()
		fromdc.SelectObject(self.buffer)
		self.Draw(dc)

		xviewoffset, yviewoffset = self.panel.GetViewStart()
		xsize, ysize = self.panel.GetClientSize()
		xoffset, yoffset = self.offset

		if self.smallScale():
			dc.Blit(0, 0, xsize, ysize, fromdc, xviewoffset, yviewoffset)
		else:
			xscale, yscale = self.getScale()
			dc.SetUserScale(xscale, yscale)
			dc.Blit(0, 0, xsize/xscale + 1, ysize/yscale + 1, fromdc,
							xviewoffset/xscale, yviewoffset/yscale)

		fromdc.SelectObject(wxNullBitmap)

		if not self.smallScale():
			dc.SetUserScale(1.0, 1.0)

		return dc

	def drawMotionBufferDC(self, dc):
		dc.EndDrawing()
		dc.SelectObject(wxNullBitmap)

		xoffset, yoffset = self.offset
		clientdc = wxClientDC(self.panel)
		clientdc.BeginDrawing()
		clientdc.DrawBitmap(self.motionbuffer, xoffset, yoffset)
		clientdc.EndDrawing()

	def OnMotion(self, evt):
		if self.buffer is None or self.motionbuffer is None:
			return

		if self.smallScale():
			xoffset, yoffset = self.offset
			if evt.m_x < xoffset or evt.m_x > xoffset + self.bitmap.GetWidth() - 1: 
				self.UpdateDrawing()
				return
			if evt.m_y < yoffset or evt.m_y > yoffset + self.bitmap.GetHeight() - 1: 
				self.UpdateDrawing()
				return

		dc = self.getMotionBufferDC()

		for tool in self.tools:
			tool.OnMotion(evt, dc)

		string = ''
		x, y = self.view2image((evt.m_x, evt.m_y))
		value = self.getValue(x, y)
		for tool in self.tools:
			if string:
				string += ' '
			string += tool.getToolTipString(x, y, value)
		if string:
			self.drawToolTip(dc, x, y, string)

		self.drawMotionBufferDC(dc)

	def OnLeftUp(self, evt):
		for tool in self.tools:
			tool.OnLeftClick(evt)

	def OnRightUp(self, evt):
		for tool in self.tools:
			tool.OnRightClick(evt)

	def OnLeftDoubleClick(self, evt):
		for tool in self.tools:
			tool.OnLeftDoubleClick(evt)

	def OnRightDoubleClick(self, evt):
		for tool in self.tools:
			tool.OnRightDoubleClick(evt)

	def drawToolTip(self, dc, x, y, string):
		dc.SetBrush(wxBrush(wxColour(255, 255, 220)))
		dc.SetPen(wxPen(wxBLACK, 1))

		xextent, yextent, d, e = dc.GetFullTextExtent(string, wxNORMAL_FONT)
		xcenter, ycenter = self.getClientCenter()

		ix, iy = self.image2view((x, y))

		if ix <= xcenter:
			xoffset = 10
		else:
			xoffset = -(10 + xextent + 4)
		if iy <= ycenter:
			yoffset = 10
		else:
			yoffset = -(10 + yextent + 4)

		ix -= self.offset[0]
		iy -= self.offset[1]

		x = int(round((ix + xoffset)))
		y = int(round((iy + yoffset)))

		dc.DrawRectangle(x, y, xextent + 4, yextent + 4)

		dc.SetFont(wxNORMAL_FONT)
		dc.DrawText(string, x + 2 , y + 2)

	def Draw(self, dc):
		dc.BeginDrawing()
		if self.bitmap is None:
			dc.Clear()
		else:
			dc.DrawBitmap(self.bitmap, 0, 0)
		dc.EndDrawing()

	def paint(self, fromdc, todc):
		xviewoffset, yviewoffset = self.panel.GetViewStart()
		xsize, ysize = self.panel.GetClientSize()

		if self.smallScale():
			xscale, yscale = (1.0, 1.0)
		else:
			xscale, yscale = self.getScale()
			todc.SetUserScale(xscale, yscale)
		xoffset, yoffset = self.offset
		todc.Blit(xoffset, yoffset, xsize/xscale + 1, ysize/yscale + 1, fromdc,
							xviewoffset/xscale, yviewoffset/yscale)

	def UpdateDrawing(self):
		if self.buffer is not None:
			dc = wxMemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wxClientDC(self.panel))
			dc.SelectObject(wxNullBitmap)
		else:
			self.panel.Refresh()

	def OnSize(self, evt):
		self.UpdateDrawing()

	def OnPaint(self, evt):
		if self.buffer is None:
			evt.Skip()
		else:
			dc = wxMemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wxPaintDC(self.panel))
			dc.SelectObject(wxNullBitmap)

	def OnLeave(self, evt):
		self.UpdateDrawing()

class ClickTool(ImageTool):
	def __init__(self, imagepanel, sizer, callback=None):
		bitmap = self.getToolBitmap('arrowtool.bmp')
		tooltip = 'Click Tool'
		cursor = wxStockCursor(wxCURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.callback = callback

	def OnLeftDoubleClick(self, evt):
		if self.button.GetToggle():
			xy = self.imagepanel.view2image((evt.m_x, evt.m_y))
			if callable(self.callback):
				self.callback(xy)

class ClickImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None):
		ImagePanel.__init__(self, parent, id)
		self.addTool(ClickTool(self, self.toolsizer, callback))

class TargetTool(ImageTool):
	def __init__(self, imagepanel, sizer, callback=None):
		bitmap = self.getToolBitmap('targettool.bmp')
		tooltip = 'Toggle Target Tool'
		cursor = wxStockCursor(wxCURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.callback = callback
		self.target_type = None
		self.closest_target = None
		self.combobox = None

	def addTargetType(self, name):
		if self.target_type is None:
			self.target_type = name
			self.setTargetButtonBitmap()
		self.addComboBox(name)

	def deleteTargetType(self, name):
		self.deleteComboBox(name)

	def OnToggle(self, value):
		if not value:
			self.imagepanel.closest_target = None
			self.imagepanel.UpdateDrawing()

	def setTargetButtonBitmap(self):
		bitmap = wxEmptyBitmap(16, 16)
		dc = wxMemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		color = self.imagepanel.colors[self.target_type]
		dc.SetPen(wxPen(color, 2))
		dc.DrawLine(8, 0, 8, 15)
		dc.DrawLine(0, 8, 15, 8)
		dc.EndDrawing()
		dc.SelectObject(wxNullBitmap)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		self.button.SetBitmapLabel(bitmap)
		self.button.Refresh()

	def OnComboBoxSelect(self, evt):
		self.target_type = evt.GetString()
		self.setTargetButtonBitmap()

	def addComboBox(self, name):
		if self.combobox is None:
			if len(self.imagepanel.targets) > 1:
				self.combobox = wxComboBox(self.imagepanel, -1, value=self.target_type,
																		choices=self.imagepanel.targets.keys(),
																		style=wxCB_DROPDOWN|wxCB_READONLY|wxCB_SORT)
				EVT_COMBOBOX(self.imagepanel, self.combobox.GetId(),
											self.OnComboBoxSelect)
				self.sizer.Add(self.combobox, 0, wxALIGN_CENTER_VERTICAL | wxALL, 3)
				self.sizer.Layout()
			elif len(self.imagepanel.targets) == 1:
				self.target_type = name
				self.sizer.Layout()
		else:
			self.combobox.Append(name)
			self.combobox.SetSize(self.combobox.GetBestSize())
			width, height = self.combobox.GetSizeTuple()
			self.sizer.SetItemMinSize(self.combobox, width, height)
			self.sizer.Layout()

	def deleteComboBox(self, name):
		if self.combobox is None:
			if len(self.imagepanel.targets) > 2:
				self.combobox.Delete(self.combobox.FindString(name))
			elif len(self.imagepanel.targets) == 2:
				self.sizer.Remove(self.combobox)
				self.sizer.Layout()
				self.target_type = self.imagepanel.targets.keys()[0]
			else:
				EVT_BUTTON(self.imagepanel, self.button.GetId(), None)
				self.sizer.Remove(self.button)
				self.sizer.Layout()
				self.target_type = None

	def OnLeftDoubleClick(self, evt):
		if self.button.GetToggle() and self.target_type is not None:
			x, y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			target = self.imagepanel.addTarget(self.target_type, x, y)
			if callable(self.callback):
				targets = self.imagepanel.getTargetTypeValue(self.target_type)
				self.callback(self.target_type, targets)

	def OnRightDoubleClick(self, evt):
		if self.button.GetToggle() and self.closest_target is not None:
			target_type, value = self.imagepanel.deleteTarget(self.closest_target)
			self.closest_target = None
			if callable(self.callback):
				self.callback(target_type, value)

	def updateClosest(self, x, y):
		closest_target = None
		minimum_magnitude = 10
		if self.imagepanel.smallScale():
			xscale, yscale = self.imagepanel.getScale()
			minimum_magnitude /= xscale
		for target_type in self.imagepanel.targets.values():
			for target in target_type:
				magnitude = math.sqrt((x - target[0])**2 +
															(y - target[1])**2)
				if magnitude < minimum_magnitude:
					minimum_magnitude = magnitude
					closest_target = target
		if self.closest_target is not None:
			if self.closest_target == closest_target:
				return
			else:
				old_target = self.closest_target
				self.closest_target = None
				self.imagepanel.UpdateDrawing()
		self.closest_target = closest_target
		if closest_target is not None:
			self.imagepanel.UpdateDrawing()

	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and  len(self.imagepanel.targets) > 0:
			viewoffset = self.imagepanel.panel.GetViewStart()
			x, y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			self.updateClosest(x, y)

class TargetImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None):
		ImagePanel.__init__(self, parent, id)
		self.targets = {}
		self.colorlist = [wxRED, wxBLUE, wxColor(255, 0, 255), wxColor(0, 255, 255)]
		self.colors = {}
		self.addTool(TargetTool(self, self.toolsizer, callback))

	def addTargetType(self, name, value=[]):
		if name in self.targets:
			raise ValueError('Target type already exists')
		try:
			self.colors[name] = self.colorlist[0]
			del self.colorlist[0]
		except IndexError:
			raise RuntimeError('Not enough colors for addition target types')
		self.targets[name] = list(value)
		for tool in self.tools:
			if hasattr(tool, 'addTargetType'):
				tool.addTargetType(name)

	def deleteTargetType(self, name):
		try:
			self.colorlist.append[self.colors[name]]
			del self.colors[name]
			del self.targets[name]
		except:
			raise ValueError('No such target type')
		for tool in self.tools:
			if hasattr(tool, 'addTargetType'):
				tool.deleteTargetType(name)
		self.UpdateDrawing()

	def getTargetTypeValue(self, name):
		try:
			return self.targets[name]
		except:
			raise ValueError('No such target type')

	def setTargetTypeValue(self, name, value):
		if name not in self.targets:
			self.addTargetType(name, value)
		else:
			self.targets[name] = list(value)
		self.UpdateDrawing()

	def addTarget(self, target_type, x, y):
		target = (x, y)
		self.targets[target_type].append(target)
		self.UpdateDrawing()
		return target

	# could be hazardous if more than same target exists in type or multiple type
	def deleteTarget(self, target):
		for target_type in self.targets:
			if target in self.targets[target_type]:
				self.targets[target_type].remove(target)
				self.UpdateDrawing()
				return target_type, self.targets[target_type]

	def clearTargets(self):
		self.targets = {}
		self.UpdateDrawing()

	# needs to be stored rather than generated
	def getTargetBitmap(self, target):
		penwidth = 1
		length = 15
		for target_type in self.targets:
			if target in self.targets[target_type]:
				color = self.colors[target_type]
				break
		# temp
		for tool in self.tools:
			if hasattr(tool, 'closest_target'):
				if target == tool.closest_target:
					color = wxColor(color.Red()/2, color.Green()/2, color.Blue()/2)
		pen = wxPen(color, 1)
		mem = wxMemoryDC()
		bitmap = wxEmptyBitmap(length, length)
		mem.SelectObject(bitmap)
		mem.BeginDrawing()
		mem.Clear()
		mem.SetBrush(wxBrush(color, wxTRANSPARENT))
		mem.SetPen(pen)
		mem.DrawLine(length/2, 0, length/2, length)
		mem.DrawLine(0, length/2, length, length/2)
		mem.EndDrawing()
		mem.SelectObject(wxNullBitmap)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		return bitmap

	def drawTarget(self, dc, target):
		memorydc = wxMemoryDC()
		bitmap = self.getTargetBitmap(target)
		memorydc.SelectObject(bitmap)
		width = bitmap.GetWidth()
		height = bitmap.GetHeight()
		targetx, targety = target
		if self.smallScale():
			xscale, yscale = self.getScale()
			targetx = targetx * xscale
			targety = targety * yscale
		dc.Blit(targetx - width/2, targety - height/2, width, height,
						memorydc, 0, 0, wxCOPY, True)

	def Draw(self, dc):
		ImagePanel.Draw(self, dc)
		dc.BeginDrawing()
		for target_type in self.targets.values():
			for target in target_type:
				self.drawTarget(dc, target)
		dc.EndDrawing()

if __name__ == '__main__':
	def bar(xy):
		print xy

	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = TargetImagePanel(frame, -1)
#			self.panel = ClickImagePanel(frame, -1, bar)
			self.panel.addTargetType('foo')
			self.panel.addTargetType('bar')
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.panel.setImageFromMrcString(open('test1.mrc', 'rb').read())
	app.MainLoop()

