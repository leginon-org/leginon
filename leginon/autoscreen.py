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

class SessionCreator(object):
	def __init__(self):
		self.old_session = None
		self.comment = None

	def setOldSession(self,old_session_name):
		r = leginondata.SessionData(name=old_session_name).query()
		if len(r) != 1:
			raise ValueError('Error: old session not unique')
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
		pid = self.getProjectIdFromSession(old_session)
		self.project = self.linkSessionProject(pid)
		self.setDateFromOld('C2ApertureSizeData',old_session)
		self.clients = self.setDateFromOld('ConnectToClientsData',old_session)['clients']
		self.setDateFromOld('LaunchedApplicationData',old_session)
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

	def setDateFromOld(self,class_name,old_session):
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

def readMapFile(filepath):
	f = open(filepath)
	lines = f.readlines()
	comment_map = {}
	for l in lines:
		bits = l.split('\t')
		comment_map[int(bits[0])] = bits[1].split('\n')[0]
	return comment_map

class Options(object):
	pass

def start(sessionname, clientlist, gridslot):
	if clientlist:
		clients = ','.join(clientlist)
	else:
		clients = None
	if gridslot:
		gridslot = '%d' % gridslot
	else:
		gridslot = None
	option_dict = {'version':None, 'session': sessionname, 'clients': clients,'prevapp':True, 'gridslot':gridslot}
	# options need to be set as attributes
	options = Options()
	for k in option_dict.keys():
		setattr(options,k,option_dict[k])
	from leginon import start
	start.start(options)

if __name__ == "__main__":
	answer = raw_input('Enter autoloader cassette-grid mapping filename=')
	if not os.path.isfile(answer):
		print 'Error: file not found'
		sys.exit(1)
	comment_map = readMapFile(answer)
	answer = raw_input('Enter an old session name to base new sessions on=')
	if not answer:
		sys.exit(0)

	app = SessionCreator()
	app.setOldSession(answer)
	keys = comment_map.keys()
	keys.sort()
	for k in keys:
		app.setComment(comment_map[k])
		app.createSession()
		start(app.session['name'],app.clients,k)
