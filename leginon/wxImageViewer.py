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
import Numeric
import wx
from wx.lib.buttons import GenBitmapToggleButton
import NumericImage
import Image
import ImageOps
import imagefun
import sys, os
import numextension

wx.InitAllImageHandlers()

toolbitmaps = {}

def getToolBitmap(filename):
	try:
		return toolbitmaps[filename]
	except KeyError:
		rundir = sys.path[0]
		iconpath = os.path.join(rundir, 'icons', filename)
		wximage = wx.Image(iconpath)
		bitmap = wx.BitmapFromImage(wximage)
		bitmap.SetMask(wx.MaskColour(bitmap, wx.WHITE))
		toolbitmaps[filename] = bitmap
		return bitmap

class ContrastTool(object):
	def __init__(self, imagepanel, sizer):
		self.imagepanel = imagepanel
		self.imagemin = 0
		self.imagemax = 0
		self.contrastmin = 0
		self.contrastmax = 0
		self.slidermin = 0
		self.slidermax = 100
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
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.minslider, 0, wx.ALIGN_BOTTOM, 0)
		self.sizer.Add(self.maxslider, 0, wx.ALIGN_TOP, 0)
		sizer.Add(self.sizer, 0, wx.ALIGN_CENTER|wx.ALL, 0)

	def updateNumericImage(self):
		self.imagepanel.setBitmap()
		self.imagepanel.setBuffer()
		self.imagepanel.UpdateDrawing()

	def getRange(self):
		return self.contrastmin, self.contrastmax

	def getScaledValue(self, position):
		return (self.imagemax - self.imagemin)*(position - self.slidermin)/(self.slidermax - self.slidermin) + self.imagemin

	def setRange(self, range):
		self.imagemin = range[0]
		self.imagemax = range[1]
		self.contrastmin = self.getScaledValue(self.minslider.GetValue())
		self.contrastmax = self.getScaledValue(self.maxslider.GetValue())

	def onMinSlider(self, evt):
		contrastmin = self.getScaledValue(evt.GetPosition())
		if contrastmin > self.contrastmax:
			self.contrastmin = self.contrastmax
			self.minslider.SetValue(self.maxslider.GetValue())
		else:
			self.contrastmin = contrastmin
		self.updateNumericImage()

	def onMaxSlider(self, evt):
		contrastmax = self.getScaledValue(evt.GetPosition())
		if contrastmax < self.contrastmin:
			self.contrastmax = self.contrastmin
			self.maxslider.SetValue(self.minslider.GetValue())
		else:
			self.contrastmax = contrastmax
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
		bitmap = getToolBitmap('valuetool.bmp')
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
		bitmap = getToolBitmap('rulertool.bmp')
		tooltip = 'Toggle Ruler Tool'
		cursor = wx.CROSS_CURSOR
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
		dc.SetPen(wx.Pen(wx.RED, 1))
		x0, y0 = self.imagepanel.image2view(self.start)
		x0 -= self.imagepanel.offset[0]
		y0 -= self.imagepanel.offset[1]
		dc.DrawLine((x0, y0), (x, y))

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
		bitmap = getToolBitmap('zoomtool.bmp')
		tooltip = 'Toggle Zoom Tool'
		cursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.zoomlevels = range(7, -8, -1)
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
		self.imagepanel.UpdateDrawing()

