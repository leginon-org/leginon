#!/usr/bin/env python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/ImagePanelTools.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-19 22:39:23 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import numpy
import math
import wx
from wx.lib.buttons import GenBitmapButton, GenBitmapToggleButton
from leginon.gui.wx.Entry import FloatEntry, EVT_ENTRY
import leginon.icons
import leginon.gui.wx.TargetPanelBitmaps
import pyami.ellipse
import time
from pyami import fftfun

DisplayEventType = wx.NewEventType()
EVT_DISPLAY = wx.PyEventBinder(DisplayEventType)

SettingsEventType = wx.NewEventType()
EVT_SETTINGS = wx.PyEventBinder(SettingsEventType)

MeasurementEventType = wx.NewEventType()
EVT_MEASUREMENT = wx.PyEventBinder(MeasurementEventType)

ImageClickedEventType = wx.NewEventType()
EVT_IMAGE_CLICKED = wx.PyEventBinder(ImageClickedEventType)

ShapeFoundEventType = wx.NewEventType()
EVT_SHAPE_FOUND = wx.PyEventBinder(ShapeFoundEventType)

ShapeNewCenterEventType = wx.NewEventType()
EVT_SHAPE_NEW_CENTER = wx.PyEventBinder(ShapeNewCenterEventType)

ShapeNewParamsEventType = wx.NewEventType()
EVT_SHAPE_NEW_PARAMS = wx.PyEventBinder(ShapeNewParamsEventType)

ImageNewPixelSizeEventType = wx.NewEventType()
EVT_IMAGE_NEW_PIXELSIZE = wx.PyEventBinder(ImageNewPixelSizeEventType)
##################################
##
##################################

class DisplayEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, DisplayEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

