# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ImageViewer.py,v $
# $Revision: 1.38 $
# $Name: not supported by cvs2svn $
# $Date: 2004-11-02 23:08:51 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import cStringIO
import Mrc
import math
try:
	import numarray as Numeric
except:
	import Numeric
import wx
from wx.lib.buttons import GenBitmapButton, GenBitmapToggleButton
import NumericImage
import Image
import imagefun
import icons
import numextension
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Stats
import time

wx.InitAllImageHandlers()

ImageClickedEventType = wx.NewEventType()
ImageClickDoneEventType = wx.NewEventType()
MeasurementEventType = wx.NewEventType()
DisplayEventType = wx.NewEventType()
TargetingEventType = wx.NewEventType()
SettingsEventType = wx.NewEventType()

EVT_IMAGE_CLICKED = wx.PyEventBinder(ImageClickedEventType)
EVT_IMAGE_CLICK_DONE = wx.PyEventBinder(ImageClickDoneEventType)
EVT_MEASUREMENT = wx.PyEventBinder(MeasurementEventType)
EVT_DISPLAY = wx.PyEventBinder(DisplayEventType)
EVT_TARGETING = wx.PyEventBinder(TargetingEventType)
EVT_SETTINGS = wx.PyEventBinder(SettingsEventType)

class ImageClickedEvent(wx.PyCommandEvent):
	def __init__(self, source, xy):
		wx.PyCommandEvent.__init__(self, ImageClickedEventType, source.GetId())
		self.SetEventObject(source)
		self.xy = xy

class ImageClickDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ImageClickDoneEventType, source.GetId())
		self.SetEventObject(source)

class MeasurementEvent(wx.PyCommandEvent):
	def __init__(self, source, measurement):
		wx.PyCommandEvent.__init__(self, MeasurementEventType, source.GetId())
		self.SetEventObject(source)
		self.measurement = measurement

class DisplayEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, DisplayEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

class TargetingEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, TargetingEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

class SettingsEvent(wx.PyCommandEvent):
	def __init__(self, source, name):
		wx.PyCommandEvent.__init__(self, SettingsEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name


bitmaps = {}

def getBitmap(filename):
	try:
		return bitmaps[filename]
	except KeyError:
		iconpath = icons.getPath(filename)
		wximage = wx.Image(iconpath)
		wximage.ConvertAlphaToMask()
		bitmap = wx.BitmapFromImage(wximage)
		bitmaps[filename] = bitmap
		return bitmap

targeticonbitmaps = {}

def getTargetIconBitmap(color):
	try:
		return targeticonbitmaps[color]
	except KeyError:
		bitmap = wx.EmptyBitmap(16, 16)
		dc = wx.MemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		dc.SetPen(wx.Pen(color, 2))
		dc.DrawLine(8, 1, 8, 14)
		dc.DrawLine(1, 8, 14, 8)
		dc.DrawPoint(1, 7)
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
		targeticonbitmaps[color] = bitmap
		return bitmap

targetbitmaps = {}

def getTargetBitmap(color):
	try:
		return targetbitmaps[color]
	except KeyError:
		penwidth = 1
		length = 15
		bitmap = wx.EmptyBitmap(length, length)
		dc = wx.MemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
		dc.SetPen(wx.Pen(color, penwidth))
		dc.DrawLine(length/2, 0, length/2, length)
		dc.DrawLine(0, length/2, length, length/2)
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
		return bitmap

def getTargetBitmaps(color):
	selectedcolor = wx.Color(color.Red()/2, color.Green()/2, color.Blue()/2)
	return getTargetBitmap(color), getTargetBitmap(selectedcolor)

# needs to adjust buffer/wximage instead of reseting from numeric image
class ContrastTool(object):
	def __init__(self, imagepanel, sizer):
		self.imagepanel = imagepanel
		self.imagemin = 0
		self.imagemax = 0
		self.contrastmin = 0
		self.contrastmax = 0
		self.slidermin = 0
		self.slidermax = 255

		self.minslider = wx.Slider(self.imagepanel, -1, self.slidermin,
															self.slidermin, self.slidermax, size=(200, -1))
		self.maxslider = wx.Slider(self.imagepanel, -1, self.slidermax,
															self.slidermin, self.slidermax, size=(200, -1))
		self.minslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onMaxSlider)
		self.minslider.Bind(wx.EVT_SCROLL_ENDSCROLL, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_ENDSCROLL, self.onMaxSlider)
		self.minslider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onMaxSlider)

		self.iemin = FloatEntry(imagepanel, -1, chars=6, allownone=False,
														value='%g' % self.contrastmin)
		self.iemax = FloatEntry(imagepanel, -1, chars=6, allownone=False,
														value='%g' % self.contrastmax)
		self.iemin.Enable(False)
		self.iemax.Enable(False)

		self.iemin.Bind(EVT_ENTRY, self.onMinEntry)
		self.iemax.Bind(EVT_ENTRY, self.onMaxEntry)

		self.sizer = wx.GridBagSizer(0, 0)
		self.sizer.Add(self.minslider, (0, 0), (1, 1),
										wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.iemin, (0, 1), (1, 1),
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 2)
		self.sizer.Add(self.maxslider, (1, 0), (1, 1),
										wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)
		self.sizer.Add(self.iemax, (1, 1), (1, 1),
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 2)
		sizer.Add(self.sizer, 0, wx.ALIGN_CENTER)

	def _setSliders(self, value):
		if value[0] is not None:
			self.minslider.SetValue(self.getSliderValue(value[0]))
		if value[1] is not None:
			self.maxslider.SetValue(self.getSliderValue(value[1]))

	def _setEntries(self, value):
		if value[0] is not None:
			self.iemin.SetValue(value[0])
		if value[1] is not None:
			self.iemax.SetValue(value[1])

	def setSliders(self, value):
		if value[0] is not None:
			self.contrastmin = value[0]
		if value[1] is not None:
			self.contrastmax = value[1]
		self._setSliders(value)
		self._setEntries(value)

	def updateNumericImage(self):
		self.imagepanel.setBitmap()
		self.imagepanel.setBuffer()
		self.imagepanel.UpdateDrawing()

	def getRange(self):
		return self.contrastmin, self.contrastmax

	def getScaledValue(self, position):
		try:
			scale = float(position - self.slidermin)/(self.slidermax - self.slidermin)
		except ZeroDivisionError:
			scale = 1.0
		return (self.imagemax - self.imagemin)*scale + self.imagemin

	def getSliderValue(self, value):
		try:
			scale = (value - self.imagemin)/(self.imagemax - self.imagemin)
		except ZeroDivisionError:
			scale = 1.0
		return int(round((self.slidermax - self.slidermin)*scale + self.slidermin))

	def setRange(self, range, value=None):
		if range is None:
			self.imagemin = 0
			self.imagemax = 0
			self.contrastmin = 0
			self.contrastmax = 0
			self.iemin.SetValue(0.0)
			self.iemax.SetValue(0.0)
			self.iemin.Enable(False)
			self.iemax.Enable(False)
		else:
			self.imagemin = range[0]
			self.imagemax = range[1]
			if value is None:
				self.contrastmin = self.getScaledValue(self.minslider.GetValue())
				self.contrastmax = self.getScaledValue(self.maxslider.GetValue())
			else:
				self.setSliders(value)
			self.iemin.Enable(True)
			self.iemax.Enable(True)

	def onMinSlider(self, evt):
		position = evt.GetPosition()
		maxposition = self.maxslider.GetValue()
		if position > maxposition:
			self.minslider.SetValue(maxposition)
			self.contrastmin = self.contrastmax
		else:
			self.contrastmin = self.getScaledValue(position)
		self._setEntries((self.contrastmin, None))
		self.updateNumericImage()

	def onMaxSlider(self, evt):
		position = evt.GetPosition()
		minposition = self.minslider.GetValue()
		if position < minposition:
			self.maxslider.SetValue(minposition)
			self.contrastmax = self.contrastmin
		else:
			self.contrastmax = self.getScaledValue(position)
		self._setEntries((None, self.contrastmax))
		self.updateNumericImage()

	def onMinEntry(self, evt):
		contrastmin = evt.GetValue()
		if contrastmin < self.imagemin:
			self.contrastmin = self.imagemin
			self.iemin.SetValue(self.contrastmin)
		elif contrastmin > self.contrastmax:
			self.contrastmin = self.contrastmax
			self.iemin.SetValue(self.contrastmin)
		else:
			self.contrastmin = contrastmin
		self._setSliders((self.contrastmin, None))
		self.updateNumericImage()

	def onMaxEntry(self, evt):
		contrastmax = evt.GetValue()
		if contrastmax > self.imagemax:
			self.contrastmax = self.imagemax
			self.iemax.SetValue(self.contrastmax)
		elif contrastmax < self.contrastmin:
			self.contrastmax = self.contrastmin
			self.iemax.SetValue(self.contrastmax)
		else:
			self.contrastmax = contrastmax
		self._setSliders((None, self.contrastmax))
		self.updateNumericImage()

