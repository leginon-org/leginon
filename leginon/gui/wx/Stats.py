import wx

class Panel(wx.Panel):
	def __init__(self, parent, id, **kwargs):
		wx.Panel.__init__(self, parent, id, **kwargs)
		self.SetBackgroundColour(wx.Colour(255, 255, 220))

		self.nonestr = ''

		self.sz = wx.GridBagSizer(0, 0)

		self.labels = {}
		self.values = {}
		for i, label in enumerate(self.order):
			self.labels[label] = wx.StaticText(self, -1, label + ':')
			self.values[label] = wx.StaticText(self, -1, self.nonestr,
																				style=wx.ALIGN_RIGHT)
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
		'Std. dev.': 'stdev',
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

