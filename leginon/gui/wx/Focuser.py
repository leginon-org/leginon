import gui.wx.Acquisition
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import wx
import wxImageViewer

class Panel(gui.wx.Acquisition.Panel):
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)
		self.SetName('%s.pFocuser' % name)

		# add controls to self.szcontrols

		self.szmain.Layout()

	def onNodeInitialized(self):
		#self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		#self.Bind(wx.EVT_TOGGLEBUTTON, self.onTogglePause, self.tbpause)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

#	def onTogglePause(self, evt):
#		if evt.IsChecked():
#			self.node.pause.clear()
#		else:
#			self.node.pause.set()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		asz = gui.wx.Acquisition.SettingsDialog.initialize(self)

		focustypes = self.node.focus_methods.keys()
		self.widgets['correction type'] = Choice(self, -1, choices=focustypes)

		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = Choice(self, -1, choices=presets)

		self.widgets['melt time'] = FloatEntry(self, -1,
																						min=0.0,
																						allownone=False,
																						chars=4,
																						value='0.0')
		szmelt = wx.GridBagSizer(5, 5)
		szmelt.Add(self.widgets['melt time'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szmelt.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		self.widgets['beam tilt'] = FloatEntry(self, -1,
																						allownone=False,
																						chars=9,
																						value='0.0')

		self.widgets['fit limit'] = FloatEntry(self, -1,
																						allownone=False,
																						chars=9,
																						value='0.0')

		self.widgets['check drift'] = wx.CheckBox(self, -1,
																								'Check for drift greater than')
		self.widgets['drift threshold'] = FloatEntry(self, -1,
																									min=0.0,
																									allownone=False,
																									chars=4,
																									value='0.0')
		szdrift = wx.GridBagSizer(5, 5)
		szdrift.Add(self.widgets['check drift'], (0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szdrift.Add(self.widgets['drift threshold'], (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szdrift.Add(wx.StaticText(self, -1, 'pixels'), (0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		self.widgets['check before'] = wx.CheckBox(self, -1,
																			'Manual focus check before autofocus')
		self.widgets['check after'] = wx.CheckBox(self, -1,
																			'Manual focus check after autofocus')

		self.widgets['stig correction'] = wx.CheckBox(self, -1, 'Correct')
		self.widgets['stig defocus min'] = FloatEntry(self, -1,
																									allownone=False,
																									chars=9,
																									value='0.0')
		self.widgets['stig defocus max'] = FloatEntry(self, -1,
																									allownone=False,
																									chars=9,
																									value='0.0')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['stig correction'], (0, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Min.'), (1, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Max.'), (1, 2), (1, 1), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Defocus:'), (2, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig defocus min'], (2, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(self.widgets['stig defocus max'], (2, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szstig = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Stigmator'), wx.VERTICAL)
		szstig.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.widgets['acquire final'] = wx.CheckBox(self, -1, 'Acquire final image')

		# settings sizer
		sz = wx.GridBagSizer(10, 5)
		sz.Add(wx.StaticText(self, -1, 'Correction type'), (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['correction type'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Preset'), (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Melt time:'), (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szmelt, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Beam tilt:'), (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['beam tilt'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'Fit limit:'), (4, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['fit limit'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(szdrift, (5, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sz.Add(self.widgets['check before'], (0, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['check after'], (1, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['acquire final'], (2, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szstig, (3, 2), (4, 1), wx.ALIGN_CENTER)
		sz.AddGrowableRow(6)

		sb = wx.StaticBox(self, -1, 'Autofocus')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(asz, (0, 0), (1, 1), wx.EXPAND)
		sz.Add(sbsz, (1, 0), (1, 1), wx.EXPAND)

		return sz

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Acquisition Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

