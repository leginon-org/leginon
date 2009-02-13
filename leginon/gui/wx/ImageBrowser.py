#!/usr/bin/env python
import copy
import leginondata
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
		self.sbsz_staticbox = wx.StaticBox(self, -1, "Image Browser")
		self.sessionlab = wx.StaticText(self, -1, "Sessions:")
		self.imagelab = wx.StaticText(self, -1, "Images:")
		names = self.getSessions()
		self.sessionbox = wx.ListBox(self, -1, choices=names, style=wx.LB_SINGLE)
		self.imagebox = wx.ListBox(self, -1, choices=[], style=wx.LB_SINGLE)
		self.publish = wx.Button(self, -1, "Publish")
		self.preview = wx.CheckBox(self, -1, "Preview")

		self.__set_properties()
		self.__do_layout()

		self.Bind(wx.EVT_LISTBOX, self.onSessionSelect, self.sessionbox)
		self.Bind(wx.EVT_LISTBOX, self.onImageSelect, self.imagebox)
		self.Bind(wx.EVT_BUTTON, self.onPublish, self.publish)

	def __set_properties(self):
		if self.imagebox.GetCount() > 0:
			self.imagebox.SetSelection(1)

	def __do_layout(self):
		sbsz = wx.StaticBoxSizer(self.sbsz_staticbox, wx.VERTICAL)
		szmain = wx.FlexGridSizer(3, 2, 5, 5)
		szmain.Add(self.sessionlab, 0, wx.ADJUST_MINSIZE, 0)
		szmain.Add(self.imagelab, 0, wx.ADJUST_MINSIZE, 0)
		szmain.Add(self.sessionbox, 0, wx.EXPAND, 0)
		szmain.Add(self.imagebox, 0, wx.EXPAND, 0)
		szmain.Add(self.publish, 0, wx.ADJUST_MINSIZE, 0)
		szmain.Add(self.preview, 0, wx.ADJUST_MINSIZE, 0)
		szmain.AddGrowableRow(1)
		szmain.AddGrowableCol(1)
		sbsz.Add(szmain, 1, wx.EXPAND, 0)
		self.SetAutoLayout(True)
		self.SetSizer(sbsz)
		sbsz.Fit(self)
		sbsz.SetSizeHints(self)

	def getSessions(self):
		user = self.node.session['user']
		qsession = leginondata.SessionData(user=user)
		sessionlist = self.node.research(qsession)
		self.session_names = [s['name'] for s in sessionlist]
		self.session_dict = dict(zip(self.session_names,sessionlist))
		return self.session_names

	def getImages(self, sessiondata):
		qimage = leginondata.AcquisitionImageData(session=sessiondata)
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

if __name__ == "__main__":
	import node
	import Icons
	class App(wx.App):
		def OnInit(self):
			mysession = leginondata.SessionData()
			mynode = node.Node('mnode', session=mysession)

			icon = wx.EmptyIcon()
			icon.CopyFromBitmap(Icons.icon("imagebrowser"))
			
			frame = wx.Frame(None, -1, 'Image Browser')
			frame.SetIcon(icon)
			frame.node=mynode
			ImageBrowserPanel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

