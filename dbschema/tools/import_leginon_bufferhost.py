#!/usr/bin/env python
import sys
import os

from leginon import leginondata, session, leginonconfig
from pyami import jsonfun, mrc, fileutil
'''
	This program creates sql statement and insert the bufferhost
	into leginon database of dest_database_host based on the existing
	bufferhost previously exported.  The dest_database_host is in sinedon.cfg
	Usage: import_leginon_bufferhost.py dest_database_hostname camera_bufferhost.json
	Requirements: InstrumentData
'''

def convertStringToSQL(value):
	if value is None:
		return 'Null'
	else:
		return "'"+value+"'"

class BufferHostJsonLoader(jsonfun.DataJsonLoader):
	def __init__(self,params):
		cam_hostname, camera_name = self.validateInput(params)
		print((cam_hostname, camera_name))
		super(BufferHostJsonLoader,self).__init__(leginondata)
		self.data = {}
		self.setSessionData()
		self.ccddata = self.getCameraInstrumentData(cam_hostname,camera_name)
		self.data['buffer host'] = None

	def addKnownData(self, q):
		if 'ccdcamera' in list(q.keys()):
			q['ccdcamera'] = self.ccddata
		q['session'] = self.session
		return q

	def insertClass(self, classname, datadict):
		if datadict is None:
			return None
		datadict = self.addKnownData(datadict)
		q = self.makequery(classname,datadict)
		q.insert(force=True)
		return q

	def insertAllData(self):
		for datadict in self.alldata:
			self.data['buffer host'] = self.insertClass('BufferHostData', datadict['BufferHostData'])

	def validateInput(self, params):
		if len(params) != 3:
			print("Usage import_leginon_bufferhost.py database_hostname camera_bufferhost_json_file")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if not os.path.exists(params[2]):
			raise ValueError('can not find %s to import' % params[2])
		self.jsonfile = params[2]
		digicam_key = self.jsonfile.split('bufferhost_')[-1].split('.json')[0]
		cam_host, cameraname = digicam_key.split('+')
		return cam_host, cameraname

	def getCameraInstrumentData(self, hostname,camname):
		results = leginondata.InstrumentData(hostname=hostname,name=camname).query(results=1)
		if not results:
			print("ERROR: incorrect hostname....")
			r = leginondata.InstrumentData(name=camname).query(results=1)
			if r:
				print(("  Try rename the json file to %s+%s.json instead to match camera host" % (r[0]['hostname'], camname)))
			else:
				print(("  No %s camera found" % camname))
			sys.exit()

		cam = results[0]
		return cam

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
			q['name']='bufferimport'
			q['comment'] = 'import bufferhost from json'
			# insert as a hidden session.
			q['hidden'] = True
			q.insert()
			self.session = q

	def printQuery(self, q):
		print(q)
		return

	def run(self):
		self.readJsonFile(self.jsonfile)
		self.insertAllData()

	def close(self, status):
		input('hit enter when ready to quit')
		if status:
			print("Exit with Error")
			sys.exit(1)

if __name__=='__main__':
	app = BufferHostJsonLoader(sys.argv)
	app.run()
	 
