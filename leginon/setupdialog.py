import wx
import wx.wizard

class WizardPage(wx.wizard.PyWizardPage):
	def __init__(self, parent, previous=None, next=None):
		self.previous = previous
		self.next = next
		wx.wizard.PyWizardPage.__init__(self, parent)

	def setPrevious(self, page):
		self.previous = page

	def setNext(self, page):
		self.next = page

	def GetPrev(self):
		return self.previous

	def GetNext(self):
		if self.next is not None:
			self.next.setPrevious(self)
		return self.next

# if no session go directly to new session page
class UserPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
												'Please select your name and press the "Next" button.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		self.userchoice = wx.Choice(self, -1)
		sizer.Add(self.userchoice, (1, 0), (1, 2), wx.ALIGN_CENTER)

		self.grouptext = wx.StaticText(self, -1, '')
		sizer.Add(self.grouptext, (2, 0), (1, 2), wx.ALIGN_CENTER)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

class SessionTypePage(WizardPage):
	def __init__(self, parent, create=None, ret=None):
		self.create = create
		self.ret = ret
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		choices = ['Create a new session', 'Return to an existing session']
		self.sessiontyperadiobox = wx.RadioBox(self, -1, 'Session Type',
																						choices=choices, majorDimension=1,
																						style=wx.RA_SPECIFY_COLS)
		sizer.Add(self.sessiontyperadiobox, (0, 0), (1, 2), wx.ALIGN_CENTER)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def setCreate(self, create):
		self.create = create

	def setReturn(self, ret):
		self.ret = ret

	def GetNext(self):
		try:
			page = self.next[self.sessiontyperadiobox.GetSelection()]
		except IndexError:
			return None

		if page is not None:
			page.setPrevious(self)
		return page

class SessionSelectPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		self.sessionchoice = wx.Choice(self, -1)
		sizer.Add(self.sessionchoice, (0, 0), (1, 2), wx.ALIGN_CENTER)

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		self.descriptiontext = wx.StaticText(self, -1, '')
		sizer.Add(self.descriptiontext, (1, 0), (1, 2), wx.ALIGN_CENTER)

		sizer.Add(wx.StaticText(self, -1, 'Instrument:'), (2, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.instrumenttext = wx.StaticText(self, -1, '')
		sizer.Add(self.instrumenttext, (2, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (3, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.imagedirectorytext = wx.StaticText(self, -1, '')
		sizer.Add(self.imagedirectorytext, (3, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1, 'Project:'), (4, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.projecttext = wx.StaticText(self, -1, '')
		sizer.Add(self.projecttext, (4, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		self.connectcheckbox = wx.CheckBox(self, -1, 'Connect to instrument')
		sizer.Add(self.connectcheckbox, (5, 0), (1, 2), wx.ALIGN_CENTER)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

class SessionNamePage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
				'You may change the suggested session name if you wish.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Name:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.nametextctrl = wx.TextCtrl(self, -1, '')
		sizer.Add(self.nametextctrl, (1, 1), (1, 1), wx.EXPAND|wx.ALL)

		sizer.Add(wx.StaticText(self, -1, 'Description:'), (2, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.descriptiontextctrl = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE)
		sizer.Add(self.descriptiontextctrl, (3, 0), (1, 2), wx.EXPAND|wx.ALL)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

class SessionProjectPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
				'Select the project this session will be associated with.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Project:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.projectchoice = wx.Choice(self, -1)
		sizer.Add(self.projectchoice, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

class SessionInstrumentPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
				'Select the instrument (if any) to be used in this session.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Instrument:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.instrumentchoice = wx.Choice(self, -1)
		sizer.Add(self.instrumentchoice, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

class SessionImageDirectoryPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
				'Select the directory where images from this session will be stored.\n(A subdirectory named after the session will be created for you)'),
												(0, 0), (1, 3))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.directorytextctrl = wx.TextCtrl(self, -1, '')
		sizer.Add(self.directorytextctrl, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.browsebutton = wx.Button(self, -1, 'Browse...')
		self.Bind(wx.EVT_BUTTON, self.onBrowse, self.browsebutton)
		sizer.Add(self.browsebutton, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sizer.AddGrowableCol(2)

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def onBrowse(self, evt):
		dlg = wx.DirDialog(self, 'Choose a directory',
												style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
		if dlg.ShowModal() == wx.ID_OK:
			self.directorytextctrl.SetLabel(dlg.GetPath())
		dlg.Destroy()

class SetupWizard(wx.wizard.Wizard):
	def __init__(self, parent):
		wx.wizard.Wizard.__init__(self, parent, -1, 'Leginon Setup')
		userpage = UserPage(self)
		sessiontypepage = SessionTypePage(self)
		sessionnamepage = SessionNamePage(self)
		sessionprojectpage = SessionProjectPage(self)
		sessioninstrumentpage = SessionInstrumentPage(self)
		sessionimagedirectorypage = SessionImageDirectoryPage(self)
		sessionselectpage = SessionSelectPage(self)

		userpage.setNext(sessiontypepage)
		sessiontypepage.setNext((sessionnamepage, sessionselectpage))
		sessionnamepage.setNext(sessionprojectpage)
		sessionprojectpage.setNext(sessioninstrumentpage)
		sessioninstrumentpage.setNext(sessionimagedirectorypage)
		sessionimagedirectorypage.setNext(sessionselectpage)

		self.FitToPage(userpage)
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

