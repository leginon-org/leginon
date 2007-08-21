#!/usr/bin/python -O

import sys
from gui.wx import ImageViewer
import wx
import pyami
import numpy

wx.InitAllImageHandlers()

ImageClickedEventType = wx.NewEventType()
ImageClickDoneEventType = wx.NewEventType()
MeasurementEventType = wx.NewEventType()
DisplayEventType = wx.NewEventType()
TargetingEventType = wx.NewEventType()
SettingsEventType = wx.NewEventType()

EVT_IMAGE_CLICKED = wx.PyEventBinder(ImageClickedEventType)
EVT_IMAGE_CLICK_DONE = wx.PyEventBinder(ImageClickDoneEventType)
EVT_MEASUREMENT = wx.PyEventBinder(MeasurementEventType)
EVT_DISPLAY = wx.PyEventBinder(DisplayEventType)
EVT_TARGETING = wx.PyEventBinder(TargetingEventType)
EVT_SETTINGS = wx.PyEventBinder(SettingsEventType)


class ManualPickerPanel(ImageViewer.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		ImageViewer.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

		self.quit = wx.Button(self, -1, 'Next')
		self.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.sizer.Add(self.quit, (0, 0), (1, 1), wx.EXPAND)

	def onQuit(self, evt):
		targets = self.getTargets('Select Particles')
		for target in targets:
			print '%s\t%s' % (target.x, target.y)
		wx.Exit()


if __name__ == '__main__':
	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			self.panel = ManualPickerPanel(frame, -1)
			self.panel.addTypeTool('Select Particles', toolclass=ImageViewer.TargetTypeTool, display=wx.RED, target=True)
			self.panel.setTargets('Select Particles', [])

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		app.panel.setImage(None)
	elif filename[-4:] == '.mrc':
		image = pyami.mrc.read(filename)
		app.panel.setImage(image.astype(numpy.float32))
	else:
		app.panel.setImage(Image.open(filename))
	app.MainLoop()

