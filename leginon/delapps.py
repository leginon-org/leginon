#!/usr/bin/env python

import dbdatakeeper
from leginon import leginondata
import MySQLdb
import sys
import getpass
import sinedon

try:
	f = open('delapps')
except:
	print '''no 'delapps' file'''
	sys.exit()

delapps = f.readlines()
f.close()
delapps = [app[:-1] for app in delapps]

appids = []
evtids = []
nodids = []

db = sinedon.getConnection('leginondata')

for delapp in delapps:
	qapp = leginondata.ApplicationData(name=delapp)
	apps = db.query(qapp)
	appids.extend([a.dbid for a in apps])

if not appids:
	print '''No apps listed in 'delapps' file exist in DB'''
	sys.exit()

host = raw_input('DB Host: ')
dbname = raw_input('DB Name: ')
user = raw_input('DB User: ')
passwd = getpass.getpass()

db = MySQLdb.connect(host=host, user=user, db=dbname, passwd=passwd)
db.autocommit(True)

for id in appids:
	cur = db.cursor()
	cur.execute('delete from ApplicationData where DEF_id = %d' % (id,))
