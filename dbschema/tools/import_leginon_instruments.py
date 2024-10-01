#!/usr/bin/env python
import sys
import os
import glob

from leginon import leginondata
from pyami import jsonfun
'''
	This program creates sql statements and insert instrument, magnifications,
	and  clients into leginon database based on json files.
	Usage: import_leginon_instruments.py database_hostname
	Requirements: instruments.json, mag_(tem_hostname)+(tem_name).json
	Optional: instrument_clients.json
'''
pixelsize_scale = 1

def convertStringToSQL(value):
	if value is None:
		return 'Null'
	else:
		return "'"+value+"'"

class ClientJsonLoader(jsonfun.DataJsonLoader):
	def __init__(self,params):
		self.validateInput(params)
		super(ClientJsonLoader,self).__init__(leginondata)
		self.setSessionData()

	def insertAllData(self, force=True):
		for datadict in self.alldata:
			classname = list(datadict.keys())[0]
			kwargs = datadict[classname]
			q = self.makequery(classname,kwargs)
			if 'ccdcamera' in list(q.keys()):
				q['ccdcamera'] = self.cameradata
			if 'tem' in list(q.keys()):
				q['tem'] = self.temdata
			# MagnificationsData
			if 'instrument' in list(q.keys()):
				q['instrument'] = self.temdata
			checkq = q.copy()
			if 'session' in list(q.keys()):
				q['session'] = self.session
			if 'vectors' in list(q.keys()):
				# convert 2 1-D array to list of list
				q['vectors'] = (q['vectors'][0].tolist(),q['vectors'][1].tolist())
			# This may be a forced insert so it is the most recent record
			q.insert(force=force)
			print(('insert %s dbid=%d' % (classname, q.dbid)))

	def validateInput(self, params):
		if len(params) != 2:
			print("Usage import_leginon_instruments.py database_hostname")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if not os.path.exists('instruments.json'):
			raise ValueError('can not find %s to import' % 'instruments.json')
		self.tem_jsonfiles = glob.glob('mags_*.json')
		self.simple_jsonfiles = ['instruments.json','instrument_clients.json']
		return

	def setSessionData(self):
		# find administrator user
		ur = leginondata.UserData(username='administrator').query()
		if ur:
			admin_user = ur[0]
		else:
			# do not process without administrator.
			print(" Need administrator user to import")
			self.close(True)
		q = leginondata.SessionData(user=admin_user)
		r = q.query(results=1)
		if r:
			# use any existing session.
			self.session = r[0]
		else:
			q['name']='calimport'
			q['comment'] = 'import calibrations from json'
			# insert as a hidden session.
			q['hidden'] = True
			q.insert()
			self.session = q

	def readMagsJsonFile(self, filename):
		hostname, temtail = '_'.join(filename.split('_')[1:]).split('+')
		temname = temtail[:-5]
		results = leginondata.InstrumentData(hostname=hostname,name=temname).query()
		if not results:
			raise ValueError('%s on %s is not in the database' % (temname, hostname))
		self.readJsonFile(filename)
		self.temdata = results[0]
		print((results[0].dbid, hostname, temname))

	def printQuery(self, q):
		print(q)
		return

	def run(self):
		for jsonfile in self.simple_jsonfiles:
			self.readJsonFile(jsonfile)
			# Not to force insert instruments
			self.insertAllData(False)
		for jsonfile in self.tem_jsonfiles:
			self.readMagsJsonFile(jsonfile)
			self.insertAllData()

	def close(self, status):
		if status:
			print("Exit with Error")
			sys.exit(1)

if __name__=='__main__':
	app = ClientJsonLoader(sys.argv)
	app.run()
	 
