#!/usr/bin/env python

from wxPython.wx import *
#from wxPython.wxc import wxPyAssertionError
import cStringIO
import Numeric
import Image
import math

import Mrc
from NumericImage import NumericImage

USE_BUFFERED_DC = False

class ImagePanel(wxPanel):
	def __init__(self, parent, id):
		self.image = None
		self.bitmap = None
		self.buffer = wxNullBitmap
		self.size = (512, 512)
		self.scale = (1.0, 1.0)

		wxPanel.__init__(self, parent, id)
		wxInitAllImageHandlers()

		self.sizer = wxBoxSizer(wxVERTICAL)
		self.SetAutoLayout(true)
		self.SetSizer(self.sizer)

		self.toolsizer = wxBoxSizer(wxHORIZONTAL)
		self.sizer.Add(self.toolsizer)

		self.initPanel()
		self.initValue()
		self.initZoom()
#		self.initScaleEntry()
#		self.initValueLabels()

		self.Fit()

		EVT_PAINT(self.panel, self.OnPaint)
		EVT_SIZE(self.panel, self.OnSize)
		EVT_MOTION(self.panel, self.motion)

	def initPanel(self):
		self.panel = wxScrolledWindow(self, -1, size=self.size)
		self.panel.SetScrollRate(1,1)
		self.panel.SetCursor(wxCROSS_CURSOR)
		self.sizer.Add(self.panel)
		width, height = self.panel.GetSizeTuple()
		self.sizer.SetItemMinSize(self.panel, width, height)

	def initValueLabels(self):
		self.xlabel = wxStaticText(self, -1, '0000',
																style=wxALIGN_CENTRE | wxST_NO_AUTORESIZE)
		self.xlabel.SetLabel('')
		self.ylabel = wxStaticText(self, -1, '0000',
																style=wxALIGN_CENTRE | wxST_NO_AUTORESIZE)
		self.ylabel.SetLabel('')
		self.valuelabel = wxStaticText(self, -1, '',
																		style=wxALIGN_CENTRE)
		self.valuelabel.SetLabel('')
		self.toolsizer.Add(wxStaticText(self, -1, 'x: '))
		self.toolsizer.Add(self.xlabel)
		self.toolsizer.Add(wxStaticText(self, -1, 'y: '))
		self.toolsizer.Add(self.ylabel)
		self.toolsizer.Add(wxStaticText(self, -1, 'Value: '))
		self.toolsizer.Add(self.valuelabel)

	def bitmapTool(self, filename):
		wximage = wxImage(filename)
		bitmap = wxBitmapFromImage(wximage)
		bitmap.SetMask(wxMaskColour(bitmap, wxWHITE))
		return bitmap

	def OnValueButton(self, evt):
		self.UpdateDrawing()
		self.valueflag = not self.valueflag

	def initValue(self):
		self.valueflag = True
		bitmap = self.bitmapTool('valuetool.bmp')
		valuebutton = wxBitmapButton(self, -1, bitmap)
		valuebutton.SetToolTip(wxToolTip('Toggle Show Value'))
		EVT_BUTTON(self, valuebutton.GetId(), self.OnValueButton)
		self.toolsizer.Add(valuebutton, 0, wxALL, 3)

	def updateZoomLabel(self):
		xscale, yscale = self.getScale()
		self.zoomlabel.SetLabel('Zoom: ' + str(xscale) + 'x')

	def OnZoomIn(self, evt):
		xscale, yscale = self.getScale()
		self.setScale((xscale*2, yscale*2), self.view2image((evt.m_x, evt.m_y)))
		self.updateZoomLabel()

	def OnZoomOut(self, evt):
		xscale, yscale = self.getScale()
		self.setScale((xscale/2, yscale/2), self.view2image((evt.m_x, evt.m_y)))
		self.updateZoomLabel()

	def OnZoomButton(self, evt):
		if self.zoomflag:
			self.panel.SetCursor(wxStockCursor(wxCURSOR_MAGNIFIER))
			EVT_LEFT_UP(self.panel, self.OnZoomIn)
			EVT_RIGHT_UP(self.panel, self.OnZoomOut)
		else:
			self.panel.SetCursor(wxCROSS_CURSOR)
			EVT_LEFT_UP(self.panel, None)
			EVT_RIGHT_UP(self.panel, None)
		self.zoomflag = not self.zoomflag

	def initZoom(self):
		self.zoomflag = True
		bitmap = self.bitmapTool('zoomtool.bmp')
		zoombutton = wxBitmapButton(self, -1, bitmap)
		zoombutton.SetToolTip(wxToolTip('Toggle Zoom Tool'))
		EVT_BUTTON(self, zoombutton.GetId(), self.OnZoomButton)
		self.toolsizer.Add(zoombutton, 0, wxALL, 3)
		self.zoomlabel = wxStaticText(self, -1, '')
		self.updateZoomLabel()
		self.toolsizer.Add(self.zoomlabel, 0, wxALL, 3)

	def getEntryScale(self):
		scale = list(self.getScale())
		for i in range(len(scale)):
			try:
				scale[i] = float(self.scale_entry[i].GetValue())
			except:
				self.scale_entry[i].SetValue(str(scale[i]))
		return scale

	def getScale(self):
		return self.scale

	def setVirtualSize(self):
		xscale, yscale = self.getScale()
		if self.bitmap is not None:
			self.panel.SetVirtualSize(((self.bitmap.GetWidth() - 1)*xscale,
																	(self.bitmap.GetHeight() - 1)*yscale))
		else:
			self.panel.SetVirtualSize((0, 0))

	def setScale(self, scale, offset=None):
		self.scale = tuple(scale)
		self.setVirtualSize()

		dc = wxClientDC(self.panel)
		dc.BeginDrawing()
		dc.Clear()
		dc.EndDrawing()

		self.UpdateDrawing()

		if offset is not None:
			xcenter, ycenter = self.getClientCenter()
			self.panel.Scroll((offset[0])*self.scale[0] - xcenter,
												(offset[1])*self.scale[1] - ycenter)
		else:
			self.panel.Scroll(0, 0)
		#self.panel.Refresh(0)

	def OnScaleEntry(self, evt):
		self.setScale(self.getEntryScale(), self.view2image(self.getClientCenter()))

	def initScaleEntry(self):
		self.scale_entry = {}
		scale = self.getScale()
		for axis, i in [('x', 0), ('y', 1)]:
			self.toolsizer.Add(wxStaticText(self, -1, axis + ':'),
													0, wxCENTER | wxALL, 5)
			self.scale_entry[i] = wxTextCtrl(self, -1, value=str(scale[i]))
			size = self.scale_entry[i].GetSize()
			size = (size[0]/2, size[1])
			self.scale_entry[i].SetSize(size)
			self.scale_entry[i].SetMaxLength(6)
			self.toolsizer.Add(self.scale_entry[i], 0, wxCENTER | wxALL, 3)
		scalebutton = wxButton(self, -1, 'Scale')
		self.toolsizer.Add(scalebutton, 0, wxCENTER | wxALL, 3)
		EVT_BUTTON(self, scalebutton.GetId(), self.OnScaleEntry)

	def PILsetImageFromMrcString(self, imagestring):
		self.clearImage()
		stream = cStringIO.StringIO(imagestring)
		self.image = Image.open(stream)
		min, max = self.image.getextrema()
		if max > 255.0 or min < 0.0:
			r = max - min
			if r:
				scale = 255.0 / r
				offset = -255.0 * min / r
				image = self.image.point(lambda p: p * scale + offset)
			else:
				image = self.image
		else:
			image = self.image
		wximage = wxEmptyImage(image.size[0], image.size[1])
		wximage.SetData(image.convert('RGB').tostring())
		self.setImage(wximage)

	def setImageFromMrcString(self, imagestring):
		self.clearImage()
		self.image = Mrc.mrcstr_to_numeric(imagestring)
		n = NumericImage(self.image)
		n.update_image()
		wximage = n.wxImage()
		self.setImage(wximage)

	def setImage(self, wximage):
		self.bitmap = wxBitmapFromImage(wximage)
		self.setVirtualSize()
		self.panel.Scroll(0, 0)
		bitmapwidth = self.bitmap.GetWidth()
		bitmapheight = self.bitmap.GetHeight()
		self.buffer = wxEmptyBitmap(bitmapwidth, bitmapheight)
		self.UpdateDrawing()

	def clearImage(self):
		self.image = None
		self.bitmap = None
		self.UpdateDrawing()

	def view2image(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		return (int(round((viewoffset[0] + xy[0]) / scale[0])),
						int(round((viewoffset[1] + xy[1]) / scale[1])))

	def image2view(self, xy, viewoffset=None, scale=None):
		if viewoffset is None:
			viewoffset = self.panel.GetViewStart()
		if scale is None:
			scale = self.getScale()
		return (int(round((xy[0] * scale[0]) - viewoffset[0])),
						int(round((xy[1] * scale[1]) - viewoffset[1])))


	def getClientCenter(self):
		center = self.panel.GetClientSize()
		return (center[0]/2, center[1]/2)

	def motion(self, evt):
		if self.image is None:
			return
		if self.valueflag:
			x, y = self.view2image((evt.m_x, evt.m_y))
			self.drawValueLabel(x, y)
#		if self.valuelabelflag:
#			self.xlabel.SetLabel(str(x))
#			self.ylabel.SetLabel(str(y))
#			self.valuelabel.SetLabel(str(value))

	def drawValueLabel(self, x, y):
		value = self.image[y, x]
		self.drawLabel((x, y), value)

	def drawLabel(self, xy, value):
		dc = wxClientDC(self.panel)
		dc.BeginDrawing()

		dc.SetBrush(wxBrush(wxWHITE))
		dc.SetPen(wxPen(wxBLACK, 1))

		string = '(%d, %d): %d' % (xy + (value,))
		#tooltip = wxToolTip(string)
		#self.panel.SetToolTip(tooltip)

		try:
			apply(self.scaledBlit, self.damaged)
		except AttributeError:
			pass

		xextent, yextent, d, e = dc.GetFullTextExtent(string, wxNORMAL_FONT)
		xcenter, ycenter = self.getClientCenter()

		x, y = self.image2view(xy)

		if x <= xcenter:
			xoffset = 10
		else:
			xoffset = -(10 + xextent + 4)
		if y <= ycenter:
			yoffset = 10
		else:
			yoffset = -(10 + yextent + 4)

		x = int(round((x + xoffset)))
		y = int(round((y + yoffset)))

		self.damaged = (x, y, xextent + 4, yextent + 4)

		apply(dc.DrawRectangle, self.damaged)

		dc.SetFont(wxNORMAL_FONT)
		dc.DrawText(string, x + 2 , y + 2)

		dc.EndDrawing()

	def scaledBlit(self, x, y, w, h):
		if self.buffer == wxNullBitmap:
			return

		dc = wxMemoryDC()
		dc.SelectObject(self.buffer)

		xscale, yscale = self.getScale()
		ix, iy = self.view2image((x, y))
		#vx, vy = self.image2view((x, y))

		clientdc = wxClientDC(self.panel)
		clientdc.SetUserScale(xscale, yscale)
		clientdc.Blit(x/xscale, y/yscale, w/xscale + 1, h/yscale + 1, dc, ix, iy)

	def Draw(self, dc):
#		try:
		dc.BeginDrawing()
		if self.bitmap is None:
			dc.Clear()
		else:
			dc.DrawBitmap(self.bitmap, 0, 0)
		dc.EndDrawing()
#		except wxPyAssertionError:
#			pass

	def UpdateDrawing(self):
		if self.buffer == wxNullBitmap:
			return

		dc = wxMemoryDC()
		dc.SelectObject(self.buffer)
		self.Draw(dc)

		xviewoffset, yviewoffset = self.panel.GetViewStart()
		xscale, yscale = self.getScale()
		xsize, ysize = self.panel.GetClientSize()

		clientdc = wxClientDC(self.panel)
		clientdc.SetUserScale(xscale, yscale)
		clientdc.Blit(0, 0, xsize/xscale + 1, ysize/yscale + 1, dc,
									xviewoffset/xscale, yviewoffset/yscale)

	def OnSize(self, evt):
#		width, height = self.panel.GetClientSize()
#		self.buffer = wxEmptyBitmap(width, height)
		self.UpdateDrawing()

	def OnPaint(self, evt):
		if self.buffer == wxNullBitmap:
			return

		dc = wxMemoryDC()
		dc.SelectObject(self.buffer)
		self.Draw(dc)

		xviewoffset, yviewoffset = self.panel.GetViewStart()
		xscale, yscale = self.getScale()
		xsize, ysize = self.panel.GetClientSize()

		paintdc = wxPaintDC(self.panel)
		paintdc.SetUserScale(xscale, yscale)
		paintdc.Blit(0, 0, xsize/xscale + 1, ysize/yscale + 1, dc,
									xviewoffset/xscale, yviewoffset/yscale)

class TargetImagePanel(ImagePanel):
	def __init__(self, parent, id, callback=None):
		self.callback = callback
		ImagePanel.__init__(self, parent, id)
		self.targets = {}
		EVT_LEFT_DCLICK(self.panel, self.OnLeftDoubleClick)
		EVT_RIGHT_DCLICK(self.panel, self.OnRightDoubleClick)
		self.closest_target = None
		self.combobox = None
		self.target_type = None
		self.colorlist = [wxRED, wxBLUE, wxColor(255, 0, 255), wxColor(0, 255, 255)]
		self.colors = {}

	def apply(self, evt):
		self.target_type = evt.GetString()
		self.combobox.SetForegroundColour(self.colors[self.target_type])

	def addComboBox(self, name):
		if self.combobox is None:
			if len(self.targets) > 1:
				sizer = wxBoxSizer(wxHORIZONTAL)
				label = wxStaticText(self, -1, 'Target Type:')
				self.combobox = wxComboBox(self, -1, value=self.target_type,
																							choices=self.targets.keys(),
																style=wxCB_DROPDOWN | wxCB_READONLY | wxCB_SORT)
				EVT_COMBOBOX(self, self.combobox.GetId(), self.apply)
				self.combobox.SetForegroundColour(self.colors[self.target_type])
				sizer.Add(label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
				sizer.Add(self.combobox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
				self.sizer.Insert(0, sizer, 0, wxALIGN_LEFT | wxALL, 5)
				self.Fit()
			elif len(self.targets) == 1:
				self.target_type = name
		else:
			self.combobox.Append(name)

	def deleteComboBox(self, name):
		if self.combobox is None:
			if len(self.targets) > 2:
				self.combobox.Delete(self.combobox.FindString(name))
			elif len(self.targets) == 2:
				self.sizer.Remove(0)
				self.target_type = self.targets.keys()[0]
			else:
				self.target_type = None

	def addTargetType(self, name, value=[]):
		if name in self.targets:
			raise ValueError('Target type already exists')
		try:
			self.colors[name] = self.colorlist[0]
		except IndexError:
			raise RuntimeError('Not enough colors for addition target types')
		del self.colorlist[0]
		self.targets[name] = value
		self.addComboBox(name)

	def deleteTargetType(self, name):
		try:
			self.colorlist.append[self.colors[name]]
			del self.colors[name]
			del self.targets[name]
		except:
			raise ValueError('No such target type')
		self.deleteComboBox(name)
		self.UpdateDrawing()

	def getTargetType(self, name):
		try:
			return self.targets[name]
		except:
			raise ValueError('No such target type')

	def setTargetType(self, name, value):
		if name not in self.targets:
			self.addTargetType(name, value)
		else:
			self.targets[name] = value
		self.UpdateDrawing()

	def clearTargets(self):
		self.targets = {}
		self.UpdateDrawing()

	def addTarget(self, target_type, x, y):
		target = (x, y)
		self.targets[target_type].append(target)
		self.UpdateDrawing()
		return target

	def motion(self, evt):
		ImagePanel.motion(self, evt)
		viewoffset = self.panel.GetViewStart()
		x, y = self.view2image((evt.m_x, evt.m_y))
		self.updateClosest(x, y)

	def updateClosest(self, x, y):
		closest_target = None
		minimum_magnitude = 10
		for target_type in self.targets.values():
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
				self.UpdateDrawing()
		self.closest_target = closest_target
		if closest_target is not None:
			self.UpdateDrawing()

	def OnLeftDoubleClick(self, evt):
		if self.target_type is not None:
			viewoffset = self.panel.GetViewStart()
			x, y = self.view2image((evt.m_x, evt.m_y))
			target = self.addTarget(self.target_type, x, y)
			if callable(self.callback):
				self.callback(self.target_type, self.targets[self.target_type])

	# needs to be stored rather than generated
	def getTargetBitmap(self, target, color=wxBLACK):
		penwidth = 1
		length = 15
		for target_type in self.targets:
			if target in self.targets[target_type]:
				color = self.colors[target_type]
		if target == self.closest_target:
			color = wxColor(color.Red()/2, color.Green()/2, color.Blue()/2)
		pen = wxPen(color, 1)
		mem = wxMemoryDC()
		bitmap = wxEmptyBitmap(length, length)
		mem.SelectObject(bitmap)
		mem.SetBrush(wxBrush(color, wxTRANSPARENT))
		mem.SetPen(pen)
		mem.DrawLine(length/2, 0, length/2, length)
		mem.DrawLine(0, length/2, length, length/2)
		mem.SelectObject(wxNullBitmap)
		bitmap.SetMask(wxMaskColour(bitmap, wxBLACK))
		return bitmap

	def drawTarget(self, dc, target):
		bitmap = self.getTargetBitmap(target)
		dc.DrawBitmap(bitmap, target[0] - bitmap.GetWidth()/2,
													target[1] - bitmap.GetHeight()/2, 1)

	def OnRightDoubleClick(self, evt):
		if self.closest_target is not None:
			target_type, value = self.deleteTarget(self.closest_target)
			self.closest_target = None
			if callable(self.callback):
				self.callback(target_type, value)

	# could be hazardous if more than same target exists in type or multiple type
	def deleteTarget(self, target):
		for target_type in self.targets:
			if target in self.targets[target_type]:
				self.targets[target_type].remove(target)
				self.UpdateDrawing()
				return target_type, self.targets[target_type]

	def Draw(self, dc):
		ImagePanel.Draw(self, dc)
		dc.BeginDrawing()
		for target_type in self.targets.values():
			for target in target_type:
				self.drawTarget(dc, target)
		dc.EndDrawing()

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = TargetImagePanel(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	#app.panel.setImage(open('test.jpg', 'rb').read())
	app.panel.setImageFromMrcString(open('test1.mrc', 'rb').read())
	app.MainLoop()

