import gui.wx.Data
import gui.wx.Node
import wx
import wx.lib.masked

class Panel(gui.wx.Node.Panel):
	icon = 'fftmaker'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1,
																name='%s.pFFTMaker' % name)
		self.szmain = wx.GridBagSizer(5, 5)

		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 1),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.szincoming = self._getStaticBoxSizer('Incoming Images',
																							(1, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.cbprocess = wx.CheckBox(self, -1,
																	'Calculate FFT and save to the database',
																	name='cbProcess')
		self.szincoming.Add(self.cbprocess, (0, 0), (1, 3),
												wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Mask radius:')
		self.szincoming.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.ncmaskradius = wx.lib.masked.NumCtrl(self, -1, 0.01,
										 													 integerWidth=2,
										 													 fractionWidth=2,
										 													 allowNone=False,
										 													 allowNegative=False,
										 													 name='ncMaskRadius')
		self.szincoming.Add(self.ncmaskradius, (1, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, '% of image width')
		self.szincoming.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.szdatabase = self._getStaticBoxSizer('Images in Database',
																							(2, 0), (1, 1), wx.EXPAND|wx.ALL)

		label = wx.StaticText(self, -1, 'Find images in this session with label:')
		self.szdatabase.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.tclabel = wx.TextCtrl(self, -1, '', name='tcLabel')
		self.szdatabase.Add(self.tclabel, (0, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.bstart = wx.Button(self, -1, 'Start')
		self.bstop = wx.Button(self, -1, 'Stop')
		self.bstop.Enable(False)
		buttonsizer = wx.GridBagSizer(0, 0)
		buttonsizer.Add(self.bstart, (0, 0), (1, 1), wx.ALIGN_CENTER)
		buttonsizer.Add(self.bstop, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.szdatabase.Add(buttonsizer, (1, 0), (1, 2), wx.ALIGN_RIGHT)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

		self.Bind(gui.wx.Node.EVT_SET_STATUS, self.onSetStatus)

	def initializeValues(self):
		gui.wx.Data.setWindowFromDB(self.cbprocess)
		gui.wx.Data.setWindowFromDB(self.ncmaskradius)
		gui.wx.Data.setWindowFromDB(self.tclabel)

		gui.wx.Data.bindWindowToDB(self.cbprocess)
		gui.wx.Data.bindWindowToDB(self.ncmaskradius)
		gui.wx.Data.bindWindowToDB(self.tclabel)

		self.node.process = self.cbprocess.GetValue()
		self.node.maskradius = self.ncmaskradius.GetValue()
		self.node.label = self.tclabel.GetValue()

		self.Bind(wx.EVT_CHECKBOX, self.onProcess, self.cbprocess)
		self.Bind(wx.lib.masked.EVT_NUM, self.onMaskRadius, self.ncmaskradius)
		self.Bind(wx.EVT_TEXT, self.onLabel, self.tclabel)
		self.Bind(wx.EVT_BUTTON, self.onStart, self.bstart)
		self.Bind(wx.EVT_BUTTON, self.onStop, self.bstop)

	def onSetStatus(self, evt):
		self.ststatus.SetLabel(evt.status)

	def onProcess(self, evt):
		self.node.process = evt.IsChecked()

	def onLabel(self, evt):
		self.node.label = evt.GetString()

	def onMaskRadius(self, evt):
		self.node.maskradius = evt.GetValue()

	def onStart(self, evt):
		self.node.onStartPostProcess()
		self.bstart.Enable(False)
		self.bstop.Enable(True)

	def onStop(self, evt):
		self.node.onStopPostProcess()
		self.bstop.Enable(False)
		self.bstart.Enable(True)

