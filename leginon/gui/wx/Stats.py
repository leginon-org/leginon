import wx

class Stats(wx.Panel):
	def __init__(self, parent, id, **kwargs):
		wx.Panel.__init__(self, parent, id, **kwargs)
		self.SetBackgroundColour(wx.Colour(255, 255, 220))

		self.nonestr = '(N/A)'

		self.statslist = [
			'Mean',
			'Min.',
			'Max.',
			'Std. dev.',
		]

		self.sz = wx.GridBagSizer(0, 5)

		self.labels = {}
		self.values = {}
		for i, stat in enumerate(self.statslist):
			self.labels[stat] = wx.StaticText(self, -1, stat + ':')
			self.values[stat] = wx.StaticText(self, -1, self.nonestr,
																				style=wx.ALIGN_RIGHT)
			self.sz.Add(self.labels[stat], (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.values[stat], (i, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.sz.AddGrowableRow(i)
		self.sz.AddGrowableCol(1)

		self.keymap = {
			'Mean': 'mean',
			'Min.': 'min',
			'Max.': 'max',
			'Std. dev.': 'stdev',
		}

		self.SetSizerAndFit(self.sz)

	def setStats(self, stats):
		for stat in self.statslist:
			try:
				s = str(stats[self.keymap[stat]])
			except KeyError:
				s = self.nonestr
			self.values[stat].SetLabel(s)
		self.sz.Layout()
		#self.Fit()