class ImagePanel(wx.Panel):
	def __init__(self, parent, id, imagesize=(512, 512)):
		# initialize image variables
		self.imagedata = None
		self.bitmap = None
		self.buffer = None

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
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetAutoLayout(True)
		self.SetSizer(self.sizer)

		# create tool size to contain individual tools
		self.toolsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer.Add(self.toolsizer)
		self.tools = []

		# create image panel, set cursor
		self.panel = wx.ScrolledWindow(self, -1, size=self.imagesize)
		self.panel.SetScrollRate(1, 1)
		self.defaultcursor = wx.CROSS_CURSOR
		self.panel.SetCursor(self.defaultcursor)
		self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
		width, height = self.panel.GetSizeTuple()
		self.sizer.SetItemMinSize(self.panel, width, height)

		# bind panel events
		self.panel.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
		self.panel.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDoubleClick)
		self.panel.Bind(wx.EVT_RIGHT_DCLICK, self.OnRightDoubleClick)
		self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
		self.panel.Bind(wx.EVT_SIZE, self.OnSize)
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.panel.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

		# add tools
		self.addTool(ValueTool(self, self.toolsizer))
		self.addTool(RulerTool(self, self.toolsizer))
		self.addTool(ZoomTool(self, self.toolsizer))

		self.contrasttool = ContrastTool(self, self.toolsizer)

		self.Fit()

	def addTool(self, tool):
		self.tools.append(tool)

	# image set functions

	def setBitmap(self):
		'''
		Set the internal wx.Bitmap to current Numeric image
		'''
		if isinstance(self.imagedata, Numeric.arraytype):
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
			width = int(wximage.GetWidth()*xscale)
			height = int(wximage.GetHeight()*yscale)
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
			bitmapwidth = self.bitmap.GetWidth()
			bitmapheight = self.bitmap.GetHeight()
			clientwidth, clientheight = self.panel.GetClientSize()

			xscale, yscale = self.scale
			if not self.scaleImage():
				bitmapwidth = int(bitmapwidth * xscale)
				bitmapheight = int(bitmapheight * yscale)

			if bitmapwidth < clientwidth:
				width = bitmapwidth
			else:
				width = clientwidth

			if bitmapheight < clientheight:
				height = bitmapheight
			else:
				height = clientheight

			self.buffer = wx.EmptyBitmap(width, height)

	def setVirtualSize(self):
		'''
		Set size of viewport and offset for scrolling if image is bigger than view
		'''
		self.panel.SetVirtualSize((0, 0))
		if self.bitmap is not None:
			width, height = self.bitmap.GetWidth(), self.bitmap.GetHeight()
			if self.scaleImage():
				virtualsize = (width - 1, height - 1)
			else:
				xscale, yscale = self.getScale()
				virtualsize = (int((width - 1) * xscale), int((height - 1) * yscale))
			self.panel.SetVirtualSize(virtualsize)
			self.virtualsize = virtualsize
		else:
			self.virtualsize = (0, 0)

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

	def setImage(self, imagedata, scroll=False):
		if isinstance(imagedata, Numeric.arraytype):
			self.setNumericImage(imagedata, scroll)
		elif isinstance(imagedata, Image.Image):
			self.setPILImage(imagedata, scroll)
		elif imagedata is None:
			self.clearImage()
		else:
			raise TypeError('Invalid image data type for setting image')

	def setPILImage(self, pilimage, scroll=False):
		if not isinstance(pilimage, Image.Image):
			raise TypeError('PIL image must be of Image.Image type')
		self.imagedata = pilimage
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		if not scroll:
			self.panel.Scroll(0, 0)
		self.UpdateDrawing()

	def setNumericImage(self, numericimage, scroll=False):
		'''
		Set the numeric image, update bitmap, update buffer, set viewport size,
		scroll, and refresh the screen.
		'''

		if not isinstance(numericimage, Numeric.arraytype):
			raise TypeError('Numeric image must be of Numeric.arraytype')

		self.imagedata = numericimage
		#self.imagerange = imagefun.minmax(self.imagedata)
		mean = imagefun.mean(self.imagedata)
		stdev = imagefun.stdev(self.imagedata, known_mean=mean)
		self.imagerange = (mean - 3*stdev, mean + 3*stdev)
		self.contrasttool.setRange(self.imagerange)
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		if not scroll:
			self.panel.Scroll(0, 0)
		self.UpdateDrawing()
		self.panel.Refresh()

	def clearImage(self):
		self.imagedata = None
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		self.panel.Scroll(0, 0)
		self.UpdateDrawing()

	def setImageFromMrcString(self, imagestring, scroll=False):
		self.setImage(Mrc.mrcstr_to_numeric(imagestring), scroll)

	def setImageFromPILString(self, imagestring, scroll=False):
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
		xv, yv = self.biggerView()
		if xv or yv:
			self.panel.Refresh()

	# utility functions

	def getValue(self, x, y):
		try:
			if isinstance(self.imagedata, Numeric.arraytype):
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
		self.panel.Scroll(int(x * xscale - xcenter), int(y * yscale - ycenter))

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

		strings = []
		x, y = self.view2image((evt.m_x, evt.m_y))
		value = self.getValue(x, y)

		for tool in self.tools:
			string = tool.getToolTipString(x, y, value)
			if string:
				strings.append(string)
		if strings:
			self.drawToolTip(dc, x, y, strings)

		dc.EndDrawing()

		self.paint(dc, wx.ClientDC(self.panel))
		dc.SelectObject(wx.NullBitmap)

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

		ix -= self.offset[0]
		iy -= self.offset[1]

		x = int(round((ix + xoffset)))
		y = int(round((iy + yoffset)))

		dc.DrawRectangle((x, y), (xextent + 4, yextent + 4))

		dc.SetFont(wx.NORMAL_FONT)
		for string in strings:
			dc.DrawText(string, (x + 2 , y + 2))
			width, height, d, e = dc.GetFullTextExtent(string, wx.NORMAL_FONT)
			y += height

	def Draw(self, dc):
		dc.BeginDrawing()
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

			dc.Blit((0, 0), (int(xsize/xscale + xscale), int(ysize/yscale + yscale)),
							bitmapdc, (int(xviewoffset/xscale), int(yviewoffset/yscale)))
			bitmapdc.SelectObject(wx.NullBitmap)
		dc.EndDrawing()
		dc.SetUserScale(1.0, 1.0)

	def paint(self, fromdc, todc):
		xsize, ysize = self.panel.GetClientSize()
		todc.Blit(self.offset, (xsize + 1, ysize + 1), fromdc, (0, 0))

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
		self.setVirtualSize()
		self.setBuffer()
		#self.UpdateDrawing()

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

