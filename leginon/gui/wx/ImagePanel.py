#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/ImagePanel.py,v $
# $Revision: 1.9 $
# $Name: not supported by cvs2svn $
# $Date: 2008-01-18 04:58:49 $
# $Author: acheng $
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
from pyami import mrc, arraystats
import numpy
import wx
import sys
import Image
import leginon.gui.wx.Stats
import ImagePanelTools
import SelectionTool
import leginon.icons
#import time

wx.InitAllImageHandlers()

ImageClickDoneEventType = wx.NewEventType()
EVT_IMAGE_CLICK_DONE = wx.PyEventBinder(ImageClickDoneEventType)

class ImageClickDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ImageClickDoneEventType, source.GetId())
		self.SetEventObject(source)

##################################
##
##################################

class ImagePanel(wx.Panel):
	def __init__(self, parent, id, imagesize=(520, 520), mode="horizontal"):
		# initialize image variables
		self.imagedata = None
		self.bitmap = None
		self.buffer = None
		self.colormap = None
		self.selectiontool = None
		self.mode = mode
		self.drawlast = False
		self.movecount = 0
		self.parent = parent

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
		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.SetEmptyCellSize((0, 0))

		# create tool size to contain individual tools
		self.toolsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.toolsizer2 = wx.BoxSizer(wx.HORIZONTAL)
		self.alltoolsizer =wx.GridBagSizer(5,5)
		
		# use compact mode if imagesize is too small
		if imagesize[0] < 512:
			toolmode = "compact"
		else:
			toolmode = "expand"
		
		if toolmode == "compact":
			self.alltoolsizer.Add(self.toolsizer, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.alltoolsizer.Add(self.toolsizer2, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		else:
			self.alltoolsizer.Add(self.toolsizer, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.alltoolsizer.Add(self.toolsizer2, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
				
		if self.mode == "vertical":
			self.sizer.Add(self.alltoolsizer, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		else:
			self.sizer.Add(self.alltoolsizer, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.tools = []

		# create image panel, set cursor
		self.panel = wx.ScrolledWindow(self, -1, style=wx.SIMPLE_BORDER|wx.EXPAND)
		#self.panel.SetBackgroundColour(wx.Colour(216, 191, 216))
		#self.panel.SetMinSize(self.imagesize)
		self.panel.SetBackgroundColour(wx.WHITE)
		self.panel.SetScrollRate(1, 1)
		try:
			cursorfile = leginon.icons.getPath('picker.png')
			self.defaultcursor = wx.Cursor(cursorfile, wx.BITMAP_TYPE_PNG, 16, 16)
		except:
			self.defaultcursor = wx.CROSS_CURSOR
		self.panel.SetCursor(self.defaultcursor)
		if self.mode == "vertical":
			self.sizer.Add(self.panel, (1, 0), (1, 1), wx.EXPAND) 
			self.sizer.AddGrowableRow(1)
			self.sizer.AddGrowableCol(0)
		else:
			self.sizer.Add(self.panel, (1, 1), (1, 1), wx.EXPAND)
			self.sizer.AddGrowableRow(1)
			self.sizer.AddGrowableCol(1)
		width, height = self.panel.GetSizeTuple()
		width,height = imagesize
		self.sizer.SetItemMinSize(self.panel, width, height)
		
		self.statstypesizer =wx.GridBagSizer(2,2)
		self.statstypesizer.SetEmptyCellSize((50, 50))
		self.statspanel = leginon.gui.wx.Stats.Stats(self, -1, style=wx.SIMPLE_BORDER)
		if self.mode == "vertical":
			self.statstypesizer.Add(self.statspanel, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)
			self.sizer.Add(self.statstypesizer, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		else:
			self.statstypesizer.Add(self.statspanel, (0, 0), (1, 1), wx.ALIGN_TOP|wx.ALL, 3)
			self.sizer.Add(self.statstypesizer, (1, 0), (1, 1), wx.ALIGN_TOP)

		#self.pospanel = leginon.gui.wx.Stats.Position(self, -1, style=wx.SIMPLE_BORDER)
		#self.sizer.Add(self.pospanel, (2, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)

		# bind panel events
		self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
		self.panel.Bind(wx.EVT_LEFT_UP, self.OnLeftClick)
		self.panel.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		self.panel.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
		self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
		self.panel.Bind(wx.EVT_SIZE, self.OnSize)
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.panel.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

		# add tools
		self.addTool(ImagePanelTools.ValueTool(self, self.toolsizer))
		self.addTool(ImagePanelTools.RulerTool(self, self.toolsizer))
		self.addTool(ImagePanelTools.ZoomTool(self, self.toolsizer))
		self.addTool(ImagePanelTools.CrosshairTool(self, self.toolsizer))
		self.addTool(ImagePanelTools.ColormapTool(self, self.toolsizer))
		self.contrasttool = ImagePanelTools.ContrastTool(self, self.toolsizer2)

		self.SetSizerAndFit(self.sizer)

	#--------------------
	def addTool(self, tool):
		self.tools.append(tool)
		return tool

	# image set functions
	#--------------------
	def setBitmap(self):
		'''
		Set the internal wx.Bitmap to current Numeric image
		'''
		if isinstance(self.imagedata, numpy.ndarray):
			wximage = self.numpyToWxImage(self.imagedata)
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

	#--------------------
	def numpyToWxImage(self, array):
		clip = self.contrasttool.getRange()
		wximage = wx.EmptyImage(array.shape[1], array.shape[0])
		normarray = array.astype(numpy.float32)
		normarray = normarray.clip(min=clip[0], max=clip[1])
		normarray = (normarray - clip[0]) / (clip[1] - clip[0]) * 255.0
		if self.colormap is None:
			normarray = normarray.astype(numpy.uint8)
			h, w = normarray.shape[:2]
			imagedata = Image.fromstring("L", (w, h), normarray.tostring())
		else:
			valarray = normarray*6.0
			valarray = valarray.astype(numpy.uint16)
			remapColor = numpy.array(self.colormap)
			rgbarray = remapColor[valarray].astype(numpy.uint8)
			print rgbarray[:,:,0]
			h, w = normarray.shape[:2]
			r = Image.fromstring("L", (w, h), rgbarray[:,:,0].tostring())
			g = Image.fromstring("L", (w, h), rgbarray[:,:,1].tostring())
			b = Image.fromstring("L", (w, h), rgbarray[:,:,2].tostring())
			imagedata = Image.merge("RGB", (r,g,b))
		wximage.SetData(imagedata.convert('RGB').tostring())
		return wximage

	#--------------------
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

	#--------------------
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

	#--------------------
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

	#--------------------
	def setImageType(self, name, imagedata, **kwargs):
		if self.selectiontool is None:
			raise ValueError('No types added')
		self.selectiontool.setImage(name, imagedata, **kwargs)
		#self.setImage(imagedata, **kwargs)

	#--------------------
	def setImage(self, imagedata):
		if isinstance(imagedata, numpy.ndarray):
			self.setNumericImage(imagedata)
		elif isinstance(imagedata, Image.Image):
			self.setPILImage(imagedata)
			stats = arraystats.all(imagedata)
			self.statspanel.set(stats)
			self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())
			self.sizer.Layout()
		elif imagedata is None:
			self.clearImage()
			self.statspanel.set({})
			self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())
			self.sizer.Layout()
		else:
			raise TypeError('Invalid image data type for setting image')

	#--------------------
	def setPILImage(self, pilimage):
		if not isinstance(pilimage, Image.Image):
			raise TypeError('PIL image must be of Image.Image type')
		self.imagedata = pilimage
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		self.UpdateDrawing()

	#--------------------
	def getScrolledCenter(self):
		x, y = self.panel.GetViewStart()
		width, height = self.panel.GetSize()
		vwidth, vheight = self.panel.GetVirtualSize()
		if vwidth == 0:
			x = 0
		else:
			x = (x + width/2.0)/vwidth
		if vheight == 0:
			y = 0
		else:
			y = (y + height/2.0)/vheight
		return x, y

	#--------------------
	def setScrolledCenter(self, center):
		cwidth, cheight = center
		width, height = self.panel.GetSize()
		vwidth, vheight = self.panel.GetVirtualSize()
		x = int(round(vwidth*cwidth - width/2.0))
		y = int(round(vheight*cheight - height/2.0))
		self.panel.Scroll(x, y)

	#--------------------
	def setNumericImage(self, numericimage):
		'''
		Set the numeric image, update bitmap, update buffer, set viewport size,
		scroll, and refresh the screen.
		'''

		if not isinstance(numericimage, numpy.ndarray):
			raise TypeError('image must be numpy.ndarray')

		center = self.getScrolledCenter()

		self.imagedata = numericimage

		stats = arraystats.all(self.imagedata)
		self.statspanel.set(stats)
		self.sizer.SetItemMinSize(self.statspanel, self.statspanel.GetSize())

		dflt_std = 5
		## use these...
		dflt_min = stats['mean'] - dflt_std * stats['std']
		dflt_max = stats['mean'] + dflt_std * stats['std']
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

	#--------------------
	def clearImage(self):
		self.contrasttool.setRange(None)
		self.imagedata = None
		self.setBitmap()
		self.setVirtualSize()
		self.setBuffer()
		self.panel.Scroll(0, 0)
		self.UpdateDrawing()

	#--------------------
	def setImageFromPILString(self, imagestring):
		buffer = cStringIO.StringIO(pilimage)
		imagedata = Image.open(buffer)
		self.setImage(imagedata)
		# Memory leak?
		#buffer.close()

	# scaling functions

	#--------------------
	def getScale(self):
		return self.scale

	#--------------------
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

	#--------------------
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

	#--------------------
	def getValue(self, x, y):
		if x < 0 or y < 0:
			return None
		try:
			if isinstance(self.imagedata, numpy.ndarray):
				return self.imagedata[y, x]
			elif isinstance(self.imagedata, Image.Image):
				return self.imagedata.getpixel((x, y))
			else:
				return None
		except (IndexError, TypeError, AttributeError), e:
			return None

	#--------------------
	def getClientCenter(self):
		center = self.panel.GetClientSize()
		return (center[0]/2, center[1]/2)

	#--------------------
	def biggerView(self):
		size = self.virtualsize
		clientsize = self.panel.GetClientSize()
		value = [False, False]
		if size[0] < clientsize[0]:
			value[0] = True
		if size[1] < clientsize[1]:
			value[1] = True
		return tuple(value)

	#--------------------
	def center(self, center):
		x, y = center
		xcenter, ycenter = self.getClientCenter()
		xscale, yscale = self.getScale()
		self.panel.Scroll(int(round(x * xscale - xcenter)),
											int(round(y * yscale - ycenter)))

	#--------------------
	def view2image(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		xoffset, yoffset = self.offset
		return (int(round((viewoffset[0] + xy[0] - xoffset) / scale[0])),
						int(round((viewoffset[1] + xy[1] - yoffset) / scale[1])))

	#--------------------
	def image2view(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		xoffset, yoffset = self.offset
		return (int(round(((xy[0]) * scale[0]) - viewoffset[0] + xoffset)),
						int(round(((xy[1]) * scale[1]) - viewoffset[1] + yoffset)))

	# tool utility functions

	#--------------------
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

	#--------------------
	def _onMotion(self, evt, dc):
		pass

	#--------------------
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

		x, y = self.view2image((evt.m_x, evt.m_y))
		value = self.getValue(x, y)
		strings = []
		for tool in self.tools:
			strings += tool.getToolTipStrings(x, y, value)
		strings += self._getToolTipStrings(x, y, value)

		#Allow drawing:
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()

		self.movecount += 1

		if self.drawlast or self.movecount % 150 == 0:
			self.drawlast = False
			self.movecount = 1
			self.Draw(dc)

		for tool in self.tools:
			self.drawlast += tool.OnMotion(evt, dc)

		self._onMotion(evt, dc)

		if strings:
			self.drawlast = True
			self.drawToolTip(dc, x, y, strings)

		dc.EndDrawing()

		self.paint(dc, wx.ClientDC(self.panel))
		dc.SelectObject(wx.NullBitmap)

	#--------------------
	def _getToolTipStrings(self, x, y, value):
		return []

	#--------------------
	def _onLeftDown(self, evt):
		pass

	#--------------------
	def _onLeftClick(self, evt):
		pass

	#--------------------
	def OnLeftDown(self, evt):
		for tool in self.tools:
			if hasattr(tool, 'OnLeftDown'):
				tool.OnLeftDown(evt)
		self._onLeftDown(evt)

	#--------------------
	def OnLeftClick(self, evt):
		for tool in self.tools:
			tool.OnLeftClick(evt)
		self._onLeftClick(evt)

	#--------------------
	def _onRightClick(self, evt):
		pass

	#--------------------
	def _onShiftRightClick(self, evt):
		pass

	#--------------------
	def _onShiftCtrlRightClick(self, evt):
		pass

	#--------------------
	def OnRightClick(self, evt):
		if not evt.ShiftDown():
			for tool in self.tools:
				tool.OnRightClick(evt)
			self._onRightClick(evt)
		else:
			if not evt.ControlDown():
				for tool in self.tools:
					tool.OnShiftRightClick(evt)
				self._onShiftRightClick(evt)
			else:
				for tool in self.tools:
					tool.OnShiftCtrlRightClick(evt)
				self._onShiftCtrlRightClick(evt)

	#--------------------
	def _onRightDown(self, evt):
		pass

	#--------------------
	def OnRightDown(self, evt):
		for tool in self.tools:
			if hasattr(tool, 'OnRightDown'):
				tool.OnRightDown(evt)
		self._onRightDown(evt)

	#--------------------
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

	#--------------------
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

	#--------------------
	def paint(self, fromdc, todc):
		xsize, ysize = self.panel.GetClientSize()
		todc.Blit(0, 0, xsize + 1, ysize + 1, fromdc, 0, 0)

	#--------------------
	def UpdateDrawing(self):
		if self.buffer is None:
			self.panel.Refresh()
		else:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wx.ClientDC(self.panel))
			dc.SelectObject(wx.NullBitmap)

	#--------------------
	def OnSize(self, evt):
		#self.setBitmap()
		#self.setVirtualSize()
		self.setViewOffset()
		self.setBuffer()
		#self.panel.Refresh()
		self.UpdateDrawing()
		evt.Skip()

	#--------------------
	def OnPaint(self, evt):
		if self.buffer is None:
			evt.Skip()
		else:
			dc = wx.MemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			self.paint(dc, wx.PaintDC(self.panel))
			dc.SelectObject(wx.NullBitmap)

	#--------------------
	def OnLeave(self, evt):
		self.UpdateDrawing()

	#--------------------
	def addTypeTool(self, name, **kwargs):
		if self.selectiontool is None:
			self.selectiontool = SelectionTool.SelectionTool(self)
			if self.mode == "vertical":
				#NEILMODE
				self.statstypesizer.Add(self.selectiontool, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)
			else:
				self.statstypesizer.Add(self.selectiontool, (2, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)
		self.selectiontool.addTypeTool(name, **kwargs)
		self.sizer.SetItemMinSize(self.selectiontool, self.selectiontool.GetSize())
		self.sizer.Layout()

##################################
##
##################################

class ClickImagePanel(ImagePanel):
	def __init__(self, parent, id, disable=False, imagesize = (520,520), mode = "horizontal"):
		ImagePanel.__init__(self, parent, id, imagesize, mode)
		if mode == "vertical":
			self.clicktool = self.addTool(ImagePanelTools.ClickTool(self, self.toolsizer, disable))
		else:
			self.clicktool = self.addTool(ImagePanelTools.ClickTool(self, self.toolsizer2, disable))
		self.Bind(EVT_IMAGE_CLICK_DONE, self.onImageClickDone)
		self.sizer.Layout()
		self.Fit()

	#--------------------
	def onImageClickDone(self, evt):
		self.clicktool.onImageClickDone(evt)






