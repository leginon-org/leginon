import wx
from gui.wx.Entry import FloatEntry
import gui.wx.Camera
import gui.wx.ImageViewer
import gui.wx.Node
import gui.wx.Settings

class Panel(gui.wx.Node.Panel):
	icon = 'driftmanager'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings

		self.bsettings = wx.Button(self, -1, 'Settings...')
		self.bmeasure = wx.Button(self, -1, 'Measure Drift')
		self.bdeclare = wx.Button(self, -1, 'Declare Drift')
		self.cbcheckdrift = wx.CheckBox(self, -1, 'Check drift')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.bsettings, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.bmeasure, (1, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.bdeclare, (2, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.cbcheckdrift, (3, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.Add(sz, (1, 0), (1, 1), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)

		# image
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (2, 1),
																						wx.EXPAND|wx.ALL)
		self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.szmain.AddGrowableCol(1)
		self.szmain.AddGrowableRow(2)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(wx.EVT_BUTTON, self.onMeasure, self.bmeasure)
		self.Bind(wx.EVT_BUTTON, self.onDeclare, self.bdeclare)
		self.Bind(wx.EVT_CHECKBOX, self.onCheckDriftCheck, self.cbcheckdrift)

		self.onCheckDriftCheck()

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

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

	def onMeasure(self, evt):
		self.node.measureDrift()

	def onDeclare(self, evt):
		self.node.declareDrift()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['threshold'] = FloatEntry(self, -1, min=0.0, chars=9)
		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.session)

		szthreshold = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Wait for drift to be less than')
		szthreshold.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szthreshold.Add(self.widgets['threshold'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'meters')
		szthreshold.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szpause = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Wait')
		szpause.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpause.Add(self.widgets['pause time'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds between checking drift')
		szpause.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(szthreshold, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpause, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (2, 0), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Drift Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return sbsz

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

