import wx

class Stats(wx.GridBagSizer):
	def __init__(self, parent):
		wx.GridBagSizer.__init__(self, 3, 3)

		self.statslist = [
			'Mean',
			'Min.',
			'Max.',
			'Std. dev.',
		]

		self.labels = {}
		self.values = {}
		for i, stat in enumerate(self.statslist):
			self.labels[stat] = wx.StaticText(parent, -1, stat + ':')
			self.values[stat] = wx.StaticText(parent, -1, '', style=wx.ALIGN_RIGHT)
			self.Add(self.labels[stat], (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.Add(self.values[stat], (i, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.AddGrowableCol(1)

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
		self.Layout()

