import wx
from gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import gui.wx.Node
import gui.wx.Settings

class Panel(gui.wx.Node.Panel):
	icon = 'fftmaker'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)
		self.bsettings = wx.Button(self, -1, 'Settings...')
		self.szmain.Add(self.bsettings, (1, 0), (1, 1), wx.ALIGN_CENTER)

		self.szdatabase = self._getStaticBoxSizer('Images in Database',
																							(2, 0), (1, 1), wx.EXPAND|wx.ALL)

		label = wx.StaticText(self, -1, 'Find images in this session with label:')
		self.szdatabase.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.telabel = Entry(self, -1)
		self.szdatabase.Add(self.telabel, (0, 1), (1, 1),
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

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(EVT_ENTRY, self.onLabelEntry, self.telabel)
		self.Bind(wx.EVT_BUTTON, self.onStart, self.bstart)
		self.Bind(wx.EVT_BUTTON, self.onStop, self.bstop)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onLabelEntry(self, evt):
		self.node.label = evt.GetValue()

	def onStart(self, evt):
		self.node.onStartPostProcess()
		self.bstart.Enable(False)
		self.bstop.Enable(True)

	def onStop(self, evt):
		self.node.onStopPostProcess()
		self.bstop.Enable(False)
		self.bstart.Enable(True)

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Calculate FFT and save to the database')
		self.widgets['mask radius'] = FloatEntry(self, -1, min=0.0, chars=6)

		szmaskradius = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mask radius:')
		szmaskradius.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmaskradius.Add(self.widgets['mask radius'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of image width')
		szmaskradius.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['process'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szmaskradius, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'FFT')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'FFT Maker Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

