import os
import wx
import wx.lib.throbber
import gui.wx.Icons

class Throbber(wx.lib.throbber.Throbber):
	def __init__(self, parent):
		emptybitmap = wx.EmptyBitmap(16, 16)
		emptybitmap.SetMask(wx.Mask(emptybitmap, wx.BLACK))
		images = [emptybitmap]
		for i in range(1, 9):
			path = os.path.join('processing', 'green%d' % i)
			bitmap = gui.wx.Icons.icon(path)
			images.append(bitmap)

		wx.lib.throbber.Throbber.__init__(self, parent, -1, images, size=(16, 16),
																			frameDelay=0.1)

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
			throbber.Start()
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

