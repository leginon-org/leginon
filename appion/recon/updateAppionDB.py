#!/usr/bin/env python
# update the status of the reconstruction in the appion database 

import MySQLdb
import sinedon

# connect
dbconf=sinedon.getConfig('appionData')
dbc=MySQLdb.connect(**dbconf)
# create a cursor
cursor = dbc.cursor()

jobid = sys.argv[1]
status = sys.argv[2]

q="UPDATE ApClusterJobData SET `status` = '%s' WHERE `DEF_id` = '%s'" %(status,jobid)
 
cursor.execute(q)
cursor.close()
dbc.close()
