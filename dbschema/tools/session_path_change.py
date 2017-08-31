#!/usr/bin/env python
import sys
import os
from leginon import leginondata
from sinedon import directq

class SessionPathChange(object):
	def __init__(self, sessionname, new_path, path_type='image'):
		if not os.path.isdir(new_path):
			raise ValueError('New image path must exists')

		if path_type not in ('image','frame'):
			raise ValueError ('Path type must be "image" or "frame"')

		# find session(s) that is named as sessionname.  It should be unique
		results = leginondata.SessionData(name=sessionname).query()
		if len(results) != 1:
			raise ValueError('Found %d session data record for %s' % (len(results),sessionname))
		self.sessiondata = results[0]
		self.new_path = new_path
		self.path_type = path_type

	def run(self):
		# DEF_id field in SessionData table is used to choose which row of data to update
		sessionid = self.sessiondata.dbid

		# update
		query = "update `SessionData` set `%s path` = '%s' where `SessionData`.`DEF_id`=%d" % (self.path_type, self.new_path, sessionid)

		# send the query to the database linked to sinedon module named leginondata
		directq.complexMysqlQuery('leginondata',query)

if __name__=='__main__':

	if len(sys.argv) <= 3:
		print 'usage: python session_path_change.py sessionname new_image_path path_type'
		print 'new_image_path needs to lead to where the images are stored'
		print 'For example, /data/leginon/14oct01a/rawdata, and exists'
		print "path_type can be either image or frame"
		sys.exit()

	sessionname = sys.argv[1]
	new_path = sys.argv[2]
	if len(sys.argv) == 4:
		path_type = sys.argv[3]
	else:
		path_type = 'image'
	try:
		app = SessionPathChange(sessionname, new_path, path_type)
		app.run()
	except ValueError, e:
		print 'Value Error: %s' % (e.message)
