import wx
import gui.wx.Node
import gui.wx.Settings

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.initialize()

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def initialize(self):
		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings

		self.bsettings = wx.Button(self, -1, 'Settings...')

		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.Add(self.bsettings, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.Add(self.szbuttons, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.AddGrowableCol(1)

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['wait for done'] = wx.CheckBox(self, -1,
					'Wait for another node to process targets before marking them done')
		self.widgets['ignore images'] = wx.CheckBox(self, -1,
					'Ignore incoming images')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['wait for done'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['ignore images'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Target finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

