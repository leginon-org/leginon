import wx
from wx.lib.masked import NumCtrl, EVT_NUM
import gui.wx.Camera
import gui.wx.Data
import gui.wx.Node
import wxImageViewer

class Panel(gui.wx.Node.Panel):
	icon = 'driftmanager'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pDriftManager' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings
		self.szsettings = self._getStaticBoxSizer('Settings', (1, 0), (1, 1),
																							wx.ALL)

		self.cbcheckdrift = wx.CheckBox(self, -1, 'Check drift',
																			name='cbCheckDrift')
		self.szsettings.Add(self.cbcheckdrift, (0, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)

		label0 = wx.StaticText(self, -1, 'Wait for drift to be less than')
		self.ncthreshold = NumCtrl(self, -1, 2e-10, integerWidth=1,
																								fractionWidth=12,
																								allowNone=False,
																								allowNegative=False,
																								name='ncThreshold')
		label1 = wx.StaticText(self, -1, 'meters')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(label0, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(self.ncthreshold, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(label1, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		self.szsettings.Add(sz, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)

		label0 = wx.StaticText(self, -1, 'Wait')
		self.ncwait = NumCtrl(self, -1, 2.0, integerWidth=2,
																					fractionWidth=1,
																					allowNone=False,
																					allowNegative=False,
																					name='ncWait')
		label1 = wx.StaticText(self, -1, 'seconds between checking')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(label0, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(self.ncwait, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sz.Add(label1, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		self.szsettings.Add(sz, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)

		self.cpcamconfig = gui.wx.Camera.CameraPanel(self)

		self.szsettings.Add(self.cpcamconfig, (3, 0), (1, 1), wx.ALIGN_CENTER)

		# controls
		self.szcontrols = self._getStaticBoxSizer('Controls', (2, 0), (1, 1),
																			wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)

		self.bmeasure = wx.Button(self, -1, 'Measure Drift')
		self.szcontrols.Add(self.bmeasure, (0, 0), (1, 1), wx.ALIGN_CENTER)

		# image
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (2, 1),
																						wx.EXPAND|wx.ALL)
		self.imagepanel = wxImageViewer.ImagePanel(self, -1)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.szmain.AddGrowableCol(1)
		self.szmain.AddGrowableRow(2)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def initializeValues(self):
		self.cpcamconfig.setSize(self.node.session)

		gui.wx.Data.setWindowFromDB(self.cbcheckdrift)
		gui.wx.Data.setWindowFromDB(self.ncthreshold)
		gui.wx.Data.setWindowFromDB(self.ncwait)
		gui.wx.Data.setWindowFromDB(self.cpcamconfig)

		self.node.threshold = self.ncthreshold.GetValue()
		self.node.wait = self.ncwait.GetValue()
		self.node.camconfig = self.cpcamconfig.getConfiguration()

		gui.wx.Data.bindWindowToDB(self.ncthreshold)
		gui.wx.Data.bindWindowToDB(self.ncwait)
		gui.wx.Data.bindWindowToDB(self.cpcamconfig)

		self.Bind(wx.EVT_CHECKBOX, self.onCheckDriftCheck, self.cbcheckdrift)
		self.Bind(EVT_NUM, self.onThresholdNum, self.ncthreshold)
		self.Bind(EVT_NUM, self.onWaitNum, self.ncwait)
		self.Bind(gui.wx.Camera.EVT_CONFIGURATION_CHANGED, self.onCamConfigChanged,
							self.cpcamconfig)
		self.Bind(wx.EVT_BUTTON, self.onMeasure, self.bmeasure)

		self.onCheckDriftCheck()
		# check drift

	def onCheckDriftCheck(self, evt=None):
		if evt is None:
			check = self.cbcheckdrift.GetValue()
		else:
			check = evt.IsChecked()
		# this doesn't really work
		if check:
			self.node.uiMonitorDrift()
		else:
			self.node.abort()

	def onThresholdNum(self, evt):
		self.node.threshold = evt.GetValue()

	def onWaitNum(self, evt):
		self.node.wait = evt.GetValue()

	def onCamConfigChanged(self, evt):
		self.node.camconfig = evt.configuration

	def onMeasure(self, evt):
		self.node.measureDrift()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Drift Manager Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

