#!/usr/bin/env python
import sys
import os
from leginon import leginondata,projectdata
from sinedon import directq
from appionlib import apProject

class AppionPathChange(object):
	def __init__(self,sessionname, old_path, new_path):
		if not os.path.isdir(new_path):
			raise ValueError('New image path must exists')

		# find session(s) that is named as sessionname.  It should be unique
		results = leginondata.SessionData(name=sessionname).query()
		if len(results) != 1:
			raise ValueError('Found %d session data record for %s' % (len(results),sessionname))
		self.sessionname = sessionname
		self.old_path = old_path
		self.new_path = new_path

	def run(self):
		# setAppionDB
		apProject.setAppiondbBySessionName(self.sessionname)

		import sinedon
		apdbname = sinedon.getConfig('appiondata')['db']
		print 'Change apPath in database %s' % apdbname

		# update
		query = "update %s.`ApPathData` set `path` = '%s' where %s.`ApPathData`.`path` like '%s'" % (apdbname,self.new_path, apdbname,self.old_path)

		print query
		# send the query to the database linked to sinedon module named appiondata
		directq.complexMysqlQuery('appiondata',query)
		print 'Path changed from %s to %s' % (self.old_path, self.new_path)		

if __name__ == '__main__':
	if len(sys.argv) != 4:
		print 'usage: python appion_path_change.py sessionname old_run_path new_run_path'
		print 'old_run_path needs to lead to where the appion run results are stored'
		print 'new_run_path needs to lead to where the appion run results are stored'
		print 'For example, /data/appion/14oct01a/stacks/stack1, and exists'
		sys.exit()

	sessionname = sys.argv[1]
	old_path = sys.argv[2]
	new_path = sys.argv[3]
	
	try:
		app = AppionPathChange(sessionname, old_path, new_path)
		app.run()
	except ValueError, e:
		print 'Value Error: %s' % (e.message)
