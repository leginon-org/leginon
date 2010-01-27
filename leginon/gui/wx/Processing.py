import os
import wx
import wx.lib.throbber

import leginon.gui.wx.Icons

class Throbber(wx.lib.throbber.Throbber):
	def __init__(self, parent):
		emptybitmap = leginon.gui.wx.Icons.null()
		images = [emptybitmap]
		for i in range(1, 9):
			path = os.path.join('processing', 'green%d' % i)
			bitmap = leginon.gui.wx.Icons.icon(path)
			images.append(bitmap)

		overlay = leginon.gui.wx.Icons.icon('userinput')

		wx.lib.throbber.Throbber.__init__(self, parent, -1, images, size=(16, 16),
																			frameDelay=0.1, overlay=overlay)
		self.ToggleOverlay(False)

	def set(self, value):
		if value == 'user input' and not self.showOverlay:
			self.ToggleOverlay(True)
		elif self.showOverlay:
			self.ToggleOverlay(False)

		if value == 'processing':
			self.SetToolTip(wx.ToolTip('Processing...'))
			self.Start()
		elif value == 'waiting':
			self.SetToolTip(wx.ToolTip('Waiting...'))
			self.OnTimer(None)
			self.Stop()
		elif value == 'user input':
			self.SetToolTip(wx.ToolTip('Waiting for user input...'))
			self.OnTimer(None)
			self.Stop()
		elif value == 'idle':
			self.SetToolTip(None)
			self.Rest()
		else:
			raise TypeError('Invalid value for set')
		self.Refresh()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Processing Test')
			panel = wx.Panel(frame, -1)
			panel.SetBackgroundColour(wx.WHITE)
			sizer = wx.GridBagSizer(0, 0)
			throbber = Throbber(panel)
			throbber.SetBackgroundColour(wx.WHITE)
			sizer.Add(throbber, (0, 0), (1, 1), wx.ALIGN_CENTER)
			sizer.AddGrowableRow(0)
			sizer.AddGrowableCol(0)
			panel.SetSizerAndFit(sizer)
			throbber.set('processing')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

