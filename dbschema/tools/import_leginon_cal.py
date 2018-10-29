#!/usr/bin/env python
import sys
import os

from leginon import leginondata
from pyami import jsonfun
'''
	This program creates sql statement and insert the calibrations
	into leginon database of dest_database_host based on the existing
	calibration on the source_database_host.  The latter is in sinedon.cfg
	Usage: import_leginon_cal.py source_database_hostname source_camera_hosthame camera_name
	Requirements: InstrumentData and MagnificationsData
'''
pixelsize_scale = 1

def convertStringToSQL(value):
	if value is None:
		return 'Null'
	else:
		return "'"+value+"'"

class CalibrationJsonLoader(jsonfun.DataJsonLoader):
	def __init__(self,params):
		tem_name, cam_hostname, camera_name = self.validateInput(params)
		super(CalibrationJsonLoader,self).__init__(leginondata)
		self.cameradata = self.getCameraInstrumentData(cam_hostname,camera_name)
		self.temdata = self.getTemInstrumentData(tem_name)
		self.setSessionData()

	def insertAllData(self):
		for datadict in self.alldata:
			classname = datadict.keys()[0]
			kwargs = datadict[classname]
			q = self.makequery(classname,kwargs)
			if 'ccdcamera' in q.keys():
				q['ccdcamera'] = self.cameradata
			if 'tem' in q.keys():
				q['tem'] = self.temdata
			checkq = q.copy()
			if 'session' in q.keys():
				q['session'] = self.session
			if 'vectors' in q.keys():
				# convert 2 1-D array to list of list
				q['vectors'] = (q['vectors'][0].tolist(),q['vectors'][1].tolist())
			if classname == 'ProjectionSubModeMappingData':
				q['magnification list'] = self.maglistdata
			# This is a forced insert so it is the most recent record
			q.insert(force=True)
			print 'insert %s dbid=%d' % (classname, q.dbid)

	def validateInput(self, params):
		if len(params) != 3:
			print "Usage import_leginon_cal.py database_hostname camera_cal_json_file"
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if not os.path.exists(params[2]):
			raise ValueError('can not find %s to import' % params[2])
		self.jsonfile = params[2]
		digicam_key = self.jsonfile.split('cal_')[-1].split('.json')[0]
		temname, cam_host, cameraname = digicam_key.split('+')
		return temname, cam_host, cameraname

	def getCameraInstrumentData(self, hostname,camname):
		results = leginondata.InstrumentData(hostname=hostname,name=camname).query(results=1)
		if not results:
			print "ERROR: incorrect hostname...."
			r = leginondata.InstrumentData(name=camname).query(results=1)
			if r:
				print "  Try rename the json file to %s+%s.json instead to match camera host" % (r[0]['hostname'], camname)
			else:
				print "  No %s camera found" % camname
			sys.exit()

		cam = results[0]
		return cam

	def getTemsByName(self, tem_name):
		results = leginondata.InstrumentData(name=tem_name).query()
		all_tems = []
		for r in results:
			if r['cs']:
				all_tems.append(r)
		return all_tems

	def getTemInstrumentData(self, tem_name):
		all_tems = self.getTemsByName(tem_name)
		if len(all_tems) == 1:
			return all_tems[0]
		print map((lambda x: x['hostname']),all_tems)
		temq = leginondata.InstrumentData(name=tem_name)
		r = leginondata.PixelSizeCalibrationData(tem=temq, ccdcamera=self.cameradata).query(results=1)
		ptemid = None # tem with pixel calibration is checked first.
		if r:
			t = r[0]['tem']
			answer = raw_input(' Is %s %s the tem to import calibration ? Y/y/N/n ' % (t['hostname'], t['name']))
			if answer.lower() == 'y':
				return t
			ptemid = t.dbid
		# check the rest
		other_tems = []
		for r in all_tems:
			if ptemid is None or ptemid!=r.dbid:
				other_tems.append(r)
		if len(other_tems) == 1:
			return other_tems[0]
		for t in other_tems:
			answer = raw_input(' Is %s %s the tem to import calibration ? Y/y/N/n ' % (t['hostname'], t['name']))
			if answer.lower() == 'y':
				return t
		print "  No tem found"
		sys.exit()

	def setSessionData(self):
		# find administrator user
		ur = leginondata.UserData(username='administrator').query()
		if ur:
			admin_user = ur[0]
		else:
			# do not process without administrator.
			print " Need administrator user to import"
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

	def setMagnificationsData(self):
		mags = []
		for datadict in self.alldata:
			classname = datadict.keys()[0]
			kwargs = datadict[classname]
			if classname == 'ProjectionSubModeMappingData':
				mags.append(float(kwargs['magnification']))
		mags.sort()
		print 'magnifications', mags
		q = leginondata.MagnificationsData(instrument=self.temdata,magnifications=mags)
		q.insert()
		return q

	def printQuery(self, q):
		print q
		return

	def run(self):
		self.readJsonFile(self.jsonfile)
		self.maglistdata = self.setMagnificationsData()
		self.insertAllData()

	def close(self, status):
		raw_input('hit enter when ready to quit')
		if status:
			print "Exit with Error"
			sys.exit(1)

if __name__=='__main__':
	app = CalibrationJsonLoader(sys.argv)
	app.run()
	 
