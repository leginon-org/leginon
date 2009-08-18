### webscripting

#python
import MySQLdb
#appion
import apProject
import appionData
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
def setJobStatus(jobid, status):
	### clean status
	newstat = str(status[0]).upper()

	### cluster job data
	clustdata = appionData.ApClusterJobData.direct_query(jobid)

	### do the query
	dbconf = sinedon.getConfig('appionData')
	db     = MySQLdb.connect(**dbconf)
	cursor = db.cursor()
	query = (
		"UPDATE \n"
		+"  `ApClusterJobData` as job \n"
		+"SET \n"
		+"  job.`status` = '"+str(newstat)+"' \n" 
		+"WHERE \n"
		+"  job.`DEF_id` = "+str(jobid)+" \n"
	)
	cursor.execute(query)
	if getJobStatus(jobid) == newstat:
		return True
	return False

#=====================
def getJobStatus(jobid):
	clustdata = appionData.ApClusterJobData.direct_query(jobid)
	if not clustdata:
		return None
	return clustdata['status']
