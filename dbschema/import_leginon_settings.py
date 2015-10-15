#!/usr/bin/env python
import os
import sys
import json
import time

from leginon import leginondata

class DataJsonLoader(object):
	def __init__(self):
		self.alldata = []

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
			print "Can not find administrator user, Aborting"
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
		from leginon import version
		leginondir = version.getInstalledLocation()
		jsonpath = os.path.join(leginondir,'applications',applicationname+'_Settings.json')
		while not os.path.isfile(jsonpath):
			jsonpath = raw_input("Can not find the file from default path, Please specify: ")
		self.jsonfile = jsonpath

	def importSettings(self):
		for settings in self.alldata:
			classname = settings.keys()[0]
			print 'inserting %s' % classname
			q = self.makequery(classname, settings[classname])
			if 'session' in q.keys():
				session = self.getSession()
				q['session'] = session
			if 'template filename' in q.keys():
				q['template filename'] = ''
			q.insert()

	def run(self):
		self.readJsonFile(self.jsonfile)
		self.importSettings()

if  __name__ == '__main__':
	if len(sys.argv) != 2:
		print "Usage: python import_leginon_settings.py <applicationname>"
		sys.exit()

	applicationname = sys.argv[1]
	app = SettingsJsonLoader(applicationname)
	app.run()
