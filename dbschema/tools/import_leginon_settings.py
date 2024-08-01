#!/usr/bin/env python
import os
import sys
import json
import time

from leginon import leginondata

ref_class_alias_dict = {
'target grouping': leginondata.TargetGroupingSettingsData,
'lpf': leginondata.LowPassFilterSettingsData,
'blobs': leginondata.BlobFinderSettingsData,
'template lpf': leginondata.LowPassFilterSettingsData,
'edge lpf': leginondata.LowPassFilterSettingsData,
}
ignored_refs = ['camera settings',]

class DataJsonLoader(object):
	def __init__(self):
		self.alldata = []

	def makequery(self,classname,kwargs):
		'''
		Make SQL query of leginondata from class name and keyword arguments.
		'''
		underline_exceptions = ['process_obj_thickness',]
		q = getattr(leginondata,classname)()
		for key in list(kwargs.keys()):
			if key not in underline_exceptions:
				# leginondata keys almost never contains '_'
				realkey = key.replace('_',' ')
			else:
				realkey = key
			if type(kwargs[key]) == type([]):
				if len(kwargs[key]) > 0:
					if type(kwargs[key][0]) == type([]):
						# json export saves coordinate tuple as list.  Need to change back in import
						kwargs[key] = list(map((lambda x: tuple(x)),kwargs[key]))
			if realkey not in list(q.keys()):
				print(('missing key %s' % (realkey)))
				continue
			if key in list(ref_class_alias_dict.keys()):
				ref_class = ref_class_alias_dict[realkey]
				values = self._insertQuery(self.makequery(ref_class.__name__,kwargs[key]))
			elif key in ignored_refs:
				print(('ignore %s' % key))
				continue
			else:
				values = kwargs[key]
			q[realkey] = values
		return q

	def readJsonFile(self,filename='test.json'):
		f =open(filename,'r')
		self.alldata = json.loads(f.read())

class SettingsJsonLoader(DataJsonLoader):
	'''
	Import Settings for a particular Application
	'''
	def __init__(self, applicationname):
		super(SettingsJsonLoader,self).__init__()
		self.setJsonFilename(applicationname)
		self.setNewSession(applicationname)

	def getAdministratorUser(self):
		try:
			return leginondata.UserData(username='administrator').query()[0]
		except:
			print("Can not find administrator user, Aborting")
			sys.exit(1)

	def setNewSession(self,applicationname):
		adminuser = self.getAdministratorUser()
		timename = time.strftime('%Y%m%d%H%M%S', time.localtime())
		sessionname = 'importsettings%s' % (timename)
		q = leginondata.SessionData(name=sessionname,user=adminuser)
		q['comment'] = 'import settings for %s' % (applicationname,)
		q['hidden'] = True
		q.insert()
		# q becomes the data once inserted
		self.session = q

	def getSession(self):
		return self.session

	def setJsonFilename(self,applicationname):
		if applicationname.endswith('.json'):
			self.jsonfile = applicationname
			return
		from leginon import version
		leginondir = version.getInstalledLocation()
		jsonpath = os.path.join(leginondir,'applications',applicationname+'_Settings.json')
		while not os.path.isfile(jsonpath):
			jsonpath = input("Can not find the file from default path, Please specify: ")
		self.jsonfile = jsonpath

	def importSettings(self):
		for settings in self.alldata:
			classname = list(settings.keys())[0]
			print(('inserting %s' % classname))
			try:
				q = self.makequery(classname, settings[classname])
				self._insertQuery(q)
			except Exception as e:
				print(('Error in ',classname, settings[classname],q))
				raise

	def _insertQuery(self, q):
			if 'session' in list(q.keys()):
				session = self.getSession()
				q['session'] = session
			if 'template filename' in list(q.keys()):
				q['template filename'] = ''
			# need to be the administrator default
			if 'isdefault' in list(q.keys()):
				q['isdefault'] = True
			# force to become the current default settings
			q.insert(force=True)
			return q

	def run(self):
		self.readJsonFile(self.jsonfile)
		self.importSettings()

if  __name__ == '__main__':
	if len(sys.argv) != 2:
		print("Usage: python import_leginon_settings.py <applicationname or json filepath>")
		sys.exit()

	applicationname = sys.argv[1]
	app = SettingsJsonLoader(applicationname)
	app.run()
