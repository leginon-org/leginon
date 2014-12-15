import sys
import sinedon
from sinedon import dbconfig
from sinedon import directq
from leginon import projectdata
from leginon import leginondata
import time

# set direct_query values
# exclude preset lable
excludelist = ()

def checkSinedon():
	try:
		destination_dbinfo = dbconfig.getConfig('importdata')
	except KeyError:
		print "Please define impordata module in sinedon.cfg"
		sys.exit(1)
	if not hasattr(sinedon.dbdatakeeper.DBDataKeeper,'initImported'):
		print "sinedon must be imported from myami-dbcopy branch"
		print "currently from %s",sinedon.__file__
		sys.exit(1)

class Archiver(object):
	def __init__(self):
		self.status = True # initialize status to o.k.
		source_dbinfo = dbconfig.getConfig('projectdata')
		destination_dbinfo = dbconfig.getConfig('importdata')
		if source_dbinfo['host'] != destination_dbinfo['host']:
			self.escape('projectdata and importdata not on the same host')
		self.dbhost = source_dbinfo['host']
		self.source_dbname = source_dbinfo['db']
		self.destination_dbname = destination_dbinfo['db']

	def isStatusGood(self):
		return self.status

	def escape(self,msg=''):
		print msg
		self.reset()
		self.status = False

	def reset(self):
		'''
		reset configuration to source db to avoid confusion
		'''
		sinedon.setConfig('projectdata', db=self.source_dbname)

	def research(self,q,most_recent=False):
		'''
		Query results from source database. Sorted by entry time. Oldest fist
		'''
		# configuration must be set before any query
		sinedon.setConfig('projectdata', db=self.source_dbname)
		if most_recent:
			r = q.query(results=1)
			if r:
				return r[0]
		else:
			r = q.query()
			r.reverse()
		return r

	def publish(self,results):
		'''
		Publish query results to destination database.
		'''
		if not results:
			return
		# configuration must be set before any query
		sinedon.setConfig('projectdata', db=self.destination_dbname)
		for q in results:
			q.insert(archive=True)
		self.reset()

	def replaceItem(self,data,key,value):
		if data.has_key(key):
			data.__setitem__(key, value, force=True)

	def avoidExcludedImage(self,fulllist):
		shortlist = []
		for data in fulllist:
			if data['image']['label'] in excludelist:
				continue
			else:
				shortlist.append(data)
		return shortlist

	def findBrightImageFromNorm(self,normdata):
		'''
		Find BrighetImageData based on imported NormImageData.
		This is needed for older data since BrightImageData was
		not linked to AcquisitionImages previously.
		'''
		if normdata['bright']:
			return normdata['bright']
		sinedon.setConfig('projectdata', db=self.source_dbname)
		timestamp = normdata.timestamp
		normcam = normdata['camera']
		qcam = projectdata.CameraEMData(dimension=normcam['dimension'],
				offset=normcam['offset'], binning=normcam['binning'],
				ccdcamera=normcam['ccdcamera'])
		qcam['exposure type'] = 'normal'
		qcam['energy filtered'] = normcam['energy filtered']

		normscope = normdata['scope']
		qscope = projectdata.ScopeEMData(tem=normscope['tem'])
		qscope['high tension'] = normscope['high tension']
		q = projectdata.BrightImageData(camera=qcam,scope=qscope,channel=normdata['channel'])
		brightlist = q.query()
		for brightdata in brightlist:
			if brightdata.timestamp < timestamp:
				break
		return brightdata

	def makequery(self,classname,kwargs):
		'''
		Make SQL query of projectdata from class name and keyword arguments.
		'''
		q = getattr(projectdata,classname)()
		for key in kwargs.keys():
			# projectdata keys never contains '_'
			realkey = key.replace('_',' ')
			q[realkey] = kwargs[key]
		return q

	def makeTimeStringFromTimeStamp(self,timestamp):
		t = timestamp
		return '%04d%02d%02d%02d%02d%02d' % (t.year,t.month,t.day,t.hour,t.minute,t.second)

