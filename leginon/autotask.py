#!/usr/bin/env python

#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

from leginon import leginondata
from pyami import mysocket

class AutoTaskOrganizer(object):
	def __init__(self, session):
		self.session_set = self.getAutoSessionSet(session)
		if not self.session_set:
			raise ValueError('No auto task session found')

	def getAutoSessionSet(self, check_session):
		# check as base session
		q = leginondata.AutoSessionSetData()
		q['main launcher'] = mysocket.gethostname().lower()
		q['base session'] = check_session
		# most recent one
		results = q.query(results=1)
		if results:
			return results[0]
		else:
			# find from auto sessions
			q = leginondata.AutoSessionData()
			q['session'] = check_session
			results = q.query(results=1)
			if results:
				return results[0]['session set']
		return []

	def getAutoSessions(self):
		q = leginondata.AutoSessionData()
		q['session set'] = self.session_set
		results = q.query()
		return results

	def getTaskOrderData(self):
		q = leginondata.AutoTaskOrderData()
		q['session set'] = self.session_set
		r = q.query(results=1)[0]
		return r

	def _popTaskOrder(self):
		orderdata = self.getTaskOrderData()
		q = leginondata.AutoTaskOrderData(initializer=orderdata)
		order = list(orderdata['task order'])
		if len(order) == 0:
			raise ValueError('Empty task order')
		order.pop(0)
		q['task order'] = order
		q.insert()
		return q
		
	def nextAutoTask(self):
		try:
			r = self._popTaskOrder()
		except:
			return None
		task_order = r['task order']
		if task_order:
			next_taskid = task_order[0]
			return leginondata.AutoTaskData().direct_query(next_taskid)
		return None

if __name__=='__main__':
	session = leginondata.SessionData().query(results=1)[0]
	print 'test with session %s' % session['name']
	app = AutoTaskOrganizer(session)
	print app.nextAutoTask()
