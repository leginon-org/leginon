#!/usr/bin/env python
"""
Continue crashed auto session set initiated by autoscreen.py
"""
import sys
from leginon import leginondata
from leginon import autotask

class Options(object):
	pass

class SessionContinuer(object):
	'''
	Define auto session and task to continue
	'''
	def __init__(self, session_name):
		try:
			check_session = leginondata.SessionData(name=session_name).query(results=1)[0]
		except IndexError:
			raise ValueError('Check session not exists.')
		self.tasker = autotask.AutoTaskOrganizer(check_session)
		self.session_set = self.tasker.session_set
		self.auto_sessions = self.tasker.getAutoSessions()
		self.continue_session = None
		self.findContinueSession()
		self.stagez = self.getSessionStageZ()
		self.slot = self.getSessionGridSlot()

	def getSessionStageZ(self):
		scopes = leginondata.ScopeEMData(session=self.continue_session).query(results=1)
		if scopes:
			stagez = scopes[0]['stage position']['z']
		else:
			stagez = self.continue_autosession['stagez']
		return stagez

	def getSessionGridSlot(self):
		return self.continue_autosession['slot number']

	def _setContinueStateFromTask(self, taskdata):
		self.continue_task = taskdata
		self.continue_autosession = taskdata['auto session']
		self.continue_session = self.continue_autosession['session']

	def findContinueSession(self):
		'''
		Find which session to continue on.
		'''
		self.continue_task_order=self.tasker.getTaskOrderData()
		if not self.continue_task_order['task order']:
				raise ValueError('Auto session set all done. Nothing to continue')
		auto_task = leginondata.AutoTaskData().direct_query(self.continue_task_order['task order'][0])
		self._setContinueStateFromTask(auto_task)
		is_last_session = self.continue_autosession.dbid == self.auto_sessions[-1].dbid
		r = leginondata.SessionDoneLog(session=self.continue_session).query(results=1)
		self.session_ended = False
		if r:
			if r[0]['done']:
				self.session_ended = True
		if not self.session_ended:
			#	need to submit targets on existing grid atlas
			self._updateContinueTask()
		else:
			# Ended session need to continue from next session
			if is_last_session:
				raise ValueError('Auto session set all done. Nothing to continue')
			else:
				# use next session and start from the beginning
				auto_task = leginondata.AutoTaskData().direct_query(self.continue_task_order['task order'][1])
				self.tasker.nextAutoTask()
				self.findContinueSession() #repeat this function
		self.clients = leginondata.ConnectToClientsData(session=self.continue_session).query(results=1)[0]
		self.launched_app = leginondata.LaunchedApplicationData(session=self.continue_session).query(results=1)[0]
		if not self.launched_app:
			raise ValueError('No launched application in the auto session set')

	def _updateContinueTask(self):
		'''
		Creates task to reload existing atlas and submit targets on it.
		This is then replace the current tast on this session.
		'''
		targetlist = leginondata.ImageTargetListData(session=self.continue_session).query()
		if len(targetlist) > 1 and targetlist[-1]['mosaic']:
			# session has more than targetlist for mosaic.  This means
			# square targets has been submitted.
			q = leginondata.AutoTaskData(task='submit squares')
			q['auto session'] = self.continue_autosession
			q.insert()
			taskid=q.dbid
			order_data = leginondata.AutoTaskOrderData(initializer=self.continue_task_order)
			order = order_data['task order']
			i = order.index(self.continue_task.dbid)
			order[i]=taskid
			order_data['task order'] = order
			order_data.insert()
			self.continue_task_order = order_data
			self.continue_task = q
		elif len(targetlist) == 1 and targetlist[0]['mosaic']:
			# in the middle grid atlas collection. Run the normal start.
			# This will generate error in Grid Targeting, but can recover manually
			pass
		else:
			# has not made any targetlist.  Probably error in autoloader.
			pass

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

if __name__ == "__main__":
	# session in the AutoSessionSet
	answer = raw_input('Enter a session name in the auto session you want to continue: ')
	if not answer:
		sys.exit(0)
	try:
		app1 = SessionContinuer(answer)
	except Exception as e:
		print('Error: %s' % e)
		sys.exit(1)
	#start the first session.  The rest will be set from Manager.
	start(app1.continue_session['name'],app1.clients,app1.slot,app1.stagez, app1.continue_task['task'])
