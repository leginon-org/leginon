# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/About.py,v $
# $Revision: 1.4 $
# $Name: not supported by cvs2svn $
# $Date: 2006-02-17 18:13:58 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import gui.wx.Dialog
import sys
import wx
import numarray
import _mysql
import Image
import version

class Dialog(gui.wx.Dialog.Dialog):
	def __init__(self, parent):
		gui.wx.Dialog.Dialog.__init__(self, parent, 'About Leginon')

	def onInitialize(self):
		label = wx.StaticText(self, -1, 'Leginon')
		font = label.GetFont()
		font.SetPointSize(font.GetPointSize()*2)
		label.SetFont(font)
		self.sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)

		label = wx.StaticText(self, -1, 'Automated Data Acquisition Software for Transmission Electron Microscopy')
		self.sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER)

		v = version.getVersion()
		if not v:
			v = '(None)'
		label = wx.StaticText(self, -1, 'Version %s' % v)
		self.sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER)

		label = wx.StaticText(self, -1, 'Tomography contributed by:')
		self.sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Christian Suloway (Jensen Lab, Caltech)')
		self.sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Shawn Zheng (Agard Lab, UCSF)')
		self.sz.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER)

		label = wx.StaticText(self, -1, 'System information')
		self.sz.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER)

		sz = wx.GridBagSizer(0, 20)

		label = wx.StaticText(self, -1, 'Python:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		try:
			v = sys.version.split()[0]
		except:
			v = 'Unknown'
		label = wx.StaticText(self, -1, v)
		sz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'wxPython:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		try:
			v = wx.__version__
		except:
			v = 'Unknown'
		label = wx.StaticText(self, -1, v)
		sz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'numarray:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		try:
			v = numarray.__version__
		except:
			v = 'Unknown'
		label = wx.StaticText(self, -1, v)
		sz.Add(label, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'mysql-python:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		try:
			v = _mysql.__version__
		except:
			v = 'Unknown'
		label = wx.StaticText(self, -1, v)
		sz.Add(label, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'PIL:')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		try:
			v = Image.VERSION
		except:
			v = 'Unknown'
		label = wx.StaticText(self, -1, v)
		sz.Add(label, (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(0)

		self.sz.Add(sz, (7, 0), (1, 1), wx.ALIGN_CENTER)

		self.addButton('OK', wx.ID_OK, wx.ALIGN_CENTER)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'About Test')
			dialog = Dialog(frame)
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

