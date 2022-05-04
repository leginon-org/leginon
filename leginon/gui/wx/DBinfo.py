# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import leginon.gui.wx.Dialog

import sys
import wx
import sinedon

class Dialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent):
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, 'Leginon DB')

	def onInitialize(self):
		label = wx.StaticText(self, -1, 'Leginon Database Info')
		font = label.GetFont()
		font.SetPointSize(font.GetPointSize()*2)
		label.SetFont(font)
		self.sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)

		try:
			dbconfig = sinedon.getConfig('leginondata')
			print dbconfig['db']
			dbinfo1 = 'host: %s' % (dbconfig['host'],)
			dbinfo2 = 'database: %s' % (dbconfig['db'])
		except KeyError:
			dbinfo1 = 'Error: can not find valid sinedon.cfg'
			dbinfo2 = ''
		except Exception:
			raise
		label = wx.StaticText(self, -1, '%s' % dbinfo1)
		self.sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, '%s' % dbinfo2)
		self.sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER)

		self.addButton('OK', wx.ID_OK, wx.ALIGN_CENTER)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'DBinfo Test')
			dialog = Dialog(frame)
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

