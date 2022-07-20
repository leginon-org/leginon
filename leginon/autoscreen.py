#!/usr/bin/env python
"""
Automatically load grids and acquire grid atlas using the same project,
Leginon clients, presets, and application of an old session.
"""
import os
import sys
import time
import wx
from leginon import leginondata
from leginon import projectdata
from leginon import gridserver
from leginon import settingsfun
import leginon.session
import leginon.leginonconfig
import leginon.ddinfo
import leginon.nodesimu
import leginon.presets
from pyami import mysocket
from leginon.gui.wx import AutoScreenProject

class Options(object):
	pass

user_map = leginon.session.getUserFullnameMap()

class SessionSetCreator(object):
	def __init__(self):
		self.old_session = None
		self.session_set = None
		self.old_project = None
		self.comment = None
		self.stagez = None
		self.all_grid_info = []

	def saveAutoSessionSet(self,old_session_name):
		self._setOldSession(old_session_name)
		q = leginondata.AutoSessionSetData()
		q['main launcher'] = mysocket.gethostname().lower()
		q['base session'] = self.old_session
		q.insert(force=True)
		self.session_set = q

	def _setOldSession(self,old_session_name):
		r = leginondata.SessionData(name=old_session_name).query()
		if len(r) > 1:
			raise ValueError('Error: old session not unique')
			sys.exit(1)
		if len(r) < 1:
			raise ValueError('Error: old session not found')
			sys.exit(1)
		self.old_session = r[0]
		self.old_project = self.getProjectFromSession(self.old_session)

	def getProjectFromSession(self,old_session):
		q = projectdata.projectexperiments(session=old_session)
		r = q.query()
		if len(r) != 1:
			print 'Project link of the old session is not unique'
			sys.exit(1)
		return r[0]['project']

	def getOldSessionStageZ(self):
		old_session = self.old_session
		scopes = leginondata.ScopeEMData(session=old_session).query(results=1)
		stagez = 0.0
		if scopes:
			stagez = scopes[0]['stage position']['z']
		return stagez

	def confirmCommentProjectWithGui(self, all_grid_info):
		'''
		Start gui to modify session comment and project assignment for each grid.
		'''
		project_choices = {}
		projects = projectdata.projects().query()
		projects.reverse()
		app = wx.App()
		AutoScreenProject.ScreenInfoMap(self, self.old_session,self.old_project,all_grid_info, projects)
		app.MainLoop()

	def uiSetGridMap(self, all_grid_info):
		self.all_grid_info = all_grid_info

	def setGridMap(self, all_grid_info):
		'''
		Set all_grid_info without gui.  project_id == None is converted to old_project
		'''
		for g in all_grid_info:
			if g['project_id'] is None:
				g['project_id'] = self.old_project.dbid
			self.all_grid_info.append(g)

