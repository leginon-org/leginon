import gui.wx.Acquisition
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import wx
import wxImageViewer

class Panel(gui.wx.Acquisition.Panel):
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)
		self.SetName('%s.pFocuser' % name)

		self.tbauto = wx.ToggleButton(self, -1, 'Autofocus')
		self.bmanual = wx.Button(self, -1, 'Manual Focus')
		self.szcontrols.Add(self.tbauto, (3, 0), (1, 1), wx.EXPAND)
		self.szcontrols.Add(self.bmanual, (4, 0), (1, 1), wx.EXPAND)

		# correlation image
		szimage = self._getStaticBoxSizer('Correlation Image', (2, 1), (1, 1),
																						wx.EXPAND|wx.ALL)
		self.ipcorrelation = wxImageViewer.TargetImagePanel(self, -1, tool=False)
		self.ipcorrelation.addTargetType('Peak')
		szimage.Add(self.ipcorrelation, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		self.szmain.AddGrowableRow(2)

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleAuto, self.tbauto)
		self.Bind(wx.EVT_BUTTON, self.onManualButton, self.bmanual)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onToggleAuto(self, evt):
		self.node.autofocus = evt.IsChecked()

	def onManualButton(self, evt):
		pass

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

class ManualFocusDialog(wx.Dialog):
	def __init__(self, parent, title='Manual Focus'):
		wx.Dialog.__init__(self, parent, -1, title)

		self.tbpause = wx.ToggleButton(self, -1, 'Pause')

		self.beftoscope = wx.Button(self, -1, 'To Scope')
		self.beffromscope = wx.Button(self, -1, 'From Scope')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.beftoscope, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.beffromscope, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szef = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Eucentric Focus'),
															wx.VERTICAL)
		szef.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.feincrement = FloatEntry(self, -1, min=0.0,
																						allownone=False,
																						chars=6,
																						value='0.0')
		self.bup = wx.Button(self, -1, 'Up')
		self.bdown = wx.Button(self, -1, 'Down')
		self.bzero = wx.Button(self, -1, 'Zero')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(wx.StaticText(self, -1, 'Increment:'), (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.feincrement, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'm'), (0, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.bup, (1, 0), (1, 3), wx.ALIGN_CENTER)
		sz.Add(self.bdown, (2, 0), (1, 3), wx.ALIGN_CENTER)
		sz.Add(self.bzero, (3, 0), (1, 3), wx.ALIGN_CENTER)
		szadjust = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Adjust'), wx.VERTICAL)
		szadjust.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.breset = wx.Button(self, -1, 'Reset')

		self.femaskradius = FloatEntry(self, -1, allownone=False,
																							chars=6,
																							value='0.0')
		szmaskradius = wx.GridBagSizer(5, 5)
		szmaskradius.Add(wx.StaticText(self, -1, 'Mask radius:'), (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		szmaskradius.Add(self.femaskradius, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szmaskradius.Add(wx.StaticText(self, -1, '% of image'), (0, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		self.rbimage = wx.RadioBox(self, -1, 'Display',
																					choices=['Image', 'Power Spectrum'],
																					style=wx.RA_VERTICAL)

		self.ipimage = wxImageViewer.ImagePanel(self, -1)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.tbpause, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(szef, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sz.Add(szadjust, (2, 0), (1, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sz.Add(self.breset, (3, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(szmaskradius, (4, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.rbimage, (5, 0), (1, 1), wx.ALIGN_CENTER)
		szmain = wx.GridBagSizer(5, 5)
		szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_TOP|wx.ALL, 10)
		szmain.Add(self.ipimage, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.SetSizerAndFit(szmain)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			panel = Panel(frame, 'Test')
			dialog = ManualFocusDialog(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