class ImageTool(object):
	def __init__(self, imagepanel, sizer, bitmap, tooltip='', cursor=None,
								untoggle=False):
		self.sizer = sizer
		self.imagepanel = imagepanel
		self.cursor = cursor
		self.button = GenBitmapToggleButton(self.imagepanel, -1, bitmap,
                                          size=(24, 24))
		self.untoggle = untoggle
		self.button.SetBezelWidth(1)
		if tooltip:
			self.button.SetToolTip(wx.ToolTip(tooltip))
		self.sizer.Add(self.button, 0, wx.ALIGN_CENTER|wx.ALL, 3)
		self.button.Bind(wx.EVT_BUTTON, self.OnButton)

	def OnButton(self, evt):
		if self.button.GetToggle():
			if self.untoggle:
				self.imagepanel.UntoggleTools(self)
			if self.cursor is not None:
				self.imagepanel.panel.SetCursor(self.cursor)
			self.OnToggle(True)
		else:
			self.imagepanel.panel.SetCursor(self.imagepanel.defaultcursor)
			self.OnToggle(False)

	def OnToggle(self, value):
		pass


	def OnLeftClick(self, evt):
		pass

	def OnRightClick(self, evt):
		pass

	def OnMotion(self, evt, dc):
		pass

	def getToolTipString(self, x, y, value):
		return ''

	def Draw(self, dc):
		pass

class ValueTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('value.png')
		tooltip = 'Toggle Show Value'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(True)

	def valueString(self, x, y, value):
		if value is None:
			valuestr = 'N/A'
		else:
			valuestr = '%g' % value
		return '(%d, %d) %s' % (x, y, valuestr)

	def getToolTipString(self, x, y, value):
		#self.imagepanel.pospanel.set({'x': x, 'y': y, 'value': value})
		if self.button.GetToggle():
			return self.valueString(x, y, value)
		else:
			return ''

class CrosshairTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getTargetIconBitmap(wx.BLUE)
		tooltip = 'Toggle Center Crosshair'
		cursor = None
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, False)

	def Draw(self, dc):
		if not self.button.GetToggle():
			return
		dc.SetPen(wx.Pen(wx.BLUE, 1))
		width = self.imagepanel.bitmap.GetWidth()
		height = self.imagepanel.bitmap.GetHeight()
		if self.imagepanel.scaleImage():
			width /= self.imagepanel.scale[0]
			height /= self.imagepanel.scale[1]
		center = width/2, height/2
		x, y = self.imagepanel.image2view(center)
		width = self.imagepanel.buffer.GetWidth()
		height = self.imagepanel.buffer.GetHeight()
		dc.DrawLine(x, 0, x, height)
		dc.DrawLine(0, y, width, y)

	def OnToggle(self, value):
		self.imagepanel.UpdateDrawing()

class RulerTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('ruler.png')
		tooltip = 'Toggle Ruler Tool'
		cursor = wx.CROSS_CURSOR
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.start = None
		self.measurement = None

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			if self.start is not None:
				x = evt.m_x #- self.imagepanel.offset[0]
				y = evt.m_y #- self.imagepanel.offset[1]
				x0, y0 = self.start
				dx, dy = x - x0, y - y0
				self.measurement = {
					'from': self.start,
					'to': (x, y),
					'delta': (dx, dy),
					'magnitude': math.hypot(dx, dy),
				}
				mevt = MeasurementEvent(self.imagepanel, dict(self.measurement))
				self.imagepanel.GetEventHandler().AddPendingEvent(mevt)
			self.start = self.imagepanel.view2image((evt.m_x, evt.m_y))

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.start = None
			self.measurement = None
			self.imagepanel.UpdateDrawing()

	def OnToggle(self, value):
		if not value:
			self.start = None
			self.measurement = None

	def DrawRuler(self, dc, x, y):
		dc.SetPen(wx.Pen(wx.RED, 1))
		x0, y0 = self.imagepanel.image2view(self.start)
		#x0 -= self.imagepanel.offset[0]
		#y0 -= self.imagepanel.offset[1]
		dc.DrawLine(x0, y0, x, y)

	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and self.start is not None:
			x = evt.m_x #- self.imagepanel.offset[0]
			y = evt.m_y #- self.imagepanel.offset[1]
			self.DrawRuler(dc, x, y)

	def getToolTipString(self, x, y, value):
		if self.button.GetToggle() and self.start is not None:
			x0, y0 = self.start
			dx, dy = x - x0, y - y0
			return 'From (%d, %d) x=%d y=%d d=%.2f' % (x0, y0, dx, dy,
																									math.hypot(dx, dy))
		else:
			return ''

class ZoomTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('zoom.png')
		tooltip = 'Toggle Zoom Tool'
		cursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.zoomlevels = range(5, -6, -1)
		# wx.Choice seems a bit slow, at least on windows
		self.zoomchoice = wx.Choice(self.imagepanel, -1,
																choices=map(self.log2str, self.zoomlevels))
		self.zoom(self.zoomlevels.index(0), (0, 0))
		self.zoomchoice.SetSelection(self.zoomlevel)
		self.sizer.Add(self.zoomchoice, 0, wx.ALIGN_CENTER|wx.ALL, 3)

		self.zoomchoice.Bind(wx.EVT_CHOICE, self.onChoice)

	def log2str(self, value):
		if value < 0:
			return '1/' + str(int(1/2**value)) + 'x'
		else:
			return str(int(2**value)) + 'x'

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.zoomIn(evt.m_x, evt.m_y)

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.zoomOut(evt.m_x, evt.m_y)

	def zoom(self, level, viewcenter):
		self.zoomlevel = level
		center = self.imagepanel.view2image(viewcenter)
		scale = 2**self.zoomlevels[self.zoomlevel]
		self.imagepanel.setScale((scale, scale))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()

	def zoomIn(self, x, y):
		if self.zoomlevel > 0:
			self.zoom(self.zoomlevel - 1, (x, y))
			self.zoomchoice.SetSelection(self.zoomlevel)

	def zoomOut(self, x, y):
		if self.zoomlevel < len(self.zoomlevels) - 1:
			self.zoom(self.zoomlevel + 1, (x, y))
			self.zoomchoice.SetSelection(self.zoomlevel)

	def onChoice(self, evt):
		selection = evt.GetSelection()
		if selection == self.zoomlevel:
			return
		size = self.imagepanel.panel.GetSize()
		viewcenter = (size[0]/2, size[1]/2)
		self.zoom(selection, viewcenter)