class SessionCreator(object):
	def __init__(self, session_set):
		self.session_set = session_set
		self.old_session = session_set['base session']
		self.project = None

	def setComment(self, comment):
		self.comment = comment

	def setProjectId(self, projectid):
		self.project_id = projectid
		self.project = projectdata.projects().direct_query(projectid)

	def createSession(self):
		old_session = self.old_session
		comment = self.comment
		if not old_session or not comment:
			raise ValueError('old session or comment not valid')
		self.session = self.makeNewSessionFromOld(old_session, comment)
		self.project = self.linkSessionProject(self.project_id)
		self.setDataFromOld('C2ApertureSizeData',old_session)
		self.clients = self.setDataFromOld('ConnectToClientsData',old_session)['clients']
		self.launched_app = self.setDataFromOld('LaunchedApplicationData',old_session)
		self.copyPresets(old_session)

	def getUser(self):
		user_fullname = leginon.leginonconfig.USERNAME
		search_name = user_fullname.strip().lower()
		if search_name in user_map:
			return user_map[search_name]
		else:
			print('Error: current leginon.cfg user %s not found.' % user_fullname)
			print('     Use example session user to create sessions.')
			return self.old_session['user']

	def makeNewSessionFromOld(self, old_session, comment):
		user = self.getUser()
		holder = old_session['holder']
		name = self.getSessionName()
		directory = leginon.leginonconfig.IMAGE_PATH
		sessionq = leginon.session.createSession(user, name, comment, directory, holder)
		sessionq.insert()
		leginon.session.cancelReservation()
		return sessionq

	def getSessionName(self):
		name = leginon.session.suggestName()
		return name

	def linkSessionProject(self,projectid):
		name = self.session['name']
		projeq = leginon.session.linkSessionProject(name, projectid)
		projeq.insert()
		return projeq['project']

	def linkGridServerSession(self):
		'''
		record session name and dbid to grid management system 
		and associate that with a grid if gridhook.cfg
		is defined.  The grid is identified in session comment.
		'''
		grid_id_string = self.session['comment']
		gapp = gridserver.GridHookServer(self.session, self.project)
		if not gapp.gridhook_server_active:
			# Do nothing
			return
		# save session info to grid management system
		gapp.setSession()
		#
		if gapp.setGridSession(grid_id_string) == False:
			raise ValueError('%s is not found in grid server database' % grid_id_string)

	def setDataFromOld(self,class_name,old_session):
		r = getattr(leginondata,class_name)(session=old_session).query()
		if r:
			q = getattr(leginondata,class_name)(initializer=r[0])
			q['session'] = self.session
			q.insert()
		return q

	def copyPresets(self, old_session):
		# Node allows session information to pass through
		test_node = leginon.nodesimu.NodeSimulator(old_session) 
		pclient = leginon.presets.PresetsClient(test_node)
		# The function in the class instance had now access to session info.
		preset_dict = pclient.getPresetsFromDB()

		for pname in preset_dict.keys():
			q = leginondata.PresetData(initializer=preset_dict[pname])
			q['session'] = self.session
			q.insert()

	def saveGridSessionMap(self, order, slot_number, stagez):
		q = leginondata.AutoSessionData()
		q['session set'] = self.session_set
		q['slot number'] = slot_number
		q['session'] = self.session
		q['stagez'] = stagez
		q.insert()
		return q

	def saveTask(self, auto_session, task='atlas'):
		q = leginondata.AutoTaskData(task=task)
		q['auto session'] = auto_session
		q.insert()
		return q

	def saveAutoTaskOrder(self, task_order):
		q = leginondata.AutoTaskOrderData()
		q['session set'] = self.session_set
		q['task order'] = list(task_order)
		q.insert(force=True)

def readMapFile(filepath):
	'''
	Read tab separated text file for slot number, comment, and project_id passing.
	# TODO: make gui to allow linking sessions from different project
	'''
	f = open(filepath,'r')
	lines = f.readlines()
	grid_info_map = []
	for l in lines:
		l = l.split('\n')[0]
		bits = l.split('\t')
		if len(bits) >= 2:
			# list of slot number and comment so that it is ordered
			info = {'slot_number':int(bits[0]),'comment':bits[1],'project_id':None}
			if len(bits) == 3:
				# try preoject name
				r = projectdata.projects(name=bits[2]).query(results=1)
				if r:
					info['project_id']=r[0].dbid
				else:
					# assume it is project dbid
					try:
						info['project_id']=int(bits[2])
					except:
						raise ValueError('project field must match a project name or an integer project id: %s' % bits[2])
			grid_info_map.append(info)
		else:
			raise ValueError('Incorrect file format.  Must use tab to separate slot_number and session_description')
	return grid_info_map

def start(sessionname, clientlist, gridslot,z, task='atlas'):
	if clientlist:
		clients = ','.join(clientlist)
	else:
		clients = None
	if gridslot:
		gridslot = '%d' % gridslot
	else:
		gridslot = None
	if not gridslot:
		z = None
	option_dict = {'version':None, 'session': sessionname, 'clients': clients,'prevapp':True, 'gridslot':gridslot, 'stagez':z, 'task':task}
	# options need to be set as attributes
	options = Options()
	for k in option_dict.keys():
		setattr(options,k,option_dict[k])
	from leginon import start
	start.start(options)

