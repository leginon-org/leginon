import wx
import gui.wx.Node
import gui.wx.Settings

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
	tools = [
		'settings',
	]
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.initialize()

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def initialize(self):
		pass

	def onSettingsTool(self, evt):
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

