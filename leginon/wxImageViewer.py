#!/usr/bin/env python

from wxPython.wx import *
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

		self.sizer = wxBoxSizer(wxVERTICAL)
		self.SetAutoLayout(true)
		self.SetSizer(self.sizer)

		# need "inside" size
		self.panel = wxScrolledWindow(self, -1, size=self.size)
		self.panel.SetScrollRate(1,1)
		self.panel.SetCursor(wxCROSS_CURSOR)
		self.sizer.Add(self.panel)
		size = self.panel.GetSize()
		self.sizer.SetItemMinSize(self.panel, size.GetWidth(), size.GetHeight())

		self.initZoom()
#		self.initScaleEntry()
#		self.initValueLabels()
		EVT_MOTION(self.panel, self.motion)

		self.Fit()

		EVT_PAINT(self.panel, self.OnPaint)
		EVT_SIZE(self.panel, self.OnSize)

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
		self.valuesizer = wxBoxSizer(wxHORIZONTAL)
		self.valuesizer.Add(wxStaticText(self, -1, 'x: '))
		self.valuesizer.Add(self.xlabel)
		self.valuesizer.Add(wxStaticText(self, -1, 'y: '))
		self.valuesizer.Add(self.ylabel)
		self.valuesizer.Add(wxStaticText(self, -1, 'Value: '))
		self.valuesizer.Add(self.valuelabel)
		self.sizer.Prepend(self.valuesizer)

	def initZoom(self):
		self.zoomsizer = wxBoxSizer(wxHORIZONTAL)
		zoombutton = wxButton(self, -1, 'Zoom')
		EVT_BUTTON(self, zoombutton.GetId(), self.OnZoomButton)
		self.zoomsizer.Add(zoombutton, 0, wxCENTER | wxALL, 3)
		self.zoomsizer.Add(wxStaticText(self, -1, 'Zoom:'), 0, wxCENTER | wxALL, 3)
		self.zoomlabel = wxStaticText(self, -1, '')
		self.updateZoomLabel()
		self.zoomsizer.Add(self.zoomlabel, 0, wxCENTER | wxALL, 3)
		self.sizer.Prepend(self.zoomsizer)

	def OnZoomButton(self, evt):
		self.panel.SetCursor(wxStockCursor(wxCURSOR_MAGNIFIER))
		EVT_LEFT_UP(self.panel, self.OnZoomIn)
		EVT_RIGHT_UP(self.panel, self.OnZoomOut)

	def OnZoomIn(self, evt):
		self.setScale((self.scale[0]*2, self.scale[1]*2),
									self.view2image((evt.m_x, evt.m_y)))
		self.updateZoomLabel()

	def OnZoomOut(self, evt):
		self.setScale((self.scale[0]/2, self.scale[1]/2),
									self.view2image((evt.m_x, evt.m_y)))
		self.updateZoomLabel()

	def updateZoomLabel(self):
		self.zoomlabel.SetLabel(str(self.scale[0]) + 'x')

	def initScaleEntry(self):
		self.scalesizer = wxBoxSizer(wxHORIZONTAL)
		self.scale_entry = {}
		for axis, i in [('x', 0), ('y', 1)]:
			self.scalesizer.Add(wxStaticText(self, -1, axis + ':'),
													0, wxCENTER | wxALL, 5)
			self.scale_entry[i] = wxTextCtrl(self, -1, value=str(self.scale[i]))
			size = self.scale_entry[i].GetSize()
			size = (size[0]/2, size[1])
			self.scale_entry[i].SetSize(size)
			self.scale_entry[i].SetMaxLength(6)
			self.scalesizer.Add(self.scale_entry[i], 0, wxCENTER | wxALL, 3)
		scalebutton = wxButton(self, -1, 'Scale')
		self.scalesizer.Add(scalebutton, 0, wxCENTER | wxALL, 3)
		EVT_BUTTON(self, scalebutton.GetId(), self.OnScale)
		self.sizer.Prepend(self.scalesizer)

	def getEntryScale(self):
		scale = list(self.scale)
		for i in range(len(self.scale)):
			try:
				scale[i] = float(self.scale_entry[i].GetValue())
			except:
				self.scale_entry[i].SetValue(str(self.scale[i]))
		return scale

	def OnScale(self, evt):
		self.setScale(self.getEntryScale(), self.getViewCenter())

	def getViewCenter(self):
		center = self.panel.GetClientSize()
		center = (center[0]/2, center[1]/2)
		return self.view2image(center)

	def setScale(self, scale, offset=None):
		self.scale = tuple(scale)
		if self.bitmap is not None:
			self.panel.SetVirtualSize((self.bitmap.GetWidth()*self.scale[0],
																	self.bitmap.GetHeight()*self.scale[1]))
		dc = wxClientDC(self.panel)
		dc.BeginDrawing()
		dc.Clear()
		dc.EndDrawing()
		self.UpdateDrawing()
		if offset is not None:
			center = self.panel.GetClientSize()
			center = (center[0]/2, center[1]/2)
			self.panel.Scroll((offset[0])*self.scale[0] - center[0],
												(offset[1])*self.scale[1] - center[1])
		else:
			self.panel.Scroll(0, 0)
		#self.panel.Refresh(0)

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
		self.panel.SetVirtualSize(wxSize(self.bitmap.GetWidth() * self.scale[0],
																			self.bitmap.GetHeight() * self.scale[1]))
		self.panel.Scroll(0, 0)
		self.buffer = wxEmptyBitmap(self.bitmap.GetWidth(), self.bitmap.GetHeight())
		self.UpdateDrawing()

	def clearImage(self):
		self.image = None
		self.bitmap = None
		self.UpdateDrawing()

	def view2image(self, xy):
		viewoffset = self.panel.GetViewStart()
		return (int(round((viewoffset[0] + xy[0]) / self.scale[0])),
						int(round((viewoffset[1] + xy[1]) / self.scale[1])))

	def image2view(self, xy):
		viewoffset = self.panel.GetViewStart()
		return (int(round((xy[0] * self.scale[0]) - viewoffset[0])),
						int(round((xy[1] * self.scale[1]) - viewoffset[1])))

	def motion(self, evt):
		if self.image is None:
			return
		try:
			x, y = self.view2image((evt.m_x, evt.m_y))
			value = self.image[y, x]
			self.drawLabel((x, y), value)
