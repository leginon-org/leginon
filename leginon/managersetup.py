import data
import leginonconfig
import os
import project
import socket
import time
import uidata

class ManagerSetup(object):
	def __init__(self, manager):
		self.manager = manager

		self.defineUserInterface()

		self.initProjects()
		self.initUsers()
		self.initInstruments()

	def start(self):
		session = self.uiGetSessionData()
		self.manager.session = session
		self.manager.publish(session, database=True)

		projectname = self.projectselection.getSelectedValue()
		try:
			projectid = self.projectmap[projectname]['projectId']
		except KeyError:
			pass
		else:
			projectsession = project.ProjectExperiment(projectid, session['name'])
			experiments = self.projectdata.getProjectExperiments()
			experiments.insert([projectsession.dumpdict()])

		if session['instrument'] is not None and \
			session['instrument']['hostname'] not in self.manager.launcherdict.keys() and not self.skipinstrument.get():
			try:
				hostname = session['instrument']['hostname']
				if hostname:
					location = {}
					location['TCP transport'] = {}
					location['TCP transport']['hostname'] = hostname
					location['TCP transport']['port'] = 55555
					self.manager.addNode(location)
			except (IOError, TypeError, socket.error), e:
				if isinstance(e, socket.error):
					self.manager.outputWarning('Cannot add instrument\'s launcher.')
		if self.container.parent is not None:
			self.container.parent.deleteObject(self.container.name)

		self.manager.defineUserInterface()
		self.manager.messagelog.information('Manager initialized')

	def uiGetSessionData(self):
		initializer = {'name': self.session_name.get(),
										'comment': self.session_comment.get(),
										'user': self.uiGetUser(),
										'instrument': self.uiGetInstrument(),
										'image path': self.image_path.get()}
		return data.SessionData(initializer=initializer)

	def initInstruments(self):
		instruments = self.getInstruments()
		self.instruments = self.indexByName(instruments)
		initializer = {'name': 'None',
										'description': 'No Instrument'}
		self.instruments['None'] = data.InstrumentData(initializer=initializer)
		self.uiUpdateInstrument()

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
		self.uiUpdateUsers()

	def initProjects(self):
		self.projectdata = project.ProjectData()
		self.projects = self.projectdata.getProjects()
		projects = self.projects.getall()
		self.projectmap = {}
		for p in projects:
			self.projectmap[p['name']] = p
		self.uiUpdateProjects()

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

	def uiProjectSelectCallback(self, index):
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

	def uiUserSelectCallback(self, index):
		if not hasattr(self, 'userselection'):
			return index
		username = self.userselection.getSelectedValue(index)
		if username in self.users:
			userdata = self.users[username]
			try:
				self.userfullname.set(userdata['full name'])
			except KeyError:
				self.userfullname.set('')
			try:
				self.usergroup.set(userdata['group']['name'])
			except KeyError:
				self.usergroup.set('')
		else:
			self.userfullname.set('')
			self.usergroup.set('')
		return index

	def uiInstrumentSelectCallback(self, index):
		if not hasattr(self, 'instrumentselection'):
			return index
		instrumentname = self.instrumentselection.getSelectedValue(index)
		if instrumentname in self.instruments:
			instrumentdata = self.instruments[instrumentname]
			try:
				self.instrumentdescription.set(instrumentdata['description'])
			except (TypeError, KeyError):
				self.instrumentdescription.set('')
			try:
				self.instrumenthostname.set(instrumentdata['hostname'])
			except (TypeError, KeyError):
				self.instrumenthostname.set('')
		else:
			self.instrumentdescription.set('')
			self.instrumenthostname.set('')
		return index

	def defineUserInterface(self):
		self.container = uidata.ExternalContainer('Manager Setup')

		projectcontainer = uidata.Container('Project')
		self.projectselection = uidata.SingleSelectFromList('Project', [], 0,
																				callback=self.uiProjectSelectCallback,
																				persist=True)
		projectcontainer.addObject(self.projectselection)
		self.container.addObject(projectcontainer)

		usercontainer = uidata.Container('User')
		self.userselection = uidata.SingleSelectFromList('Name', [], 0,
																						callback=self.uiUserSelectCallback,
																						persist=True)
		self.userfullname = uidata.String('Full Name', '', 'r')
		self.usergroup = uidata.String('Group Name', '', 'r')
		usercontainer.addObjects((self.userselection,
																		self.userfullname,
																		self.usergroup))
		self.container.addObject(usercontainer)

		instrumentcontainer = uidata.Container('Instrument')
		self.instrumentselection = uidata.SingleSelectFromList('Name', [], 0,
																			callback=self.uiInstrumentSelectCallback,
																			persist=True)
		self.instrumentdescription = uidata.String('Description', '', 'r')
		self.instrumenthostname = uidata.String('Hostname', '', 'r')

		instrumentcontainer.addObjects((self.instrumentselection,
																		self.instrumentdescription,
																		self.instrumenthostname))

		self.container.addObject(instrumentcontainer)

		session_name = time.strftime('%Y-%m-%d')
		self.session_name = uidata.String('Session Name', session_name, 'rw',
																				persist=True)
		self.container.addObject(self.session_name)
		self.session_comment = uidata.String('Session Comment', '', 'rw',
																					persist=True)
		self.container.addObject(self.session_comment)
		## default path comes from leginonconfig
		image_path = os.path.join(leginonconfig.IMAGE_PATH,session_name)
		self.image_path = uidata.String('Image Path', image_path, 'rw',
																		persist=True)
		self.container.addObject(self.image_path)

		self.skipinstrument = uidata.Boolean('Do Not Connect Instrument Launcher', False, 'rw', persist=True)
		self.container.addObject(self.skipinstrument)

		startmethod = uidata.Method('Start', self.start)
		self.container.addObject(startmethod)

	def getUserInterface(self):
		return self.container

