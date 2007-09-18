# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Stats.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-18 17:25:26 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx

class Panel(wx.Panel):
	nonestr = ''
	def __init__(self, parent, id, **kwargs):
		wx.Panel.__init__(self, parent, id, **kwargs)
		self.SetBackgroundColour(wx.Colour(255, 255, 210))

		self.sz = wx.GridBagSizer(0, 0)

		self.labels = {}
		self.values = {}
		for i, label in enumerate(self.order):
			self.labels[label] = wx.StaticText(self, -1, label + ':')
			self.values[label] = wx.StaticText(self, -1, self.nonestr, style=wx.ALIGN_RIGHT)
			#smaller font size
			#sfont = self.labels[label].GetFont()
			#sfont.SetPointSize(sfont.GetPointSize() - 2)
			#self.labels[label].SetFont(sfont)
			#self.values[label].SetFont(sfont)

			#add widgets to frame
			self.sz.Add(self.labels[label], (i, 0), (1, 1),
				wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
			self.sz.Add(self.values[label], (i, 1), (1, 1),
				wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 3)
			self.sz.AddGrowableRow(i)

		self.sz.AddGrowableCol(1)

		self.SetSizerAndFit(self.sz)

	def set(self, values):
		for label in self.order:
			try:
				s = '%g' % values[self.map[label]]
			except KeyError:
				s = self.nonestr
			self.values[label].SetLabel(s)
		self.sz.Layout()
		self.Fit()

class Stats(Panel):
	nonestr = 'N/A'
	order = [
		'Mean',
		'Min.',
		'Max.',
		'Std. dev.',
	]

	map = {
		'Mean': 'mean',
		'Min.': 'min',
		'Max.': 'max',
		'Std. dev.': 'std',
	}

class Position(Panel):
	order = [
		'x',
		'y',
		'Value',
	]

	map = {
		'x': 'x',
		'y': 'y',
		'Value': 'value',
	}