#--------------------
class SettingsEvent(wx.PyCommandEvent):
	def __init__(self, source, name):
		wx.PyCommandEvent.__init__(self, SettingsEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name

#--------------------
class MeasurementEvent(wx.PyCommandEvent):
	def __init__(self, source, measurement):
		wx.PyCommandEvent.__init__(self, MeasurementEventType, source.GetId())
		self.SetEventObject(source)
		self.measurement = measurement

#--------------------
class ImageClickedEvent(wx.PyCommandEvent):
	def __init__(self, source, xy):
		wx.PyCommandEvent.__init__(self, ImageClickedEventType, source.GetId())
		self.SetEventObject(source)
		self.xy = xy

#--------------------
class ShapeFoundEvent(wx.PyCommandEvent):
	def __init__(self, source, params):
		wx.PyCommandEvent.__init__(self, ShapeFoundEventType, source.GetId())
		self.SetEventObject(source)
		self.params = params

#--------------------
class ShapeNewCenterEvent(wx.PyCommandEvent):
	def __init__(self, source, centers):
		wx.PyCommandEvent.__init__(self, ShapeNewCenterEventType, source.GetId())
		self.SetEventObject(source)
		self.centers = centers

class ShapeNewParamsEvent(wx.PyCommandEvent):
	def __init__(self, source, params):
		wx.PyCommandEvent.__init__(self, ShapeNewParamsEventType, source.GetId())
		self.SetEventObject(source)
		self.params = params

class ImageNewPixelSizeEvent(wx.PyCommandEvent):
	def __init__(self, source, pixelsize,center,hightension,cs):
		wx.PyCommandEvent.__init__(self, ImageNewPixelSizeEventType, source.GetId())
		self.SetEventObject(source)
		self.pixelsize = pixelsize
		self.center = center
		self.hightension = hightension
		self.cs = cs

#--------------------
def getColorMap():
	b = [0] * 512 + range(256) + [255] * 512 + range(255, -1, -1)
	g = b[512:] + b[:512]
	r = g[512:] + g[:512]
	return zip(r, g, b)

colormap = getColorMap()

#--------------------
bitmaps = {}
def getBitmap(filename):
	try:
		return bitmaps[filename]
	except KeyError:
		iconpath = leginon.icons.getPath(filename)
		wximage = wx.Image(iconpath)
		wximage.ConvertAlphaToMask()
		bitmap = wx.BitmapFromImage(wximage)
		bitmaps[filename] = bitmap
		return bitmap

##################################
##
##################################

class ContrastTool(object):
	def __init__(self, imagepanel, sizer):
		self.imagepanel = imagepanel
		self.imagemin = 0
		self.imagemax = 0
		self.contrastmin = 0
		self.contrastmax = 0
		self.slidermin = 0
		self.slidermax = 255

		self.minslider = wx.Slider(self.imagepanel, -1, self.slidermin, self.slidermin, self.slidermax, size=(180, -1))
		self.maxslider = wx.Slider(self.imagepanel, -1, self.slidermax, self.slidermin, self.slidermax, size=(180, -1))
		self.minslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onMaxSlider)
		self.minslider.Bind(wx.EVT_SCROLL_ENDSCROLL, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_ENDSCROLL, self.onMaxSlider)
		self.minslider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onMinSlider)
		self.maxslider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onMaxSlider)

		self.iemin = FloatEntry(imagepanel, -1, chars=6, allownone=False, value='%g' % self.contrastmin)
		self.iemax = FloatEntry(imagepanel, -1, chars=6, allownone=False, value='%g' % self.contrastmax)
		self.iemin.Enable(False)
		self.iemax.Enable(False)

		self.iemin.Bind(EVT_ENTRY, self.onMinEntry)
		self.iemax.Bind(EVT_ENTRY, self.onMaxEntry)

		self.sizer = wx.GridBagSizer(0, 0)
		self.sizer.Add(self.minslider, (0, 0), (1, 1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_BOTTOM)
		self.sizer.Add(self.iemin, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 2)
		self.sizer.Add(self.maxslider, (1, 0), (1, 1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)
		self.sizer.Add(self.iemax, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.ALL, 2)
		sizer.Add(self.sizer, 0, wx.ALIGN_CENTER)

	#--------------------
	def _setSliders(self, value):
		if value[0] is not None:
			self.minslider.SetValue(self.getSliderValue(value[0]))
		if value[1] is not None:
			self.maxslider.SetValue(self.getSliderValue(value[1]))

	#--------------------
	def _setEntries(self, value):
		if value[0] is not None:
			self.iemin.SetValue(value[0])
		if value[1] is not None:
			self.iemax.SetValue(value[1])

	#--------------------
	def setSliders(self, value):
		if value[0] is not None:
			self.contrastmin = value[0]
		if value[1] is not None:
			self.contrastmax = value[1]
		self._setSliders(value)
		self._setEntries(value)

	#--------------------
	def updateNumericImage(self):
		self.imagepanel.setBitmap()
		self.imagepanel.setBuffer()
		self.imagepanel.UpdateDrawing()

	#--------------------
	def getRange(self):
		return self.contrastmin, self.contrastmax

	#--------------------
	def getScaledValue(self, position):
		try:
			scale = float(position - self.slidermin)/(self.slidermax - self.slidermin)
		except ZeroDivisionError:
			scale = 1.0
		return (self.imagemax - self.imagemin)*scale + self.imagemin

	#--------------------
	def getSliderValue(self, value):
		if self.imagemax == self.imagemin:
			return self.imagemin
		scale = (value - self.imagemin)/(self.imagemax - self.imagemin)
		return int(round((self.slidermax - self.slidermin)*scale + self.slidermin))

	#--------------------
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
			self.minslider.Enable(False)
			self.maxslider.Enable(False)
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
			self.minslider.Enable(True)
			self.maxslider.Enable(True)

	#--------------------
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

	#--------------------
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

	#--------------------
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

	#--------------------
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

##################################
##
##################################

class ImageTool(object):
	def __init__(self, imagepanel, sizer, bitmap, tooltip='', cursor=None,
			untoggle=False, button=None):
		self.sizer = sizer
		self.imagepanel = imagepanel
		self.cursor = cursor
		if button is None:
			self.button = GenBitmapToggleButton(self.imagepanel, -1, bitmap, size=(24, 24))
		else:
			self.button = button
		self.untoggle = untoggle
		self.button.SetBezelWidth(3)
		if tooltip:
			self.button.SetToolTip(wx.ToolTip(tooltip))
		self.sizer.Add(self.button, 0, wx.ALIGN_CENTER|wx.ALL, 3)
		self.button.Bind(wx.EVT_BUTTON, self.OnButton)

	#--------------------
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

	#--------------------
	def OnToggle(self, value):
		pass

	#--------------------
	def OnLeftClick(self, evt):
		pass

	#--------------------
	def OnShiftLeftClick(self, evt):
		pass

	#--------------------
	def OnRightClick(self, evt):
		pass

	#--------------------
	def OnShiftRightClick(self, evt):
		pass

	#--------------------
	def OnShiftCtrlRightClick(self, evt):
		pass

	#--------------------
	def OnMotion(self, evt, dc):
		return False

	#--------------------
	def getToolTipStrings(self, x, y, value):
		return []

	#--------------------
	def Draw(self, dc):
		pass

##################################
##
##################################

class TraceTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('ellipse.png')
		tooltip = 'Toggle Fit Shape'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(False)
		self.start = None
		self.xypath = []
		self.leftisdown = False
		self.rightisdown = False
		self.lastx = 0
		self.lasty = 0

	def OnLeftDown(self, evt):
		if self.button.GetToggle():
			self.leftisdown = True
			self.rightisdown = False
			self.xypath = []
			self.fitted_shape_points = []
			if self.start is not None:
				x = evt.GetX() #- self.imagepanel.offset[0]
				y = evt.GetY() #- self.imagepanel.offset[1]
				x0, y0 = self.start
				self.xypath.append((x,y))
			self.start = self.imagepanel.view2image((evt.GetX(), evt.GetY()))

	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.leftisdown = False
			self.rightisdown = False
			self.start = None
			self.imagepanel.UpdateDrawing()

	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.leftisdown = False
			self.rightisdown = False
			self.start = None
			self.imagepanel.UpdateDrawing()

	def OnMotion(self, evt, dc):
		if self.button.GetToggle():
			if self.leftisdown or self.rightisdown:
				x,y = self.imagepanel.view2image((evt.GetX(), evt.GetY()))
				self.xypath.append((x,y))
				return True
		return False

	def OnToggle(self, value):
		if not value:
			self.start = None
			self.xypath = []
			self.imagepanel.UpdateDrawing()

	def Draw(self, dc):
		if self.xypath:
			dc.SetPen(wx.Pen(wx.RED, 1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			scaledpoints = map(self.imagepanel.image2view, self.xypath)
			if len(scaledpoints) > 1:
				dc.DrawLines(scaledpoints)

class FitShapeTool(TraceTool):
	def __init__(self, imagepanel, sizer):
		TraceTool.__init__(self,imagepanel,sizer)
		self.shiftxypath = []
		self.fitted_shape_points = []
		self.shape_params = None
		self.shapepoint = None
		self.shapepointaxis = None
		self.shapepointangle = None
		self.start_shape_params = None
		self.imagepanel.Bind(leginon.gui.wx.ImagePanelTools.EVT_SHAPE_NEW_CENTER, self.onNewShapeCenter, self.imagepanel)
		self.imagepanel.Bind(leginon.gui.wx.ImagePanelTools.EVT_SHAPE_NEW_PARAMS, self.onNewShapeParams, self.imagepanel)


	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.leftisdown = False
			self.rightisdown = False
			self.start = None
			self.fitted_shape_points = self.ellipsePoints(self.xypath)
			self.imagepanel.UpdateDrawing()

	def OnShiftLeftClick(self, evt):
		if not self.button.GetToggle():
			return
		self.leftisdown = False
		self.rightisdown = False
		self.shape_params['shape'] = 'rectangle'
		x,y = self.imagepanel.view2image((evt.GetX(), evt.GetY()))
		if len(self.shiftxypath) > 1:
			self.shiftxypath = []
		self.shiftxypath.append((x,y))
		if len(self.shiftxypath) == 2:
			self.rectanglePoints(self.shiftxypath)
			self.fitted_shape_points = self.drawShape()
			self.imagepanel.UpdateDrawing()

	def distance(self, p1, p2):
		return math.hypot(p2[0]-p1[0], p2[1]-p1[1])

	def ellipsePoints(self, points):
		try:
			params = pyami.ellipse.solveEllipseB2AC(points)
		#params = pyami.ellipse.solveEllipseGander(points)
		except:
			params = None
		if params is None:
			## ellipse not fit
			return []
		params['shape'] = 'ellipse'
		self.shape_params = params
		return self.drawShape()

	def rectanglePoints(self,points):
		if self.shape_params['center'] is None:
			return
		dx = []
		dy = []
		dx.append(points[0][0] - self.shape_params['center'][0])
		dy.append(points[0][1] - self.shape_params['center'][1])
		dx.append(points[1][0] - self.shape_params['center'][0])
		dy.append(points[1][1] - self.shape_params['center'][1])
		axy = (dx[0]+dx[1]) / 2 ,(dy[0]+dy[1]) / 2
		bxy = (dx[0]-dx[1]) / 2 ,(dy[0]-dy[1]) / 2
		self.shape_params['alpha'] = math.atan2(axy[1],axy[0])
		self.shape_params['a'] = math.hypot(axy[0],axy[1])
		self.shape_params['b'] = math.hypot(bxy[0],bxy[1])
		return self.drawShape()

	def drawShape(self):
		if len(set.difference(set(['a','b','alpha','center','shape']),set(self.shape_params.keys()))) > 0:
			return
		if self.shape_params['shape'] == 'ellipse':
			angleinc = 5 * 3.14159 / 180.0
			ellipse_params = self.shape_params.copy()
			ellipse_params.pop('shape')
			ellipsepoints = pyami.ellipse.ellipsePoints(angleinc,  **ellipse_params)
			idcevt = ShapeFoundEvent(self.imagepanel, self.shape_params)
			self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
			return ellipsepoints
		else:
			if self.shape_params['shape'] == 'rectangle':
				idcevt = ShapeFoundEvent(self.imagepanel, self.shape_params)
				self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)
				x0, y0 = self.shape_params['center']
				alpha = self.shape_params['alpha']
				a = self.shape_params['a']
				b = self.shape_params['b']
				magnitude = math.hypot(a,b)
				angle = math.atan2(a,b)
				xa,ya = a * math.cos(alpha), a * math.sin(alpha)
				xb,yb = b * math.cos(alpha - math.pi/2), b * math.sin(alpha - math.pi/2)
				dx,dy = xa+xb, ya+yb 
				x1 = x0 + dx
				y1 = y0 + dy
				x2 = x0 + dx * math.cos(2*angle) + dy * math.sin(2*angle) 
				y2 = y0 + dy * math.cos(2*angle) - dx * math.sin(2*angle)
				x3,y3 = x0-dx, y0-dy
				x4,y4 = x0-(x2-x0), y0-(y2-y0)
				polypoints = [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
				return polypoints

	def updateShape(self, deltaparams):
		for key in ('a','b','alpha'):
			if key in deltaparams:
				self.shape_params[key] += deltaparams[key]
		if 'shape' in deltaparams:
				self.shape_params['shape'] = deltaparams['shape']
		if 'center' in deltaparams:
			oldcenter = self.shape_params['center']
			dcenter = deltaparams['center']
			newcenter = oldcenter[0] + dcenter[0], oldcenter[1] + dcenter[1]
			self.shape_params['center'] = newcenter
		self.drawShape()

	def onNewShapeParams(self, evt):
		if self.shape_params is None:
			return
		for key in ('a','b','alpha','shape'):
			if key in evt.params:
				self.shape_params[key] = evt.params[key]
		self.fitted_shape_points = self.drawShape()
		self.xypath = []
		self.shiftxypath = []
		self.imagepanel.UpdateDrawing()

	def onNewShapeCenter(self,evt):
		if self.shape_params is None:
			if evt.centers:
				self.shape_params = {'center': numpy.array(evt.centers[0])}
			return
		else:
			if not evt.centers:
				return
		oldcenter = self.shape_params['center']
		centers = []
		distances = []
		for center in evt.centers:
			centers.append(center)
			distances.append(self.distance(oldcenter,center))
		closest_center = centers[distances.index(min(distances))]
		# draw shape at the input center closest to the shape 
		# made from the shape fit tool
		if self.shape_params and list(oldcenter) != list(closest_center):
			self.shape_params['center'][0] = closest_center[0]
			self.shape_params['center'][1] = closest_center[1]
			self.fitted_shape_points = self.drawShape()
			self.xypath = []
			self.shiftxypath = []
			self.imagepanel.UpdateDrawing()


	#--------------------
	def OnToggle(self, value):
		if not value:
			self.start = None
			self.xypath = []
			self.shiftxypath = []
			self.fitted_shape_points = []
			self.imagepanel.UpdateDrawing()

	def Draw(self, dc):
		super(FitShapeTool,self).Draw(dc)
		if self.shiftxypath:
			dc.SetPen(wx.Pen(wx.RED, 1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			scaledpoints = map(self.imagepanel.image2view, self.shiftxypath)
			dc.DrawPointList(scaledpoints)
		if self.fitted_shape_points:
			dc.SetPen(wx.Pen(wx.GREEN, 1))
			dc.SetBrush(wx.TRANSPARENT_BRUSH)
			polypoints = map(self.imagepanel.image2view, self.fitted_shape_points)
			dc.DrawPolygon(polypoints)

class ValueTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('value.png')
		tooltip = 'Toggle Show Value'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(False)

	#--------------------
	def valueString(self, x, y, value):
		if value is None:
			valuestr = 'N/A'
		else:
			valuestr = '%g' % value
		return '(%d, %d) %s' % (x, y, valuestr)

	#--------------------
	def getToolTipStrings(self, x, y, value):
		#self.imagepanel.pospanel.set({'x': x, 'y': y, 'value': value})
		if self.button.GetToggle():
			return [self.valueString(x, y, value)]
		else:
			return []

class ResolutionTool(ValueTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('valueinverse.png')
		tooltip = 'Toggle Show Resolution/Defocus'
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip)
		self.button.SetToggle(False)
		self.pixelsize = 1.0
		self.hightension = 120000
		self.imagepanel.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_NEW_PIXELSIZE, self.onNewPixelSize, self.imagepanel)

	def valueString(self, x, y, value):
		if self.pixelsize and self.center:
			distance = math.sqrt((x-self.center['x'])**2+(y-self.center['y'])**2)
			if distance < 1.0:
				# avoid divide by zero error
				return ''
			resolution = 1/math.sqrt(((x-self.center['x'])*self.pixelsize['x'])**2+((y-self.center['y'])*self.pixelsize['y'])**2)
			defocus = fftfun.calculateDefocus(self.hightension,1/resolution,self.cs)
			if resolution < 1e-6:
				resolutionstr = "%.2f nm" % (resolution*1e9,)
			else:
				resolutionstr = "%.1f um" % (resolution*1e6,)
		else:
			resolutionstr = "N/A"
		return 'r= %s,defocus=%.0f nm' % (resolutionstr,defocus*1e9)

	def onNewPixelSize(self,evt):
		self.pixelsize = evt.pixelsize
		self.center = evt.center
		self.hightension = evt.hightension
		self.cs = evt.cs

	def OnLeftClick(self, evt):
		xy = self.imagepanel.view2image((evt.GetX(), evt.GetY()))
		idcevt = ImageClickedEvent(self.imagepanel, xy)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)

##################################
##
##################################

class CrosshairTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		self.color = wx.Colour(0,150,150) #dark teal green
		bitmap = leginon.gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, shape='+')
		tooltip = 'Toggle Center Crosshair'
		cursor = None
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, False)

	#--------------------
	def Draw(self, dc):
		if not self.button.GetToggle():
			return
		dc.SetPen(wx.Pen(self.color, 1))
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

	#--------------------
	def OnToggle(self, value):
		self.imagepanel.UpdateDrawing()

##################################
##
##################################

class ColormapTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('color.png')
		tooltip = 'Show Color'
		cursor = None
		imagepanel.colormap = None
		self.grayscalebitmap = getBitmap('grayscale.png')
		self.colorbitmap = bitmap
		button = GenBitmapButton(imagepanel, -1, bitmap, size=(24, 24))
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, False,
												button=button)

	#--------------------
	def OnButton(self, evt):
		if self.imagepanel.colormap is None:
			self.imagepanel.colormap = colormap
			self.button.SetBitmapLabel(self.grayscalebitmap)
			self.button.SetToolTip(wx.ToolTip('Show Grayscale'))
		else:
			self.imagepanel.colormap = None
			self.button.SetBitmapLabel(self.colorbitmap)
			self.button.SetToolTip(wx.ToolTip('Show Color'))
		self.imagepanel.setBitmap()
		self.imagepanel.UpdateDrawing()

##################################
##
##################################

class RulerTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('ruler.png')
		tooltip = 'Toggle Ruler Tool'
		cursor = wx.CROSS_CURSOR
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.start = None
		self.measurement = None

	#--------------------
	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			if self.start is not None:
				x = evt.GetX() #- self.imagepanel.offset[0]
				y = evt.GetY() #- self.imagepanel.offset[1]
				x0, y0 = self.start
				dx, dy = x - x0, y - y0
				self.measurement = {
					'from': self.start,
					'to': (x, y),
					'delta': (dx, dy),
					'magnitude': math.hypot(dx, dy),
					'angle': math.degrees(math.atan2(dy, dx)),
				}
				mevt = MeasurementEvent(self.imagepanel, dict(self.measurement))
				self.imagepanel.GetEventHandler().AddPendingEvent(mevt)
			self.start = self.imagepanel.view2image((evt.GetX(), evt.GetY()))

	#--------------------
	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.start = None
			self.measurement = None
			self.imagepanel.UpdateDrawing()

	#--------------------
	def OnToggle(self, value):
		if not value:
			self.start = None
			self.measurement = None

	#--------------------
	def DrawRuler(self, dc, x, y):
		dc.SetPen(wx.Pen(wx.RED, 2))
		x0, y0 = self.imagepanel.image2view(self.start)
		#x0 -= self.imagepanel.offset[0]
		#y0 -= self.imagepanel.offset[1]
		dc.DrawLine(x0, y0, x, y)

	#--------------------
	def OnMotion(self, evt, dc):
		if self.button.GetToggle() and self.start is not None:
			x = evt.GetX() #- self.imagepanel.offset[0]
			y = evt.GetY() #- self.imagepanel.offset[1]
			self.DrawRuler(dc, x, y)
			return True
		return False

	#--------------------
	def getToolTipStrings(self, x, y, value):
		if self.button.GetToggle() and self.start is not None:
			x0, y0 = self.start
			dx, dy = x - x0, y - y0
			return ['From (%d, %d) x=%d y=%d d=%.2f a=%.0f' % (x0, y0, dx, dy, math.hypot(dx, dy),math.degrees(math.atan2(dy, dx)))]
		else:
			return []

##################################
##
##################################

class ZoomTool(ImageTool):
	def __init__(self, imagepanel, sizer):
		bitmap = getBitmap('zoom.png')
		tooltip = 'Toggle Zoom Tool'
		cursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)
		self.zoomlevels = [0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 32, 128,]
		self.zoomlabels = ['4x', '2x', '1x', '2/3x', '1/2x', '1/3x', '1/4x', '1/6x', '1/8x',
			'1/12x', '1/16x', '1/32x', '1/128x']
		# wx.Choice seems a bit slow, at least on windows
		self.zoomchoice = wx.Choice(self.imagepanel, -1,
			choices=self.zoomlabels)
			#map(self.zoomlabels, self.zoomlevels))
		self.zoom(self.zoomlevels.index(1), (0, 0))
		self.zoomchoice.SetSelection(self.zoomlevel)
		self.sizer.Add(self.zoomchoice, 0, wx.ALIGN_CENTER|wx.ALL, 3)

		self.zoomchoice.Bind(wx.EVT_CHOICE, self.onChoice)

	#--------------------
	def log2str(self, value):
		if value == 1:
			return "1x"
		return '1/' + str(value) + 'x'
		if value < 0:
			return '1/' + str(int(1/2**value)) + 'x'
		else:
			return str(int(2**value)) + 'x'

	#--------------------
	def OnLeftClick(self, evt):
		if self.button.GetToggle():
			self.zoomIn(evt.GetX(), evt.GetY())

	#--------------------
	def OnRightClick(self, evt):
		if self.button.GetToggle():
			self.zoomOut(evt.GetX(), evt.GetY())

	#--------------------
	def zoom(self, level, viewcenter):
		self.zoomlevel = level
		center = self.imagepanel.view2image(viewcenter)
		#scale = 2**self.zoomlevels[self.zoomlevel]
		scale = 1.0/float(self.zoomlevels[self.zoomlevel])
		self.imagepanel.setScale((scale, scale))
		self.imagepanel.center(center)
		self.imagepanel.UpdateDrawing()

	#--------------------
	def zoomIn(self, x, y):
		if self.zoomlevel > 0:
			self.zoom(self.zoomlevel - 1, (x, y))
			self.zoomchoice.SetSelection(self.zoomlevel)

	#--------------------
	def zoomOut(self, x, y):
		if self.zoomlevel < len(self.zoomlevels) - 1:
			self.zoom(self.zoomlevel + 1, (x, y))
			self.zoomchoice.SetSelection(self.zoomlevel)

	#--------------------
	def onChoice(self, evt):
		selection = evt.GetSelection()
		if selection == self.zoomlevel:
			return
		size = self.imagepanel.panel.GetSize()
		viewcenter = (size[0]/2, size[1]/2)
		self.zoom(selection, viewcenter)

