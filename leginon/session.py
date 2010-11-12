'''
This modules defines functions for creating sessions and reserving a session
name while in the process of creating a session.
'''

import os.path
import time

import leginon.leginondata
import leginon.projectdata
import leginon.leginonconfig
import leginon.project

projectdata = leginon.project.ProjectData()

reserved = None

def makeReservation(name):
	global reserved
	if reserved and reserved.name == name:
		return
	reserved = Reservation(name)

def cancelReservation():
	global reserved
	if reserved:
		reserved.cancel()
		reserved = None

class ReservationFailed(Exception):
	pass

class Reservation(object):
	'''reserves a name in __init__, cancels reservation in __del__'''
	def __init__(self, name):
		self.name = None
		if not self.create(name):
			raise ReservationFailed('name already reserved: %s' % (name,))
		self.name = name

	def __del__(self):
		self.cancel()

	def create(self, name):
		'''
		Try to reserve a session name.
		Return True if reservation is successful.
		Return False if it is already used, or reserved by another process.
		'''
		## fail reservation if name exists in SessionData
		sessiondata = leginon.leginondata.SessionData(name=name)
		sessions = sessiondata.query()
		if sessions:
			return False
	
		## fail if reservation found in SessionReservationData
		sessionres = leginon.leginondata.SessionReservationData(name=name)
		sessionres = sessionres.query(results=1)
		if sessionres and sessionres[0]['reserved']:
			return False
	
		## make new reservation
		sessionres = leginon.leginondata.SessionReservationData(name=name, reserved=True)
		sessionres.insert(force=True)
	
		return True

	def cancel(self):
		if self.name is None:
			return
		sessionres = leginon.leginondata.SessionReservationData(name=self.name, reserved=False)
		sessionres.insert(force=True)
		self.name = None

def suggestName():
	session_name = '<cannot suggest a name>'
	for suffix in 'abcdefghijklmnopqrstuvwxyz':
		maybe_name = time.strftime('%y%b%d'+suffix).lower()
		try:
			makeReservation(maybe_name)
		except ReservationFailed:
			continue
		else:
			session_name = maybe_name
			break
	return session_name

def createSession(user, name, description, directory):
	imagedirectory = os.path.join(leginon.leginonconfig.unmapPath(directory), name, 'rawdata').replace('\\', '/')
	initializer = {
		'name': name,
		'comment': description,
		'user': user,
		'image path': imagedirectory,
	}
	return leginon.leginondata.SessionData(initializer=initializer)

def linkSessionProject(sessionname, projectid):
	if projectdata is None:
		raise RuntimeError('Cannot link session, not connected to database.')
	projq = leginon.projectdata.projects()
	projdata = projq.direct_query(projectid)
	projeq = leginon.projectdata.projectexperiments()
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sdata = sessionq.query()
	projeq['session'] = sdata[0]
	projeq['project'] = projdata
	return projeq