#			self.xlabel.SetLabel(str(x))
#			self.ylabel.SetLabel(str(y))
#			self.valuelabel.SetLabel(str(value))
		except:
			pass

	def drawLabel(self, xy, value):
		dc = wxClientDC(self.panel)
		dc.BeginDrawing()

		dc.SetBrush(wxBrush(wxWHITE))
		dc.SetPen(wxPen(wxBLACK, 1))

		string = '(%d, %d), %d' % (xy[0], xy[1], value)

		try:
			apply(self.blit, self.damaged)
		except AttributeError:
			pass

		extent = dc.GetFullTextExtent(string, wxNORMAL_FONT)

		center = self.panel.GetClientSize()
		center = (center[0]/2, center[1]/2)

		xy = self.image2view(xy)

		if xy[0] <= center[0]:
			xoffset = 10
		else:
			xoffset = -(10 + extent[0] + 4)
		if xy[1] <= center[1]:
			yoffset = 10
		else:
			yoffset = -(10 + extent[1] + 4)

		xy = (int(round((xy[0] + xoffset))),
					int(round((xy[1] + yoffset))))

		self.damaged = (xy[0], xy[1],
										extent[0] + 4, extent[1] + 4)

		#dc.DrawRectangle(xy[0], xy[1], 50, 20)
		apply(dc.DrawRectangle, self.damaged)

		dc.SetFont(wxNORMAL_FONT)
		dc.DrawText(string, xy[0] + 2 , xy[1] + 2)

		dc.EndDrawing()

	def blit(self, x, y, w, h):
		dc = wxMemoryDC()
		dc.SelectObject(self.buffer)
		#dc.SetUserScale(self.scale[0], self.scale[1])
		viewoffset = self.panel.GetViewStart()
		clientdc = wxClientDC(self.panel)
		size = self.panel.GetClientSize()
		clientdc.SetUserScale(self.scale[0], self.scale[1])
		ix, iy = self.view2image((x, y))
		vx, vy = self.image2view((x, y))
		#clientdc.Blit(x, y, w, h, dc, ix, iy)
		clientdc.Blit(x/self.scale[0], y/self.scale[1],
									w/self.scale[0] + 1, h/self.scale[1] + 1, dc, ix, iy)

	def UpdateDrawing(self):
		if USE_BUFFERED_DC:
			clientdc = wxClientDC(self.panel)
			self.panel.PrepareDC(clientdc)
			dc = wxBufferedDC(clientdc, self.buffer)
			self.Draw(dc)
		else:
			dc = wxMemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			viewoffset = self.panel.GetViewStart()
			clientdc = wxClientDC(self.panel)
			clientdc.SetUserScale(self.scale[0], self.scale[1])
			size = self.panel.GetClientSize()
			clientdc.Blit(0, 0, Numeric.ceil(size[0]/self.scale[0]),
													Numeric.ceil(size[1]/self.scale[1]), dc,
													viewoffset[0]/self.scale[0],
													viewoffset[1]/self.scale[1])

	def Draw(self, dc):
		dc.BeginDrawing()
		if self.bitmap is None:
			dc.Clear()
		else:
			dc.DrawBitmap(self.bitmap, 0, 0)
		dc.EndDrawing()

	def OnSize(self, evt):
		width, height = self.panel.GetSizeTuple()
		self.buffer = wxEmptyBitmap(width, height)
		self.UpdateDrawing()

	def OnPaint(self, evt):
		if USE_BUFFERED_DC:
			dc = wxBufferedPaintDC(self.panel, self.buffer)
		else:
			dc = wxMemoryDC()
			dc.SelectObject(self.buffer)
			self.Draw(dc)
			viewoffset = self.panel.GetViewStart()
			paintdc = wxPaintDC(self.panel)
			paintdc.SetUserScale(self.scale[0], self.scale[1])
			size = self.panel.GetClientSize()
			paintdc.Blit(0, 0, Numeric.ceil(size[0]/self.scale[0]),
													Numeric.ceil(size[1]/self.scale[1]), dc,
													viewoffset[0]/self.scale[0],
													viewoffset[1]/self.scale[1])

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

