# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Dialog.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx

class Dialog(wx.Dialog):
	def __init__(self, parent, title, subtitle):
		wx.Dialog.__init__(self, parent, -1, title)

		self.sz = wx.GridBagSizer(5, 5)

		self.buttons = {}

		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.AddGrowableCol(0)

		self.sbsz = wx.StaticBoxSizer(wx.StaticBox(self, -1, subtitle), wx.VERTICAL)
		self.sbsz.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		self.szdialog = wx.GridBagSizer(5, 5)
		self.szdialog.Add(self.sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szdialog.Add(self.szbuttons, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szdialog.AddGrowableRow(0)
		self.szdialog.AddGrowableCol(0)

		self.onInitialize()

		self.SetSizerAndFit(self.szdialog)

	def onInitialize(self):
		pass

	def addButton(self, label, id=-1):
		col = len(self.buttons)
		self.buttons[label] = wx.Button(self, id, label)
		if col > 0:
			flags = wx.ALIGN_CENTER
		else:
			flags = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
		self.szbuttons.Add(self.buttons[label], (0, col), (1, 1), flags)
		return self.buttons[label]

