import logging
import wx

class LoggingConfiguration(object):
	def __init__(self):
		self.printhandler = logging.StreamHandler()

class LoggingConfigurationDialog(wx.Dialog, LoggingConfiguration):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Logging Configuration')
		LoggingConfiguration.__init__(self)

		self.dialogsizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer(5, 5)

		self.tree = wx.TreeCtrl(self, -1)#, style=wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS)
		sizer.Add(self.tree, (0, 0), (5, 1), wx.EXPAND)

		self.cbpropagate = wx.CheckBox(self, -1, 'Propagate')
		self.Bind(wx.EVT_CHECKBOX, self.onPropagateCheckbox, self.cbpropagate)
		sizer.Add(self.cbpropagate, (0, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1, 'Level:'), (1, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		self.clevel = wx.Choice(self, -1, choices=self._getLevelNames())
		self.clevel.SetSelection(0)
		self.Bind(wx.EVT_CHOICE, self.onLevelChoice, self.clevel)
		sizer.Add(self.clevel, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.cbprint = wx.CheckBox(self, -1, 'Print')
		self.Bind(wx.EVT_CHECKBOX, self.onPrintCheckbox, self.cbprint)
		sizer.Add(self.cbprint, (2, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1, 'Format:'), (3, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		self.tcformat = wx.TextCtrl(self, -1, '')
		sizer.Add(self.tcformat, (3, 2), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.Bind(wx.EVT_TEXT, self.onFormat, self.tcformat)

		sizer.Add(wx.StaticText(self, -1, 'Date Format:'), (4, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		self.tcdateformat = wx.TextCtrl(self, -1, '')
		sizer.Add(self.tcdateformat, (4, 2), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.Bind(wx.EVT_TEXT, self.onDateFormat, self.tcdateformat)

		sizer.AddGrowableCol(2)

		buttonsizer = wx.GridBagSizer(0, 0)
		donebutton = wx.Button(self, wx.ID_OK, 'Done')
		donebutton.SetDefault()
		buttonsizer.Add(donebutton, (0, 0), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		buttonsizer.AddGrowableCol(0)
		sizer.Add(buttonsizer, (5, 1), (1, 3), wx.EXPAND)

		self.setTree()
		self.onTreeSelectionChanged()
		sizer.SetItemMinSize(self.tree, (self.tree.GetSize()[0]*2, -1))

		self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onTreeSelectionChanged, self.tree)
		self.dialogsizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.SetSizerAndFit(self.dialogsizer)

	def onPropagateCheckbox(self, evt):
		logger = self.tree.GetPyData(self.tree.GetSelection())
		logger.propagate = evt.IsChecked()

	def onLevelChoice(self, evt):
		logger = self.tree.GetPyData(self.tree.GetSelection())
		logger.setLevel(evt.GetString())

	def onPrintCheckbox(self, evt):
		logger = self.tree.GetPyData(self.tree.GetSelection())
		print logger
		if evt.IsChecked():
			logger.addHandler(self.printhandler)
		else:
			logger.removeHandler(self.printhandler)

	def onFormat(self, evt):
		logger = self.tree.GetPyData(self.tree.GetSelection())
		if logger is logging.root:
			return
		logger.format = evt.GetString() 
		logger.setPrintFormatter()

	def onDateFormat(self, evt):
		logger = self.tree.GetPyData(self.tree.GetSelection())
		if logger is logging.root:
			return
		logger.dateformat = evt.GetString() 
		logger.setPrintFormatter()

	def _getLevel(self, logger):
		level = logger.level
		if type(level) is not str:
			level = logging.getLevelName(level)
		return level

	def _getLevelNames(self):
		levelnames = []
		for i in logging._levelNames:
			if type(i) is int:
				levelnames.append(i)
		levelnames.sort()
		levelnames = map(lambda n: logging._levelNames[n], levelnames)
		return levelnames

	def _getLoggerNames(self):
		# not accurate, but you can't delete loggers...
		# ideally you'd want two locks in logging
		logging._acquireLock()
		try:
			names = logging.root.manager.loggerDict.keys()
		finally:
			logging._releaseLock()
		names.sort()
		return names

	def onTreeSelectionChanged(self, evt=None):
		if evt is None:
			logger = self.tree.GetPyData(self.tree.GetSelection())
		else:
			logger = self.tree.GetPyData(evt.GetItem())

		enable = not logger is logging.root
		self.cbpropagate.Enable(enable)
		self.clevel.Enable(enable)
		self.cbprint.Enable(enable)
		self.tcformat.Enable(enable)
		self.tcdateformat.Enable(enable)

		self.cbpropagate.SetValue(logger.propagate)
		level = self._getLevel(logger)
		if type(level) is not str:
			level = logging.getLevelName(level)
		self.clevel.SetStringSelection(level)
		if enable:
			self.cbprint.SetValue(self.printhandler in logger.handlers)
			self.tcformat.SetValue(logger.format)
			self.tcdateformat.SetValue(logger.dateformat)
		else:
			self.cbprint.SetValue(False)
			self.tcformat.SetValue('')
			self.tcdateformat.SetValue('')

	def expandAll(self, item):
		self.tree.Expand(item)
		child, cookie = self.tree.GetFirstChild(item)
		while child:
			self.expandAll(child)
			child, cookie = self.tree.GetNextChild(child, cookie)

	def setTree(self):
		self.root = self.tree.AddRoot('Root')
		self.tree.SetPyData(self.root, logging.root)
		for loggername in self._getLoggerNames():
			names = loggername.split('.')
			parent = self.root
			for name in names[:-1]:
				child, cookie = self.tree.GetFirstChild(parent)
				while self.tree.GetItemText(child) != name:
					child, cookie = self.tree.GetNextChild(child, cookie)
				parent = child
			child = self.tree.AppendItem(parent, names[-1])
			self.tree.SetPyData(child, logging.getLogger(loggername))
		self.expandAll(self.root)
		self.tree.SelectItem(self.root)
		self.tree.EnsureVisible(self.root)

