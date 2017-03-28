import os
import sys
import json
import sinedon
from sinedon import dbconfig
from leginon import leginondata
import time

class DataJsonMaker(object):
	def __init__(self):
		self.alldata = []
		self.ignorelist = ['session',]
		pass

	def makequery(self,classname,kwargs):
		'''
		Make SQL query of leginondata from class name and keyword arguments.
		'''
		q = getattr(leginondata,classname)()
		for key in kwargs.keys():
			# leginondata keys never contains '_'
			realkey = key.replace('_',' ')
			q[realkey] = kwargs[key]
		return q

	def makeTimeStringFromTimeStamp(self,timestamp):
		t = timestamp
		return '%04d%02d%02d%02d%02d%02d' % (t.year,t.month,t.day,t.hour,t.minute,t.second)

	def research(self,q,most_recent=False):
		'''
		Query results from source database. Sorted by entry time. Oldest fist
		'''
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
		Publish query results to xml file
		'''
		if not results:
			return
			
		for r in results:
			classname = r.__class__.__name__
			data = {}
			for k in r.keys():
				if k not in self.ignorelist:
					if hasattr(r[k],'dbid'):
						print "ignored ",k
					else:
						data[k] = r[k]
			self.alldata.append({classname:data})

	def writeJsonFile(self,filename='test.json'):
		jstr = json.dumps(self.alldata, indent=2, separators=(',',':'))
		f = open(filename,'w')
		f.write(jstr)
		f.close()

class SettingsJsonMaker(DataJsonMaker):
	'''
	Export Settings used in a Session as xml file
	'''
	def __init__(self,sessionname):
		super(SettingsJsonMaker,self).__init__()
		self.setSession(sessionname)
		self.bad_settings_class = []

	def setSession(self,sessionname):
		r = leginondata.SessionData(name=sessionname).query()
		if not r:
			raise ValueError('Session name %s not found' % sessionname)
		self.session = r[0]

	def getSession(self):
		'''
		Get Session data reference.
		'''
		return self.session

	def researchSettings(self, classname,**kwargs):
		'''
		Find Legion Settings that may be used by the source session.
		This could be those in the session or the last one in a previous
		session by the user.
		'''
		sessiondata = self.getSession()
		t = sessiondata.timestamp
		sessiontime = self.makeTimeStringFromTimeStamp(t)
		# search in the session
		q = self.makequery(classname,kwargs)
		q['session'] = self.session
		r1 = q.query(results=1)
		if r1:
			return r1
		# search by user
		found_by_user = False
		if sessiondata['user'] and sessiondata.dbid:
			sessionq = leginondata.SessionData(user=sessiondata['user'])
			q = self.makequery(classname,kwargs)
			q['session'] = sessionq
			r2 = q.query(results=1,timelimit='19000000000000\t%s' % (sessiontime,))
			if r2:
				return r2
		# search by isdefault
		if found_by_user == False:
			q = self.makequery(classname,kwargs)
			q['isdefault'] = True
			r2 = q.query(results=1,timelimit='19000000000000\t%s' % (sessiontime,))
			if r2:
				return r2

	def importFocusSequenceSettings(self, allalias):
		print 'importing Focus Sequence Settings....'
		if 'Focuser' not in allalias.keys():
			return
		sequence_names = []
		focuser_aliases = allalias['Focuser']
		focuser_aliases.sort()
		for node_name in (focuser_aliases):
			results = self.researchSettings('FocusSequenceData',node_name=node_name)
			self.publish(results)
			for r in results:
				sequence = r['sequence']
				for s in sequence:
					if s not in sequence_names:
						# only keep the first of the multiple settings in the session
						sequence_names.append(s)
		for node_name in (allalias['Focuser']):
			for seq_name in sequence_names:
				results = self.researchSettings('FocusSettingData',node_name=node_name,name=seq_name)
				self.publish(results)

	def importSettingsByClassAndAlias(self,allalias):
		unusual_settingsnames = {
				'AlignZeroLossPeak':None,
				'MeasureDose':None,
				'IntensityCalibrator':None,
				'AutoNitrogenFiller':'AutoFillerSettingsData',
				'EM':None,
				'FileNames':'ImageProcessorSettingsData',
		}
		aliaskeys = allalias.keys()
		aliaskeys.sort()
		for classname in aliaskeys:
			settingsname = classname+'SettingsData'
			if classname in unusual_settingsnames.keys():
				settingsname = unusual_settingsnames[classname]
			if not settingsname:
				continue
			if classname in aliaskeys:
				print 'importing %s Settings....' % (classname,)
				# allalias[classname] may have duplicates
				for node_name in (set(allalias[classname])):
					try:
						results = self.researchSettings(settingsname,name=node_name)
					except:
						if classname not in self.bad_settings_class:
							print 'ERROR: %s class node %s settings query failed' % (classname,node_name)
							self.bad_settings_class.append(classname)
					self.publish(results)
		# FocusSequence and FocusSettings needs a different importing method
		self.importFocusSequenceSettings(allalias)

	def importSettings(self,appname=None):
		'''
		Import Settings based on launched applications of the session
		'''
		source_session = self.getSession()
		q = leginondata.LaunchedApplicationData(session=source_session)
		launched_apps = self.research(q)
		allalias = {}
		for appdata in map((lambda x: x['application']), launched_apps):
			if appname is not None and appname not in appdata['name']:
				# only export specified application name
				continue
			q = leginondata.NodeSpecData(application=appdata)
			results = self.research(q)
			for r in results:
				if r['class string'] not in allalias.keys():
					# initialize
					allalias[r['class string']] = []
				if r['alias'] not in allalias[r['class string']]:
					# only keep the first of the multiple settings in the session
					allalias[r['class string']].append(r['alias'])
		# import settings
		self.importSettingsByClassAndAlias(allalias)

	def run(self, appname=None):
		source_session = self.getSession()
		print "****Session %s ****" % (source_session['name'])
		self.importSettings(appname)
		self.writeJsonFile()
		print ''

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print "Usage: python export_leginon_settings.py <sessionname> <optional partial application name"
		sys.exit()
	sessionname = sys.argv[1]
	if len(sys.argv) == 3:
		appname = sys.argv[2]
	else:
		appname = None
	app = SettingsJsonMaker(sessionname)
	app.run(appname)
