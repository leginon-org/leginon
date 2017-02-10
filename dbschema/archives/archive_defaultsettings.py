import os
import sys
import sinedon
from sinedon import dbconfig
from leginon import leginondata
from leginon import projectdata
from leginon import correctorclient
from dbschema import archive_leginondb
import time

# set direct_query values
# exclude preset lable
excludelist = ()

class AdminUserArchiver(archive_leginondb.Archiver):
	def __init__(self):
		super(AdminUserArchiver,self).__init__()
		self.adminid = None

	def run(self):
		sinedon.setConfig('leginondata', db=self.source_dbname)
		userdata = leginondata.UserData(username='administrator').query()[0]
		self.publish([userdata,])
		self.adminid = userdata.dbid

	def getAdminId(self):
		return self.adminid

class SettingArchiver(archive_leginondb.Archiver):
	'''
	Archive all recent settings
	'''
	def __init__(self, sessionname):
		super(SettingArchiver,self).__init__()
		self.sessionname = sessionname
		self.setSourceSession(sessionname)
		self.setDestinationSession(sessionname)

	def researchSettings(self, classname,**kwargs):
		'''
		Find Legion Settings that may be used by the source session.
		This could be those in the session or the last one in a previous
		session by the user.
		'''
		if classname not in dir(leginondata):
			return []
		source_session = self.getSourceSession()
		t = source_session.timestamp
		sessiontime = self.makeTimeStringFromTimeStamp(t)
		# search in the session
		q = self.makequery(classname,kwargs)
		q['session'] = source_session
		r1 = q.query()
		# search by user
		found_by_user = False
		# query session again since for some reason it is mapped to destination
		source_session = self.getSourceSession()
		if source_session['user'] and source_session.dbid:
			sessionq = leginondata.SessionData(user=source_session['user'])
			q = self.makequery(classname,kwargs)
			q['session'] = sessionq
			r2 = q.query(results=1,timelimit='19000000000000\t%s' % (sessiontime,))
			if r2:
				r1.append(r2[0])
				found_by_user = True
		# search by isdefault
		if found_by_user == False:
			q = self.makequery(classname,kwargs)
			q['isdefault'] = True
			r2 = q.query(results=1,timelimit='19000000000000\tsessiontime')
			if r2:
				r1.append(r2[0])

		r1.reverse()
		return r1

	def setSourceSession(self, sessionname):
		sinedon.setConfig('leginondata', db=self.source_dbname)
		q = leginondata.SessionData(name=sessionname)
		self.source_session = self.research(q,most_recent=True)

	def getSourceSession(self):
		'''
		Get Source Session data reference.
		'''
		#This redo the query since the reference often get mapped to
		#the destination database for unknown reason after some queries.
		self.setSourceSession(self.sessionname)
		return self.source_session

	def setDestinationSession(self, sessionname):
		self.destination_session = None
		sinedon.setConfig('leginondata', db=self.destination_dbname)
		q = leginondata.SessionData(name=sessionname)
		r = q.query()
		if r:
			session = r[0]
			self.destination_session = session
		self.reset()

	def getDestinationSession(self):
		'''
		Get Destination Session data reference.
		'''
		# Redo query for the same reason as in getSourceSession
		self.setDestinationSession(self.sessionname)
		return self.destination_session

	def importSession(self, comment=''):
		print "Importing session...."
		session = self.getSourceSession()
		source_sessionid = session.dbid
		# change session description if needed
		if comment:
			self.replaceItem(session,'comment',comment)

		sinedon.setConfig('leginondata', db=self.destination_dbname)
		session.insert(force=False,archive=True)
		q = leginondata.SessionData()
		sessiondata = q.direct_query(session.dbid)

		if not sessiondata:
			self.escape("Session Not Inserted Successfully")
			return
		self.setDestinationSession(sessiondata)

	def importSessionDependentData(self,dataclassname):
		source_session = self.getSourceSession()
		print "Importing %s...." % (dataclassname[:-4])
		q = getattr(leginondata,dataclassname)(session=source_session)
		results = self.research(q)
		self.publish(results)

	def importFocusSequenceSettings(self, allalias):
		print 'importing Focus Sequence Settings....'
		if 'Focuser' not in allalias.keys():
			return
		sequence_names = []
		for node_name in (allalias['Focuser']):
			results = self.researchSettings('FocusSequenceData',node_name=node_name)
			self.publish(results[:1])
			for r in results:
				sequence = r['sequence']
				for s in sequence:
					if s not in sequence_names:
						sequence_names.append(s)
		for node_name in (allalias['Focuser']):
			for seq_name in sequence_names:
				results = self.researchSettings('FocusSettingData',node_name=node_name,name=seq_name)
				self.publish(results[:1])

	def importSettingsByClassAndAlias(self,allalias):
		unusual_settingsnames = {
				'AlignZeroLossPeak':None,
				'MeasureDose':None,
				'IntensityCalibrator':None,
				'AutoNitrogenFiller':'AutoFillerSettingsData',
				'EM':None,
				'FileNames':'ImageProcessorSettingsData',
		}
		for classname in allalias.keys():
			settingsname = classname+'SettingsData'
			if classname in unusual_settingsnames.keys():
				settingsname = unusual_settingsnames[classname]
			if not settingsname:
				continue
			if classname in allalias.keys():
				print 'importing %s Settings....' % (classname,)
				for node_name in (allalias[classname]):
					try:
						results = self.researchSettings(settingsname,name=node_name)
					except:
						raise
						print 'ERROR: %s class node %s settings query failed' % (classname,node_name)
					self.publish(results[:1])
		# FocusSequence and FocusSettings needs a different importing method
		self.importFocusSequenceSettings(allalias)

	def importRecentSettings(self):
		'''
		Import Settings based on recent applications
		'''
		# getSourceSession resets sinedon
		source_session = self.getSourceSession()
		q = leginondata.ApplicationData()
		all_apps = self.research(q)
		unique_apps = []
		allalias = {}
		for appdata in all_apps:
			if appdata['name'] in unique_apps:
				continue
			q = leginondata.NodeSpecData(application=appdata)
			results = self.research(q)
			for r in results:
				if r['class string'] not in allalias.keys():
					allalias[r['class string']] = []
				allalias[r['class string']].append(r['alias'])
			unique_apps.append(appdata['name'])
		# import settings
		self.importSettingsByClassAndAlias(allalias)

	def run(self):
		source_session = self.getSourceSession()
		print "****Session %s ****" % (source_session['name'])
		self.importRecentSettings()
		print ''

def archiveAdminUser():
	print "Importing Administrator User...."
	userarchiver = AdminUserArchiver()
	userarchiver.run()
	return userarchiver.getAdminId()

def archiveAdminSettings():
	'''
	Archive all users and sessions in the project identified by id number
	'''
	adminid = archiveAdminUser()

	if adminid is None:
		print "No administration user found, Abort"
		sys.exit(1)
	u = leginondata.UserData().direct_query(adminid)
	recent_session = leginondata.SessionData(user=u).query()[0]
	app = SettingArchiver(recent_session['name'])
	app.run()
	app = None

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 1:
		print "Usage: python archive_defaultsettings.py"
		print ""
		print "sinedon.cfg should include a module"
		print "[importdata]"
		print "db: writable_archive_database"
		
		sys.exit()

	archive_leginondb.checkSinedon()
	archiveAdminSettings()
