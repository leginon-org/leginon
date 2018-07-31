#!/usr/bin/env python
import sys
import os
from leginon import leginondata
from sinedon import directq

if len(sys.argv) < 2:
	print 'usage: python batch_leginon_path_change.py new_path_base (datatype)'
	print 'this searches database based on the session name in the new_path_base'
	print 'and make the image path or frame path change'
	print 'new_path_base needs to be the parent directory of the sessionname'
	print 'For example, /data/leginon, and exists'
	print 'Optionally, you can enter the datatype: (leginon,frames, or references)'
	sys.exit()

new_path_base = sys.argv[1]

if not os.path.isdir(new_path_base):
	print 'New path must exists'
	sys.exit()

datatypes = {'leginon': 'image','frames':'frame','references':'image'}
new_path_base = os.path.abspath(new_path_base)
datatype = None
if len(sys.argv) > 2:
		try:
			datatype = datatypes[sys.argv[2]]
		except:
			print 'Input datatype not matching any possible values'
			sys.exit(1)
else:
	for key in datatypes.keys():
		if key in new_path_base:
			datatype = datatypes[key]
			print 'datatype set to %s' % (datatype)
	if not datatype:
		print 'Can not determine datatype'
		sys.exit(1)

new_sessionnames = os.listdir(new_path_base)

for sessionname in new_sessionnames:
	# find session(s) that is named as sessionname.  It should be unique
	results = leginondata.SessionData(name=sessionname).query()
	if len(results) != 1:
		print 'Found %d session data record for %s' % (len(results),sessionname)
		continue

	new_path = os.path.join(new_path_base,sessionname,'rawdata')
	if not os.path.isdir(new_path):
		print 'New  path %s must exists' % (new_path)
		continue

	# DEF_id field in SessionData table is used to choose which row of data to update
	sessionid = results[0].dbid

	# update
	query = "update `SessionData` set `%s path` = '%s' where `SessionData`.`DEF_id`=%d" % (datatype, new_path, sessionid)

	# send the query to the database linked to sinedon module named leginondata
	directq.complexMysqlQuery('leginondata',query)
	print 'Session %s %s path is now set to %s' % (sessionname, datatype, new_path)
