import wx
from gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import gui.wx.Node
import gui.wx.Settings

class Panel(gui.wx.Node.Panel):
	icon = 'fftmaker'
	tools = [
		'settings',
		'play',
		'stop',
	]
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.enable(self, 'stop', False)

		self.szmain.AddGrowableCol(0)
		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def onNodeInitialized(self):
		pass

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		self.node.onStartPostProcess()
		self.toolbar.enable(self, 'play', False)
		self.toolbar.enable(self, 'stop', True)

	def onStopTool(self, evt):
		self.node.onStopPostProcess()
		self.toolbar.enable(self, 'stop', False)
		self.toolbar.enable(self, 'play', True)

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Calculate FFT and save to the database')
		self.widgets['mask radius'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['label'] = Entry(self, -1)

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

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Find images in this session with label:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['label'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sb = wx.StaticBox(self, -1, 'Images in Database')
		sbszdb = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszdb.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz, sbszdb]

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

