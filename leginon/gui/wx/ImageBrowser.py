#!/usr/bin/env python
import copy
import data
import wx
from gui.wx.Entry import IntEntry, FloatEntry, EVT_ENTRY

ConfigurationChangedEventType = wx.NewEventType()
SetConfigurationEventType = wx.NewEventType()

EVT_CONFIGURATION_CHANGED = wx.PyEventBinder(ConfigurationChangedEventType)
EVT_SET_CONFIGURATION = wx.PyEventBinder(SetConfigurationEventType)

class ConfigurationChangedEvent(wx.PyCommandEvent):
	def __init__(self, configuration, source):
		wx.PyCommandEvent.__init__(self, ConfigurationChangedEventType,
																source.GetId())
		self.SetEventObject(source)
		self.configuration = configuration

class SetConfigurationEvent(wx.PyCommandEvent):
	def __init__(self, configuration, source):
		wx.PyCommandEvent.__init__(self, SetConfigurationEventType, source.GetId())
		self.SetEventObject(source)
		self.configuration = configuration

class ImageBrowserPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)
		self.node = parent.node

		self.image = None
		self.szmain = wx.GridBagSizer(3, 3)

		## two list boxes
		sessionlab = wx.StaticText(self, -1, 'Session:')
		names = self.getSessions()
		self.sessionbox = wx.ListBox(self, -1, choices=names)
		self.szmain.Add(sessionlab, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		self.szmain.Add(self.sessionbox, (1, 0), (1, 1), wx.EXPAND|wx.ALL)

		imagelab = wx.StaticText(self, -1, 'Image:')
		self.imagebox = wx.ListBox(self, -1)
		self.szmain.Add(imagelab, (0, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.szmain.Add(self.imagebox, (1, 1), (1, 1), wx.EXPAND|wx.ALL)

		self.Bind(wx.EVT_LISTBOX, self.onSessionSelect, self.sessionbox)
		self.Bind(wx.EVT_LISTBOX, self.onImageSelect, self.imagebox)

		## buttons
		butsz = wx.GridBagSizer(3, 3)
		publish = wx.Button(self, -1, 'Publish')
		self.Bind(wx.EVT_BUTTON, self.onPublish, publish)
		butsz.Add(publish, (0,0), (1,1))
		self.szmain.Add(butsz, (2,0), (1,1))

		## checkbox for view image
		self.preview = wx.CheckBox(self, -1, label='Preview')
		self.szmain.Add(self.preview, (2,1), (1,1), wx.EXPAND|wx.ALL)

		## main box
		sb = wx.StaticBox(self, -1, 'Image Browser')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sbsz.Add(self.szmain, 0, wx.EXPAND|wx.ALL, 5)

		self.SetSizerAndFit(self.sbsz)

		'''
		self.Bind(wx.EVT_CHOICE, self.onCommonChoice, self.ccommon)
		self.Bind(wx.EVT_BUTTON, self.onCustomButton, bcustom)
		self.Bind(EVT_ENTRY, self.onExposureTime, self.feexposuretime)
		self.Bind(EVT_SET_CONFIGURATION, self.onSetConfiguration)
		'''

		#self.Enable(False)
		self.imagebox.Enable(False)

	def getSessions(self):
		user = self.node.session['user']
		qsession = data.SessionData(user=user)
		sessionlist = self.node.research(qsession)
		self.session_names = [s['name'] for s in sessionlist]
		self.session_dict = dict(zip(self.session_names,sessionlist))
		return self.session_names

	def getImages(self, sessiondata):
		qimage = data.AcquisitionImageData(session=sessiondata)
		imdatalist = self.node.research(qimage, readimages=False)
		imagenames = [imdata['filename'] for imdata in imdatalist]
		self.image_dict = dict(zip(imagenames,imdatalist))
		return imagenames

	def onSessionSelect(self, evt):
		sesname = evt.GetString()
		sesdata = self.session_dict[sesname]
		imagenames = self.getImages(sesdata)
		if imagenames:
			self.imagebox.Set(imagenames)
			self.imagebox.Enable(True)
		else:
			self.imagebox.Set(['no images'])
			self.imagebox.Enable(False)

	def onImageSelect(self, evt):
		previewstate = self.preview.GetValue()
		imname = evt.GetString()
		self.image = self.image_dict[imname]
		if previewstate:
						self.node.loadImage(self.image)

	def onPublish(self, evt):
		if self.image is None:
			return
		self.node.publishImage(self.image)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Browser Test')
			panel = ImageBrowserPanel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

