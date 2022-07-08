# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import sys
import os.path
import time
import wx
import wx.wizard
import wx.lib.intctrl
import wx.lib.agw.hyperlink as hl
from pyami import mysocket

import leginon.leginondata
import leginon.projectdata
import leginon.icons
import leginon.leginonconfig
import leginon.project
import leginon.gui.wx.Dialog
import leginon.gui.wx.ListBox
import leginon.version
import leginon.session
import leginon.ddinfo
from leginon.gui.wx.Entry import IntEntry

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
		if hasattr(leginon.leginonconfig, 'USERNAME') and leginon.leginonconfig.USERNAME:
			usernames = _indexBy(('firstname','lastname'), self.users.values())
			if leginon.leginonconfig.USERNAME in usernames:
				self.userchoice.SetStringSelection(leginon.leginonconfig.USERNAME)
				self.skip = True
			else:
				dlg = wx.MessageDialog(self,
									'Cannot find user "%s" in database' % leginon.leginonconfig.USERNAME,
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
		sd = self.GetParent().setup.getSettings(userdata)
		self.GetParent().setSettings(sd)

		self.names, self.sessions = self.GetParent().setup.getSessions(userdata)
		self.projects = self.GetParent().setup.getProjects(userdata)

		parent = self.GetParent()

		# update sessions
		parent.sessionselectpage.setSessionNames(self.names)

		#update projects
		project_choices = self.projects.keys()
		project_choices.sort()
		parent.projectpage.setProjectNames(project_choices)

		# update database values
		session = parent.sessionselectpage.getSelectedSession()
		if session:
			parent.sessionselectpage.updateText(session['name'])

	def GetNext(self):
		parent = self.GetParent()
		if self.sessions:
			return parent.sessiontypepage
		else:
			parent.namepage.suggestName()
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
		label = wx.StaticText(self, -1, '''NOTE:
You can skip the entire setup wizard if you want to continue
a previous session.  Start leginon with the -s and -c options:

     %s -s <session> -c <clients>

Examples:

     %s -s 07apr16b -c tecnai2
         (restart session 07apr16b, connect to tecnai2)
     %s -s 07apr16b -c tecnai2,somehost
         (restart session 07apr16b, connect to clients tecnai2 and somehost)

Starting Leginon this way will instantly connect to the clients,
so be sure the clients are running before starting Leginon.
''' % (sys.argv[0], sys.argv[0], sys.argv[0]))
		sizer.Add(label, (5, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def setCreate(self, create):
		self.create = create

	def setReturn(self, ret):
		self.ret = ret

	def GetPrev(self):
		parent = self.GetParent()
		return parent.userpage

	def GetNext(self):
		parent = self.GetParent()
		n = self.sessiontyperadiobox.GetSelection()
		if n == 0:
			# create new session
			parent.namepage.suggestName()
			return parent.projectpage
		else:
			leginon.session.cancelReservation()
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
		sessiondata = self.getSelectedSession()
		if sessiondata and self.checkPresetExistance(sessiondata):
			self.clientEditWarningDialog()
		dialog = EditClientsDialog(self, self.clients, self.history)
		if dialog.ShowModal() == wx.ID_OK:
			self.setClients(dialog.listbox.getValues())
		dialog.Destroy()

	def clientEditWarningDialog(self):
		dlg = wx.MessageDialog(self,
											'You should not switch instrument hosts in this session. Addition is OK.',
											'Preset Exists In This Session', wx.OK|wx.ICON_WARNING)
		dlg.ShowModal()
		dlg.Destroy()

	def checkPresetExistance(self,sessiondata):
		presets = self.GetParent().setup.getPresets(sessiondata)
		return bool(presets)
		
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
			if session['comment']:
				self.descriptiontext.SetLabel(session['comment'])
			else:
				self.descriptiontext.SetLabel('(No description)')
			if session['image path']:
				directory = leginon.leginonconfig.mapPath(session['image path'])
				self.imagedirectorytext.SetLabel(directory)
			else:
				self.imagedirectorytext.SetLabel('(No image path)')
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
			## catching exception generated by wxPython 2.6.3.2
			try:
				selection = self.sessionchoice.GetString(0)
			except:
				selection = ""
		self.updateText(selection)

	def GetPrev(self):
		return self.GetParent().sessiontypepage

	def getSelectedSession(self):
		name = self.sessionchoice.GetStringSelection()
		if name:
			return self.GetParent().userpage.sessions[name]
		else:
			return None

class SessionNamePage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer(10,5)

		sizer.Add(wx.StaticText(self, -1,
				'Please confirm the session name and optionally select the holder.\n'+
				'You may change the suggested session name if needed.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Name:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.nametextctrl = wx.TextCtrl(self, -1, '', style=wx.TE_PROCESS_ENTER)
		self.Bind(wx.EVT_TEXT_ENTER, self.onValidateName, self.nametextctrl)
		sizer.Add(self.nametextctrl, (1, 1), (1, 1), wx.EXPAND|wx.ALL)

		holders = leginon.leginondata.GridHolderData(hidden=False)
		holders = holders.query()
		# Trick the system to be back compatible
		if not holders:
			holders = leginon.leginondata.GridHolderData(hidden=False).query()
			if not holders:
				leginon.leginondata.GridHolderData(name='fake',hidden=True).insert()
				holders = leginon.leginondata.GridHolderData(hidden=False).query()
		holders = [holder['name'] for holder in holders]
		holders.sort()
		self.holderctrl = wx.ComboBox(self, -1, choices=holders, style=wx.CB_DROPDOWN)
		self.holderctrl.SetValue('Unknown Holder')
		sizer.Add(wx.StaticText(self, -1, 'Choose holder from list or enter new one:'), (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.holderctrl, (2,1), (1,1))

		sizer.Add(wx.StaticText(self, -1,
									'Then press the "Next" button to continue.'), (3, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def suggestName(self):
		name = leginon.session.suggestName()
		self.nametextctrl.SetValue(name)

	def onValidateName(self, evt):
		name = evt.GetString()
		safename = name.replace(' ','_')
		if safename != name:
			self.nameAutoChangeDialog()
		try:
			leginon.session.makeReservation(safename)
		except leginon.session.ReservationFailed:
			self.nameExistsDialog()

	def nameAutoChangeDialog(self):
		dlg = wx.MessageDialog(self,
											'"_" has replaced " " in the name\nfor easier file managemnet',
											'Changed Session Name', wx.OK|wx.ICON_WARNING)
		dlg.ShowModal()
		dlg.Destroy()


	def nameExistsDialog(self):
		dlg = wx.MessageDialog(self,
											'A session with this name already exists.',
											'Invalid Session Name', wx.OK|wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()

	def GetPrev(self):
		parent = self.GetParent()
		if parent.projectpage:
			return parent.projectpage
		else:
			if parent.userpage.sessions:
				return parent.sessiontypepage
			return parent.userpage

	def GetNext(self):
		parent = self.GetParent()
		return parent.descriptionpage

class SessionDescriptionPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer(5,5)

		sizer.Add(wx.StaticText(self, -1,
				'Please enter an optional description.'),
												(0, 0), (1, 2))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Description:'), (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.descriptiontextctrl = wx.TextCtrl(self, -1, '', size=wx.Size(-1,50), style=wx.TE_MULTILINE)
		sizer.Add(self.descriptiontextctrl, (4, 0), (1, 2), wx.EXPAND|wx.ALL)


		sizer.Add(wx.StaticText(self, -1,
									'Then press the "Next" button to continue.'), (6, 0), (1, 2))

		pagesizer.Add(sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		pagesizer.AddGrowableRow(0)
		pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(pagesizer)

	def GridDescriptionDialog(self):
		'''
		Called before discription is shown if gridhook is present to set
		Description control with.
		'''
		parent = self.GetParent()
		grid_url = parent.gridhook.getWebLinkUrl()
		dlg = ImportGridTextDialog(self, grid_url)
		grid_description = ''
		if dlg.ShowModal() == wx.ID_OK:
			grid_description = parent.gridhook.getGridDisplay()
		dlg.Destroy()
		self.descriptiontextctrl.SetValue(grid_description)

	def GetPrev(self):
		#reset
		parent = self.GetParent()
		return parent.namepage

	def GetNext(self):
		parent = self.GetParent()
		if parent.gridhook_failed == True:
			# could not save session in grid management because of project not found.
			# Blocks moving forward.
			return parent.descriptionpage
		return parent.imagedirectorypage

class NoProjectDatabaseError(Exception):
	pass

class SessionProjectPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		self.pagesizer = wx.GridBagSizer()
		self.sizer = wx.GridBagSizer(5,5)

		self.sizer.Add(wx.StaticText(self, -1,
				'Select the project this session will be associated with,'),
												(0, 0), (1, 2))

		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)

		self.sizer.Add(wx.StaticText(self, -1, 'Project:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		if parent.setup.projectdata is None:
			raise NoProjectDatabaseError
		self.projects = parent.setup.getProjects()
		choices = self.projects.keys()
		choices.sort()
		self.projectchoice = wx.Choice(self, -1, choices=choices)
		# select default project
		default = 0
		if leginon.leginonconfig.default_project is not None:
			try:
				default = choices.index(leginon.leginonconfig.default_project)
			except:
				pass
		self.projectchoice.SetSelection(default)
		self.sizer.Add(self.projectchoice, (1, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)

		self.sizer.Add(wx.StaticText(self, -1,
									'then press the "Next" button to continue.'), (3, 0), (1, 2))

		self.pagesizer.Add(self.sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(self.pagesizer)

	def noProjectDialog(self):
		dlg = wx.MessageDialog(self,
											'Please Set up a Project First',
											'User does not own any project for data collection.',
											 wx.OK|wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()

	def setProjectNames(self, names):
		if not names:
			self.noProjectDialog()

		selection = self.projectchoice.GetStringSelection()
		self.projectchoice.Clear()
		self.projectchoice.AppendItems(names)
		size = self.projectchoice.GetBestSize()
		self.sizer.SetItemMinSize(self.projectchoice, size.width, size.height)
		self.pagesizer.Layout()
		if self.projectchoice.FindString(selection) is not wx.NOT_FOUND:
			self.projectchoice.SetStringSelection(selection)
		else:
			self.projectchoice.SetSelection(0)
			## catching exception generated by wxPython 2.6.3.2
			try:
				selection = self.projectchoice.GetString(0)
			except:
				selection = ""

	def getSelectedProjectId(self):
		project = self.projectchoice.GetStringSelection()
		return self.projects[project].dbid

	def getSelectedProjectName(self):
		project = self.projectchoice.GetStringSelection()
		return project

	def GetPrev(self):
		parent = self.GetParent()
		if parent.userpage.sessions:
			return parent.sessiontypepage
		else:
			return parent.userpage

	def GetNext(self):
		return self.GetParent().namepage

# might want to check if directory exists and warn...
class SessionImageDirectoryPage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		pagesizer = wx.GridBagSizer()
		sizer = wx.GridBagSizer(5, 5)

		sizer.Add(wx.StaticText(self, -1,
				'Select the directory where images from this session will be stored.\n(A subdirectory named after the session will be created for you)'),
												(0, 0), (1, 3))

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(1)

		sizer.Add(wx.StaticText(self, -1, 'Image Directory:'), (1, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		try:
			defaultdirectory = leginon.leginonconfig.mapPath(leginon.leginonconfig.IMAGE_PATH)
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
		return parent.descriptionpage

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
					'Please press the "Next" button if these settings are correct.'),
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

	def GetNext(self):
		parent = self.GetParent()
		return parent.c2sizepage

class C2SizePage(WizardPage):
	def __init__(self, parent):
		WizardPage.__init__(self, parent)
		self.pagesizer = wx.GridBagSizer()
		self.sizer = wx.GridBagSizer()

		self.sizer.Add(wx.StaticText(self, -1,
									'''Enter illumination limiting aperture size
(likely C2) you will use at high magnification imaging
if you would like to see its imprint when targeting'''
									),
									(0, 0), (1, 1))
		
		c2sizer = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'C2 size: ')
		c2sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_LEFT)
		self.c2sizectrl = IntEntry(self, -1, chars=6, value='100')
		c2sizer.Add(self.c2sizectrl, (0, 1), (1, 1), wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'um')
		c2sizer.Add(label, (0, 2), (1, 1), wx.ALIGN_LEFT)

		self.sizer.Add(c2sizer, (2, 0), (1, 1), wx.EXPAND|wx.ALL,10)

		self.sizer.AddGrowableCol(0)

		self.pagesizer.Add(self.sizer, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.SetSizerAndFit(self.pagesizer)
	
	def GetPrev(self):
		return self.GetParent().sessioncreatepage

class SetupWizard(wx.wizard.Wizard):
	def __init__(self, manager):
		self.manager = manager
		parent = manager.frame
		self.setup = Setup(manager.research, manager.publish)
		self.publish = manager.publish
		self.session = None
		self.gridhook = None
		self.gridhook_failed = False
		self.clients = []
		image = wx.Image(leginon.icons.getPath('setup.png'))
		bitmap = wx.BitmapFromImage(image)
		wx.wizard.Wizard.__init__(self, parent, -1, 'Leginon Setup', bitmap=bitmap)
		self.SetName('wLeginonSetup')

		# create pages
		self.userpage = UserPage(self)
		self.sessiontypepage = SessionTypePage(self)
		try:
			self.projectpage = SessionProjectPage(self)
		except NoProjectDatabaseError:
			self.projectpage.noProjectDialog()
		self.namepage = SessionNamePage(self)
		self.descriptionpage = SessionDescriptionPage(self)
		self.imagedirectorypage = SessionImageDirectoryPage(self)
		self.sessionselectpage = SessionSelectPage(self)
		self.sessioncreatepage = SessionCreatePage(self)
		self.c2sizepage = C2SizePage(self)

		# initialize page values
		users = self.getUsers()
		self.userpage.setUsers(users)

		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGING, self.onPageChanging, self)
		self.Bind(wx.wizard.EVT_WIZARD_PAGE_CHANGED, self.onPageChanged, self)
		self.Bind(wx.wizard.EVT_WIZARD_FINISHED, self.onFinished)
		self.Bind(wx.wizard.EVT_WIZARD_CANCEL, self.onCancel)

		self.FitToPage(self.userpage)

	def noProjectDialog(self, exception):
		dlg = wx.MessageDialog(self,
											'User does not own any project for data collection.',
											'Set up project in myamiweb', wx.OK|wx.ICON_ERROR)
		dlg.ShowModal()
		dlg.Destroy()

	def run(self):
		self.Raise()
		if self.userpage.skip:
			result = self.RunWizard(self.userpage.GetNext())
		else:
			result = self.RunWizard(self.userpage)
		if result and self.session is not None:
			return True
		return False

	def onFinished(self, evt):
		if self.session is not None:
			initializer = self.getSettings()
			self.setup.saveSettings(self.session, initializer)

	def onCancel(self, evt):
		leginon.session.cancelReservation()

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
			safename = name.replace(' ','_')
			if safename != name:
				self.namepage.nameAutoChangeDialog()
				self.namepage.nametextctrl.SetValue(safename)
			try:
				leginon.session.makeReservation(safename)
			except leginon.session.ReservationFailed:
				evt.Veto()
				self.namepage.nameExistsDialog()
			if not leginon.session.hasGridHook():
				self.gridhook_failed = False
				self.gridhook = None
			else:
				# hook to grid management system
				session_dict = {'name':safename}
				project_dict = {'name':self.projectpage.getSelectedProjectName()}
				self.gridhook = leginon.session.createGridHook(session_dict,project_dict)
				try:
					if not self.gridhook.gridhook_server_active:
						raise RuntimeError('Grid Management System is not up')
					self.gridhook.setSession()
					self.gridhook_failed = False
					self.descriptionpage.GridDescriptionDialog()
				except ValueError as e:
					# invalid project name. leginon_session not set in grid management
					# system even though it is connected.  Need to block session saving.
					self.gridhook_failed = True
					self.descriptionpage.descriptiontextctrl.SetValue(str(e))
				except Exception as e:
					# inform but not fatal
					self.gridhook_failed = False
					self.descriptionpage.descriptiontextctrl.SetValue(str(e))
		elif page is self.descriptionpage:
			pass
		elif page is self.sessionselectpage:
			self.session = self.sessionselectpage.getSelectedSession()
			self.clients = self.sessionselectpage.clients
			self.history = self.sessionselectpage.history
			self.setup.saveClients(self.session, self.clients)
		elif page is self.sessioncreatepage:
			user = self.userpage.getSelectedUser()
			name = self.namepage.nametextctrl.GetValue()
			description = self.descriptionpage.descriptiontextctrl.GetValue()
			description = description.strip()
			holder = self.namepage.holderctrl.GetValue()
			holderdata = leginon.leginondata.GridHolderData(name=holder,hidden=False)
			directory = self.imagedirectorypage.directorytextctrl.GetValue()
			self.session = self.setup.createSession(user, name, description,
																							directory)
			self.session['holder'] = holderdata
			# FIX ME: Issue #5450 workaround:
			# Not to generate passcode until remote is working.
			# insertion of this makes any other session creation unique
			#self.session['remote passcode'] = self.generatePassCode()

			#Issue #4634 use insert method so that self.session becomes sinedon
			#query result after this first insert.
			self.session.insert()
			#Reservation can be canceled since self.session is inserted
			leginon.session.cancelReservation()
			projectid = self.projectpage.getSelectedProjectId()
			project_experiment = self.setup.linkSessionProject(self.session['name'], projectid)
			self.publish(project_experiment, database=True)
			if self.gridhook and not self.gridhook_failed:
				try:
					# update grid management LeginonSession leginon_id
					self.gridhook.setSession(self.session.dbid)
				except RuntimeError as e:
					# not connected. OK. to let go. 
					pass
			self.clients = self.sessioncreatepage.clients
			self.history = self.sessioncreatepage.history
			self.setup.saveClients(self.session, self.clients)
		elif page is self.c2sizepage:
			if self.session:
				c2size = self.c2sizepage.c2sizectrl.GetValue()
				self.setup.setC2Size(self.session, self.clients,c2size)

	def generatePassCode(self):
		length = 8
		import binascii
		return binascii.hexlify(os.urandom(64))[:length]

	def onPageChanged(self, evt):
		page = evt.GetPage()
		if page is self.sessioncreatepage:
			name = self.namepage.nametextctrl.GetValue()
			description = self.descriptionpage.descriptiontextctrl.GetValue()
			project = self.projectpage.projectchoice.GetStringSelection()
			directory = self.imagedirectorypage.directorytextctrl.GetValue()
			self.sessioncreatepage.nametext.SetLabel(name)
			self.sessioncreatepage.descriptiontext.SetLabel(description)
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
		elif page is self.namepage:
			if not self.userpage.projects:
				self.projectpage.noProjectDialog()
				self.cancelSetup()

	def cancelSetup(self):
		self.onCancel(None)
		self.Close()

	def setSettings(self, sd):
		if sd['session type']:
			s = sd['session type']
			n = self.sessiontypepage.sessiontyperadiobox.FindString(s)
			if n != wx.NOT_FOUND:
				self.sessiontypepage.sessiontyperadiobox.SetSelection(n)
		self.sessionselectpage.limitcheckbox.SetValue(sd['limit'])
		self.sessionselectpage.limitintctrl.SetValue(sd['n limit'])
		if sd['c2 size']:
			self.c2sizepage.c2sizectrl.SetValue(sd['c2 size'])
		else:
			self.c2sizepage.c2sizectrl.SetValue(100)
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
			'c2 size':
				self.c2sizepage.c2sizectrl.GetValue(),
		}
		return initializer

def _indexBy(bys, datalist):
	index = {}
	bydone = []
	if isinstance(bys, str):
		bys = (bys,)
	for indexdata in datalist:
		keylist = []
		for by in bys:
			key = indexdata[by]
			if isinstance(key,str):
				keylist.append(key)
		if keylist:
			if len(keylist) == 1:
				finalkey = keylist[0]
			else:
				finalkey = ' '.join(keylist)
			finalkey = finalkey.strip()
			index[finalkey] = indexdata
	return index

class Setup(object):
	def __init__(self, research, publish):
		self.research = research
		self.publish = publish
		try:
			self.projectdata = leginon.project.ProjectData()
		except:
			self.projectdata = None

	def isLeginonUser(self, userdata):
		return not userdata['noleginon']

	def getUsers(self):
		userdata = leginon.leginondata.UserData()
		userdatalist = userdata.query()
		userdatalist = filter(self.isLeginonUser, userdatalist)	
		if not userdatalist:
			raise RuntimeError('No users in the database.')
		return _indexBy(('firstname','lastname'), userdatalist)

	def getPresets(self,sessiondata):
		presetq = leginon.leginondata.PresetData(session=sessiondata)
		presetdatalist = presetq.query()
		return presetdatalist

	def getSettings(self, userdata):
		settingsclass = leginon.leginondata.SetupWizardSettingsData
		defaultsettings = {
			'session type': 'Create a new session',
			'selected session': None,
			'limit': True,
			'n limit': 10,
			'connect': True,
			'c2 size': 100,
		}
		qsession = leginon.leginondata.SessionData(initializer={'user': userdata})
		qdata = settingsclass(initializer={'session': qsession})
		try:
			settings = self.research(qdata, results=1)[0]
		except IndexError:
			settings = settingsclass(initializer=defaultsettings)
		return settings

	def getClients(self, name):
		sessiondata = leginon.leginondata.SessionData(initializer={'name': name})
		querydata = leginon.leginondata.ConnectToClientsData(session=sessiondata)
		try:
			return self.research(querydata, results=1)[0]['clients']
		except IndexError:
			return []

	def getRecentClients(self):
		try:
			results = self.research(leginon.leginondata.ConnectToClientsData(), results=500)
		except IndexError:
			results = []
		
		try:
			q = leginon.leginondata.InstrumentData()
			# Hide instruments from client list
			if 'hidden' in q.keys():
				q['hidden']=False
				instruments = q.query()
				if len(instruments) == 0:
					# hidden field is not made, fake an insert Issue #4176
					# This updates the database with hidden field inserted and default to False
					q = leginon.leginondata.InstrumentData(hostname='fake',name='fake',hidden=True).insert()
					q2 = leginon.leginondata.InstrumentData(hidden=False)
					instruments = q2.query()
			hosts = map((lambda x: x['hostname']),instruments)
			hosts = set(hosts)
		except IndexError:
			hosts = []
		except:
			raise
		clients = {}
		for result in results:
			for client in result['clients']:
				# hide mis-spelled client hosts that does not have an instrument
				if str(client) not in hosts:
					continue
				clients[str(client)] = None
		clients = clients.keys()
		clients.sort()
		return clients

	def saveClients(self, session, clients):
		ver = leginon.version.getVersion()
		loc = leginon.version.getInstalledLocation()
		host = mysocket.gethostname()
		initializer = {'session': session, 'clients': clients, 'localhost':host, 'version': ver, 'installation': loc}
		clientsdata = leginon.leginondata.ConnectToClientsData(initializer=initializer)
		self.publish(clientsdata, database=True, dbforce=True)

	def saveSettings(self, sessiondata, initializer):
		settingsclass = leginon.leginondata.SetupWizardSettingsData
		sd = settingsclass(initializer=initializer)
		sd['session'] = sessiondata
		self.publish(sd, database=True, dbforce=True)

	def getSessions(self, userdata, n=None):
		names, sessiondatalist = leginon.session.getSessions(userdata, n)
		return names, _indexBy('name', sessiondatalist)

	def getProjects(self, userdata=None):
		if self.projectdata is None:
			return {}
		projectdatalist = self.projectdata.getProjects(userdata)
		return _indexBy('name', projectdatalist)

	def createSession(self, user, name, description, directory):
		# get unpublished new SessionData instance
		return leginon.session.createSession(user, name, description, directory, holder=None, hidden=False)

	def linkSessionProject(self, sessionname, projectid):
		if self.projectdata is None:
			raise RuntimeError('Cannot link session, not connected to database.')
		projq = leginon.projectdata.projects()
		projdata = projq.direct_query(projectid)
		projeq = leginon.projectdata.projectexperiments()
		sessionq = leginon.leginondata.SessionData(name=sessionname)
		sdata = sessionq.query()
		projeq['session'] = sdata[0]
		projeq['project'] = projdata
		return projeq

	def getTEM(self,hostname, no_sim=True):
			temdata = None
			r = leginon.leginondata.InstrumentData(hostname=hostname).query()
			if r:
				for idata in r:
					if no_sim and 'Sim' in idata['name']:
						continue
					if idata['cs']:
						temdata = idata
						break
			return temdata

	def setC2Size(self,session,clients,c2size):
		temdata = None
		# set it to the first tem found in the hosts list
		for host in clients:
			# avoid simulated tem on clients
			temdata = self.getTEM(host,True)
			if temdata:
				break
		if not temdata:
			localhost = mysocket.gethostname()
			# use tem on localhost, including simulation
			temdata = self.getTEM(localhost,False)
		if temdata and c2size:
			c2data = leginon.leginondata.C2ApertureSizeData(session=session,tem=temdata,size=c2size)
			self.publish(c2data, database=True, dbforce=True)

class EditClientsDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, clients, history):
		self.clients = clients
		self.history = history
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, 'Edit Clients')

	def onInitialize(self):
		self.listbox = leginon.gui.wx.ListBox.EditListBox(self, -1, 'Clients', choices=self.history)
		self.listbox.setValues(self.clients)
		self.sz.Add(self.listbox, (0, 0), (1, 1), wx.EXPAND)
		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)
		self.addButton('OK', id=wx.ID_OK)
		self.addButton('Cancel', id=wx.ID_CANCEL)

class ImportGridTextDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, url):
		self.parent = parent
		self.url = url
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, 'Import Grid Description')
	def onInitialize(self):
		label1 = wx.StaticText(self, -1, 'Go to')
		self.linksz = hl.HyperLinkCtrl(self, -1, self.url, pos=(100,100),URL=self.url)
		label2 = wx.StaticText(self, -1, 'to link the session to a grid')
		self.sz.Add(label1, (0,0),(1,1))
		self.sz.Add(self.linksz, (0,1),(1,1))
		self.sz.Add(label2, (0,2),(1,1))
		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)
		self.addButton('OK', id=wx.ID_OK)
		self.addButton('Cancel', id=wx.ID_CANCEL)

if __name__ == '__main__':
	class TestApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Test')
			self.SetTopWindow(frame)
			import node
			n = node.Node('Dummy', None)
			wizard = SetupWizard(frame, n.research, None)
			frame.Show(True)
			return True

	app = TestApp(0)
	app.MainLoop()

