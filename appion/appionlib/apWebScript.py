### webscripting

#python
import MySQLdb
#appion
from appionlib import appiondata
#leginon
import sinedon

#=====================
def setJobToRun(jobid):
	if getJobStatus(jobid) == "R":
		return False
	return setJobStatus(jobid, "R")

#=====================
def setJobToDone(jobid):
	if getJobStatus(jobid) == "D":
		return False
	return setJobStatus(jobid, "D")

#=====================
def setJobToError(jobid):
	if getJobStatus(jobid) == "E":
		return False
	return setJobStatus(jobid, "E")

#=====================
def setJobStatus(jobid, status):
	### clean status
	newstat = str(status[0]).upper()

	### cluster job data
	clustdata = appiondata.ApAppionJobData.direct_query(jobid)
	if not clustdata:
		print "Did not find jobid=%d"%(jobid)
		return False

	### do the query
	dbconf = sinedon.getConfig('appiondata')
	db     = MySQLdb.connect(**dbconf)
	db.autocommit(True)
	cursor = db.cursor()
	query = (
		"UPDATE \n"
		+"  `ApAppionJobData` as job \n"
		+"SET \n"
		+"  job.`status` = '"+str(newstat)+"' \n"
		+"WHERE \n"
		+"  job.`DEF_id` = "+str(clustdata.dbid)+" \n"
	)
	try:
		cursor.execute(query)
	except:
		print "MySQL query failed:\n======\n%s"%(query)
		return False
	if getJobStatus(jobid) == newstat:
		return True
	return False

#=====================
def getJobStatus(jobid):
	clustdata = appiondata.ApAppionJobData.direct_query(jobid)
	if not clustdata:
		return None
	return clustdata['status']

