import wx
import gui.wx.ImageViewer
import gui.wx.Settings
import gui.wx.TargetFinder

AddTargetTypesEventType = wx.NewEventType()
AddTargetsEventType = wx.NewEventType()
SetTargetsEventType = wx.NewEventType()

EVT_ADD_TARGET_TYPES = wx.PyEventBinder(AddTargetTypesEventType)
EVT_ADD_TARGETS = wx.PyEventBinder(AddTargetsEventType)
EVT_SET_TARGETS = wx.PyEventBinder(SetTargetsEventType)

class AddTargetTypesEvent(wx.PyCommandEvent):
	def __init__(self, source, typenames):
		wx.PyCommandEvent.__init__(self, AddTargetTypesEventType, source.GetId())
		self.SetEventObject(source)
		self.typenames = typenames

class AddTargetsEvent(wx.PyCommandEvent):
	def __init__(self, source, typename, targets):
		wx.PyCommandEvent.__init__(self, AddTargetsEventType, source.GetId())
		self.SetEventObject(source)
		self.typename = typename
		self.targets = targets

class SetTargetsEvent(wx.PyCommandEvent):
	def __init__(self, source, typename, targets):
		wx.PyCommandEvent.__init__(self, SetTargetsEventType, source.GetId())
		self.SetEventObject(source)
		self.typename = typename
		self.targets = targets

class Panel(gui.wx.TargetFinder.Panel):
	def initialize(self):
		gui.wx.TargetFinder.Panel.initialize(self)

		self.targetcolors = {
			'acquisition': wx.GREEN,
			'focus': wx.BLUE,
			'done': wx.RED,
			'position': wx.Color(255, 255, 0),
		}

		self.bsubmit = wx.Button(self, -1, 'Submit Targets')
		self.szbuttons.Add(self.bsubmit, (1, 0), (1, 1), wx.EXPAND)

		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.szimage = self._getStaticBoxSizer('Target Image', (1, 1), (3, 1),
																						wx.EXPAND|wx.ALL)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szimage.AddGrowableRow(0)
		self.szimage.AddGrowableCol(0)
		self.szmain.AddGrowableRow(3)

		self.Bind(EVT_ADD_TARGET_TYPES, self.onAddTargetTypes)
		self.Bind(EVT_ADD_TARGETS, self.onAddTargets)
		self.Bind(EVT_SET_TARGETS, self.onSetTargets)

	def onAddTargetTypes(self, evt):
		for typename in evt.typenames:
			try:
				color = self.targetcolors[typename]
			except KeyError:
				color = None
			self.imagepanel.addTargetType(typename, color)

	def onAddTargets(self, evt):
		for target in evt.targets:
			x, y = target
			self.imagepanel.addTarget(evt.typename, x, y)

	def onSetTargets(self, evt):
		self.imagepanel.clearTargets(evt.typename)
		self.onAddTargets(evt)

	def addTargetTypes(self, typenames):
		evt = AddTargetTypesEvent(self, typenames)
		self.GetEventHandler().AddPendingEvent(evt)

	def addTargets(self, typename, targets):
		evt = AddTargetsEvent(self, typename, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def setTargets(self, typename, targets):
		evt = SetTargetsEvent(self, typename, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def getTargets(self, typename):
		return self.imagepanel.getTargetTypeValue(typename)

	def onNodeInitialized(self):
		gui.wx.TargetFinder.Panel.onNodeInitialized(self)
		self.Bind(wx.EVT_BUTTON, self.onSubmitButton, self.bsubmit)

	def onSubmitButton(self, evt):
		self.node.submitTargets()

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.TargetFinder.SettingsDialog):
	def initialize(self):
		tfsbsz = gui.wx.TargetFinder.SettingsDialog.initialize(self)

		self.widgets['no resubmit'] = wx.CheckBox(self, -1,
				'Do not allow targets to be resubmitted for an image')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['no resubmit'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Click target finding')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return tfsbsz + [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Click Target Finder Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

