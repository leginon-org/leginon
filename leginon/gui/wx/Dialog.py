# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Dialog.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-15 02:59:09 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import wx

class Dialog(wx.Dialog):
	def __init__(self, parent, title, subtitle='',
			style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,pos=wx.DefaultPosition):
		wx.Dialog.__init__(self, parent, -1, title, style=style,pos=pos)

		self.parent = parent
		if subtitle:
			sb = wx.StaticBox(self, -1, subtitle)
			self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
	
		self.sz = wx.GridBagSizer(5, 5)

		self.buttons = {}

		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.AddGrowableCol(0)

		if subtitle:
			self.sbsz.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)
			self.mainsz = self.sbsz
		else:
			self.mainsz = self.sz

		self.szdialog = wx.GridBagSizer(5, 5)
		self.szdialog.Add(self.mainsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szdialog.Add(self.szbuttons, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szdialog.AddGrowableRow(0)
		self.szdialog.AddGrowableCol(0)

		self.onInitialize()

		self.SetSizerAndFit(self.szdialog)

	def onInitialize(self):
		pass

	def addButton(self, label, id=-1, flags=None):
		col = len(self.buttons)
		self.buttons[label] = wx.Button(self, id, label)
		if flags is None:
			if col > 0:
				flags = wx.ALIGN_CENTER
			else:
				flags = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
		self.szbuttons.Add(self.buttons[label], (0, col), (1, 1), flags)
		return self.buttons[label]

class ConfirmationDialog(Dialog):
	def onInitialize(self):
		self.bok = self.addButton('&OK')
		self.bcancel = self.addButton('&Cancel')
		self.addDescriptionSizers()
		self.Bind(wx.EVT_BUTTON, self.onOK, self.bok)
		self.Bind(wx.EVT_BUTTON, self.onCancel, self.bcancel)

	def addDescriptionSizers(self):
		'''
		Add stuff into self.mainsz. Need to be implemented in the subclasses
		'''
		pass

	def onOK(self,evt):
		self.EndModal(wx.ID_OK)

	def onCancel(self,evt):
		self.EndModal(wx.ID_CANCEL)