##################################
##
##################################

class ClickTool(ImageTool):
	def __init__(self, imagepanel, sizer, disable=False):
		self._disable = disable
		self._disabled = False
		bitmap = getBitmap('arrow.png')
		tooltip = 'Click Tool'
		cursor = wx.StockCursor(wx.CURSOR_BULLSEYE)
		ImageTool.__init__(self, imagepanel, sizer, bitmap, tooltip, cursor, True)

	#--------------------
	def OnLeftClick(self, evt):
		if not self.button.GetToggle() or self._disabled:
			return
		if self._disable:
			self._disabled = True
		xy = self.imagepanel.view2image((evt.GetX(), evt.GetY()))
		idcevt = ImageClickedEvent(self.imagepanel, xy)
		self.imagepanel.GetEventHandler().AddPendingEvent(idcevt)

	#--------------------
	def onImageClickDone(self, evt):
		self._disabled = False

##################################
##
##################################

class TypeTool(object):
	def __init__(self, parent, name, display=None, target=None, settings=None):
		self.parent = parent

		self.name = name

		self.label = wx.StaticText(parent, -1, name)

		self.bitmaps = self.getBitmaps()

		self.bitmap = wx.StaticBitmap(parent, -1, self.bitmaps['red'],
			(self.bitmaps['red'].GetWidth(), self.bitmaps['red'].GetHeight()) )

		self.togglebuttons = {}

		if display is not None:
			togglebutton = self.addToggleButton('display', 'Display')
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleDisplay)

		if settings is not None:
			togglebutton = self.addToggleButton('settings', 'Settings')
			togglebutton.Bind(wx.EVT_BUTTON, self.onSettingsButton)

	#--------------------
	def getBitmaps(self):
		return {
			'red': getBitmap('red.png'),
			'green': getBitmap('green.png'),
			'display': getBitmap('display.png'),
			'settings': getBitmap('settings.png'),
		}

	#--------------------
	def enableToggleButton(self, toolname, enable=True):
		togglebutton = self.togglebuttons[toolname]
		if enable:
			togglebutton.SetBezelWidth(3)
			#togglebutton.SetBackgroundColour(wx.Colour(160, 160, 160))
		else:
			togglebutton.SetBezelWidth(0)
			#togglebutton.SetBackgroundColour(wx.WHITE)
		togglebutton.Enable(enable)

	#--------------------
	def addToggleButton(self, toolname, tooltip=None):
		bitmap = self.bitmaps[toolname]
		size = (24, 24)
		togglebutton = GenBitmapToggleButton(self.parent, -1, bitmap, size=size)
		togglebutton.SetBezelWidth(3)
		if tooltip is not None:
			togglebutton.SetToolTip(wx.ToolTip(tooltip))
		self.togglebuttons[toolname] = togglebutton
		return togglebutton

	#--------------------
	def SetBitmap(self, name):
		try:
			self.bitmap.SetBitmap(self.bitmaps[name])
		except KeyError:
			raise AttributeError

	#--------------------
	def onToggleDisplay(self, evt):
		#if self.togglebuttons['display'].GetValue() is True:
		#	self.togglebuttons['display'].SetBackgroundColour(wx.Colour(160,160,160))
		#else:
		#	self.togglebuttons['display'].SetBackgroundColour(wx.WHITE)
		evt = DisplayEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['display'].GetEventHandler().AddPendingEvent(evt)

	#--------------------
	def onSettingsButton(self, evt):
		evt = SettingsEvent(evt.GetEventObject(), self.name)
		self.togglebuttons['settings'].GetEventHandler().AddPendingEvent(evt)


