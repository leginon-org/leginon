import wx
import wx.wizard

# if no session go directly to new session page
class UserPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent):
		wx.wizard.WizardPageSimple.__init__(self, parent)
		sizer = wx.GridBagSizer()

		self.userchoice = wx.Choice(self, -1)
		sizer.Add(self.userchoice, (0, 0), (1, 2), wx.ALIGN_CENTER|wx.ALL)

		sizer.Add(wx.StaticText(self, -1, 'Group:'), (1, 0), (1, 1))
		self.grouptext = wx.StaticText(self, -1, '')
		sizer.Add(self.grouptext, (1, 1), (1, 1))

		self.SetSizerAndFit(sizer)

class SessionPage(wx.wizard.WizardPageSimple):
	def __init__(self, parent):
		wx.wizard.WizardPageSimple.__init__(self, parent)
		sizer = wx.GridBagSizer()

		self.userchoice = wx.Choice(self, -1)
		sizer.Add(self.userchoice, (0, 0), (1, 2), wx.ALIGN_CENTER|wx.ALL)

		self.descriptiontext = wx.StaticText(self, -1, '')
		sizer.Add(self.descriptiontext, (1, 1), (1, 2))

		sizer.Add(wx.StaticText(self, -1, 'Instrument:'), (2, 0), (1, 1))
		self.instrumenttext = wx.StaticText(self, -1, '')
		sizer.Add(self.instrumenttext, (2, 1), (1, 1))

		self.connectcheckbox = wx.CheckBox(self, -1, 'Connect to instrument')
		sizer.Add(self.connectcheckbox, (3, 1), (1, 2))

		sizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (4, 0), (1, 1))
		self.imagedirectorytext = wx.StaticText(self, -1, '')
		sizer.Add(self.imagedirectorytext, (4, 1), (1, 1))

		sizer.Add(wx.StaticText(self, -1, 'Project:'), (5, 0), (1, 1))
		self.projecttext = wx.StaticText(self, -1, '')
		sizer.Add(self.projecttext, (5, 1), (1, 1))

		self.SetSizerAndFit(sizer)

class SetupWizard(wx.wizard.Wizard):
	def __init__(self, parent):
		wx.wizard.Wizard.__init__(self, parent, -1, 'Leginon Setup')
		userpage = UserPage(self)
		sessionpage = SessionPage(self)

		self.FitToPage(userpage)

		wx.wizard.WizardPageSimple_Chain(userpage, sessionpage)

		self.RunWizard(userpage)

if __name__ == '__main__':
	class TestApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Test')
			self.SetTopWindow(frame)
			wizard = SetupWizard(frame)
			frame.Show(True)
			return True

	app = TestApp(0)
	app.MainLoop()

