from wxPython.wx import *

import sys, os

rundir = sys.path[0]
iconsdir = os.path.join(rundir, 'icons')
types = ['info', 'warning', 'error']

class wxMessage(wxPanel):
	def __init__(self, parent, type, message, clearcallback=None):
		if type not in types:
			raise ValueError
		self.clearcallback = clearcallback
		wxPanel.__init__(self, parent, -1, style=wxSIMPLE_BORDER)

		self.SetBackgroundColour(wxWHITE)

		self.type = type
		try:
			image = wxImage('%s/%s.bmp' % (iconsdir, type))
			bitmap = wxBitmapFromImage(image)
		except:
			bitmap = wxNullBitmap
		self.icon = wxStaticBitmap(self, -1, bitmap, size=wxSize(bitmap.GetWidth(),
																														bitmap.GetHeight()))

		self.message = message
		self.text = wxStaticText(self, -1, '', style=wxST_NO_AUTORESIZE)
		self.text.SetLabel(self.message)

		self.button = wxButton(self, -1, 'Clear')

		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.sizer.Add(self.icon, 0, wxALIGN_CENTER|wxALL, 3)
		self.sizer.Add(self.text, 1, wxALIGN_CENTER|wxALL, 3)
		self.sizer.Add(self.button, 0, wxALIGN_CENTER|wxALL, 3)
		self.SetSizerAndFit(self.sizer)

		EVT_SIZE(self.text, self.OnTextSize)
		EVT_BUTTON(self.button, self.button.GetId(), self.OnButton)

	def OnTextSize(self, evt):
		size = evt.GetSize()
		width = size[0]
		if self.text.GetTextExtent(self.message)[0] < width:
			label = self.message
			tooltip = ''
		elif self.text.GetTextExtent('...')[0] > width:
			label = ''
			tooltip = ''
		else:
			label = self.message[:self.findTextExtent(width)] + '...'
			tooltip = self.message
		self.text.SetLabel(label)
		self.SetToolTip(wxToolTip(tooltip))

	def findTextExtent(self, width):
		i0 = 0
		i1 = len(self.message)
		while True:
			i = (i1 - i0)/2 + i0
			extent = self.text.GetTextExtent(self.message[:i] + '...')
			if extent[0] < width:
				if i <= i0:
					return i
				i0 = i
			elif extent[0]  > width:
				if i >= i1:
					return i
				i1 = i
			else:
				return i

	def OnButton(self, evt):
		if callable(self.clearcallback):
			self.clearcallback(self)
		else:
			self.Destroy()

class wxMessageLog(wxScrolledWindow):
	def __init__(self, parent):
		wxScrolledWindow.__init__(self, parent, -1, style=wxSIMPLE_BORDER)
		self.SetBackgroundColour(wxWHITE)
		self.SetScrollRate(10, 10)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.emptylabel = wxStaticText(self, -1, 'Message log empty')
		self.sizer.Add(self.emptylabel, 0, wxALL, 3)
		self.messages = []
		self.updateEmptyLabel()
		self.SetSizer(self.sizer)
		self.updateSize()
		EVT_SIZE(self, self.updateSize)

	def updateEmptyLabel(self):
		if len(self.messages) == 0:
			self.sizer.Show(self.emptylabel, True)
		else:
			self.sizer.Show(self.emptylabel, False)

	def updateSize(self, evt=None):
		if len(self.messages) == 0:
			height = self.sizer.GetMinSize()[1]
		else:
			height = 0
			for i, message in enumerate(self.messages):
				if i >= 3:
					break
				height += message.GetSize()[1]
		self.SetSizeHints(-1, height)
		self.SetSize((-1, height))
		self.sizer.FitInside(self)

	def addMessage(self, type, message, clearcallback=None):
		messagewidget = wxMessage(self, type, message, clearcallback)
		self.sizer.Add(messagewidget, 0, wxEXPAND|wxBOTTOM)
		self.messages.append(messagewidget)
		self.updateEmptyLabel()
		self.sizer.Layout()
		self.updateSize()
		return messagewidget

	def removeMessage(self, messagewidget):
		self.messages.remove(messagewidget)
		self.sizer.Remove(messagewidget)
		messagewidget.Destroy()
		self.updateEmptyLabel()
		self.sizer.Layout()
		self.updateSize()

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Message Log')
			self.SetTopWindow(frame)
			self.panel = wxPanel(frame, -1)
			self.sizer = wxBoxSizer(wxVERTICAL)
			self.messagelog = wxMessageLog(self.panel)
			self.sizer.Add(self.messagelog, 1, wxEXPAND, 10)
			self.panel.SetSizerAndFit(self.sizer)
			frame.Fit()
			frame.Show(True)
			return True

	app = MyApp(0)
	app.messagelog.addMessage('error', 'This is an error')
	app.messagelog.addMessage('warning', 'This is a warning')
	app.messagelog.addMessage('info', 'This is information' + ' blah'*50)
	app.MainLoop()

