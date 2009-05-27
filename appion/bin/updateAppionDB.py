#!/usr/bin/env python
# update the status of the reconstruction in the appion database 

import MySQLdb
import dbconfig
import sys

if __name__ == "__main__":
	# parse options
	projectid = None	
	if len(sys.argv) < 3:
		print "Usage: %s jobid status [projectid]" % (sys.argv[0],)
		sys.exit()

	jobid = sys.argv[1]
	status = sys.argv[2]

	if len(sys.argv) > 3:
		projectid = sys.argv[3]

	# set new db
	if projectid is not None:
		pjc = dbconfig.getConfig('projectdata')
		q = "select db from processingdb where projectId='%s'" % (projectid,)
		dbc = MySQLdb.Connect(**pjc)
		cursor = dbc.cursor()
		result = cursor.execute(q)
		if result:
			newdbname, = cursor.fetchone()
			dbconfig.setConfig('appionData', db=newdbname)
		cursor.close()
		dbc.close()

	# connect to database
	c = dbconfig.getConfig('appionData')

	dbc = MySQLdb.Connect(**c)
	cursor = dbc.cursor()

	# execute update
	q = "UPDATE ApClusterJobData SET `status` = '%s' WHERE `DEF_id` = '%s'" %(status,jobid)	 
	cursor.execute(q)

	# close
	cursor.close()
	dbc.close()
