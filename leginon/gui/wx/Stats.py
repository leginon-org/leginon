import wx

class StatsPanel(wx.Panel):
	def __init__(self, parent, title='Statistics'):
		wx.Panel.__init__(self, parent, -1)

		self.statslist = [
			'Mean',
			'Min.',
			'Max.',
			'Std. dev.',
		]

		self.labels = {}
		self.values = {}
		self.sz = wx.GridBagSizer(5, 5)
		for i, stat in enumerate(self.statslist):
			self.labels[stat] = wx.StaticText(self, -1, stat + ':')
			self.values[stat] = wx.StaticText(self, -1, '', style=wx.ALIGN_RIGHT)
			self.sz.Add(self.labels[stat], (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.values[stat], (i, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.sz.AddGrowableCol(1)

		self.sbsz = wx.StaticBoxSizer(wx.StaticBox(self, -1, title), wx.VERTICAL)
		self.sbsz.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)
		self.SetSizerAndFit(self.sbsz)

		self.keymap = {
			'Mean': 'mean',
			'Min.': 'min',
			'Max.': 'max',
			'Std. dev.': 'stdev',
		}

	def setStats(self, stats):
		for stat in self.statslist:
			try:
				value = stats[self.keymap[stat]]
			except KeyError:
				value = ''
			self.values[stat].SetLabel(str(value))
		self.sbsz.Layout()

