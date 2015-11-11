#!/usr/bin/env python
'''
This program changes all appion run path for a session with the given parent dir
to another parent dir.  The sessionname is always included in the search and replace.
'''
import os
from sinedon import directq
from appionlib import apProject


class AppionPathChange(object):
	def __init__(self, sessionname):
		apProject.setAppiondbBySessionName(sessionname)
		self.sessionname = sessionname
		import sinedon
		self.apdbname = sinedon.getConfig('appiondata')['db']

	def setOldParentPath(self, old_parent_path):
		if self.sessionname not in old_parent_path:
			old_parent_path = os.path.join(old_parent_path,self.sessionname)
		self.old_parent_path = old_parent_path

	def setNewParentPath(self, new_parent_path):
		if self.sessionname not in new_parent_path:
			new_parent_path = os.path.join(new_parent_path,self.sessionname)
		if not os.path.isdir(new_parent_path):
			raise ValueError('New directory %s must exists' % (new_parent_path))
		self.new_parent_path = new_parent_path

	def queryOldPath(self):
		print 'Change apPath in database %s' % self.apdbname
		query = "Select DEF_id as dbid, path from %s.ApPathData where path like '%s%%'" % (self.apdbname, self.old_parent_path)
		print query
		return directq.complexMysqlQuery('appiondata',query)

	def updatePath(self,old_path_list):
		for pathdict in old_path_list:
			dbid = pathdict['dbid']
			old_path = pathdict['path']
			old_parent_len = len(self.old_parent_path)
			trail_part = old_path[old_parent_len:]
			new_path = self.new_parent_path + trail_part
			query = "Update %s.ApPathData set path='%s' where `DEF_id`=%d" % (self.apdbname, new_path,dbid)
			print query
			directq.complexMysqlQuery('appiondata',query)
			
if __name__ == '__main__':
	import sys
	if len(sys.argv) != 4:
		print 'usage: python batch_appion_path_change.py sessionname old_parent_path new_parent_path'
		print 'old_parent_path needs to be the head part of the run path with or without sessionname'
		print 'new_parent_path needs to the equivalent part of the run path'
		print 'For example, /data/appion/14oct10a can be replaced by /data2/appion/14oct10a'
		print 'sessionname is always appended to the parent_path if not included'
		sys.exit()

	sessionname = sys.argv[1]
	old_parent = sys.argv[2]
	new_parent = sys.argv[3]

	app = AppionPathChange(sessionname)
	app.setOldParentPath(old_parent)
	app.setNewParentPath(new_parent)
	old_path_list = app.queryOldPath()
	print 'Found %d records' % (len(old_path_list))
	if len(old_path_list) and raw_input('Ready to update ? (Y/N)(y/n)').lower() == 'y':
		print 'do it'
		app.updatePath(old_path_list)