class ImagePanel(wx.Panel):
	def __init__(self, parent, id, imagesize=(512, 512)):
		# initialize image variables
		self.imagedata = None
		self.bitmap = None
		self.buffer = None

		self.selectiontool = None

		# get size of image panel (image display dimensions)
		if type(imagesize) != tuple:
			raise TypeError('Invalid type for image panel size, must be tuple')
		if len(imagesize) != 2:
			raise ValueError('Invalid image panel dimension, must be 2 element tuple')
		for element in imagesize:
			if type(element) != int:
				raise TypeError('Image panel dimension must be integer')
			if element < 0:
				raise ValueError('Image panel dimension must be greater than 0')
		self.imagesize = imagesize

		# set scale of image (zoom factor)
		self.scale = (1.0, 1.0)

		# set offset of image (if image size * scale > image panel size)
		self.offset = (0, 0)

		wx.Panel.__init__(self, parent, id)

		# create main sizer, will contain tool sizer and imagepanel
		self.sizer = wx.GridBagSizer(3, 3)
		self.sizer.SetEmptyCellSize((0, 0))

		# create tool size to contain individual tools
		self.toolsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer.Add(self.toolsizer, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.tools = []

		# create image panel, set cursor
		self.panel = wx.ScrolledWindow(self, -1, size=self.imagesize,
																		style=wx.SIMPLE_BORDER)
		self.panel.SetBackgroundColour(wx.WHITE)
		self.panel.SetScrollRate(1, 1)
		self.defaultcursor = wx.CROSS_CURSOR
		self.panel.SetCursor(self.defaultcursor)
		self.sizer.Add(self.panel, (1, 1), (3, 1), wx.EXPAND)
		self.sizer.AddGrowableRow(3)
		self.sizer.AddGrowableCol(1)
		width, height = self.panel.GetSizeTuple()
		self.sizer.SetItemMinSize(self.panel, width, height)

		self.statspanel = gui.wx.Stats.Stats(self, -1, style=wx.SIMPLE_BORDER)
		self.sizer.Add(self.statspanel, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)
		#self.pospanel = gui.wx.Stats.Position(self, -1, style=wx.SIMPLE_BORDER)
		#self.sizer.Add(self.pospanel, (2, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)

		# bind panel events
		self.panel.Bind(wx.EVT_LEFT_UP, self.OnLeftClick)
		self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
		self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
		self.panel.Bind(wx.EVT_SIZE, self.OnSize)
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.panel.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

		# add tools
		self.addTool(ValueTool(self, self.toolsizer))
		self.addTool(RulerTool(self, self.toolsizer))
		self.addTool(ZoomTool(self, self.toolsizer))
		self.addTool(CrosshairTool(self, self.toolsizer))

		self.contrasttool = ContrastTool(self, self.toolsizer)

		self.SetSizerAndFit(self.sizer)

	def addTool(self, tool):
		self.tools.append(tool)
		return tool

	# image set functions

	def setBitmap(self):
		'''
		Set the internal wx.Bitmap to current Numeric image
		'''
		if isinstance(self.imagedata, Numeric.ArrayType):
			clip = self.contrasttool.getRange()
			wximage = wx.EmptyImage(self.imagedata.shape[1], self.imagedata.shape[0])
			wximage.SetData(numextension.rgbstring(self.imagedata, clip[0], clip[1]))
		elif isinstance(self.imagedata, Image.Image):
			wximage = wx.EmptyImage(self.imagedata.size[0], self.imagedata.size[1])
			wximage.SetData(self.imagedata.convert('RGB').tostring())
		else:
			self.bitmap = None
			return

		if self.scaleImage():
			xscale, yscale = self.getScale()
			width = int(round(wximage.GetWidth()*xscale))
			height = int((wximage.GetHeight()*yscale))
			self.bitmap = wx.BitmapFromImage(wximage.Scale(width, height))
		else:
			self.bitmap = wx.BitmapFromImage(wximage)

	def setBuffer(self):
		'''
		Set the interal buffer to empty bitmap the least size of bitmap or client
		'''
		if self.bitmap is None:
			self.buffer = None
		else:
			#bitmapwidth = self.bitmap.GetWidth()
			#bitmapheight = self.bitmap.GetHeight()
			#clientwidth, clientheight = self.panel.GetClientSize()

			#xscale, yscale = self.scale
			#if not self.scaleImage():
			#	bitmapwidth = int(bitmapwidth * xscale)
			#	bitmapheight = int(bitmapheight * yscale)

			#if bitmapwidth < clientwidth:
			#	width = bitmapwidth
			#else:
			#	width = clientwidth

			#if bitmapheight < clientheight:
			#	height = bitmapheight
			#else:
			#	height = clientheight

			width, height = self.panel.GetClientSize()
			self.buffer = wx.EmptyBitmap(width, height)

	def setVirtualSize(self):
		'''
		Set size of viewport and offset for scrolling if image is bigger than view
		'''
		if self.bitmap is not None:
			width, height = self.bitmap.GetWidth(), self.bitmap.GetHeight()
			if self.scaleImage():
				virtualsize = (width - 1, height - 1)
			else:
				xscale, yscale = self.getScale()
				virtualsize = (int(round((width - 1) * xscale)),
												int(round((height - 1) * yscale)))
			self.virtualsize = virtualsize
		else:
			self.virtualsize = (0, 0)
		self.panel.SetVirtualSize(self.virtualsize)
		self.setViewOffset()

	def setViewOffset(self):
		xv, yv = self.biggerView()
		xsize, ysize = self.virtualsize
		xclientsize, yclientsize = self.panel.GetClientSize()
		if xv:
			xoffset = (xclientsize - xsize)/2
		else:
			xoffset = 0
		if yv:
			yoffset = (yclientsize - ysize)/2
		else:
			yoffset = 0
		self.offset = (xoffset, yoffset)

	def setImageType(self, name, imagedata, **kwargs):
		if self.selectiontool is None:
			raise ValueError('No types added')
		self.selectiontool.setImage(name, imagedata, **kwargs)
		#self.setImage(imagedata, **kwargs)

	def setImage(self, imagedata, stats={}):
		stats = dict(stats)
		if isinstance(imagedata, Numeric.ArrayType):
			self.setNumericImage(imagedata, stats)
		elif isinstance(imagedata, Image.Image):
			self.setPILImage(imagedata)
			self.statspanel.set(stats)
			self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())
			self.sizer.Layout()
		elif imagedata is None:
			self.clearImage()
			self.statspanel.set(stats)
			self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())
			self.sizer.Layout()
		else:
			raise TypeError('Invalid image data type for setting image')

	def setPILImage(self, pilimage):
		if not isinstance(pilimage, Image.Image):
			raise TypeError('PIL image must be of Image.Image type')
		self.imagedata = pilimage
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		self.UpdateDrawing()

	def getScrolledCenter(self):
		x, y = self.panel.GetViewStart()
		width, height = self.panel.GetSize()
		vwidth, vheight = self.panel.GetVirtualSize()
		return (x + width/2.0)/vwidth, (y + height/2.0)/vheight

	def setScrolledCenter(self, center):
		cwidth, cheight = center
		width, height = self.panel.GetSize()
		vwidth, vheight = self.panel.GetVirtualSize()
		x = int(round(vwidth*cwidth - width/2.0))
		y = int(round(vheight*cheight - height/2.0))
		self.panel.Scroll(x, y)

	def setNumericImage(self, numericimage, stats={}):
		'''
		Set the numeric image, update bitmap, update buffer, set viewport size,
		scroll, and refresh the screen.
		'''

		if not isinstance(numericimage, Numeric.ArrayType):
			raise TypeError('Numeric image must be of Numeric.ArrayType')

		center = self.getScrolledCenter()

		self.imagedata = numericimage

		if 'min' not in stats or 'max' not in stats:
			stats['min'], stats['max'] = imagefun.minmax(self.imagedata)
		if 'mean' not in stats:
			stats['mean'] = imagefun.mean(self.imagedata)
		if 'stdev' not in stats:
			stats['stdev'] = imagefun.stdev(self.imagedata, known_mean=stats['mean'])

		self.statspanel.set(stats)
		self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())

		dflt_std = 5
		## use these...
		dflt_min = stats['mean'] - dflt_std * stats['stdev']
		dflt_max = stats['mean'] + dflt_std * stats['stdev']
		## unless they go beyond min and max of image
		dflt_min = max(dflt_min, stats['min'])
		dflt_max = min(dflt_max, stats['max'])

		value = (dflt_min, dflt_max)
		self.contrasttool.setRange((stats['min'], stats['max']), value)
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		self.setScrolledCenter(center)
		self.UpdateDrawing()
		self.sizer.Layout()
		#self.panel.Refresh()

	def clearImage(self):
		self.contrasttool.setRange(None)
		self.imagedata = None
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		self.panel.Scroll(0, 0)
		self.UpdateDrawing()

	def setImageFromMrcString(self, imagestring):
		self.setImage(Mrc.mrcstr_to_numeric(imagestring))

	def setImageFromPILString(self, imagestring):
		buffer = cStringIO.StringIO(pilimage)
		imagedata = Image.open(buffer)
		self.setImage(imagedata)
		# Memory leak?
		#buffer.close()

	# scaling functions

	def getScale(self):
		return self.scale

	def scaleImage(self, scale=None):
		'''
		If image is being compressed
		'''
		if scale is None:
			scale = self.getScale()
		if scale[0] < 1.0 or scale[1] < 1.0:
			return True
		else:
			return False

	def setScale(self, scale):
		for n in scale:
			# from one test
			if n > 128.0 or n < 0.002:
				return
		oldscale = self.getScale()
		self.scale = (float(scale[0]), float(scale[1]))
		if self.scaleImage() or self.scaleImage(oldscale):
			self.setBitmap()

		self.setVirtualSize()
		self.setBuffer()
		#xv, yv = self.biggerView()
		#if xv or yv:
		#	self.panel.Refresh()

	# utility functions

	def getValue(self, x, y):
		if x < 0 or y < 0:
			return None
		try:
			if isinstance(self.imagedata, Numeric.ArrayType):
				return self.imagedata[y, x]
			elif isinstance(self.imagedata, Image.Image):
				return self.imagedata.getpixel((x, y))
			else:
				return None
		except (IndexError, TypeError, AttributeError), e:
			return None

	def getClientCenter(self):
		center = self.panel.GetClientSize()
		return (center[0]/2, center[1]/2)

	def biggerView(self):
		size = self.virtualsize
		clientsize = self.panel.GetClientSize()
		value = [False, False]
		if size[0] < clientsize[0]:
			value[0] = True
		if size[1] < clientsize[1]:
			value[1] = True
		return tuple(value)

	def center(self, center):
		x, y = center
		xcenter, ycenter = self.getClientCenter()
		xscale, yscale = self.getScale()
		self.panel.Scroll(int(round(x * xscale - xcenter)),
											int(round(y * yscale - ycenter)))

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

	def UntoggleTools(self, tool):
		for t in self.tools:
			if t is tool:
				continue
			if t.untoggle:
				t.button.SetToggle(False)
		if tool is None:
			self.panel.SetCursor(self.defaultcursor)
		elif self.selectiontool is not None:
			for name in self.selectiontool.targets:
				if self.selectiontool.isTargeting(name):
					self.selectiontool.setTargeting(name, False)

	# eventhandlers

	def _onMotion(self, evt, dc):
		pass

	def OnMotion(self, evt):
		if self.buffer is None:
			return

		if self.scaleImage():
			xoffset, yoffset = self.offset
			width, height = self.virtualsize
			if evt.m_x < xoffset or evt.m_x > xoffset + width: 
				self.UpdateDrawing()
				return
			if evt.m_y < yoffset or evt.m_y > yoffset + height: 
				self.UpdateDrawing()
				return

		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()

		self.Draw(dc)


		for tool in self.tools:
			tool.OnMotion(evt, dc)

		self._onMotion(evt, dc)

		strings = []
		x, y = self.view2image((evt.m_x, evt.m_y))
		value = self.getValue(x, y)

		for tool in self.tools:
			string = tool.getToolTipString(x, y, value)
			if string:
				strings.append(string)
		string = self._getToolTipString(x, y, value)
		if string:
			strings.append(string)
		if strings:
			self.drawToolTip(dc, x, y, strings)

		dc.EndDrawing()

		self.paint(dc, wx.ClientDC(self.panel))
		dc.SelectObject(wx.NullBitmap)

	def _getToolTipString(self, x, y, value):
		return ''

	def _onLeftClick(self, evt):
		pass

	def OnLeftClick(self, evt):
		for tool in self.tools:
			tool.OnLeftClick(evt)
		self._onLeftClick(evt)

	def _onRightClick(self, evt):
		pass

	def OnRightClick(self, evt):
		for tool in self.tools:
			tool.OnRightClick(evt)
		self._onRightClick(evt)

	def drawToolTip(self, dc, x, y, strings):
		dc.SetBrush(wx.Brush(wx.Colour(255, 255, 220)))
		dc.SetPen(wx.Pen(wx.BLACK, 1))

		xextent = 0
		yextent = 0
		for string in strings:
			width, height, d, e = dc.GetFullTextExtent(string, wx.NORMAL_FONT)
			if width > xextent:
				xextent = width
			yextent += height

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

		#ix -= self.offset[0]
		#iy -= self.offset[1]

		x = int(round((ix + xoffset)))
		y = int(round((iy + yoffset)))

		dc.DrawRectangle(x, y, xextent + 4, yextent + 4)

		dc.SetFont(wx.NORMAL_FONT)
		for string in strings:
			dc.DrawText(string, x + 2 , y + 2)
			width, height, d, e = dc.GetFullTextExtent(string, wx.NORMAL_FONT)
			y += height

	def Draw(self, dc):
		#print 'Draw'
		#now = time.time()
		dc.BeginDrawing()
		dc.Clear()
		if self.bitmap is None:
			dc.Clear()
		else:
			bitmapdc = wx.MemoryDC()
			bitmapdc.SelectObject(self.bitmap)

			if self.scaleImage():
				xscale, yscale = (1.0, 1.0)
			else:
				xscale, yscale = self.getScale()
				dc.SetUserScale(xscale, yscale)

			xviewoffset, yviewoffset = self.panel.GetViewStart()
			xsize, ysize = self.panel.GetClientSize()

			width = self.bitmap.GetWidth()
			height = self.bitmap.GetHeight()
			dc.DestroyClippingRegion()
			dc.SetClippingRegion(0, 0, #self.offset[0], self.offset[1],
														int(round(xsize/xscale)),
														int(round(ysize/yscale)))

			dc.Blit(int(round((self.offset[0] - xviewoffset)/xscale)),
							int(round((self.offset[1] - yviewoffset)/yscale)),
							width, height, bitmapdc, 0, 0)

			dc.SetUserScale(1.0, 1.0)
			for t in self.tools:
				t.Draw(dc)
			bitmapdc.SelectObject(wx.NullBitmap)
		dc.EndDrawing()
		#print 'Drawn', time.time() - now

	def paint(self, fromdc, todc):
		xsize, ysize = self.panel.GetClientSize()
		todc.Blit(0, 0, xsize + 1, ysize + 1, fromdc, 0, 0)

	def UpdateDrawing(self):
		if self.buffer is None:
			self.panel.Refresh()
		else:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wx.ClientDC(self.panel))
			dc.SelectObject(wx.NullBitmap)

	def OnSize(self, evt):
		#self.setBitmap()
		#self.setVirtualSize()
		self.setViewOffset()
		self.setBuffer()
		#self.panel.Refresh()
		self.UpdateDrawing()
		evt.Skip()

	def OnPaint(self, evt):
		if self.buffer is None:
			evt.Skip()
		else:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wx.PaintDC(self.panel))
			dc.SelectObject(wx.NullBitmap)

	def OnLeave(self, evt):
		self.UpdateDrawing()

	def addTypeTool(self, name, **kwargs):
		if self.selectiontool is None:
			self.selectiontool = SelectionTool(self)
			self.sizer.Add(self.selectiontool, (2, 0), (1, 1),
											wx.ALIGN_CENTER|wx.ALL, 3)
		self.selectiontool.addTypeTool(name, **kwargs)
		self.sizer.SetItemMinSize(self.selectiontool, self.selectiontool.GetSize())
		self.sizer.Layout()

