#!/usr/bin/env python
import sys
import os

from leginon import leginondata
from pyami import jsonfun
'''
	This program creates sql statement and insert presets
	into leginon database of dest_database_host based on the json file
	Usage: import_leginon_presets.py dest_database_hostname tem_camera_preset_json_file
	Requirement: preset_(tem_name)+(camera_hostname)+(camera_name).json
'''
pixelsize_scale = 1

def convertStringToSQL(value):
	if value is None:
		return 'Null'
	else:
		return "'"+value+"'"

class CalibrationJsonLoader(jsonfun.DataJsonLoader):
	def __init__(self,params):
		tem_hostname, tem_name, cam_hostname, camera_name = self.validateInput(params)
		super(CalibrationJsonLoader,self).__init__(leginondata)
		self.cameradata = self.getCameraInstrumentData(cam_hostname,camera_name)
		self.temdata = self.getTemInstrumentData(tem_hostname, tem_name)
		self.session_name='preset-import-tem%dcam%d' % (self.temdata.dbid, self.cameradata.dbid)
		self.setSessionData()

	def insertAllData(self):
		for datadict in self.alldata:
			classname = list(datadict.keys())[0]
			kwargs = datadict[classname]
			q = self.makequery(classname,kwargs)
			print((self.cameradata))
			if 'ccdcamera' in list(q.keys()):
				q['ccdcamera'] = self.cameradata
			if 'tem' in list(q.keys()):
				q['tem'] = self.temdata
			checkq = q.copy()
			if 'session' in list(q.keys()):
				q['session'] = self.session
			# This is a forced insert so it is the most recent record
			q.insert(force=True)
			print(('insert %s dbid=%d' % (classname, q.dbid)))

	def validateInput(self, params):
		if len(params) != 3:
			print("Usage import_leginon_presets.py database_hostname tem_camera_presets_json_file")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if not os.path.exists(params[2]):
			raise ValueError('can not find %s to import' % params[2])
		self.jsonfile = params[2]
		digicam_key = self.jsonfile.split('preset_')[-1].split('.json')[0]
		tem_host, temname, cam_host, cameraname = digicam_key.split('+')
		return tem_host, temname, cam_host, cameraname

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
		print((cam.dbid))
		return cam

	def getTemInstrumentData(self, tem_host, tem_name):
		temq = leginondata.InstrumentData(hostname=tem_host, name=tem_name)
		r = leginondata.PixelSizeCalibrationData(tem=temq, ccdcamera=self.cameradata).query(results=1)
		if r:
			t = r[0]['tem']
			return t
		else:
			print("No tem/camera pair with pixel size calibration found")
			results = leginondata.InstrumentData().query()
			tems = []
			for r in results:
				if r['cs']:
					tems.append(r)
			for t in tems:
				answer = input(' Is %s %s the tem to import calibration ? Y/y/N/n' % (t['hostname'], t['name']))
				if answer.lower() == 'y':
					return t
			print("  No tem found")
			sys.exit()

	def isTemInSessionPreset(self, session):
		'''
		Check if the session uses the tem for this import.
		Leginon PresetsManager does not allow preset to be imported
		from a session with more than one tem.
		'''
		presets = leginondata.PresetData(session=session).query()
		for p in presets:
			if p['tem'] == self.temdata:
				return True
		return False

	def setSessionData(self):
		# find administrator user
		ur = leginondata.UserData(username='administrator').query()
		if ur:
			admin_user = ur[0]
		else:
			# do not process without administrator.
			print(" Need administrator user to import")
			self.close(True)
		q = leginondata.SessionData(user=admin_user, name=self.session_name)
		r = q.query(timelimit='-90 0:0:0') # twenty day limit
		if r and self.isTemInSessionPreset(r[0]):
			# use recent existing session.
			self.session = r[0]
		else:
			q = leginondata.SessionData(user=admin_user)
			# make unique name so it won't stop the insert since this is not forced.
			q['name']=self.session_name
			q['comment'] = 'import presets from json'
			q['hidden'] = True
			q.insert(force=True)
			self.session = q
		print(('Using Session %s to import' % self.session['name']))

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
	app = CalibrationJsonLoader(sys.argv)
	app.run()
	 
