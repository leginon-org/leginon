import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Camera
import gui.wx.Calibrator
import gui.wx.Settings
import gui.wx.ImageViewer
import gui.wx.ToolBar

def capitalize(string):
	if string:
		string = string[0].upper() + string[1:]
	return string

class Panel(gui.wx.Calibrator.Panel):
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)

		self.toolbar.InsertSeparator(2)
		self.cparameter = wx.Choice(self.toolbar, -1)
		self.cparameter.SetSelection(0)
		self.toolbar.InsertControl(3, self.cparameter)
		self.toolbar.InsertTool(4, gui.wx.ToolBar.ID_PARAMETER_SETTINGS,
													'settings',
													shortHelpString='Parameter Settings')

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.cparameter.AppendItems(map(capitalize, self.node.parameters.keys()))
		self.cparameter.SetStringSelection(capitalize(self.node.parameter))
		self.Bind(wx.EVT_CHOICE, self.onParameterChoice, self.cparameter)
		self.toolbar.Bind(wx.EVT_TOOL, self.onParameterSettingsTool,
											id=gui.wx.ToolBar.ID_PARAMETER_SETTINGS)
		self.toolbar.Realize()

	def onParameterSettingsTool(self, evt):
		parameter = self.cparameter.GetStringSelection()
		dialog = MatrixSettingsDialog(self, parameter.lower(), parameter)
		dialog.ShowModal()
		dialog.Destroy()

	def onParameterChoice(self, evt):
		self.node.parameter = evt.GetString().lower()

	def onCalibrateTool(self, evt):
		self.node.uiCalibrate()

	def onAbortTool(self, evt):
		self.node.uiAbort()

class MatrixSettingsDialog(gui.wx.Settings.Dialog):
	def __init__(self, parent, parameter, parametername):
		self.parameter = parameter
		self.parametername = parametername
		gui.wx.Settings.Dialog.__init__(self, parent)

	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['%s tolerance' % self.parameter] = FloatEntry(self, -1,
																																chars=9)
		self.widgets['%s shift fraction' % self.parameter] = FloatEntry(self, -1,
																																		chars=9)
		self.widgets['%s n average' % self.parameter] = IntEntry(self, -1, min=1,
																															chars=2)
		self.widgets['%s interval' % self.parameter] = FloatEntry(self, -1, chars=9)
		self.widgets['%s current as base' % self.parameter] = wx.CheckBox(self, -1,
																		'Use current position as starting point')
		self.widgets['%s base' % self.parameter] = {}
		self.widgets['%s base' % self.parameter]['x'] = FloatEntry(self, -1,
																																chars=9)
		self.widgets['%s base' % self.parameter]['y'] = FloatEntry(self, -1,
																																chars=9)

		szbase = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'x')
		szbase.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'y')
		szbase.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Base:')
		szbase.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szbase.Add(self.widgets['%s base' % self.parameter]['x'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szbase.Add(self.widgets['%s base' % self.parameter]['y'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Tolerance:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s tolerance' % self.parameter], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '%')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Shift fraction:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s shift fraction' % self.parameter], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '%')
		sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Average:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s n average' % self.parameter], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'positions')
		sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Interval:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s interval' % self.parameter], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['%s current as base' % self.parameter], (4, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szbase, (5, 0), (1, 3), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		self.sb = wx.StaticBox(self, -1, '%s calibration' % self.parametername)
		sbsz = wx.StaticBoxSizer(self.sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Matrix Calibration Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