class ClickTool(ImageTool):
	def __init__(self, imagepanel, sizer, disable=False):
		self._disable = disable
		self._disabled = False
		bitmap = getBitmap('arrow.png')
		tooltip = 'Click Tool'
		cursor = wx.StockCursor(wx.CURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)

	def OnLeftClick(self, evt):
		if not self.button.GetToggle() or self._disabled:
			return
		if self._disable:
			self._disabled = True
		xy = self.imagepanel.view2image((evt.m_x, evt.m_y))
		idcevt = ImageClickedEvent(self.imagepanel, xy)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)

	def onImageClickDone(self, evt):
		self._disabled = False

class ClickImagePanel(ImagePanel):
	def __init__(self, parent, id, disable=False):
		ImagePanel.__init__(self, parent, id)
		self.clicktool = self.addTool(ClickTool(self, self.toolsizer, disable))
		self.Bind(EVT_IMAGE_CLICK_DONE, self.onImageClickDone)
		self.sizer.Layout()
		self.Fit()

	def onImageClickDone(self, evt):
		self.clicktool.onImageClickDone(evt)

class TypeTool(object):
	def __init__(self, parent, name, display=None, target=None, settings=None):
		self.parent = parent

		self.name = name

		self.label = wx.StaticText(parent, -1, name)

		self.bitmaps = self.getBitmaps()

		self.bitmap = wx.StaticBitmap(parent, -1, self.bitmaps['red'],
																	(self.bitmaps['red'].GetWidth(),
																		self.bitmaps['red'].GetHeight()))

		self.togglebuttons = {}

		if display is not None:
			togglebutton = self.addToggleButton('display', 'Display')
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleDisplay)

		if settings is not None:
			togglebutton = self.addToggleButton('settings', 'Settings')
			togglebutton.Bind(wx.EVT_BUTTON, self.onSettingsButton)

	def getBitmaps(self):
		return {
			'red': getBitmap('red.png'),
			'green': getBitmap('green.png'),
			'display': getBitmap('display.png'),
			'settings': getBitmap('settings.png'),
		}

	def enableToggleButton(self, toolname, enable=True):
		togglebutton = self.togglebuttons[toolname]
		if enable:
			togglebutton.SetBezelWidth(1)
		else:
			togglebutton.SetBezelWidth(0)
		togglebutton.Enable(enable)

	def addToggleButton(self, toolname, tooltip=None):
		bitmap = self.bitmaps[toolname]
		size = (24, 24)
		togglebutton = GenBitmapToggleButton(self.parent, -1, bitmap, size=size)
		togglebutton.SetBezelWidth(1)
		if tooltip is not None:
			togglebutton.SetToolTip(wx.ToolTip(tooltip))
		self.togglebuttons[toolname] = togglebutton
		return togglebutton

	def SetBitmap(self, name):
		try:
			self.bitmap.SetBitmap(self.bitmaps[name])
		except KeyError:
			raise AttributeError

	def onToggleDisplay(self, evt):
		evt = DisplayEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['display'].GetEventHandler().AddPendingEvent(evt)

	def onSettingsButton(self, evt):
		evt = SettingsEvent(evt.GetEventObject(), self.name)
		self.togglebuttons['settings'].GetEventHandler().AddPendingEvent(evt)

