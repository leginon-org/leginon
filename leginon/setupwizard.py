import wx
import wx.wizard
import wx.lib.intctrl
import leginonconfig
import os
import data
import project
import time
import sys

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
		sizer = wx.GridBagSizer(5, 5)

		welcometext = wx.StaticText(self, -1, 'Welcome to Leginon')
		font = welcometext.GetFont()
		font.SetPointSize(font.GetPointSize()*2)
		welcometext.SetFont(font)
		sizer.Add(welcometext, (0, 0), (1, 2))

		sizer.Add(wx.StaticText(self, -1,
						'Please select your name:'),
												(2, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		choices = parent.users.keys()
		choices.sort()
		self.userchoice = wx.Choice(self, -1, choices=choices)
		self.userchoice.SetSelection(0)
		sizer.Add(self.userchoice, (3, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)

		sizer.Add(wx.StaticText(self, -1,
									'then press the "Next" button to continue.'), (4, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def GetNext(self):
		return WizardPage.GetNext(self)

class SessionTypePage(WizardPage):
	def __init__(self, parent, create=None, ret=None):
		self.create = create
		self.ret = ret
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
						'Please indicate whether you would like to create a new session or use an existing session,'),
												(0, 0), (1, 2))

		choices = ['Create a new session', 'Return to an existing session']
		self.sessiontyperadiobox = wx.RadioBox(self, -1, 'Session Type',
																						choices=choices, majorDimension=1,
																						style=wx.RA_SPECIFY_COLS)
		sizer.Add(self.sessiontyperadiobox, (1, 0), (1, 2), wx.ALIGN_CENTER)

		sizer.Add(wx.StaticText(self, -1,
									'then press the "Next" button to continue.'), (3, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def setCreate(self, create):
		self.create = create

	def setReturn(self, ret):
		self.ret = ret

	def GetNext(self):
		n = self.sessiontyperadiobox.GetSelection()
		try:
			page = self.next[n]
		except IndexError:
			return None

		if page is not None:
			page.setPrevious(self)
		return page

class SessionSelectPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		self.pagesizer = wx.GridBagSizer()
		self.sizer = wx.GridBagSizer()

		self.sizer.Add(wx.StaticText(self, -1,
			'Please select the session you would like to continue.'),
							(0, 0), (1, 2))

		self.sessionchoice = wx.Choice(self, -1)
		self.sizer.Add(self.sessionchoice, (1, 0), (1, 2), wx.ALIGN_CENTER)

		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.limitsizer = wx.GridBagSizer(0, 3)
		self.limitcheckbox = wx.CheckBox(self, -1, '')
		self.limitcheckbox.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.onLimitChange, self.limitcheckbox)
		self.limitsizer.Add(self.limitcheckbox, (0, 0), (1, 1),
										wx.ALIGN_CENTER)
		self.limitsizer.Add(wx.StaticText(self, -1, 'List only last'),
												(0, 1), (1, 1), wx.ALIGN_CENTER)
		self.limitintctrl = wx.lib.intctrl.IntCtrl(self, -1, 10, size=(32, -1),
																								style=wx.TE_CENTER,
																								min=1, max=99, limited=True)
		self.limitintctrl.Bind(wx.EVT_TEXT, self.onLimitChange, self.limitintctrl)
		self.limitsizer.Add(self.limitintctrl, (0, 2), (1, 1), wx.ALIGN_CENTER)
		self.limitsizer.Add(wx.StaticText(self, -1, 'sessions'), (0, 3), (1, 1),
												wx.ALIGN_CENTER)

		self.sizer.Add(self.limitsizer, (2, 0), (1, 2), wx.ALIGN_CENTER)

		self.descriptiontext = wx.StaticText(self, -1, '')
		self.sizer.Add(self.descriptiontext, (4, 0), (1, 2), wx.ALIGN_CENTER)

		textsizer = wx.GridBagSizer(0, 3)

		textsizer.Add(wx.StaticText(self, -1, 'Instrument:'), (0, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.instrumenttext = wx.StaticText(self, -1, '')
		textsizer.Add(self.instrumenttext, (0, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		textsizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.imagedirectorytext = wx.StaticText(self, -1, '')
		textsizer.Add(self.imagedirectorytext, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		self.sizer.Add(textsizer, (5, 0), (1, 2), wx.ALIGN_CENTER)

		self.Bind(wx.EVT_CHOICE, self.onChoice, self.sessionchoice)

		self.connectcheckbox = wx.CheckBox(self, -1, 'Connect to instrument')
		self.sizer.Add(self.connectcheckbox, (7, 0), (1, 2), wx.ALIGN_CENTER)

		self.sizer.Add(wx.StaticText(self, -1,
							'Finally, press the "Finish" button to begin.'), (9, 0), (1, 2))

		self.pagesizer.Add(self.sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(self.pagesizer)

	def onLimitChange(self, evt):
		self.setSessionNames(self.GetParent().names)

	def onChoice(self, evt):
		self.updateText(evt.GetSelection())

	def updateText(self, n):
		parent = self.GetParent()
		session = parent.sessions[self.sessionchoice.GetString(n)]
		self.descriptiontext.SetLabel(session['comment'])
		try:
			self.instrumenttext.SetLabel(session['instrument']['name'])
			self.connectcheckbox.Enable(True)
		except (AttributeError, KeyError, TypeError):
			self.instrumenttext.SetLabel('(No instrument)')
			self.connectcheckbox.Enable(False)
		directory = leginonconfig.mapPath(session['image path'])
		self.imagedirectorytext.SetLabel(directory)
		# autoresize on static text gets reset by sizer during layout
		for i in [self.descriptiontext, self.instrumenttext,
							self.imagedirectorytext]:
			# if label is too big for wizard (presized) need to resize or truncate
			self.sizer.SetItemMinSize(i, i.GetSize())
		self.pagesizer.Layout()

	def setSessionNames(self, names):
		self.Freeze()
		self.sessionchoice.Clear()
		if self.limitcheckbox.IsChecked():
			self.sessionchoice.AppendItems(names[:self.limitintctrl.GetValue()])
		else:
			self.sessionchoice.AppendItems(names)
		size = self.sessionchoice.GetBestSize()
		self.sizer.SetItemMinSize(self.sessionchoice, size.width, size.height)
		self.pagesizer.Layout()
		self.sessionchoice.SetSelection(0)
		self.updateText(0)
		self.Thaw()

class SessionNamePage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
				'Please confirm the session name and enter an optional description.\n'+
				'You may change the suggested session name if needed.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Name:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		name = parent.setup.suggestSessionName()
		self.nametextctrl = wx.TextCtrl(self, -1, name, style=wx.TE_PROCESS_ENTER)
		self.Bind(wx.EVT_TEXT_ENTER, self.onValidateName, self.nametextctrl)
		sizer.Add(self.nametextctrl, (1, 1), (1, 1), wx.EXPAND|wx.ALL)

		sizer.Add(wx.StaticText(self, -1, 'Description:'), (2, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.descriptiontextctrl = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE)
		sizer.Add(self.descriptiontextctrl, (3, 0), (1, 2), wx.EXPAND|wx.ALL)

		sizer.Add(wx.StaticText(self, -1,
									'Then press the "Next" button to continue.'), (5, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def onValidateName(self, evt):
		if self.GetParent().setup.existsSessionName(evt.GetString()):
			self.nameExistsDialog()

	def nameExistsDialog(self):
		dlg = wx.MessageDialog(self,
											'A session with this name already exists.',
											'Invalid Session Name', wx.OK|wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()

class SessionProjectPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		sizer.Add(wx.StaticText(self, -1,
				'Select the project this session will be associated with,'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Project:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		choices = parent.projects.keys()
		choices.sort()
		self.projectchoice = wx.Choice(self, -1, choices=choices)
		self.projectchoice.SetSelection(0)
		sizer.Add(self.projectchoice, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1,
									'then press the "Next" button to continue.'), (3, 0), (1, 2))

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
				'Select the instrument (if any) to be used in this session,'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Instrument:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		choices = parent.instruments.keys()
		choices.sort()
		choices.insert(0, 'No instrument')
		self.instrumentchoice = wx.Choice(self, -1, choices=choices)
		self.instrumentchoice.SetSelection(0)
		sizer.Add(self.instrumentchoice, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(wx.StaticText(self, -1,
									'then press the "Next" button to continue.'), (3, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

# might want to check if directory exists and warn...
class SessionImageDirectoryPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer(0, 5)

		sizer.Add(wx.StaticText(self, -1,
				'Select the directory where images from this session will be stored.\n(A subdirectory named after the session will be created for you)'),
												(0, 0), (1, 3))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		try:
			defaultdirectory = leginonconfig.mapPath(leginonconfig.IMAGE_PATH)
		except AttributeError:
			defaultdirectory = ''
		self.directorytextctrl = wx.TextCtrl(self, -1, defaultdirectory)
		sizer.Add(self.directorytextctrl, (1, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT|wx.RIGHT)
		self.browsebutton = wx.Button(self, -1, 'Browse...')
		self.Bind(wx.EVT_BUTTON, self.onBrowse, self.browsebutton)
		sizer.Add(self.browsebutton, (1, 2), (1, 1), wx.ALIGN_CENTER)

		sizer.AddGrowableCol(2)

		sizer.Add(wx.StaticText(self, -1,
									'Then press the "Next" button to continue.'), (3, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def onBrowse(self, evt):
		dlg = wx.DirDialog(self, 'Select a base directory',
												self.directorytextctrl.GetValue(),
												style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
		if dlg.ShowModal() == wx.ID_OK:
			self.directorytextctrl.SetValue(dlg.GetPath())
		dlg.Destroy()

class SessionCreatePage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		self.pagesizer = wx.GridBagSizer()
		self.sizer = wx.GridBagSizer()

		self.sizer.Add(wx.StaticText(self, -1,
									'Would you like to create the following session?'),
									(0, 0), (1, 2))

		self.nametext = wx.StaticText(self, -1, '')
		self.sizer.Add(self.nametext, (1, 0), (1, 2), wx.ALIGN_CENTER)

		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.descriptiontext = wx.StaticText(self, -1, '')
		self.sizer.Add(self.descriptiontext, (2, 0), (1, 2), wx.ALIGN_CENTER)

		textsizer = wx.GridBagSizer(0, 3)

		if parent.projects:
			textsizer.Add(wx.StaticText(self, -1, 'Project:'), (0, 0), (1, 1),
															wx.ALIGN_CENTER_VERTICAL)
			self.projecttext = wx.StaticText(self, -1, '')
			textsizer.Add(self.projecttext, (0, 1), (1, 1),
															wx.ALIGN_CENTER_VERTICAL)

		textsizer.Add(wx.StaticText(self, -1, 'Instrument:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.instrumenttext = wx.StaticText(self, -1, '')
		textsizer.Add(self.instrumenttext, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		textsizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (2, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.imagedirectorytext = wx.StaticText(self, -1, '')
		textsizer.Add(self.imagedirectorytext, (2, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		self.sizer.Add(textsizer, (3, 0), (1, 2), wx.ALIGN_CENTER)

		self.connectcheckbox = wx.CheckBox(self, -1, 'Connect to instrument')
		self.sizer.Add(self.connectcheckbox, (5, 0), (1, 2), wx.ALIGN_CENTER)

		self.sizer.Add(wx.StaticText(self, -1,
					'Please press the "Finish" button if these settings are correct.'),
									(7, 0), (1, 2))

		self.pagesizer.Add(self.sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(self.pagesizer)

class SetupWizard(wx.wizard.Wizard):
	def __init__(self, parent, research, publish):
		self.setup = Setup(research)
		self.publish = publish
		self.session = None
		image = wx.Image(os.path.join(sys.path[0], 'setup.png'))
		bitmap = wx.BitmapFromImage(image)
		wx.wizard.Wizard.__init__(self, parent, -1, 'Leginon Setup', bitmap=bitmap)

		self.users = self.setup.getUsers()
		if not self.users:
			dlg = wx.MessageDialog(self,
												'Databases with no users are not currently supported',
												'Fatal Error', wx.OK|wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			raise RuntimeError('Databases with no users are not current supported')

		self.userpage = UserPage(self)

		sessiontypepage = SessionTypePage(self)
		self.namepage = SessionNamePage(self)

		self.projects = self.setup.getProjects()
		if self.projects:
			self.projectpage = SessionProjectPage(self)

		self.instruments = self.setup.getInstruments()
		self.instrumentpage = SessionInstrumentPage(self)
		self.imagedirectorypage = SessionImageDirectoryPage(self)
		self.sessionselectpage = SessionSelectPage(self)
		self.sessioncreatepage = SessionCreatePage(self)

		self.userpage.setNext(sessiontypepage)
		sessiontypepage.setNext((self.namepage, self.sessionselectpage))
		if self.projects:
			self.namepage.setNext(self.projectpage)
			self.projectpage.setNext(self.instrumentpage)
		else:
			self.namepage.setNext(self.instrumentpage)
		self.instrumentpage.setNext(self.imagedirectorypage)
		self.imagedirectorypage.setNext(self.sessioncreatepage)

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.onPageChanging, self)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.onPageChanged, self)

		self.FitToPage(self.userpage)

		if hasattr(leginonconfig, 'USERNAME') and leginonconfig.USERNAME:
			usernames = self.setup._indexBy('name', self.users.values())
			try:
				name = usernames[leginonconfig.USERNAME]['full name']
				self.userpage.userchoice.SetStringSelection(name)
				userdata = self.users[self.userpage.userchoice.GetStringSelection()]
				self.names, self.sessions = self.setup.getSessions(userdata)
				if not self.sessions:
					self.userpage.setNext(self.namepage)
				self.RunWizard(self.userpage.GetNext())
			except KeyError:
				dlg = wx.MessageDialog(self,
									'Cannot find user "%s" in database' % leginonconfig.USERNAME,
									'Warning', wx.OK|wx.ICON_WARNING)
				dlg.ShowModal()
				dlg.Destroy()
				self.RunWizard(self.userpage)
		else:
			self.RunWizard(self.userpage)

	def onPageChanging(self, evt):
		# this count only for forward
		if not evt.GetDirection():
			return
		page = evt.GetPage()
		if page is self.userpage:
			userdata = self.users[self.userpage.userchoice.GetStringSelection()]
			self.names, self.sessions = self.setup.getSessions(userdata)
			if not self.sessions:
				self.userpage.setNext(self.namepage)
		elif page is self.namepage:
			name = self.namepage.nametextctrl.GetValue()
			if self.setup.existsSessionName(name):
				evt.Veto()
				self.namepage.nameExistsDialog()
		elif page is self.sessionselectpage:
			name = self.sessionselectpage.sessionchoice.GetStringSelection()
			self.session = self.sessions[name]
			self.connect = self.sessionselectpage.connectcheckbox.GetValue()
		elif page is self.sessioncreatepage:
			user = self.userpage.userchoice.GetStringSelection()
			user = self.users[user]
			name = self.namepage.nametextctrl.GetValue()
			description = self.namepage.descriptiontextctrl.GetValue()
			project = self.projectpage.projectchoice.GetStringSelection()
			instrument = self.instrumentpage.instrumentchoice.GetStringSelection()
			try:
				instrument = self.instruments[instrument]
			except KeyError:
				instrument = None
			directory = self.imagedirectorypage.directorytextctrl.GetValue()
			self.session = self.setup.createSession(user, name, description,
																							instrument, directory)
			self.publish(self.session, database=True)
			if self.projects:
				projectid = self.projects[project]['projectId']
				self.setup.linkSessionProject(self.session, projectid)
			self.connect = self.sessioncreatepage.connectcheckbox.GetValue()

	def onPageChanged(self, evt):
		page = evt.GetPage()
		if page is self.sessionselectpage:
			self.sessionselectpage.setSessionNames(self.names)
		elif page is self.sessioncreatepage:
			name = self.namepage.nametextctrl.GetValue()
			description = self.namepage.descriptiontextctrl.GetValue()
			project = self.projectpage.projectchoice.GetStringSelection()
			instrument = self.instrumentpage.instrumentchoice.GetStringSelection()
			directory = self.imagedirectorypage.directorytextctrl.GetValue()
			self.sessioncreatepage.nametext.SetLabel(name)
			self.sessioncreatepage.descriptiontext.SetLabel(description)
			if self.projects:
				self.sessioncreatepage.projecttext.SetLabel(project)
			self.sessioncreatepage.instrumenttext.SetLabel(instrument)
			self.sessioncreatepage.imagedirectorytext.SetLabel(directory)
			# autoresize on static text gets reset by sizer during layout
			texts = ['name', 'description', 'project', 'instrument', 'imagedirectory']
			for i in texts:
				# if label is too big for wizard (presized) need to resize or truncate
				o = getattr(self.sessioncreatepage, i + 'text')
				self.sessioncreatepage.sizer.SetItemMinSize(o, o.GetSize())
			self.sessioncreatepage.pagesizer.Layout()

class Setup(object):
	def __init__(self, research):
		self.research = research
		self.projectdata = project.ProjectData()

	def _indexBy(self, by, datalist):
		index = {}
		bydone = []
		for indexdata in datalist:
			try:
				key = indexdata[by]
				if key not in bydone:
					index[key] = indexdata
					bydone.append(key)
			except (TypeError, IndexError):
				pass
		return index

	def getUsers(self):
		userdata = data.UserData(initializer={})
		userdatalist = self.research(datainstance=userdata)
		return self._indexBy('full name', userdatalist)

	def getSessions(self, userdata, n=None):
		sessiondata = data.SessionData(initializer={'user': userdata})
		sessiondatalist = self.research(datainstance=sessiondata, results=n)
		return (map(lambda d: d['name'], sessiondatalist),
						self._indexBy('name', sessiondatalist))

	def getProjects(self):
		if not self.projectdata.isConnected():
			return {}
		projects = self.projectdata.getProjects()
		projectdatalist = projects.getall()
		return self._indexBy('name', projectdatalist)

	def getInstruments(self):
		instrumentdata = data.InstrumentData(initializer={})
		instrumentdatalist = self.research(datainstance=instrumentdata)
		return self._indexBy('name', instrumentdatalist)

	def suggestSessionName(self):
		session_name = '<cannot suggest a name>'
		for suffix in 'abcdefghijklmnopqrstuvwxyz':
			maybe_name = time.strftime('%y%b%d'+suffix).lower()
			if self.existsSessionName(maybe_name):
				continue
			else:
				session_name = maybe_name
				break
		return session_name

	def existsSessionName(self, name):
		sessiondata = data.SessionData(name=name)
		if self.research(datainstance=sessiondata):
			return True
		return False

	def createSession(self, user, name, description, instrument, directory):
		imagedirectory = os.path.join(leginonconfig.unmapPath(directory), name).replace('\\', '/')
		initializer = {
			'name': name,
			'comment': description,
			'user': user,
			'instrument': instrument,
			'image path': imagedirectory,
		}
		return data.SessionData(initializer=initializer)

	def linkSessionProject(self, sessiondata, projectid):
		if not self.projectdata.isConnected():
			raise RuntimeError('Cannot link session, not connected to database.')
		projectsession = project.ProjectExperiment(projectid, sessiondata['name'])
		experiments = self.projectdata.getProjectExperiments()
		experiments.insert([projectsession.dumpdict()])

if __name__ == '__main__':
	class TestApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Test')
			self.SetTopWindow(frame)
			wizard = SetupWizard(frame, None)
			frame.Show(True)
			return True

	app = TestApp(0)
	app.MainLoop()

