from wxPython.wx import *
from cStringIO import StringIO

class ImagePanel(wxPanel):
	def __init__(self, parent, id):
		wxPanel.__init__(self, parent, id)
		self.image = None
		self.bitmap = None
		EVT_MOTION(self, self.motion)
		EVT_PAINT(self, self.OnPaint)
		wxInitAllImageHandlers()

	def setImage(self, image):
		self.clearImage()
		self.image = wxImageFromStream(StringIO(image))
		self.SetSize(wxSize(self.image.GetWidth(), self.image.GetHeight()))
		self.bitmap = wxBitmapFromImage(self.image)
		dc = wxClientDC(self)
		dc.BeginDrawing()
		dc.Clear()
		dc.DrawBitmap(self.bitmap, 0, 0)
		dc.EndDrawing()

	def clearImage(self):
		self.image = None
		self.bitmap = None
		dc = wxClientDC(self)
		dc.BeginDrawing()
		dc.Clear()
		dc.EndDrawing()

	def motion(self, evt):
		if self.image is None:
			return
		try:
			rgb = (self.image.GetRed(evt.m_x, evt.m_y),
							self.image.GetGreen(evt.m_x, evt.m_y),
							self.image.GetBlue(evt.m_x, evt.m_y))
			print (evt.m_x, evt.m_y), '=', rgb
		except:
			pass

	def OnPaint(self, evt):
		if self.image is None:
			return
		# needs clipping
		dc = wxPaintDC(self)
		dc.BeginDrawing()
		dc.DrawBitmap(self.bitmap, 0, 0)
		dc.EndDrawing()

class TargetImagePanel(ImagePanel):
	def __init__(self, parent, id):
		ImagePanel.__init__(self, parent, id)
		self.targets = []
		EVT_LEFT_DCLICK(self, self.drawTarget)
		EVT_RIGHT_DCLICK(self, self.eraseTarget)

	def clearImage(self):
		self.targets = []
		ImagePanel.clearImage(self)

	def drawTarget(self, evt):
		if self.image is None:
			return
		self.targets.append((evt.m_x, evt.m_y))
		dc = wxClientDC(self)
		dc.BeginDrawing()
		dc.SetBrush(wxBrush('RED', wxTRANSPARENT))
		dc.SetPen(wxPen('RED', 2))
		dc.DrawCircle(evt.m_x, evt.m_y, 15)
		dc.EndDrawing()

	def eraseTarget(self, evt):
		try:
			self.targets.remove((evt.m_x, evt.m_y))
		except:
			return
		# lame
		dc = wxClientDC(self)
		dc.BeginDrawing()
		dc.DrawBitmap(self.bitmap, 0, 0)
		dc.SetBrush(wxBrush('RED', wxTRANSPARENT))
		dc.SetPen(wxPen('RED', 2))
		for target in self.targets:
			dc.DrawCircle(target[0], target[1], 15)
		dc.EndDrawing()

	def OnPaint(self, evt):
		ImagePanel.OnPaint(self, evt)
		dc = wxPaintDC(self)
		dc.BeginDrawing()
		dc.SetBrush(wxBrush('RED', wxTRANSPARENT))
		dc.SetPen(wxPen('RED', 2))
		for target in self.targets:
			dc.DrawCircle(target[0], target[1], 15)
		dc.EndDrawing()

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			frame.Show(true)
			self.SetTopWindow(frame)
			self.panel = TargetImagePanel(frame, -1)
			return true

	app = MyApp(0)
	app.panel.setImage(open('test.jpg', 'rb').read())
	app.MainLoop()

