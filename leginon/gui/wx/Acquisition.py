import gui.wx.Node
import gui.wx.Settings
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY
from gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import wx
import gui.wx.ImageViewer
import gui.wx.ToolBar

class Panel(gui.wx.Node.Panel):
	icon = 'acquisition'
	def __init__(self, parent, name):
		self.tools = [
			'settings',
			'play',
			'pause',
			'stop',
		]
		gui.wx.Node.Panel.__init__(self, parent, -1)

		# image
		self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

		self.szmain.AddGrowableRow(1)
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
		self.node.pause.set()
		self.node.abort = False

	def onPauseTool(self, evt):
		self.node.abort = False
		self.node.pause.clear()

	def onStopTool(self, evt):
		self.node.pause.set()
		self.node.abort = True

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		# move type
		movetypes = self.node.calclients.keys()
		self.widgets['move type'] = Choice(self, -1, choices=movetypes)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to target'),
										(0, 2), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		# preset order
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset order'] = EditPresetOrder(self, -1)
		self.widgets['preset order'].setChoices(presets)

		# misc. checkboxes
		self.widgets['correct image'] = wx.CheckBox(self, -1, 'Correct image')
		self.widgets['display image'] = wx.CheckBox(self, -1, 'Display image')
		self.widgets['save image'] = wx.CheckBox(self, -1, 'Save image to database')
		self.widgets['wait for process'] = wx.CheckBox(self, -1,
																				'Wait for a node to process the image')
		self.widgets['wait for rejects'] = wx.CheckBox(self, -1,
																				'Publish and wait for rejected targets')
		# duplicate target
		self.widgets['duplicate targets'] = wx.CheckBox(self, -1,
																				'Duplicate targets with type:')
		self.widgets['duplicate target type'] = Choice(self, -1,
																							choices=self.node.duplicatetypes)

		szduplicate = wx.GridBagSizer(0, 0)
		szduplicate.Add(self.widgets['duplicate targets'], (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szduplicate.Add(self.widgets['duplicate target type'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# settings sizer
		sz = wx.GridBagSizer(5, 25)
		sz.Add(szmovetype, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpausetime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset order'], (2, 0), (5, 1), wx.ALIGN_CENTER)
		sz.Add(self.widgets['correct image'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['display image'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['save image'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['wait for process'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['wait for rejects'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szduplicate, (5, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableRow(6)

		sb = wx.StaticBox(self, -1, 'Image Acquisition')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

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

