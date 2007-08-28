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

	def openImageFile(self, filename):
		self.filename = filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = pyami.mrc.read(filename)
			self.setImage(image.astype(numpy.float32))
		else:
			self.setImage(Image.open(filename))

class MyApp(wx.App):
	def OnInit(self):
		self.frame = wx.Frame(None, -1, 'Image Viewer')
		self.sizer = wx.FlexGridSizer(2,1)

		self.panel = ManualPickerPanel(self.frame, -1)
		self.panel.addTypeTool('Select Particles', toolclass=ImageViewer.TargetTypeTool, display=wx.RED, target=True)
		self.panel.setTargets('Select Particles', [])
		self.panel.SetMinSize((300,300))
		self.sizer.Add(self.panel, 1, wx.EXPAND)

		self.quit = wx.Button(self.frame, -1, 'Next')
		self.quit.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.sizer.Add(self.quit, 0, wx.wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.sizer.AddGrowableRow(0)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	def onQuit(self, evt):
		targets = self.panel.getTargets('Select Particles')
		for target in targets:
			print '%s\t%s' % (target.x, target.y)
		wx.Exit()

if __name__ == '__main__':
	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

	app = MyApp(0)
	app.panel.openImageFile(filename)
	app.MainLoop()

