import data
import leginonconfig
import os
import project
import socket
import time
import uidata
import node
import launcher

class ManagerSetup(object):
	def __init__(self, manager):
		self.manager = manager
		self.initUsers()
		self.createLoginContainer()
		if (hasattr(leginonconfig, 'USERNAME') and
				leginonconfig.USERNAME in self.users):
			self.setUser(leginonconfig.USERNAME)
			session = data.SessionData(user=self.uiGetUser())
			self.manager.session = session
			self.manager.uicontainer.session = session
			self.createSelectSessionContainer()
		else:
			self.addLoginContainer()

	def onStartSession(self):
		session_name = self.sessionselector.getSelectedValue()
		session = self.session_dict[session_name]
		self.manager.session = session
		self.manager.uicontainer.session = session

		if (session['instrument'] is not None and session['instrument']['hostname']
				not in self.manager.launcherdict.keys() and
				self.connectinstrument.get()):
			try:
				hostname = session['instrument']['hostname']
				if hostname:
					location = {}
					location['TCP transport'] = {}
					location['TCP transport']['hostname'] = hostname
					location['TCP transport']['port'] = 55555
					self.manager.addNode(location, (hostname,))
			except (IOError, TypeError, socket.error):
				self.manager.messagelog.warning('Cannot add instrument\'s launcher.')
		self.selectsessioncontainer.delete()

		self.manager.defineUserInterface()
		launcher.Launcher((socket.gethostname().lower(),), session=session,
              					    nodelocations={'manager': self.manager.location()})


	def uiCreateSession(self):
		self.createmethod.disable()
		self.cancelcreatemethod.disable()
		## publish a new session
		sessiondata = self.buildSessionData()
		# check if session already exists
		session_name = sessiondata['name']
		if session_name in self.session_dict:
			self.createmessages.error('session name already used')
			self.createmethod.enable()
			self.cancelcreatemethod.enable()
			return
		self.manager.publish(sessiondata, database=True)
		if self.projectdataconnected:
			projectname = self.projectselection.getSelectedValue()
			self.linkSessionProject(sessiondata, projectname)
		# refresh session list
		self.uiUpdateSessionList()
		self.createsessioncontainer.delete()
		self.createsessionmethod.enable()

	def onCancelCreateSession(self):
		self.createsessioncontainer.delete()
		self.createsessionmethod.enable()

	def linkSessionProject(self, sessiondata, projectname):
		try:
			projectid = self.projectmap[projectname]['projectId']
		except KeyError:
			return
		projectsession = project.ProjectExperiment(projectid, sessiondata['name'])
		experiments = self.projectdata.getProjectExperiments()
		experiments.insert([projectsession.dumpdict()])

	def buildSessionData(self):
		initializer = {
		  'name': self.createsessionname.get(),
		  'comment': self.createsessioncomment.get(),
		  'user': self.uiGetUser(),
		  'instrument': self.uiGetInstrument(),
		}
		imagepath = os.path.join(leginonconfig.IMAGE_PATH, initializer['name'])
		imagepath = imagepath.replace('\\', '/')
		initializer['image path'] = imagepath
		return data.SessionData(initializer=initializer)

	def initInstruments(self):
		instruments = self.getInstruments()
		self.instruments = self.indexByName(instruments)
		initializer = {'name': 'None',
										'description': 'No Instrument'}
		self.instruments['None'] = data.InstrumentData(initializer=initializer)

	def uiUpdateInstrument(self):
		instrumentnames = self.instruments.keys()
		instrumentnames.sort()
		try:
			index = instrumentnames.index('None')
		except ValueError:
			index = 0
		self.instrumentselection.set(instrumentnames, index)

	def uiGetInstrument(self):
		instrumentname = self.instrumentselection.getSelectedValue()
		if instrumentname in self.instruments:
			return self.instruments[instrumentname]
		else:
			return None

	def getInstruments(self):
		instrumentinitializer = {}
		instrumentinstance = data.InstrumentData(initializer=instrumentinitializer)
		instrumentdatalist = self.manager.research(datainstance=instrumentinstance)
		return instrumentdatalist

	def initUsers(self):
		self.initAdmin()
		users = self.getUsers()
		self.users = self.indexByName(users)

	def initProjectConnection(self):
		self.projectdata = project.ProjectData()
		self.projectdataconnected = self.projectdata.isConnected()

	def initProjects(self):
		if not self.projectdataconnected:
			return
		self.projects = self.projectdata.getProjects()
		projects = self.projects.getall()
		self.projectmap = {}
		for p in projects:
			self.projectmap[p['name']] = p

	def uiUpdateProjects(self):
		projectnames = self.projectmap.keys()
		projectnames.sort()
		self.projectselection.set(projectnames, 0)

	def uiUpdateUsers(self):
		usernames = self.users.keys()
		usernames.sort()
		self.userselection.set(usernames, 0)

	def uiGetUser(self):
		username = self.userselection.getSelectedValue()
		if username in self.users:
			return self.users[username]
		else:
			return None

	def indexByName(self, datalist):
		### assuming datalist is ordered by timestamp (default from
		### a research), this gets the latest instance by each name
		index = {}
		namesdone = []
		for indexdata in datalist:
			try:
				name = indexdata['name']
				if name not in namesdone:
					index[name] = indexdata
					namesdone.append(name)
			except (TypeError, IndexError):
				pass
		return index

	def getUsers(self):
		self.initAdmin()
		groupinstance = data.GroupData()
		userinitializer = {'group': groupinstance}
		userinstance = data.UserData(initializer=userinitializer)
		userdatalist = self.manager.research(datainstance=userinstance)
		return userdatalist

	def initAdmin(self):
		adminuser = self.getAdminUser()
		if adminuser is None:
			admingroup = self.getAdminGroup()
			if admingroup is None:
				admingroup = self.addAdminGroup()
			adminuser = self.addAdminUser(admingroup)

	def getAdminGroup(self):
		groupinitializer = {'name': 'administrators'}
		groupinstance = data.GroupData(initializer=groupinitializer)
		groupdatalist = self.manager.research(datainstance=groupinstance)
		try:
			return groupdatalist[0]
		except (TypeError, IndexError):
			return None

	def addAdminGroup(self):
		groupinitializer = {'name': 'administrators',
												'description': 'Administrators'}
		groupinstance = data.GroupData(initializer=groupinitializer)
		self.manager.publish(groupinstance, database=True)
		return groupinstance

	def getAdminUser(self):
		userinitializer = {'name': 'administrator', 'group': data.GroupData()}
		userinstance = data.UserData(initializer=userinitializer)
		userdatalist = self.manager.research(datainstance=userinstance)
		try:
			return userdatalist[0]
		except (TypeError, IndexError):
			return None

	def addAdminUser(self, group):
		userinitializer = {'name': 'administrator',
												'full name': 'Administrator',
												'group': group}
		userinstance = data.UserData(initializer=userinitializer)
		self.manager.publish(userinstance, database=True)
		return userinstance

	def onProjectSelect(self, index):
		if not hasattr(self, 'projectselection'):
			return index
		'''
		projectname = self.projectselection.getSelectedValue(index)
		try:
			# show description
			print self.projectmap[projectname]
		except KeyError:
			pass
		'''
		return index

	def setUser(self, username):
		if username in self.users:
			self.userdata = self.users[username]
			try:
				self.userfullname.set(self.userdata['full name'])
			except KeyError:
				self.userfullname.set('')
			try:
				self.usergroup.set(self.userdata['group']['name'])
			except KeyError:
				self.usergroup.set('')
		else:
			self.userfullname.set('')
			self.usergroup.set('')

	def uiUserSelectCallback(self, index):
		if not hasattr(self, 'userselection'):
			return index
		username = self.userselection.getSelectedValue(index)
		self.setUser(username)
		return index

	def onInstrumentSelect(self, index):
		instrumentname = self.instrumentselection.getSelectedValue(index)
		if instrumentname in self.instruments:
			instrumentdata = self.instruments[instrumentname]
			try:
				self.createinstrumentdescription.set(instrumentdata['description'],
																							thread=True)
			except (TypeError, KeyError):
				self.createinstrumentdescription.set('', thread=True)
			try:
				self.createinstrumenthostname.set(instrumentdata['hostname'],
																					thread=True)
			except (TypeError, KeyError):
				self.instrumenthostname.set('', thread=True)
		else:
			self.createinstrumentdescription.set('', thread=True)
			self.createinstrumenthostname.set('', thread=True)
		return index

	def suggestSessionName(self):
		session_name = 'enter unique name here'
		for suffix in 'abcdefghijklmnopqrstuvwxyz':
			maybe_name = time.strftime('%y%b%d'+suffix).lower()
			qsession = data.SessionData(name=maybe_name)
			maybe_session = self.manager.research(datainstance=qsession)
			if maybe_session:
				continue
			else:
				session_name = maybe_name
				break
		return session_name

	def onSuggestName(self):
		session_name = self.suggestSessionName()
		self.createsessionname.set(session_name)

	def onSessionSelect(self, index):
		try:
			session_name = self.sessionselector.getSelectedValue(index)
		except AttributeError:
			return index
		sessiondata = self.session_dict[session_name]
		self.uiShowSessionInfo(sessiondata)
		return index

	def uiShowSessionInfo(self, sessiondata):
		comment = sessiondata['comment']
		self.selectsessioncomment.set(comment)

		user = sessiondata['user']['name']

		inst = sessiondata['instrument']['name']
		self.selectsessioninstrument.set(inst)

		path = leginonconfig.mapPath(sessiondata['image path'])
		self.selectsessionpath.set(path)

	def getSessionDataName(self, sessiondata):
		return sessiondata['name']

	def uiUpdateSessionList(self):
		self.session_limit = 30
		sessionlist = self.researchSessions(self.session_limit)
		session_names = map(self.getSessionDataName, sessionlist)
		self.session_dict = dict(zip(session_names, sessionlist))
		# XXX This will get into some kind of big loop if session_limit is too high
		self.sessionselector.set(session_names, 0)

	def researchSessions(self, limit):
		qsession = data.SessionData(user=self.userdata)
		sessionlist = self.manager.research(datainstance=qsession, results=limit)
		return sessionlist

	def onCreateSession(self):
		self.createsessionmethod.disable()
		self.initProjectConnection()
		self.initProjects()
		self.initInstruments()
		self.createCreateSessionContainer()
		self.createmethod.enable()
		self.cancelcreatemethod.enable()

	def onLogin(self):
		self.logincontainer.delete()
		session = data.SessionData(user=self.uiGetUser())
		self.manager.session = session
		self.manager.uicontainer.session = session
		self.createSelectSessionContainer()

	def createLoginContainer(self):
		self.logincontainer = uidata.ExternalContainer('Leginon II Login')
		userselectcontainer = uidata.Container('Select User')
		self.userselection = uidata.SingleSelectFromList('Name', [], 0,
																						callback=self.uiUserSelectCallback)
		self.userfullname = uidata.String('Full Name', '', 'r')
		self.usergroup = uidata.String('Group Name', '', 'r')
		userselectcontainer.addObjects((self.userselection, self.userfullname,
																		self.usergroup))
		self.loginmethod = uidata.Method('Login', self.onLogin)
		self.logincontainer.addObjects((userselectcontainer,))
		self.logincontainer.addObject(self.loginmethod,
																	position={'justify': ['center']})
		self.uiUpdateUsers()

	def addLoginContainer(self):
		self.manager.uicontainer.addObject(self.logincontainer)

	def createSelectSessionContainer(self):
		self.sessionselector = uidata.SingleSelectFromList('Session', [], 0, 'rw',
													tooltip='Leginon II session to be used when starting')
		self.selectsessioncomment = uidata.String('Comment', '', 'r')
		self.selectsessioninstrument = uidata.String('Instrument', '', 'r')
		self.selectsessionpath = uidata.String('Image Path', '', 'r')

		self.sessionselector.setCallback(self.onSessionSelect)

		self.connectinstrument = uidata.Boolean('Connect to instrument launcher',
																							True, 'rw', persist=True,
				tooltip='When the session is started, connect to the launcher on the '
									+ 'machine where the instrument is located')
		self.startsessionmethod = uidata.Method('Begin Session',
																						self.onStartSession,
				tooltip='Begin the selected Leginon II session with the given settings')
		self.createsessionmethod = uidata.Method('Create Session',
																							self.onCreateSession,
												tooltip='Configure and create a new Leginon II session')

		selectsessioncontainer = uidata.Container('Select Session')
		selectsessioncontainer.addObjects((self.sessionselector,
																					  self.selectsessioncomment,
																					  self.selectsessioninstrument,
																					  self.selectsessionpath))
		selectsessioncontainer.addObject(self.connectinstrument,
																			position={'justify': ['center']})
		title = 'Leginon II Session'
		fullname = self.userfullname.get()
		if fullname:
			title += ' for %s' % fullname
		self.selectsessioncontainer = uidata.ExternalContainer(title)
		self.selectsessioncontainer.addObjects((selectsessioncontainer,
																						self.startsessionmethod,
                                            self.createsessionmethod))
		self.selectsessioncontainer.positionObject(selectsessioncontainer,
																							{'position': (0, 0),
																								'span': (1, 2),
																								'justify': ['center']})
		self.selectsessioncontainer.positionObject(self.startsessionmethod,
																							{'position': (1, 0),
																								'justify': ['top', 'bottom']})
		self.selectsessioncontainer.positionObject(self.createsessionmethod,
																				{'position': (1, 1),
																				'justify': ['top', 'bottom', 'right']})
		self.uiUpdateSessionList()
		self.manager.uicontainer.addObject(self.selectsessioncontainer)

	def createCreateSessionContainer(self):
