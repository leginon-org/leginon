#!/usr/bin/env python
# update the status of the reconstruction in the appion database 

import MySQLdb
import dbconfig
import sys

if __name__ == "__main__":
	# parse options
	projectid = None	
	jobid = sys.argv[1]
	status = sys.argv[2]
	if len(sys.argv) > 3:
		projectid = sys.argv[3]

	# set new db
	if projectid is not None:
		newdbname = "ap"+projectid
		dbconfig.setConfig('appionData', db=newdbname)

	# connect to database
	c = dbconfig.getConfig('appionData')
	dbc = MySQLdb.Connect(**c)
	cursor = dbc.cursor()

	# execute update
	q="UPDATE ApClusterJobData SET `status` = '%s' WHERE `DEF_id` = '%s'" %(status,jobid)	 
	cursor.execute(q)

	# close
	cursor.close()
	dbc.close()

