
#!/usr/bin/env python

# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/ManualComaFree.py,v $
# $Revision: 1.60 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-31 02:37:06 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import threading
import wx

from pyami import fftfun

import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.ImagePanel

UpdateImagesEventType = wx.NewEventType()
#ManualCheckEventType = wx.NewEventType()
#ManualCheckDoneEventType = wx.NewEventType()

class UpdateImagesEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, UpdateImagesEventType, source.GetId())
		self.SetEventObject(source)

class ManualComaFreeDialog(leginon.gui.wx.Dialog.ConfirmationDialog):
	def __init__(self, parent, title='ManualComaFree'):
		self.node = parent.node
		self.center = (256,256)
		super(ManualComaFreeDialog,self).__init__(parent, title, size=wx.Size(750,750), 
			style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)

	def onInitialize(self):
		super(ManualComaFreeDialog,self).onInitialize()
		self.imagepanel = leginon.gui.wx.ImagePanel.ClickImagePanel(self,-1, mode='horizontal',imagesize=(612,612))

		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.addTypeTool('Tableau', display=True)
		self.imagepanel.selectiontool.setDisplayed('Tableau', True)
		self.mainsz.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.mainsz.AddGrowableRow(0)
		self.mainsz.AddGrowableCol(0)
		#self.SetSizerAndFit(self.mainsz)
		self.SetAutoLayout(True)
		self.Layout()

		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(leginon.gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(leginon.gui.wx.Events.EVT_MANUAL_UPDATED, self.onManualUpdated)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)
		# init values
		self.progress_text = ''
		self.totalcount = 5
		self.count = 0
		self.enableActions(False)

	def onManualUpdated(self, evt):
		# tableau is updated
		pass

	def onImageClicked(self, evt):
		if not self.accept_click:
			return
		# navigate beam tilt and reacquire
		self.count = 0
		self.enableActions(False)
		threading.Thread(target=self.node.navigate, args=(evt.xy,)).start()

	def enableActions(self,active=False):
		self.imagepanel.clicktool.button.SetValue(active)
		self.accept_click = active
		self.bok.Enable(active)
		self.bcancel.Enable(active)

	def onClose(self, evt):
		evt.Skip(True)

	def onSetImage(self, evt):
		if evt.typename == 'Tableau':
			if self.count == self.totalcount:
				self.enableActions(True)
				self.count = 0
				self.progress_text = ''
		else:
			self.count += 1
			self.progress_text = '%d/5' % self.count
		self.setProgress('PREOGRESS: %s' % (self.progress_text,))
		self.imagepanel.setImageType(evt.typename, evt.image)

if __name__ == '__main__':
	from leginon import player
	class Node(object):
		def __init__(self):
			self.beamtilt = 0.01
			self.sites = 4

	class App(wx.App):
		def OnInit(self):
			node = Node()
			frame = wx.Frame(None, -1, 'Focuser Test')
			frame.node = node
			dialog = ManualComaFreeDialog(frame, 'Testing')
			node.manualdialog = dialog
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

