import wx
from gui.wx.Choice import Choice
import gui.wx.Camera
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ImageViewer

AddTargetTypesEventType = wx.NewEventType()
EVT_ADD_TARGET_TYPES = wx.PyEventBinder(AddTargetTypesEventType)
class AddTargetTypesEvent(wx.PyCommandEvent):
	def __init__(self, source, typenames):
		wx.PyCommandEvent.__init__(self, AddTargetTypesEventType, source.GetId())
		self.SetEventObject(source)
		self.typenames = typenames

ImageUpdatedEventType = wx.NewEventType()
EVT_IMAGE_UPDATED = wx.PyEventBinder(ImageUpdatedEventType)
class ImageUpdatedEvent(wx.PyCommandEvent):
	def __init__(self, source, name, image, targets=None):
		wx.PyCommandEvent.__init__(self, ImageUpdatedEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.image = image
		self.targets = targets

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
		self.bcalibrate = wx.Button(self, -1, 'Calibrate')
		self.babort = wx.Button(self, -1, 'Abort')

		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.Add(self.bsettings, (0, 0), (1, 1), wx.EXPAND)
		self.szbuttons.Add(self.bcalibrate, (1, 0), (1, 1), wx.EXPAND)
		self.szbuttons.Add(self.babort, (2, 0), (1, 1), wx.EXPAND)
		self.szmain.Add(self.szbuttons, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.AddGrowableCol(1)

		self.targetcolors = {
			'Peak': wx.Color(255, 128, 0),
		}

		self.imagetypes = [
			'None',
			'Image',
			'Correlation',
		]

		self.cdisplay = wx.Choice(self, -1, choices=self.imagetypes)
		self.cdisplay.SetStringSelection('Image')
		self.szdisplay = self._getStaticBoxSizer('Display', (2, 0), (1, 1),
																							wx.ALIGN_CENTER)
		self.szdisplay.Add(self.cdisplay, (0, 0), (1, 1), wx.ALIGN_CENTER)

		# image
		self.imagepanel = gui.wx.ImageViewer.TargetImagePanel(self, -1)
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (5, 1),
																						wx.EXPAND|wx.ALL)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szimage.AddGrowableRow(0)
		self.szimage.AddGrowableCol(0)
		self.szmain.AddGrowableRow(5)

		self.Bind(EVT_ADD_TARGET_TYPES, self.onAddTargetTypes)
		self.Bind(EVT_IMAGE_UPDATED, self.onImageUpdated)

	def onAddTargetTypes(self, evt):
		for typename in evt.typenames:
			try:
				color = self.targetcolors[typename]
			except KeyError:
				color = None
			self.imagepanel.addTargetType(typename, color)

	def addTargetTypes(self, typenames):
		evt = AddTargetTypesEvent(self, typenames)
		self.GetEventHandler().AddPendingEvent(evt)

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(wx.EVT_BUTTON, self.onCalibrateButton, self.bcalibrate)
		self.Bind(wx.EVT_BUTTON, self.onAbortButton, self.babort)
		self.Bind(wx.EVT_CHOICE, self.onDisplayChoice, self.cdisplay)

	def onImageUpdated(self, evt):
		if self.cdisplay.GetStringSelection() == evt.name:
			self.imagepanel.setImage(evt.image)
			if evt.targets is not None:
				self._setTargets(evt.targets)

	def _setTargets(self, targets):
		for typename, targetlist in targets.items():
			self.imagepanel.clearTargets(typename)
			for target in targetlist:
				x, y = target
				self.imagepanel.addTarget(typename, x, y)

	def onDisplayChoice(self, evt):
		key = evt.GetString()
		try:
			image = self.node.images[key]
		except KeyError:
			image = None
		self.imagepanel.setImage(image)
		try:
			targets = self.node.imagetargets[key]
		except KeyError:
			targets = {}
		self._setTargets(targets)

	def imageUpdated(self, name, image, targets=None):
		evt = ImageUpdatedEvent(self, name, image, targets)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onCalibrateButton(self, evt):
		raise NotImplementedError

	def onAbortButton(self, evt):
		raise NotImplementedError

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.session)
		self.widgets['correlation type'] = Choice(self, -1,
																							choices=self.node.cortypes)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['correlation type'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (1, 0), (1, 1),
						wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Calibration Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

