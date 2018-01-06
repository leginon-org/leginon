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
		Query results from source database. Sorted by entry time. Newest fist
		'''
		if most_recent:
			r = q.query(results=1)
			if r:
				return r
		else:
			r = q.query()
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
						# not to include data reference
						pass
					else:
						data[k] = r[k]
			self.alldata.append({classname:data})

	def resetData(self):
		self.alldata = []

	def writeJsonFile(self,filename='test.json'):
		print 'Writing to %s' % filename
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
		self.setNodeNamePrefix(None)

	def setSession(self,sessionname):
		r = leginondata.SessionData(name=sessionname).query()
		if not r:
			raise ValueError('Session name %s not found' % sessionname)
		self.session = r[0]

	def setNodeNamePrefix(self,nodename=None):
		self.node_name_prefix = nodename

	def getSession(self):
		'''
		Get Session data reference.
		'''
		return self.session

	def getPresets(self):
		'''
		Get most recent presets of the session by tem and ccdcamera
		'''
		source_session = self.getSession()
		q = leginondata.PresetData(session=source_session)
		presets = self.research(q)
		all_presets = {}
		all_digicam_presets = {}
		for p in presets:
			pname = p['name']
			if pname not in all_presets.keys() and '-' not in pname:
				all_presets[pname] = p
				digicam_name = p['ccdcamera']['name']
				digicam_hostname = p['ccdcamera']['hostname']
				digi_key = digicam_hostname+'_'+digicam_name
				digi_key = '%s+%s+%s' % (p['tem']['name'],digicam_hostname,digicam_name)
				if digi_key not in all_digicam_presets.keys():
					all_digicam_presets[digi_key] = []
				all_digicam_presets[digi_key].append(p)
		return all_digicam_presets

	def exportPresets(self):
		all_digicam_presets = self.getPresets()
		for k in all_digicam_presets.keys():
			self.resetData()
			presets = all_digicam_presets[k]
			self.publish(presets)
			self.writeJsonFile('preset_'+k+'.json')

	def run(self, appname=None):
		source_session = self.getSession()
		print "****Session %s ****" % (source_session['name'])
		self.exportPresets()
		print ''

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print "Usage: python export_leginon_settings.py <sessionname> <optional partial application name> <optional node name prefix>"
		sys.exit()
	sessionname = sys.argv[1]
	if len(sys.argv) >= 3:
		appname = sys.argv[2]
	else:
		appname = None
	if len(sys.argv) >= 4:
		nodename = sys.argv[3]
	else:
		nodename = None
	app = SettingsJsonMaker(sessionname)
	app.setNodeNamePrefix(nodename)
	app.run(appname)
