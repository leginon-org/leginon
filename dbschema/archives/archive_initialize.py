#!/usr/bin/env python
'''
This module creates archive_users_%projectid.cfg.  It maker
sure the few users that is essential for the project is imported
even if they have not created any session that will be imported later.
'''
import os

from leginon import projectdata, leginondata
import sinedon

def checkSinedon():
	if hasattr(sinedon.dbdatakeeper.DBDataKeeper,'initImported'):
		print "sinedon must be imported from NON-myami-dbcopy branch"
		print "currently from %s",sinedon.__file__
		sys.exit(1)

class UserSearcher(object):
	def __init__(self, projectid):
		self.setProject(projectid)
		self.essential_userids = [self.getAdministratorUserId(),]
		self.run()

	def setProject(self, projectid):
		self.project = projectdata.projects().direct_query(projectid)

	def getAdministratorUserId(self):
		return leginondata.UserData(username='administrator').query()[0].dbid
		#return leginondata.UserData(username='anonymous').query()[0].dbid

	def getIdFromDataList(self,datalist):
		'''
		get dbid from a list of data object that may contain None.
		'''		
		valid_objects = filter(lambda x: x is not None,datalist)
		return map((lambda x: x.dbid),valid_objects)
		
	def getOwnerUserId(self):
		owners = projectdata.projectowners(project=self.project).query()
		users = map((lambda x: x['user']),owners)
		return self.getIdFromDataList(users)
		
	def getSharerUserId(self):
		project_sessions = projectdata.projectexperiments(project=self.project).query()
		allsharers = []
		for session in map((lambda x:x['session']),project_sessions):
			if session is None or session['name'] != '14may29anchitestA7':
				continue
			sharers = projectdata.shareexperiments(experiment=session).query()
			users = map((lambda x: x['user']),sharers)
			allsharers.extend(self.getIdFromDataList(users))
		return allsharers
		
	def run(self):
		self.essential_userids.extend(self.getOwnerUserId())
		self.essential_userids.extend(self.getSharerUserId())
		self.essential_useids = list(set(self.essential_userids))

		f = open('archive_users_%s.cfg' % (self.project.dbid), 'w')
		f.write('\n'.join(map((lambda x: '%d' % x),set(self.essential_userids))))
		f.close()

if __name__=="__main__":
	import sys
	if len(sys.argv) != 2:
		print "Usage: python archive_initialize.py <project id number>"
		sys.exit()
	checkSinedon()
	projectid = int(sys.argv[1])
	app = UserSearcher(projectid)
