#!/usr/bin/env python

from wxPython.wx import *
import cStringIO
import Numeric
import Image
import math

import Mrc
from NumericImage import NumericImage

class ImagePanel(wxPanel):
	def __init__(self, parent, id):
		self.image = None
		self.bitmap = None
		self.buffer = wxEmptyBitmap(1, 1)
#		wxPanel.__init__(self, parent, id, size=wxSize(256, 256))
#		wxPanel.__init__(self, parent, id, style=wxNO_FULL_REPAINT_ON_RESIZE)
		wxPanel.__init__(self, parent, id)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.SetAutoLayout(true)
		self.SetSizer(self.sizer)
		self.panel = wxScrolledWindow(self, -1, size=(512, 512))
		self.panel.SetScrollRate(1,1)
		self.sizer.Add(self.panel)
		size = self.panel.GetSize()
		self.sizer.SetItemMinSize(self.panel, size.GetWidth(), size.GetHeight())
		self.Fit()
		EVT_MOTION(self.panel, self.motion)
		EVT_PAINT(self.panel, self.OnPaint)
		EVT_SIZE(self.panel, self.OnSize)
#		wxInitAllImageHandlers()

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
		self.panel.SetVirtualSize(wxSize(self.bitmap.GetWidth(), self.bitmap.GetHeight()))
		self.panel.Scroll(0, 0)
#		self.panel.SetSize(wxSize(self.bitmap.GetWidth(), self.bitmap.GetHeight()))
#		size = self.panel.GetSize()
#		self.sizer.SetItemMinSize(self.panel, size.GetWidth(), size.GetHeight())
#		self.Fit()
		self.buffer = wxEmptyBitmap(self.bitmap.GetWidth(), self.bitmap.GetHeight())
		self.UpdateDrawing()

	def clearImage(self):
		self.image = None
		self.bitmap = None
		self.UpdateDrawing()

	def motion(self, evt):
		if self.image is None:
			return
		try:
			viewoffset = self.panel.GetViewStart()
			xy = (viewoffset[0] + evt.m_x, viewoffset[1] + evt.m_y)
			#rgb = self.image.getpixel(xy)
			rgb = self.image[xy[1], xy[0]]
			print xy, '=', rgb
		except:
			pass

	def UpdateDrawing(self):
		clientdc = wxClientDC(self.panel)
		self.panel.PrepareDC(clientdc)
		dc = wxBufferedDC(clientdc, self.buffer)
		self.Draw(dc)

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
		dc = wxBufferedDC(wxClientDC(self.panel), self.buffer)
		self.Draw(dc)

	def OnPaint(self, evt):
		dc = wxBufferedPaintDC(self.panel, self.buffer)

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
		self.updateClosest(viewoffset[0] + evt.m_x, viewoffset[1] + evt.m_y)

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
			target = self.addTarget(self.target_type, viewoffset[0] + evt.m_x,
																								viewoffset[1] + evt.m_y)
			if callable(self.callback):
				self.callback(self.target_type, self.targets[self.target_type])

	def drawTarget(self, dc, target, color=wxBLACK):
		for target_type in self.targets:
			if target in self.targets[target_type]:
				color = self.colors[target_type]
		if target == self.closest_target:
			color = wxColor(color.Red()/2, color.Green()/2, color.Blue()/2)
		dc.SetBrush(wxBrush(color, wxTRANSPARENT))
		pen = wxPen(color, 1)
		dc.SetPen(pen)
		#dc.SetPen(wxPen(color, 3))

		#dc.DrawCircle(target[0], target[1], 15)

		dc.DrawLine(target[0] - 10, target[1], target[0] + 11, target[1])
		dc.DrawLine(target[0], target[1] - 10, target[0], target[1] + 11)

#		for i in range(target[0] - 10, target[0] + 11):
#			for j in range(-1, 2):
#				color = wxColour(dc.GetPixel(i, target[1] + j).Red(), 0, 0)
#				pen.SetColour(color)
#				dc.SetPen(pen)
#				dc.DrawPoint(i, target[1] + j)
#
#		for i in range(target[1] - 10, target[1] + 11):
#			for j in range(-1, 2):
#				color = wxColour(dc.GetPixel(target[0] + j, i).Red(), 0, 0)
#				pen.SetColour(color)
#				dc.SetPen(pen)
#				dc.DrawPoint(target[0] + j, i)

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

