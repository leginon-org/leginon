from wxPython.wx import *

class wxMessage(wxPanel):
	def __init__(self, parent, type, message):
		wxPanel.__init__(self, parent, -1, style=wxSIMPLE_BORDER)

		self.SetBackgroundColour(wxWHITE)

		image = wxImage('icons/%s.bmp' % type)
		bitmap = wxBitmapFromImage(image)
		self.icon = wxStaticBitmap(self, -1, bitmap,
														size=wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
		self.message = message
		self.text = wxStaticText(self, -1, '', style=wxST_NO_AUTORESIZE)
		self.text.SetLabel(self.message)
		EVT_SIZE(self.text, self.OnTextSize)
		self.button = wxButton(self, -1, 'Clear')

		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.sizer.Add(self.icon, 0, wxALIGN_CENTER|wxALL, 3)
		self.sizer.Add(self.text, 1, wxALIGN_CENTER|wxALL, 3)
		self.sizer.Add(self.button, 0, wxALIGN_CENTER|wxALL, 3)
		self.SetSizerAndFit(self.sizer)

	def OnTextSize(self, evt):
		self.SetToolTip(wxToolTip(''))
		size = evt.GetSize()
		if self.text.GetTextExtent(self.message)[0] < size[0]:
			self.text.SetLabel(self.message)
		elif self.text.GetTextExtent('...')[0] > size[0]:
			self.text.SetLabel('')
		else:
			min = 0
			max = len(self.message) - 1
			while True:
				i = (max - min)/2 + min
				extent = self.text.GetTextExtent(self.message[:i] + '...')
				if extent[0] < size[0]:
					if i <= min:
						break
					min = i
				elif extent[0]  > size[0]:
					max = i
				else:
					break
			self.text.SetLabel(self.message[:i] + '...')
			self.SetToolTip(wxToolTip(self.message))

	def wordWrap(self, width):
		start = 0
		i = 0
		message = self.message
		while i < len(message):
			if self.text.GetTextExtent(message[start:i])[0] > width:
				message = message[:i - 1] + '\n' + message[i - 1:]
				i += 1
				start = i + 1
			i += 1
		self.text.SetLabel(message)

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
	app.messagelog.addMessage('info', 'This is information blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah')
	app.MainLoop()

