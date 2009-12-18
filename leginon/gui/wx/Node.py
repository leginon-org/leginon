# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Node.py,v $
# $Revision: 1.30 $
# $Name: not supported by cvs2svn $
# $Date: 2005-04-21 00:39:19 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import icons
import threading
import wx
import wx.lib.scrolledpanel
import gui.wx.MessageLog
import gui.wx.ToolBar
import gui.wx.Events

NodeInitializedEventType = wx.NewEventType()

EVT_NODE_INITIALIZED = wx.PyEventBinder(NodeInitializedEventType)

class NodeInitializedEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(NodeInitializedEventType)
		self.node = node
		self.event = threading.Event()

class Panel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent, id=-1, nodeclass=None, **kwargs):

		self.node = None
		self.nodeclass = nodeclass
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id, **kwargs)

		self.toolbar = parent.getToolBar()

		self.szmain = wx.GridBagSizer(5, 5)

		self.messagelog = gui.wx.MessageLog.MessageLog(parent.swmessage, self)
		self.messagelog.Show(False)

		self.Bind(EVT_NODE_INITIALIZED, self._onNodeInitialized)
		self.Bind(gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(gui.wx.Events.EVT_SET_TARGETS, self.onSetTargets)
		self.Bind(gui.wx.Events.EVT_ACQUISITION_DONE, self.onAcquisitionDone)
		self.Bind(gui.wx.MessageLog.EVT_ADD_MESSAGE, self.onAddMessage)

	def OnChildFocus(self, evt):
		evt.Skip()

	def onAddMessage(self, evt):
		self.messagelog.addMessage(evt.level, evt.message)

	def _onNodeInitialized(self, evt):
		self.node = evt.node
		self.onNodeInitialized()
		evt.event.set()

	def onNodeInitialized(self):
		pass

	def onSetImage(self, evt):
		if evt.typename is None:
			self.imagepanel.setImage(evt.image)
		else:
			self.imagepanel.setImageType(evt.typename, evt.image)

	def onSetTargets(self, evt):
		self.imagepanel.setTargets(evt.typename, evt.targets)
		if hasattr(evt, 'event'):
			evt.event.set()

	def _getStaticBoxSizer(self, label, *args):
		sbs = wx.StaticBoxSizer(wx.StaticBox(self, -1, label), wx.VERTICAL)
		gbsz = wx.GridBagSizer(5, 5)
		sbs.Add(gbsz, 1, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbs, *args)
		return gbsz

	def onAcquisitionDone(self, evt):
		pass

	def acquisitionDone(self):
		evt = gui.wx.Events.AcquisitionDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onGetInstrumentDone(self, evt):
		pass

	def getInstrumentDone(self):
		evt = gui.wx.Events.GetInstrumentDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetInstrumentDone(self, evt):
		pass

	def setInstrumentDone(self):
		evt = gui.wx.Events.SetInstrumentDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def playerEvent(self, state, window=None):
		evt = gui.wx.Events.PlayerEvent(state)
		if window is None:
			window = self
		window.GetEventHandler().AddPendingEvent(evt)

	def setStatus(self, status):
		level = 'STATUS'
		evt = gui.wx.Events.StatusUpdatedEvent(self, level, status)
		self.GetEventHandler().AddPendingEvent(evt)

