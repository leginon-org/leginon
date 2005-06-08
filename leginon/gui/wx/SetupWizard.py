# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/SetupWizard.py,v $
# $Revision: 1.17 $
# $Name: not supported by cvs2svn $
# $Date: 2005-06-08 18:27:09 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import data
import icons
import leginonconfig
import os.path
import project
import time
import wx
import wx.wizard
import wx.lib.intctrl
import gui.wx.Dialog
import gui.wx.ListBox

class WizardPage(wx.wizard.PyWizardPage):
	pass

# if no session go directly to new session page
class UserPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Welcome to Leginon')
		font = label.GetFont()
		font.SetPointSize(font.GetPointSize()*2)
		label.SetFont(font)
		sizer.Add(label, (0, 0), (1, 2))

		label = wx.StaticText(self, -1, 'Please select your name:')
		sizer.Add(label, (2, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		self.userchoice = wx.Choice(self, -1)
		sizer.Add(self.userchoice, (3, 0), (1, 2), wx.ALIGN_CENTER_HORIZONTAL)

		label = wx.StaticText(self, -1, 'then press the "Next" button to continue.')
		sizer.Add(label, (4, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def getSelectedUser(self):
		return self.users[self.userchoice.GetStringSelection()]

	def setUserSelection(self):
		self.skip = False
		if hasattr(leginonconfig, 'USERNAME') and leginonconfig.USERNAME:
			usernames = _indexBy('full name', self.users.values())
			if leginonconfig.USERNAME in usernames:
				self.userchoice.SetStringSelection(leginonconfig.USERNAME)
				self.skip = True
			else:
				dlg = wx.MessageDialog(self,
									'Cannot find user "%s" in database' % leginonconfig.USERNAME,
									'Warning', wx.OK|wx.ICON_WARNING)
				dlg.ShowModal()
				dlg.Destroy()
				self.userchoice.SetSelection(0)
		else:
			self.userchoice.SetSelection(0)
		self.onUserChoice()

	def setUsers(self, users):
		self.users = users
		choices = users.keys()
		choices.sort()
		self.userchoice.AppendItems(choices)
		self.setUserSelection()
		self.Bind(wx.EVT_CHOICE, self.onUserChoice, self.userchoice)

	def onUserChoice(self, evt=None):
		if evt is None:
			name = self.userchoice.GetStringSelection()
		else:
			name = evt.GetString()
		userdata = self.users[name]
		self.names, self.sessions = self.GetParent().setup.getSessions(userdata)

		parent = self.GetParent()

		# update sessions
		parent.sessionselectpage.setSessionNames(self.names)

		# update database values
		sd = self.GetParent().setup.getSettings(userdata)
		self.GetParent().setSettings(sd)
		# oops...
		parent.sessionselectpage.setSessionNames(self.names)

	def GetNext(self):
		parent = self.GetParent()
		if self.sessions:
			return parent.sessiontypepage
		else:
			return parent.namepage

class SessionTypePage(WizardPage):
	def __init__(self, parent, create=None, ret=None):
		self.create = create
		self.ret = ret
		WizardPage.__init__(self, parent)
		self.SetName('wpSessionType')
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer()

		label = wx.StaticText(self, -1, 'Please indicate whether you would like'\
																			' to create a new session or use an'\
																			' existing session,')
		sizer.Add(label, (0, 0), (1, 2))

		choices = ['Create a new session', 'Return to an existing session']
		self.sessiontyperadiobox = wx.RadioBox(self, -1, 'Session Type',
																						choices=choices,
																						majorDimension=1,
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

	def GetPrev(self):
		return self.GetParent().userpage

	def GetNext(self):
		parent = self.GetParent()
		n = self.sessiontyperadiobox.GetSelection()
		if n == 0:
			return parent.namepage
		else:
			return parent.sessionselectpage

class SessionSelectPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		self.SetName('wpSessionSelect')
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
		self.Bind(wx.EVT_CHECKBOX, self.onLimitChange, self.limitcheckbox)
		self.limitsizer.Add(self.limitcheckbox, (0, 0), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'List only last')
		self.limitsizer.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.limitintctrl = wx.lib.intctrl.IntCtrl(self, -1, 10, size=(32, -1),
																								style=wx.TE_CENTER,
																								min=1, max=99, limited=True)
		self.limitintctrl.Bind(wx.EVT_TEXT, self.onLimitChange, self.limitintctrl)
		self.limitsizer.Add(self.limitintctrl, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'sessions')
		self.limitsizer.Add(label, (0, 3), (1, 1), wx.ALIGN_CENTER)

		self.sizer.Add(self.limitsizer, (2, 0), (1, 2), wx.ALIGN_CENTER)

		self.descriptiontext = wx.StaticText(self, -1, '')
		self.sizer.Add(self.descriptiontext, (4, 0), (1, 2), wx.ALIGN_CENTER)

		textsizer = wx.GridBagSizer(0, 3)
		label = wx.StaticText(self, -1, 'Image Directory:')
		textsizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.imagedirectorytext = wx.StaticText(self, -1, '')
		textsizer.Add(self.imagedirectorytext, (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(textsizer, (5, 0), (1, 2), wx.ALIGN_CENTER)

		self.Bind(wx.EVT_CHOICE, self.onSessionChoice, self.sessionchoice)

		clientssizer = wx.GridBagSizer(5, 5)
		self.clientslabel = wx.StaticText(self, -1, '')
		self.setClients([])
		clientssizer.Add(self.clientslabel, (0, 0), (1, 1),
											wx.ALIGN_CENTER_VERTICAL)
		editclientsbutton = wx.Button(self, -1, 'Edit...')
		clientssizer.Add(editclientsbutton, (0, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		clientssizer.AddGrowableCol(0)
		clientssizer.AddGrowableCol(1)
		self.sizer.Add(clientssizer, (7, 0), (1, 2), wx.EXPAND)

		self.sizer.Add(wx.StaticText(self, -1,
							'Finally, press the "Finish" button to begin.'), (9, 0), (1, 2))

		self.pagesizer.Add(self.sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(self.pagesizer)

		self.Bind(wx.EVT_BUTTON, self.onEditClientsButton, editclientsbutton)

	def setClients(self, clients):
		self.clients = clients
		self.history = self.GetParent().setup.getRecentClients()
		label = 'Connect to clients: '
		if clients:
			for i in clients:
				label += i
				label += ', '
			label = label[:-2]
		else:
			label += '(no clients selected)'
		self.clientslabel.SetLabel(label)

	def onEditClientsButton(self, evt):
		dialog = EditClientsDialog(self, self.clients, self.history)
		if dialog.ShowModal() == wx.ID_OK:
			self.setClients(dialog.listbox.getValues())
		dialog.Destroy()

	def onLimitChange(self, evt):
		if self.IsShown():
			self.Freeze()
			self.setSessionNames(self.GetParent().userpage.names)
			self.Thaw()

	def onSessionChoice(self, evt):
		self.updateText(evt.GetString())

	def updateText(self, selection):
		parent = self.GetParent()
		if not selection:
			self.descriptiontext.SetLabel('')
			self.imagedirectorytext.SetLabel('')
		else:
			session = parent.userpage.sessions[selection]
			self.descriptiontext.SetLabel(session['comment'])
			directory = leginonconfig.mapPath(session['image path'])
			self.imagedirectorytext.SetLabel(directory)
		# autoresize on static text gets reset by sizer during layout
		for i in [self.descriptiontext, self.imagedirectorytext]:
			# if label is too big for wizard (presized) need to resize or truncate
			self.sizer.SetItemMinSize(i, i.GetSize())
		self.pagesizer.Layout()
		self.setClients(parent.setup.getClients(selection))

	def setSessionNames(self, names):
		if self.limitcheckbox.IsChecked():
			limit = self.limitintctrl.GetValue()
			if not limit:
				return
			names = names[:limit]
		selection = self.sessionchoice.GetStringSelection()
		self.sessionchoice.Clear()
		self.sessionchoice.AppendItems(names)
		size = self.sessionchoice.GetBestSize()
		self.sizer.SetItemMinSize(self.sessionchoice, size.width, size.height)
		self.pagesizer.Layout()
		if self.sessionchoice.FindString(selection) is not wx.NOT_FOUND:
			self.sessionchoice.SetStringSelection(selection)
		else:
			self.sessionchoice.SetSelection(0)
			selection = self.sessionchoice.GetString(0)
		self.updateText(selection)

	def GetPrev(self):
		return self.GetParent().sessiontypepage

	def getSelectedSession(self):
		name = self.sessionchoice.GetStringSelection()
		return self.GetParent().userpage.sessions[name]

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

	def GetPrev(self):
		parent = self.GetParent()
		if parent.userpage.sessions:
			return parent.sessiontypepage
		else:
			return parent.userpage

	def GetNext(self):
		parent = self.GetParent()
		if parent.projectpage is None:
			return parent.imagedirectorypage
		else:
			return parent.projectpage

class NoProjectDatabaseError(Exception):
	pass

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
		if parent.setup.projectdata is None:
			raise NoProjectDatabaseError
		self.projects = parent.setup.getProjects()
		choices = self.projects.keys()
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

	def getSelectedProjectId(self):
		project = self.projectchoice.GetStringSelection()
		return self.projects[project]['projectId']

	def GetPrev(self):
		return self.GetParent().namepage

	def GetNext(self):
		return self.GetParent().imagedirectorypage

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

	def GetPrev(self):
		parent = self.GetParent()
		if parent.projectpage is None:
			return parent.namepage
		else:
			return parent.projectpage

	def GetNext(self):
		return self.GetParent().sessioncreatepage

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

		if parent.projectpage is not None:
			textsizer.Add(wx.StaticText(self, -1, 'Project:'), (0, 0), (1, 1),
															wx.ALIGN_CENTER_VERTICAL)
			self.projecttext = wx.StaticText(self, -1, '')
			textsizer.Add(self.projecttext, (0, 1), (1, 1),
															wx.ALIGN_CENTER_VERTICAL)


		textsizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.imagedirectorytext = wx.StaticText(self, -1, '')
		textsizer.Add(self.imagedirectorytext, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		self.sizer.Add(textsizer, (3, 0), (1, 2), wx.ALIGN_CENTER)

		clientssizer = wx.GridBagSizer(5, 5)
		self.clientslabel = wx.StaticText(self, -1, '')
		self.setClients([])
		clientssizer.Add(self.clientslabel, (0, 0), (1, 1),
											wx.ALIGN_CENTER_VERTICAL)
		editclientsbutton = wx.Button(self, -1, 'Edit...')
		clientssizer.Add(editclientsbutton, (0, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		clientssizer.AddGrowableCol(0)
		clientssizer.AddGrowableCol(1)
		self.sizer.Add(clientssizer, (5, 0), (1, 2), wx.EXPAND)

		self.sizer.Add(wx.StaticText(self, -1,
					'Please press the "Finish" button if these settings are correct.'),
									(7, 0), (1, 2))

		self.pagesizer.Add(self.sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(self.pagesizer)

		self.Bind(wx.EVT_BUTTON, self.onEditClientsButton, editclientsbutton)

	def setClients(self, clients):
		self.clients = clients
		self.history = self.GetParent().setup.getRecentClients()
		label = 'Connect to clients: '
		if clients:
			for i in clients:
				label += i
				label += ', '
			label = label[:-2]
		else:
			label += '(no clients selected)'
		self.clientslabel.SetLabel(label)

	def onEditClientsButton(self, evt):
		dialog = EditClientsDialog(self, self.clients, self.history)
		if dialog.ShowModal() == wx.ID_OK:
			self.setClients(dialog.listbox.getValues())
		dialog.Destroy()

	def GetPrev(self):
		return self.GetParent().imagedirectorypage

class SetupWizard(wx.wizard.Wizard):
	def __init__(self, parent, research, publish):
		self.setup = Setup(research, publish)
		self.publish = publish
		self.session = None
		image = wx.Image(icons.getPath('setup.png'))
		bitmap = wx.BitmapFromImage(image)
		wx.wizard.Wizard.__init__(self, parent, -1, 'Leginon Setup', bitmap=bitmap)
		self.SetName('wLeginonSetup')

		# create pages
		self.userpage = UserPage(self)
		self.sessiontypepage = SessionTypePage(self)
		self.namepage = SessionNamePage(self)
		try:
			self.projectpage = SessionProjectPage(self)
		except NoProjectDatabaseError:
			self.projectpage = None
		self.imagedirectorypage = SessionImageDirectoryPage(self)
		self.sessionselectpage = SessionSelectPage(self)
		self.sessioncreatepage = SessionCreatePage(self)

		# initialize page values
		users = self.getUsers()
		self.userpage.setUsers(users)

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.onPageChanging, self)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.onPageChanged, self)
		self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.onFinished)

		self.FitToPage(self.userpage)
		self.Raise()
		if self.userpage.skip:
			self.RunWizard(self.userpage.GetNext())
		else:
			self.RunWizard(self.userpage)

	def onFinished(self, evt):
		if self.session is not None:
			initializer = self.getSettings()
			self.setup.saveSettings(self.session['user'], initializer)

	def getUsers(self):
		users = self.setup.getUsers()
		if not users:
			dlg = wx.MessageDialog(self,
												'Databases with no users are not currently supported',
												'Fatal Error', wx.OK|wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()
			raise RuntimeError('Databases with no users are not currently supported')
		return users

	def onPageChanging(self, evt):
		# this counts only for forward
		if not evt.GetDirection():
			return
		page = evt.GetPage()
		if page is self.namepage:
			name = self.namepage.nametextctrl.GetValue()
			if self.setup.existsSessionName(name):
				evt.Veto()
				self.namepage.nameExistsDialog()
		elif page is self.sessionselectpage:
			self.session = self.sessionselectpage.getSelectedSession()
			self.clients = self.sessionselectpage.clients
			self.history = self.sessionselectpage.history
			self.setup.saveClients(self.session, self.clients)
		elif page is self.sessioncreatepage:
			user = self.userpage.getSelectedUser()
			name = self.namepage.nametextctrl.GetValue()
			description = self.namepage.descriptiontextctrl.GetValue()
			directory = self.imagedirectorypage.directorytextctrl.GetValue()
			self.session = self.setup.createSession(user, name, description,
																							directory)
			self.publish(self.session, database=True)
			if self.projectpage is not None:
				projectid = self.projectpage.getSelectedProjectId()
				self.setup.linkSessionProject(self.session, projectid)
			self.clients = self.sessioncreatepage.clients
			self.history = self.sessioncreatepage.history
			self.setup.saveClients(self.session, self.clients)

	def onPageChanged(self, evt):
		page = evt.GetPage()
		if page is self.sessioncreatepage:
			name = self.namepage.nametextctrl.GetValue()
			description = self.namepage.descriptiontextctrl.GetValue()
			if self.projectpage is not None:
				project = self.projectpage.projectchoice.GetStringSelection()
			directory = self.imagedirectorypage.directorytextctrl.GetValue()
			self.sessioncreatepage.nametext.SetLabel(name)
			self.sessioncreatepage.descriptiontext.SetLabel(description)
			if self.projectpage is not None:
				self.sessioncreatepage.projecttext.SetLabel(project)
			self.sessioncreatepage.imagedirectorytext.SetLabel(directory)
			# autoresize on static text gets reset by sizer during layout
			texts = ['name', 'description', 'project', 'imagedirectory']
			for i in texts:
				# if label is too big for wizard (presized) need to resize or truncate
				try:
					o = getattr(self.sessioncreatepage, i + 'text')
				except AttributeError:
					pass
				self.sessioncreatepage.sizer.SetItemMinSize(o, o.GetSize())
			self.sessioncreatepage.pagesizer.Layout()

	def setSettings(self, sd):
		if sd['session type']:
			s = sd['session type']
			n = self.sessiontypepage.sessiontyperadiobox.FindString(s)
			if n != wx.NOT_FOUND:
				self.sessiontypepage.sessiontyperadiobox.SetSelection(n)
		self.sessionselectpage.limitcheckbox.SetValue(sd['limit'])
		self.sessionselectpage.limitintctrl.SetValue(sd['n limit'])
		if sd['selected session'] is not None:
			s = sd['selected session']
			n = self.sessionselectpage.sessionchoice.FindString(s)
			if n != wx.NOT_FOUND:
				self.sessionselectpage.sessionchoice.SetSelection(n)

	def getSettings(self):
		initializer = {
			'session type':
				self.sessiontypepage.sessiontyperadiobox.GetStringSelection(),
			'selected session':
				self.session['name'],
			'limit':
				self.sessionselectpage.limitcheckbox.GetValue(),
			'n limit':
				self.sessionselectpage.limitintctrl.GetValue(),
		}
		return initializer

def _indexBy(by, datalist):
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

class Setup(object):
	def __init__(self, research, publish):
		self.research = research
		self.publish = publish
		try:
			self.projectdata = project.ProjectData()
		except project.NotConnectedError:
			self.projectdata = None

	def getUsers(self):
		userdata = data.UserData(initializer={})
		userdatalist = self.research(datainstance=userdata)
		return _indexBy('full name', userdatalist)

	def getSettings(self, userdata):
		settingsclass = data.SetupWizardSettingsData
		defaultsettings = {
			'session type': 'Create a new session',
			'selected session': None,
			'limit': True,
			'n limit': 10,
			'connect': True,
		}
		qsession = data.SessionData(initializer={'user': userdata})
		qdata = settingsclass(initializer={'session': qsession})
		try:
			settings = self.research(qdata, results=1)[0]
		except IndexError:
			settings = settingsclass(initializer=defaultsettings)
		return settings

	def getClients(self, name):
		sessiondata = data.SessionData(initializer={'name': name})
		querydata = data.ConnectToClientsData(session=sessiondata)
		try:
			return self.research(querydata, results=1)[0]['clients']
		except IndexError:
			return []

	def getRecentClients(self):
		try:
			results = self.research(data.ConnectToClientsData(), results=100)
		except IndexError:
			results = []
		clients = {}
		for result in results:
			for client in result['clients']:
				clients[str(client)] = None
		clients = clients.keys()
		clients.sort()
		return clients

	def saveClients(self, session, clients):
		initializer = {'session': session, 'clients': clients}
		clientsdata = data.ConnectToClientsData(initializer=initializer)
		self.publish(clientsdata, database=True, dbforce=True)

	def saveSettings(self, userdata, initializer):
		settingsclass = data.SetupWizardSettingsData
		sd = settingsclass(initializer=initializer)
		sd['session'] = data.SessionData(initializer={'user': userdata})
		self.publish(sd, database=True, dbforce=True)

	def getSessions(self, userdata, n=None):
		sessiondata = data.SessionData(initializer={'user': userdata})
		sessiondatalist = self.research(datainstance=sessiondata, results=n)
		return (map(lambda d: d['name'], sessiondatalist),
						_indexBy('name', sessiondatalist))

	def getProjects(self):
		if self.projectdata is None:
			return {}
		projects = self.projectdata.getProjects()
		projectdatalist = projects.getall()
		return _indexBy('name', projectdatalist)

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

	def createSession(self, user, name, description, directory):
		imagedirectory = os.path.join(leginonconfig.unmapPath(directory), name, 'rawdata').replace('\\', '/')
		initializer = {
			'name': name,
			'comment': description,
			'user': user,
			'image path': imagedirectory,
		}
		return data.SessionData(initializer=initializer)

	def linkSessionProject(self, sessiondata, projectid):
		if self.projectdata is None:
			raise RuntimeError('Cannot link session, not connected to database.')
		projectsession = project.ProjectExperiment(projectid, sessiondata['name'])
		experiments = self.projectdata.getProjectExperiments()
		experiments.insert([projectsession.dumpdict()])

class EditClientsDialog(gui.wx.Dialog.Dialog):
	def __init__(self, parent, clients, history):
		self.clients = clients
		self.history = history
		gui.wx.Dialog.Dialog.__init__(self, parent, 'Edit Clients')

	def onInitialize(self):
		self.listbox = gui.wx.ListBox.EditListBox(self, -1, 'Clients', choices=self.history)
		self.listbox.setValues(self.clients)
		self.sz.Add(self.listbox, (0, 0), (1, 1), wx.EXPAND)
		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)
		self.addButton('OK', id=wx.ID_OK)
		self.addButton('Cancel', id=wx.ID_CANCEL)

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

