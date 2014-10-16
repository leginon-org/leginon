#!/usr/bin/env python
import os

from leginon import projectdata, leginondata
import sinedon

def checkSinedon():
	if hasattr(sinedon.dbdatakeeper.DBDataKeeper,'initImported'):
		print "sinedon must be imported from NON-myami-dbcopy branch"
		print "currently from %s",sinedon.__file__
		sys.exit(1)

class Searcher(object):
	def __init__(self, projectid):
		self.project = projectdata.projects().direct_query(projectid)
		self.essential_userids = [self.getAdministratorUserId(),]
		self.run()

	def getAdministratorUserId(self):
		return leginondata.UserData(username='administrator').query()[0].dbid
		#return leginondata.UserData(username='anonymous').query()[0].dbid
		
	def getOwnerUserId(self):
		owners = projectdata.projectowners(project=self.project).query()
		return map((lambda x: x['user'].dbid),owners)
		
	def getSharerUserId(self):
		project_sessions = projectdata.projectexperiments(project=self.project).query()
		allsharers = []
		for session in map((lambda x:x['session']),project_sessions):
			sharers = projectdata.shareexperiments(experiment=session).query()
			allsharers.extend(map((lambda x: x['user'].dbid),sharers))
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
	app = Searcher(projectid)
