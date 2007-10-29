#!/usr/bin/env python
# update the status of the reconstruction in the appion database 

import MySQLdb
import sys
 
dbc=MySQLdb.Connect(
  host="cronus4",
  user="usr_object",
  db="dbappiondata")
 
cursor=dbc.cursor(MySQLdb.cursors.DictCursor)

jobid = sys.argv[1]
status = sys.argv[2]

q="UPDATE ApClusterJobData SET `status` = '%s' WHERE `DEF_id` = '%s'" %(status,jobid)
 
cursor.execute(q)
cursor.close()
dbc.close()
 