class TargetTypeTool(TypeTool):
	def __init__(self, parent, name, display=None, settings=None, target=None):
		self.color = display
		TypeTool.__init__(self, parent, name, display=display, settings=settings)

		self.targettype = TargetType(self.name, self.color)

		self.togglebuttons['display'].SetBitmapDisabled(self.bitmaps['display'])

		if target is not None:
			togglebutton = self.addToggleButton('target', 'Add Targets')
			self.enableToggleButton('target', False)
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleTarget)

	def getBitmaps(self):
		bitmaps = TypeTool.getBitmaps(self)
		bitmaps['display'] = getTargetIconBitmap(self.color)
		bitmaps['target'] = getBitmap('arrow.png')
		return bitmaps

	def onToggleTarget(self, evt):
		if not self.togglebuttons['target'].IsEnabled():
			self.togglebuttons['target'].SetValue(False)
			return
		evt = TargetingEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['target'].GetEventHandler().AddPendingEvent(evt)

class SelectionTool(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1, style=wx.SIMPLE_BORDER)
		self.SetBackgroundColour(wx.Colour(255, 255, 220))

		self.parent = parent

		self.sz = wx.GridBagSizer(3, 3)
		self.sz.AddGrowableCol(1)
		self.sz.SetEmptyCellSize((0, 24))

		self.order = []
		self.tools = {}
		self.images = {}
		self.targets = {}

		self.SetSizerAndFit(self.sz)

	def _addTypeTool(self, typetool):
		n = len(self.tools)
		self.sz.Add(typetool.bitmap, (n, 0), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add(typetool.label, (n, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		if 'display' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['display'], (n, 2), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['display'].Bind(EVT_DISPLAY, self.onDisplay)
		if 'target' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['target'], (n, 3), (1, 1), wx.ALIGN_CENTER)
			self.targets[typetool.name] = None
			typetool.togglebuttons['target'].Bind(EVT_TARGETING, self.onTargeting)
		else:
			self.images[typetool.name] = None
		if 'settings' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['settings'], (n, 4), (1, 1), wx.ALIGN_CENTER)

	def addTypeTool(self, name, toolclass=TypeTool, **kwargs):
		if name in self.tools:
			raise ValueError('Type \'%s\' already exists' % name)
		typetool = toolclass(self, name, **kwargs)
		self._addTypeTool(typetool)
		self.order.append(name)
		self.tools[name] = typetool
		self.sz.Layout()
		self.Fit()

	def hasType(self, name):
		if name in self.tools:
			return True
		else:
			return False

	def _getTypeTool(self, name):
		try:
			return self.tools[name]
		except KeyError:
			raise ValueError('No type \'%s\' added' % name)

	def isDisplayed(self, name):
		tool = self._getTypeTool(name)
		try:
			return tool.togglebuttons['display'].GetValue()
		except KeyError:
			return True

	def setDisplayed(self, name, value):
		tool = self._getTypeTool(name)
		try:
			tool.togglebuttons['display'].SetValue(value)
		except KeyError:
			raise AttributeError
		self._setDisplayed(name, value)

	def _setDisplayed(self, name, value):
		tool = self._getTypeTool(name)
		if isinstance(tool, TargetTypeTool):
			if value:
				targets = self.getTargets(name)
			else:
				targets = None
			self.parent.setDisplayedTargets(tool.targettype, targets)
			if not value and self.isTargeting(name):
				self.setTargeting(name, False)
		else:
			for n in self.images:
				if n == name:
					continue
				tool = self._getTypeTool(n)
				try:
					tool.togglebuttons['display'].SetValue(False)
				except KeyError:
					pass
			if value:
				image = self.images[name]
				self.parent.setImage(image)
			else:
				self.parent.setImage(None)

	def onDisplay(self, evt):
		self._setDisplayed(evt.name, evt.value)

	def setImage(self, name, image):
		tool = self._getTypeTool(name)
		if image is None:
			tool.SetBitmap('red')
		else:
			tool.SetBitmap('green')
		self.images[name] = image
		if self.isDisplayed(name):
			self.parent.setImage(image)

	def getTargets(self, name):
		return self._getTypeTool(name).targettype.getTargets()

	def addTarget(self, name, x, y):
		tool = self._getTypeTool(name)
		tool.targettype.addTarget(x, y)
		if self.isDisplayed(name):
			# ...
			targets = tool.targettype.getTargets()
			self.parent.setDisplayedTargets(tool.targettype, targets)

	def insertTarget(self, name, pos, x, y):
		tool = self._getTypeTool(name)
		tool.targettype.insertTarget(pos, x, y)
		if self.isDisplayed(name):
			# ...
			targets = tool.targettype.getTargets()
			self.parent.setDisplayedTargets(tool.targettype, targets)

	def deleteTarget(self, target):
		name = target.type.name
		tool = self._getTypeTool(name)
		tool.targettype.deleteTarget(target)
		if self.isDisplayed(name):
			# ...
			targets = tool.targettype.getTargets()
			self.parent.setDisplayedTargets(tool.targettype, targets)

	def setTargets(self, name, targets):
		tool = self._getTypeTool(name)
		tool.targettype.setTargets(targets)
		if self.isDisplayed(name):
			self.parent.setDisplayedTargets(tool.targettype, tool.targettype.targets)
		if targets is None:
			#if self.isTargeting(name):
			#	self.setTargeting(name, False)
			if 'target' in tool.togglebuttons:
				tool.enableToggleButton('target', False)
			tool.SetBitmap('red')
		else:
			if 'target' in tool.togglebuttons:
				tool.enableToggleButton('target', True)
			tool.SetBitmap('green')
		if 'target' in tool.togglebuttons:
			tool.togglebuttons['target'].Refresh()

	def getTargetPositions(self, name):
		return self._getTypeTool(name).targettype.getTargetPositions()

	def isTargeting(self, name):
		tool = self._getTypeTool(name)
		return tool.togglebuttons['target'].GetValue()

	def _setTargeting(self, name, value):
		tool = self._getTypeTool(name)

		if value and tool.targettype.getTargets() is None:
			raise ValueError('Cannot set targetting when targets is None')

		for n in self.targets:
			if n == name:
				continue
			t = self._getTypeTool(n)
			try:
				t.togglebuttons['target'].SetValue(False)
			except KeyError:
				pass

		if value and not self.isDisplayed(name):
			self.setDisplayed(name, True)

		if value:
			self.parent.selectedtype = tool.targettype
		else:
			self.parent.selectedtype = None

		if value:
			self.parent.UntoggleTools(None)

	def onTargeting(self, evt):
		self._setTargeting(evt.name, evt.value)

	def setTargeting(self, name, value):
		tool = self._getTypeTool(name)
		try:
			tool.togglebuttons['target'].SetValue(value)
		except KeyError:
			pass
		self._setTargeting(name, value)

class Target(object):
	def __init__(self, x, y, type):
		self.position = (x, y)
		self.x = x
		self.y = y
		self.type = type

class TargetType(object):
	def __init__(self, name, color):
		self.name = name
		self.bitmaps = {}
		self.bitmaps['default'], self.bitmaps['selected'] = getTargetBitmaps(color)
		self.targets = None

	def getTargets(self):
		if self.targets is None:
			return None
		return list(self.targets)

	def addTarget(self, x, y):
		target = Target(x, y, self)
		self.targets.append(target)

	def insertTarget(self, pos, x, y):
		target = Target(x, y, self)
		self.targets.insert(pos, target)

	def deleteTarget(self, target):
		if target not in self.targets:
			raise ValueError('Target not in targets')
		self.targets.remove(target)

	def setTargets(self, targets):
		self.targets = map(lambda (x, y): Target(x, y, self), targets)

	def getTargetPositions(self):
		if self.targets is None:
			return []
		return map(lambda t: t.position, self.targets)

class TargetImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		ImagePanel.__init__(self, parent, id)
		self.order = []
		self.targets = {}
		self.selectedtype = None
		self.selectedtarget = None

	def _getSelectionTool(self):
		if self.selectiontool is None:
			raise ValueError('No types added')
		return self.selectiontool

	def addTargetTool(self, name, color, **kwargs):
		kwargs['display'] = color
		kwargs['toolclass'] = TargetTypeTool
		self.addTypeTool(name, **kwargs)

	def getTargets(self, name):
		return self._getSelectionTool().getTargets(name)

	def addTarget(self, name, x, y):
		return self._getSelectionTool().addTarget(name, x, y)

	def insertTarget(self, name, pos, x, y):
		return self._getSelectionTool().insertTarget(name, pos, x, y)

	def deleteTarget(self, target):
		return self._getSelectionTool().deleteTarget(target)

	def setTargets(self, name, targets):
		return self._getSelectionTool().setTargets(name, targets)

	def getTargetPositions(self, name):
		return self._getSelectionTool().getTargetPositions(name)

	def setDisplayedTargets(self, type, targets):
		if targets is None:
			if type in self.targets:
				del self.targets[type]
				self.order.remove(type)
		else:
			targets = list(targets)
			for t in targets:
				if not isinstance(t, Target):
					raise TypeError
			self.targets[type] = targets
			if type not in self.order:
				self.order.append(type)
		self.UpdateDrawing()

	def _drawTargets(self, dc, bitmap, targets, scale):
		memorydc = wx.MemoryDC()
		memorydc.BeginDrawing()
		memorydc.SelectObject(bitmap)

		width = bitmap.GetWidth()
		height = bitmap.GetHeight()
		if self.scaleImage():
			xscale, yscale = (1.0, 1.0)
		else:
			xscale, yscale = self.getScale()
			dc.SetUserScale(xscale, yscale)

		halfwidth = width/2.0
		halfheight = height/2.0

		xv, yv = self.biggerView()

		for target in targets:
			x, y = self.image2view((target.x, target.y))
			dc.Blit(int(round(x/xscale - halfwidth)),
							int(round(y/xscale - halfheight)),
							width, height,
							memorydc, 0, 0,
							wx.COPY, True)

		dc.SetUserScale(1.0, 1.0)
		memorydc.SelectObject(wx.NullBitmap)
		memorydc.EndDrawing()

	def drawTargets(self, dc):
		scale = self.getScale()

		for type in self.order:
			targets = self.targets[type]
			if targets:
				self._drawTargets(dc, type.bitmaps['default'], targets, scale)

		if self.selectedtarget is not None:
			if self.selectedtarget.type in self.targets:
				bitmap = self.selectedtarget.type.bitmaps['selected']
				self._drawTargets(dc, bitmap, [self.selectedtarget], scale)

	def Draw(self, dc):
		ImagePanel.Draw(self, dc)
		dc.BeginDrawing()
		self.drawTargets(dc)
		dc.EndDrawing()

	def _onLeftClick(self, evt):
		if self.selectedtype is not None:
			x, y = self.view2image((evt.m_x, evt.m_y))
			self.addTarget(self.selectedtype.name, x, y)

	def _onRightClick(self, evt):
		if self.selectedtarget is not None:
			self.deleteTarget(self.selectedtarget)

	def closestTarget(self, type, x, y):
		minimum_magnitude = 10

		if self.scaleImage():
			xscale, yscale = self.getScale()
			minimum_magnitude /= xscale

		closest_target = None
		for target in self.targets[type]:
			magnitude = math.hypot(x - target.x, y - target.y)
			if magnitude < minimum_magnitude:
				minimum_magnitude = magnitude
				closest_target = target

		return closest_target

	def _onMotion(self, evt, dc):
		ImagePanel._onMotion(self, evt, dc)
		if self.selectedtype is not None:
			viewoffset = self.panel.GetViewStart()
			x, y = self.view2image((evt.m_x, evt.m_y))
			self.selectedtarget = self.closestTarget(self.selectedtype, x, y)
		else:
			self.selectedtarget = None

	def _getToolTipString(self, x, y, value):
		string = ImagePanel._getToolTipString(self, x, y, value)
		selectedtarget = self.selectedtarget
		if selectedtarget is not None:
			name = selectedtarget.type.name
			position = selectedtarget.position
			string += name + ' ' + str(position)
		return string

if __name__ == '__main__':
	import sys

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

#			self.panel = ImagePanel(frame, -1)

#			self.panel = ClickImagePanel(frame, -1)
#			self.panel.Bind(EVT_IMAGE_CLICKED,
#							lambda e: self.panel.setImage(self.panel.imagedata))

			self.panel = TargetImagePanel(frame, -1)
			self.panel.addTypeTool('Target Practice', toolclass=TargetTypeTool, display=wx.RED, target=True)
			self.panel.setTargets('Target Practice', [])

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		app.panel.setImage(None)
	elif filename[-4:] == '.mrc':
		#app.panel.setImageFromMrcString(
		image = Mrc.mrcstr_to_numeric(open(filename, 'rb').read())
		app.panel.setImage(image)
	else:
		app.panel.setImage(Image.open(filename))
	app.MainLoop()