#		suggestnamemethod = uidata.Method('Suggest A Name', self.onSuggestName)
		self.createsessionname = uidata.String('Session Name', '', 'rw',
																						persist=False)
		self.onSuggestName()
		self.createsessioncomment = uidata.String('Session Comment', '', 'rw',
																							persist=False)
		if self.projectdataconnected:
			projectcontainer = uidata.Container('Project')
			self.projectselection = uidata.SingleSelectFromList('Project', [], 0,
																													persist=True)
			self.projectselection.setCallback(self.onProjectSelect)
			self.uiUpdateProjects()
			projectcontainer.addObject(self.projectselection)

		createinstrumentcontainer = uidata.Container('Instrument')
		self.instrumentselection = uidata.SingleSelectFromList('Name', [], 0,
																														persist=True)
		self.instrumentselection.setCallback(self.onInstrumentSelect)
		self.createinstrumentdescription = uidata.String('Description', '', 'r')
		self.createinstrumenthostname = uidata.String('Hostname', '', 'r')
		self.uiUpdateInstrument()

		createinstrumentcontainer.addObjects((self.instrumentselection,
																		self.createinstrumentdescription,
																		self.createinstrumenthostname))

		self.createmethod = uidata.Method('Create Session', self.uiCreateSession)
		self.cancelcreatemethod = uidata.Method('Cancel',
																						self.onCancelCreateSession)
		self.createmessages = uidata.MessageLog('Messages')

		self.createsessioncontainer = uidata.ExternalContainer(
																										'Create Leginon II Session')

		self.createsessioncontainer.addObject(self.createmessages,
																					position={'span': (1,2)})
		self.createsessioncontainer.addObject(self.createsessionname,
																					position={'span': (1,2)})
		self.createsessioncontainer.addObject(self.createsessioncomment,
																					position={'span': (1,2)})
		self.createsessioncontainer.addObject(createinstrumentcontainer,
																					position={'span': (1,2)})
		if self.projectdataconnected:
			self.createsessioncontainer.addObject(projectcontainer,
																						position={'span': (1,2)})
		self.createsessioncontainer.addObject(self.createmethod)
		position = self.createmethod.getPosition()['position']
		self.createsessioncontainer.addObject(self.cancelcreatemethod,
													position={'position': (position[0], position[1] + 1),
																		'justify': ['right']})

		self.selectsessioncontainer.addObject(self.createsessioncontainer)

