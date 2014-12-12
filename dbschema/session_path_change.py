#!/usr/bin/env python
import sys
import os
from leginon import leginondata
from sinedon import directq

if len(sys.argv) != 3:
	print 'usage: python pathchang.py sessionname new_image_path'
	print 'new_image_path needs to lead to where the images are stored'
	print 'For example, /data/leginon/14oct01a/rawdata, and exists'
	sys.exit()

sessionname = sys.argv[1]
new_path = sys.argv[2]

if not os.path.isdir(new_path):
	print 'New image path must exists'
	sys.exit()

# find session(s) that is named as sessionname.  It should be unique
results = leginondata.SessionData(name=sessionname).query()
if len(results) != 1:
	print 'Found %d session data record for %s' % (len(results),sessionname)
	sys.exit()

# DEF_id field in SessionData table is used to choose which row of data to update
sessionid = results[0].dbid

# update
query = "update `SessionData` set `image path` = '%s' where `SessionData`.`DEF_id`=%d" % (new_path, sessionid)

# send the query to the database linked to sinedon module named leginondata
directq.complexMysqlQuery('leginondata',query)
