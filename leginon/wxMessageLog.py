from wxPython.wx import *

class wxMessage(wxPanel):
	def __init__(self, parent, type, message):
		wxPanel.__init__(self, parent, -1, style=wxSIMPLE_BORDER)

		self.SetBackgroundColour(wxWHITE)

		image = wxImage('icons/%s.bmp' % type)
		bitmap = wxBitmapFromImage(image)
		self.icon = wxStaticBitmap(self, -1, bitmap,
														size=wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
		self.text = wxStaticText(self, -1, message)
		self.button = wxButton(self, -1, 'Clear')

		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.sizer.Add(self.icon, 0, wxALIGN_CENTER|wxALL, 3)
		self.sizer.Add(self.text, 0, wxALIGN_CENTER|wxALL, 3)
		self.sizer.Add(0, 0, 1)
		self.sizer.Add(self.button, 0, wxALIGN_CENTER|wxALL, 3)
		self.SetSizerAndFit(self.sizer)

class wxMessageLog(wxScrolledWindow):
	def __init__(self, parent):
		wxScrolledWindow.__init__(self, parent, -1)
		self.SetScrollRate(10, 10)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.SetSizer(self.sizer)

	def addMessage(self, type, message):
		messagewidget = wxMessage(self, type, message)
		self.sizer.Add(messagewidget, 0, wxEXPAND|wxBOTTOM)
		EVT_BUTTON(self, messagewidget.button.GetId(), self.OnButton)

	def OnButton(self, evt):
		button = evt.GetEventObject()
		panel = button.GetParent()
		self.sizer.Remove(panel)
		panel.Destroy()
		self.sizer.Layout()
		self.sizer.FitInside(self)

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = wxPanel(frame, -1)
			self.sizer = wxBoxSizer(wxVERTICAL)
			self.panel.SetSizer(self.sizer)
			self.messagelog = wxMessageLog(self.panel)
			self.sizer.Add(self.messagelog, 1, wxEXPAND)
			frame.Fit()
			frame.Show(True)
			return True

	app = MyApp(0)
	app.messagelog.addMessage('error', 'This is an error')
	app.messagelog.addMessage('warning', 'This is a warning')
	app.messagelog.addMessage('info', 'This is information')
	app.MainLoop()