class ProjectArchiver(Archiver):
	'''
	Archive a project in projectdb
	'''
	def __init__(self,projectid):
		super(ProjectArchiver,self).__init__()
		self.projectid = projectid
		self.setSourceProject(projectid)
		self.setDestinationProject(projectid)

	def setSourceProject(self, projectid):
		sinedon.setConfig('projectdata', db=self.source_dbname)
		self.source_project = projectdata.projects().direct_query(projectid)

	def getSourceProject(self):
		'''
		Get Source Project data reference.
		'''
		#This redo the query since the reference often get mapped to
		#the destination database for unknown reason after some queries.
		self.setSourceProject(self.projectid)
		return self.source_project

	def setDestinationProject(self, projectid):
		self.destination_project = None
		sinedon.setConfig('projectdata', db=self.destination_dbname)
		project = projectdata.projects().direct_query(projectid)
		self.destination_project = project
		self.reset()

	def getDestinationProject(self):
		'''
		Get Destination Project data reference.
		'''
		# Redo query for the same reason as in getSourceProject
		self.setDestinationProject(self.projectid)
		return self.destination_project

	def importProjectValueDependentData(self,dataclassname,value,search_alias):
		sinedon.setConfig('projectdata', db=self.source_dbname)
		print "Importing %s...." % (dataclassname)
		q = getattr(projectdata,dataclassname)()
		q[search_alias] = value
		results = self.research(q)
		self.publish(results)
		return results

	def importProjectDependentData(self,dataclassname):
		source_project = self.getSourceProject()
		return self.importProjectValueDependentData(dataclassname,source_project,'project')

	def importProject(self):
		print "Importing project...."
		projectdata = self.getSourceProject()

		sinedon.setConfig('projectdata', db=self.destination_dbname)
		projectdata.insert(force=False,archive=True)
		projectdata = self.getDestinationProject()

		if not projectdata:
			self.escape("Session Not Inserted Successfully")
			return

	def importPrivileges(self):
		print "Importing privileges...."
		q	= projectdata.privileges()
		results = self.research(q)
		self.publish(results)
		
	def importProjectExperiments(self):
		projectexperiments = self.importProjectDependentData('projectexperiments')
		sessionids = []
		# There are cases without session alias
		for p in projectexperiments:
			if p['session'] is None:
				print ' projectexperiment id %d has no session reference' % p.dbid
				continue
			sessionids.append(p['session'].dbid)
		self.importShareExperiments(sessionids)

	def importProjectOwners(self):
		self.importProjectDependentData('projectowners')

	def importProcessingDB(self):
		self.importProjectDependentData('processingdb')

	def importLeginonDependentData(self,project_classname, leginon_classname, leginon_alias):
		dataclassname = project_classname

		# Work around leginondata can not be map properly when projectdata is queried for import
		q = getattr(leginondata,leginon_classname)()
		results = self.research(q)
		leginon_ids = map((lambda x: x.dbid),results)
		self.importLeginonValueDependentData(project_classname, leginon_ids, leginon_alias)

	def importLeginonValueDependentData(self,project_classname, leginon_ids, leginon_alias):
		print "Importing %s...." % (project_classname)
		q = getattr(projectdata,project_classname)()
		results = self.research(q)
		for r in results:
			if r[leginon_alias] and r[leginon_alias].dbid in leginon_ids:
				try:
					self.publish([r,])
				except:
					open('error.log','a')
					f.write('%s,%d,%s,%d\n' %(project_classname,r.dbid,leginon_alias,r[leginon_alias].dbid))
					f.close()
	def importUserDetails(self):
		self.importLeginonDependentData('userdetails', 'UserData', 'user')

	def importShareExperiments(self,expids):
		self.importLeginonValueDependentData('shareexperiments',expids,'experiment')

	def importInstall(self):
		print "Importing Installation Log...."
		source_dbinfo = dbconfig.getConfig('projectdata')
		destination_dbinfo = dbconfig.getConfig('importdata')
		q = 'select * from install where 1;'
		results = directq.complexMysqlQuery('projectdata',q)

		q = 'select * from install where 1;'
		imported_results = directq.complexMysqlQuery('importdata',q)

		for row in results:
			keys = row.keys()
			values = map((lambda x: row[x]),keys)
			if not imported_results:
				keystring = '`'+'`,`'.join(keys)+'`'
				valuestring = "'"+"','".join(values)+"'"
				q = "INSERT into `install` (%s) VALUES (%s)" % (keystring, valuestring)
				directq.complexMysqlQuery('importdata',q)
			else:
				q = "UPDATE `install` SET `value` = '%s' where `install`.`key` = '%s';" % (row['value'],row['key'])
				directq.complexMysqlQuery('importdata',q)

	def run(self):
		'''
		STEP 1: 
		import project and map basic information about it
		'''
		self.importProject()
		self.importPrivileges()
		self.importProjectExperiments()
		self.importProcessingDB()
		self.importProjectOwners()
		self.importUserDetails()
		self.importInstall()
		self.reset()
		print ''

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 2:
		print "Usage: python archive_projectdb.py <project id number>"
		print ""
		print "sinedon.cfg should include a module"
		print "[importdata]"
		print "db: writable_archive_database for projectdb"
		
		sys.exit()
	projectid = int(sys.argv[1])

	checkSinedon()
	app = ProjectArchiver(projectid)
	app.run()