class ClickTool(ImageTool):
	def __init__(self, imagepanel, sizer, callback=None):
		bitmap = getToolBitmap('arrowtool.bmp')
		tooltip = 'Click Tool'
		cursor = wx.StockCursor(wx.CURSOR_BULLSEYE)
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
		self.sizer.Layout()
		self.Fit()

class TargetTool(ImageTool):
	def __init__(self, imagepanel, sizer, callback=None):
		bitmap = getToolBitmap('targettool.bmp')
		tooltip = 'Toggle Target Tool'
		cursor = wx.StockCursor(wx.CURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.callback = callback
		self.target_type = None
		self.combobox = None

	def getTargetType(self):
		return self.target_type

	def setTargetType(self, name):
		self.target_type = name
		self.setTargetButtonBitmap()

	def addTargetType(self, name):
		if self.getTargetType is None:
			self.setTargetType(name)
		self.addComboBox(name)

	def deleteTargetType(self, name):
		self.deleteComboBox(name)

	def OnToggle(self, value):
		if not value:
			self.imagepanel.closest_target = None
			self.imagepanel.UpdateDrawing()

	def setTargetButtonBitmap(self):
		bitmap = wx.EmptyBitmap(16, 16)
		dc = wx.MemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		color = self.imagepanel.target_types[self.target_type].getColor()
		dc.SetPen(wx.Pen(color, 2))
		dc.DrawLine((8, 0), (8, 15))
		dc.DrawLine((0, 8), (15, 8))
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		bitmap.SetMask(wx.MaskColour(bitmap, wx.WHITE))
		self.button.SetBitmapLabel(bitmap, False)
		self.button.Refresh()

	def OnComboBoxSelect(self, evt):
		self.setTargetType(evt.GetString())

	def addComboBox(self, name):
		if self.combobox is None:
			if len(self.imagepanel.target_types) > 1:
				self.combobox = wx.Choice(self.imagepanel, -1,
																		choices=self.imagepanel.target_types.keys())
				self.combobox.SetStringSelection(self.target_type)
				self.combobox.Bind(wx.EVT_CHOICE, self.OnComboBoxSelect)
				self.sizer.Add(self.combobox, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 3)
				self.sizer.Layout()
			elif len(self.imagepanel.target_types) == 1:
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
				self.button.Bind(wx.EVT_BUTTON, None)
				self.sizer.Remove(self.button)
				self.sizer.Layout()
				self.target_type = None

	def OnLeftClick(self, evt):
		if self.button.GetToggle() and self.target_type is not None:
			x, y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			target = self.imagepanel.addTarget(self.target_type, x, y)
			if callable(self.callback):
				name = target.target_type.getName()
				targets = self.imagepanel.getTargetTypeValue(name)
				self.callback(target.target_type.getName(), targets)

	def OnRightClick(self, evt):
		selectedtarget = self.imagepanel.getSelectedTarget()
		if self.button.GetToggle() and selectedtarget is not None:
			target_type, value = self.imagepanel.deleteTarget(selectedtarget)
			if callable(self.callback):
				self.callback(target_type, value)

	def closestTarget(self, x, y):
		minimum_magnitude = 10

		if self.imagepanel.scaleImage():
			xscale, yscale = self.imagepanel.getScale()
			minimum_magnitude /= xscale

		closest_target = None
		for target in self.imagepanel.getTargets():
			tx, ty = target.getPosition()
			magnitude = math.sqrt((x - tx)**2 + (y - ty)**2)
			if magnitude < minimum_magnitude:
				minimum_magnitude = magnitude
				closest_target = target

		return closest_target

	def OnMotion(self, evt, dc):
		if self.button.GetToggle():
			viewoffset = self.imagepanel.panel.GetViewStart()
			x, y = self.imagepanel.view2image((evt.m_x, evt.m_y))
			self.imagepanel.setSelectedTarget(self.closestTarget(x, y))

	def getToolTipString(self, x, y, value):
		selectedtarget = self.imagepanel.getSelectedTarget()
		if selectedtarget is not None:
			name = selectedtarget.target_type.getName()
			position = selectedtarget.getPosition()
			return name + ' ' + str(position)
		else:
			return ''

class Target(object):
	def __init__(self, x, y, target_type=None):
		self.setPosition(x, y)
		self.target_type = target_type

	def getPosition(self):
		return self.x, self.y

	def setPosition(self, x, y):
		self.x = x
		self.y = y

	def getTargetType(self):
		return self.target_type

	def setTargetType(self, target_type):
		self.target_type = target_type

class TargetType(object):
	def __init__(self, name, color):
		self.targets = []
		self.bitmaps = {}
		self.setName(name)
		self.setColor(color)

	def getTargets(self):
		return self.targets

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getColor(self):
		return self.color

	def setColor(self, color):
		self.color = color
		self.setBitmaps(self.color)

	def addTarget(self, target):
		if target in self.targets:
			raise ValueError('cannot add target, target already exists')
		if target.target_type != self:
			if target.target_type is not None:
				target.target_type.removeTarget(target)
			target.setTargetType(self)
			self.targets.append(target)

	def removeTarget(self, target):
		if target not in self.targets:
			raise ValueError('cannot remove target, no such target')
		target.setTargetType(None)
		self.targets.remove(target)

	def clearTargets(self):
		for target in self.targets:
			target.setTargetType(None)
		self.targets = []

	def getTargetPositions(self):
		targetpositions = []
		for target in self.targets:
			targetpositions.append(target.getPosition())
		return targetpositions

	def getBitmap(self, name):
		try:
			return self.bitmaps[name]
		except KeyError:
			raise ValueError('no such bitmap')

	def getDefaultBitmap(self):
		return self.getBitmap('default')

	def getSelectedBitmap(self):
		return self.getBitmap('selected')

	def makeBitmap(self, color):
		penwidth = 1
		length = 15
		bitmap = wx.EmptyBitmap(length, length)
		dc = wx.MemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
		dc.SetPen(wx.Pen(color, penwidth))
		dc.DrawLine((length/2, 0), (length/2, length))
		dc.DrawLine((0, length/2), (length, length/2))
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		bitmap.SetMask(wx.MaskColour(bitmap, wx.WHITE))
		return bitmap

	def setBitmaps(self, color):
		default = self.makeBitmap(color)
		self.bitmaps['default'] = default

		selectedcolor = wx.Color(color.Red()/2, color.Green()/2, color.Blue()/2)
		selected = self.makeBitmap(selectedcolor)
		self.bitmaps['selected'] = selected

class TargetImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None):
		ImagePanel.__init__(self, parent, id)

		self.target_types = {}
		self.selectedtarget = None
		self.colorlist = [wx.RED, wx.BLUE, wx.Color(255, 0, 255), wx.Color(0, 255, 255)]

		self.addTool(TargetTool(self, self.toolsizer, callback))
		self.sizer.Layout()
		self.Fit()

	def addTargetTypeColor(self, color):
		self.colorlist.append(color)

	def removeTargetTypeColor(self):
		try:
			color = self.colorlist[0]
			del self.colorlist[0]
		except IndexError:
			raise RuntimeError('Not enough colors for addition target types')
		return color

	def addTargetType(self, name, color=None):
		if name in self.target_types:
			raise ValueError('Target type already exists')
		if color is None:
			wx.color = self.removeTargetTypeColor()
		else:
			wx.color = wx.Color(*color)
		self.target_types[name] = TargetType(name, wx.color)

		for tool in self.tools:
			if hasattr(tool, 'addTargetType'):
				tool.addTargetType(name)

	def deleteTargetType(self, name):
		try:
			target_type = self.target_types[name]
		except KeyError:
			raise ValueError('No such target type')
		color = target_type.color
		del self.target_types[name]
		self.addTargetTypeColor(color)

		for tool in self.tools:
			if hasattr(tool, 'addTargetType'):
				tool.deleteTargetType(name)

	# compat function
	def getTargetTypeValue(self, name):
		try:
			return self.target_types[name].getTargetPositions()
		except KeyError:
			raise ValueError('No such target type')

	# compat function
	def setTargetTypeValue(self, name, value, color=None):
		if name not in self.target_types:
			self.addTargetType(name, color)
		else:
			self.target_types[name].clearTargets()
		for position in value:
			x, y = position
			self.addTarget(name, x, y)

		self.UpdateDrawing()

	def addTarget(self, name, x, y):
		if name not in self.target_types:
			raise ValueError('No such target type to add target')
		target = Target(x, y)
		self.target_types[name].addTarget(target)
		self.UpdateDrawing()
		return target

	def deleteTarget(self, target):
		target_type = target.target_type
		if target_type in self.target_types.values():
			target_type.removeTarget(target)
		else:
			raise ValueError('Target\'s target type does not exist')
		if self.getSelectedTarget() == target:
			self.setSelectedTarget(None)
		self.UpdateDrawing()

		return target_type.getName(), target_type.getTargetPositions()

	def clearTargets(self):
		for target_type in self.target_types.values():
			target_type.clearTargets()
		self.UpdateDrawing()

	def getTargets(self):
		targetlist = []
		for target_type in self.target_types.values():
			targetlist += target_type.getTargets()
		return targetlist

	def getSelectedTarget(self):
		return self.selectedtarget

	def setSelectedTarget(self, target):
		if target is not None:
			if target not in self.getTargets():
				raise ValueError('no such target')
		self.selectedtarget = target

	def getTargetBitmap(self, target):
		for target_type in self.targets:
			if target in self.targets[target_type]:
				# temp
				for tool in self.tools:
					if hasattr(tool, 'closest_target'):
						if target == tool.closest_target:
							return self.targetbitmaps[target_type]['selected']
				return self.targetbitmaps[target_type]['default']

	def drawTarget(self, dc, target):
		if target_type not in self.target_types.values():
			return

		if target == self.getSelectedTarget():
			bitmap = target.target_type.getSelectedBitmap()
		else:
			bitmap = target.target_type.getDefaultBitmap()

		memorydc = wx.MemoryDC()
		memorydc.SelectObject(bitmap)
		width = bitmap.GetWidth()
		height = bitmap.GetHeight()

		xscale, yscale = self.getScale()
		position = target.getPosition()
		xv, yv = self.biggerView()
		nx, ny = self.image2view(position)
		if xv:
			x = position[0] * xscale
		else:
			x = nx
		if yv:
			y = position[1] * yscale
		else:
			y = ny

		if not self.scaleImage():
			memorydc.SetUserScale(1.0/xscale, 1.0/yscale)
			width *= xscale
			height *= yscale

		dc.Blit(int(x - width/2), int(y - height/2), int(width), int(height),
						memorydc, 0, 0, wx.COPY, True)

		memorydc.SelectObject(wx.NullBitmap)

	def drawTargets(self, dc):
		xscale, yscale = self.getScale()
		memorydc = wx.MemoryDC()

		for target in self.getTargets():

			if target == self.getSelectedTarget():
				bitmap = target.target_type.getSelectedBitmap()
			else:
				bitmap = target.target_type.getDefaultBitmap()

			position = target.getPosition()
			xv, yv = self.biggerView()
			nx, ny = self.image2view(position)
			if xv:
				x = position[0] * xscale
			else:
				x = nx
			if yv:
				y = position[1] * yscale
			else:
				y = ny

			#memorydc.Clear()
			memorydc.SelectObject(bitmap)
			width = bitmap.GetWidth()
			height = bitmap.GetHeight()

			if not self.scaleImage():
				memorydc.SetUserScale(1.0/xscale, 1.0/yscale)
				width *= xscale
				height *= yscale

			dc.Blit((int(x - width/2), int(y - height/2)),
							(int(width), int(height)), memorydc, (0, 0), wx.COPY, True)

			memorydc.SelectObject(wx.NullBitmap)

	def Draw(self, dc):
		ImagePanel.Draw(self, dc)
		dc.BeginDrawing()
		self.drawTargets(dc)
		dc.EndDrawing()

if __name__ == '__main__':
	import sys

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

#	def bar(xy):
#		print xy

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			self.panel = TargetImagePanel(frame, -1)
			self.panel.addTargetType('foo')
			self.panel.addTargetType('bar')

#			self.panel = ClickImagePanel(frame, -1, bar)

#			self.panel = ImagePanel(frame, -1)

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		app.panel.setImage(None)
	elif filename[-4:] == '.mrc':
		app.panel.setImageFromMrcString(open(filename, 'rb').read())
	else:
		app.panel.setImage(Image.open(filename))
	app.MainLoop()

