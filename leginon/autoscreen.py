#!/usr/bin/env python
import os
import sys
import time
from leginon import leginondata
from leginon import projectdata
import leginon.session
import leginon.leginonconfig
import leginon.ddinfo
import leginon.nodesimu
import leginon.presets
from pyami import mysocket

class Options(object):
	pass

class SessionCreator(object):
	def __init__(self):
		self.old_session = None
		self.session_set = None
		self.comment = None
		self.stagez = None

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

	def setComment(self, comment):
		self.comment = comment

	def createSession(self):
		old_session = self.old_session
		comment = self.comment
		if not old_session or not comment:
			raise ValueError('old session or comment not valid')
		self.session = self.makeNewSessionFromOld(old_session, comment)
		# TODO: need gui to allow linking sessions from different project
		pid = self.getProjectIdFromSession(old_session)
		self.project = self.linkSessionProject(pid)
		self.setDataFromOld('C2ApertureSizeData',old_session)
		self.clients = self.setDataFromOld('ConnectToClientsData',old_session)['clients']
		self.setDataFromOld('LaunchedApplicationData',old_session)
		self.copyPresets(old_session)

	def makeNewSessionFromOld(self, old_session, comment):
		user = old_session['user']
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

	def getProjectIdFromSession(self,old_session):
		q = projectdata.projectexperiments(session=old_session)
		r = q.query()
		if len(r) != 1:
			print 'Project link of the old session is not unique'
			sys.exit(1)
		return r[0]['project'].dbid
		
	def linkSessionProject(self,projectid):
		name = self.session['name']
		projeq = leginon.session.linkSessionProject(name, projectid)
		projeq.insert()
		return projeq['project']

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

	def getOldSessionStageZ(self):
		old_session = self.old_session
		scope = leginondata.ScopeEMData(session=old_session).query(results=1)[0]
		stagez = scope['stage position']['z']
		return stagez

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
	f = open(filepath)
	lines = f.readlines()
	comment_map = []
	for l in lines:
		bits = l.split('\t')
		# list of slot number and comment so that it is ordered
		comment_map.append((int(bits[0]),bits[1].split('\n')[0]))
	return comment_map

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
	print option_dict
	# options need to be set as attributes
	options = Options()
	for k in option_dict.keys():
		setattr(options,k,option_dict[k])
	from leginon import start
	start.start(options)

if __name__ == "__main__":
	answer = raw_input('Enter autoloader cassette-grid mapping filename=')
	if answer:
		if not os.path.isfile(answer):
			print 'Error: file not found'
			sys.exit(1)
		comment_map = readMapFile(answer)
	else:
		comment_map = []
		ganswer = raw_input('Grid loader slot number for the grid= ')
		if not ganswer:
			print 'Error: Invalid grid loader slot number'
			sys.exit(1)
		answer = raw_input('Session comment field entry: ')
		# grid slot, comment
		comment_map.append((int(ganswer),answer))
	# old session
	answer = raw_input('Enter an old session name to base new sessions on: ')
	if not answer:
		sys.exit(0)
	app = SessionCreator()
	app.saveAutoSessionSet(answer)
	# z value
	stagez = app.getOldSessionStageZ()
	zanswer = raw_input('Enter Z stage height to return to in um (default: the old sessionvalue %.1f): ' % (stagez*1e6,))
	if zanswer != '':
		try:
			stagez = float(zanswer)*1e-6
		except ValueError:
			print('Invalid number entry: %s' % zanswer)
			sys.exit(1)
	# create by the order of the comment_map
	slot_order = map((lambda x:x[0]),comment_map)
	task_order = []
	for i, slot_number in enumerate(slot_order):
		app.setComment(comment_map[i][1])
		app.createSession()
		auto_session = app.saveGridSessionMap(i, slot_number, stagez)
		task = app.saveTask(auto_session,'atlas')
		task_order.append(task.dbid)
		if i == 0:
			first_session = app.session
			first_slot = slot_number
		time.sleep(1.0) # to prevent session out of order on the viewer.
	app.saveAutoTaskOrder(task_order)
	#TODO: start the first session.  The rest will be set from there.
	start(first_session['name'],app.clients,first_slot,stagez, task['task'])
