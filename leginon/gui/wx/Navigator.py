import wx
import wx.lib.masked
import wx.lib.scrolledpanel
import gui.wx.Data
import wxImageViewer
import gui.wx.Node
import gui.wx.Presets

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pNavigator' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings
		self.szsettings = self._getStaticBoxSizer('Settings', (1, 0), (1, 1),
																							wx.ALL)

		sz = wx.GridBagSizer(5, 5)
		label0 = wx.StaticText(self, -1, 'Wait')
		self.ncwait = wx.lib.masked.NumCtrl(self, -1, 2.5,
																				integerWidth=2,
																				fractionWidth=1,
																				allowNone=False,
																				allowNegative=False,
																				name='ncWait')
		label1 = wx.StaticText(self, -1, 'seconds and use')
		self.cmovetype = wx.Choice(self, -1, name='cMoveType')
		label2 = wx.StaticText(self, -1, 'to move to target')

		sz.Add(label0, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(self.ncwait, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(label1, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(self.cmovetype, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(label2, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)

		self.cbcheckerror = wx.CheckBox(self, -1, 'Check calibration error',
																			name='cbCheckError')
		self.cbcompletestate = wx.CheckBox(self, -1, 'Set complete state',
																			name='cbCompleteState')
		self.cpcamconfig = gui.wx.Camera.CameraPanel(self)

		self.szsettings.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		self.szsettings.Add(self.cbcheckerror, (1, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbcompletestate, (2, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cpcamconfig, (3, 0), (1, 1),
												wx.ALIGN_CENTER)

		# controls
		self.szlocations = self._getStaticBoxSizer('Stage Locations',
																								(2, 0), (1, 1),
																			wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)

		stposition = {}
		self.stposition = {}
		axes = ['x', 'y', 'z', 'a', 'b']
		for i, a in enumerate(axes):
			stposition[a] = wx.StaticText(self, -1, a)
			self.stposition[a] = wx.StaticText(self, -1, 'N/A')
			self.szlocations.Add(stposition[a], (0, i + 1), (1, 1), wx.ALIGN_CENTER)
			self.szlocations.Add(self.stposition[a], (1, i + 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label0 = wx.StaticText(self, -1, 'Position:')
		label1 = wx.StaticText(self, -1, 'Comment:')
		self.stcomment = wx.StaticText(self, -1, '(No location selected)')
		label2 = wx.StaticText(self, -1, 'Locations')
		self.lblocations = wx.ListBox(self, -1, style=wx.LB_SINGLE)
		self.bnew = wx.Button(self, -1, 'New...')
		self.btoscope = wx.Button(self, -1, 'To scope')
		self.bfromscope = wx.Button(self, -1, 'From scope')
		self.bremove = wx.Button(self, -1, 'Remove')

		self.szlocations.Add(label0, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(label1, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(self.stcomment, (2, 1), (1, 5),
													wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(label2, (3, 1), (1, 5), wx.ALIGN_CENTER_VERTICAL)
		self.szlocations.Add(self.lblocations, (4, 1), (4, 5), wx.EXPAND)
		self.szlocations.Add(self.bnew, (4, 0), (1, 1), wx.ALIGN_CENTER)
		self.szlocations.Add(self.btoscope, (5, 0), (1, 1), wx.ALIGN_CENTER)
		self.szlocations.Add(self.bfromscope, (6, 0), (1, 1), wx.ALIGN_CENTER)
		self.szlocations.Add(self.bremove, (7, 0), (1, 1), wx.ALIGN_CENTER)

		# image
		self.szimage = self._getStaticBoxSizer('Navigation', (1, 1), (2, 1),
																						wx.EXPAND|wx.ALL)
		self.bacquire = wx.Button(self, -1, 'Acquire')
		self.imagepanel = wxImageViewer.ClickImagePanel(self, -1)
		self.szimage.Add(self.bacquire, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.szimage.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL)
		self.szimage.AddGrowableCol(0)

		self.szmain.AddGrowableRow(2)
		self.szmain.AddGrowableCol(1)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def initializeValues(self):
		movetypes = self.node.calclients.keys()
		if movetypes:
			self.cmovetype.AppendItems(movetypes)
			self.cmovetype.SetSelection(0)

		gui.wx.Data.setWindowFromDB(self.ncwait)
		gui.wx.Data.setWindowFromDB(self.cmovetype)
		gui.wx.Data.setWindowFromDB(self.cbcheckerror)
		gui.wx.Data.setWindowFromDB(self.cbcompletestate)
		gui.wx.Data.setWindowFromDB(self.cpcamconfig)

		self.node.wait = self.ncwait.GetValue()
		self.node.movetype = self.cmovetype.GetStringSelection()
		self.node.checkerror = self.cbcheckerror.GetValue()
		self.node.completestate = self.cbcompletestate.GetValue()
		self.node.camconfig = self.cpcamconfig.getConfiguration()

		gui.wx.Data.bindWindowToDB(self.ncwait)
		gui.wx.Data.bindWindowToDB(self.cmovetype)
		gui.wx.Data.bindWindowToDB(self.cbcheckerror)
		gui.wx.Data.bindWindowToDB(self.cbcompletestate)
		gui.wx.Data.bindWindowToDB(self.cpcamconfig)

		self.Bind(wx.lib.masked.EVT_NUM, self.onWaitNum, self.ncwait)
		self.Bind(wx.EVT_CHOICE, self.onMoveTypeChoice, self.cmovetype)
		self.Bind(wx.EVT_CHECKBOX, self.onErrorCheckCheck, self.cbcheckerror)
		self.Bind(wx.EVT_CHECKBOX, self.onCompleteStateCheck, self.cbcompletestate)
		self.Bind(gui.wx.Camera.EVT_CONFIGURATION_CHANGED, self.onCamConfigChanged,
							self.cpcamconfig)
		self.Bind(wx.EVT_BUTTON, self.onAcquire, self.bacquire)
		self.Bind(wx.EVT_BUTTON, self.onNew, self.bnew)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)

	def onWaitNum(self, evt):
		if self.node is not None:
			self.node.wait = evt.GetValue()

	def onMoveTypeChoice(self, evt):
		self.node.movetype = evt.GetString()

	def onErrorCheckCheck(self, evt):
		self.node.checkerror = evt.IsChecked()

	def onCompleteStateCheck(self, evt):
		self.node.completestate = evt.IsChecked()

	def onCamConfigChanged(self, evt):
		self.node.camconfig = evt.configuration

	def onAcquire(self, evt):
		print 'ACQUIRE'

	def onNew(self, evt):
		print 'NEW'

	def onToScope(self, evt):
		print 'TO SCOPE'

	def onFromScope(self, evt):
		print 'FROM SCOPE'

	def onRemove(self, evt):
		print 'REMOVE'

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Navigator Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