class SessionSettingsCopier(object):
	'''
	Copy application settings from an old session to the new session.
	'''
	def __init__(self, session, old_session, application):
		self.session = session
		self.old_session = old_session
		nodes = self.getApplicationNodes(application)
		for n in nodes:
			class_name = n['class string']
			alias = n['alias']
			settings_classname = settingsfun.getSettingsName(class_name)
			if not settings_classname:
				continue
			try:
				self.copyOldSettings(settings_classname, alias)
			except Exception as e:
				print(e)
				continue
			if 'Focuser' in class_name:
				settings_classname = 'FocusSequenceData'
				seqdata = self.copyOldSettings(settings_classname, alias)
				for step_name in seqdata['sequence']:
					self.copyOldFocusSettings(alias, step_name)

	def copyOldFocusSettings(self, alias, step_name):
		settings_classname = 'FocusSettingData'
		settings_class = getattr(leginondata, settings_classname)
		extra = ('node name', alias)
		try:
			old_settings = settingsfun.researchDBSettings(settings_class, step_name, self.old_session, None, extra)[0]
		except IndexError as e:
			print('ERROR: no focus settings found, use default')
			return
		q = settings_class(initializer=old_settings)
		q['session'] = self.session
		q.insert()
		return q

	def copyOldSettings(self, settings_classname, alias):
		settings_class = getattr(leginondata, settings_classname)
		old_settings = self._getOldDBSettings(settings_class, alias)[0]
		if old_settings:
			q = settings_class(initializer=old_settings)
			q['session'] = self.session
			q.insert()
		return q


	def getApplicationNodes(self, appdata):
		nodeinstance = leginondata.NodeSpecData(application=appdata)
		return nodeinstance.query()

	def _getOldDBSettings(self, settingsclass, inst_alias, extra=None):
		'''
		Return settings based on the old session which might belong to a different user.
		'''
		return settingsfun.researchDBSettings(settingsclass, inst_alias, self.old_session, None, extra)

if __name__ == "__main__":
	answer = raw_input('Enter autoloader cassette-grid mapping filename (leave it blank to use gui): ')
	grid_info_map = []
	if answer:
		if not os.path.isfile(answer):
			print 'Error: file not found'
			sys.exit(1)
		use_gui = False
		grid_info_map = readMapFile(answer)
	else:
		slot_list = raw_input('List comma-separated slot number to screen, i.e., 1,11,12: ')
		slots = slot_list.split(',')
		if not slots:
			sys.exit(1)
		use_gui = True
		for s in slots:
			grid_info_map.append({'slot_number':int(s),'comment':'','project_id':None})
	# workflow choice
	wanswer = raw_input('Full workflow or atlas only (full/atlas): ')
	while wanswer.lower() not in ('full','atlas'):
		wanswer = raw_input('Invalid workflow name. Please try again: full or atlas')
	workflow = wanswer.lower()
	# old session
	answer = raw_input('Enter an old session name to base new sessions on: ')
	if not answer:
		sys.exit(0)
	app1 = SessionSetCreator()
	try:
		app1.saveAutoSessionSet(answer)
	except Exception as e:
		print('Error: %s' % e)
		sys.exit(1)
	# z value
	stagez = app1.getOldSessionStageZ()
	zanswer = raw_input('Enter Z stage height to return to in um (default: the old sessionvalue %.1f): ' % (stagez*1e6,))
	if zanswer != '':
		try:
			stagez = float(zanswer)*1e-6
		except ValueError:
			print('Invalid number entry: %s' % zanswer)
			sys.exit(1)
	# confirm session project assignment
	if use_gui:
		app1.confirmCommentProjectWithGui(grid_info_map)
	else:
		app1.setGridMap(grid_info_map)

	if app1.all_grid_info == False:
		sys.exit(1)
	# create by the order of the confirmed all_grid_info
	# app.all_grid_info may have been modified by the gui.
	slot_order = map((lambda x:x['slot_number']),app1.all_grid_info)
	task_order = []

	# SessionData are created before starting.
	app2 = SessionCreator(app1.session_set)
	for i, slot_number in enumerate(slot_order):
		# project_id and comment are set before creating the session
		app2.setProjectId(app1.all_grid_info[i]['project_id'])
		app2.setComment(app1.all_grid_info[i]['comment'])
		app2.createSession()
		# create gridhook link in grid server
		app2.linkGridServerSession()
		# save grid session map in leginondb
		auto_session = app2.saveGridSessionMap(i, slot_number, stagez)
		task = app2.saveTask(auto_session,workflow)
		task_order.append(task.dbid)
		if i == 0:
			first_session = app2.session
			first_slot = slot_number
			# copy the last settings from the old session instead of most recent user settings.
			launched_app = app2.launched_app
			app3 = SessionSettingsCopier(first_session, app2.old_session, launched_app['application'])
		time.sleep(1.0) # to prevent session out of order on the viewer.
	app2.saveAutoTaskOrder(task_order)
	#start the first session.  The rest will be set from Manager.
	start(first_session['name'],app2.clients,first_slot,stagez, task['task'])
