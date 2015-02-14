#!/usr/bin/env python
import sys
import os
from leginon import leginondata
from sinedon import directq

class SessionPathChange(object):
	def __init__(self, sessionname, new_path):
		if not os.path.isdir(new_path):
			raise ValueError('New image path must exists')

		# find session(s) that is named as sessionname.  It should be unique
		results = leginondata.SessionData(name=sessionname).query()
		if len(results) != 1:
			raise ValueError('Found %d session data record for %s' % (len(results),sessionname))
		self.sessiondata = results[0]
		self.new_path = new_path

	def run(self):
		# DEF_id field in SessionData table is used to choose which row of data to update
		sessionid = self.sessiondata.dbid

		# update
		query = "update `SessionData` set `image path` = '%s' where `SessionData`.`DEF_id`=%d" % (self.new_path, sessionid)

		# send the query to the database linked to sinedon module named leginondata
		directq.complexMysqlQuery('leginondata',query)

if __name__=='__main__':

	if len(sys.argv) != 3:
		print 'usage: python session_path_change.py sessionname new_image_path'
		print 'new_image_path needs to lead to where the images are stored'
		print 'For example, /data/leginon/14oct01a/rawdata, and exists'
		sys.exit()

	sessionname = sys.argv[1]
	new_path = sys.argv[2]

	try:
		app = SessionPathChange(sessionname, new_path)
		app.run()
	except ValueError, e:
		print 'Value Error: %s' % (e.message)
