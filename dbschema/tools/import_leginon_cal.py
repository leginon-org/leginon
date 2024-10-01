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
		tem_host, tem_name, cam_hostname, camera_name = self.validateInput(params)
		super(CalibrationJsonLoader,self).__init__(leginondata)
		self.cameradata = self.getCameraInstrumentData(cam_hostname,camera_name)
		self.temdata = self.getTemInstrumentData(tem_host,tem_name)
		self.setProjectionSubModeOrder()
		self.setSessionData()

	def setProjectionSubModeOrder(self):
		# all submode names
		sub_mode_order = ['LM','Mi','SA','Mh','D'] # FEI
		sub_mode_order.extend(['lowmag','mag1']) # JEOL
		sub_mode_order.extend(['mode0','mode1']) # SimTEM
		sub_mode_order.extend(['LowMag','Zoom-1']) # HT7800
		self.sub_mode_order = sub_mode_order

	def insertAllData(self):
		for datadict in self.alldata:
			classname = list(datadict.keys())[0]
			kwargs = datadict[classname]
			q = self.makequery(classname,kwargs)
			if 'ccdcamera' in list(q.keys()):
				q['ccdcamera'] = self.cameradata
			if 'tem' in list(q.keys()):
				q['tem'] = self.temdata
			checkq = q.copy()
			if 'session' in list(q.keys()):
				q['session'] = self.session
			if 'vectors' in list(q.keys()):
				# convert 2 1-D array to list of list
				q['vectors'] = (q['vectors'][0].tolist(),q['vectors'][1].tolist())
			if classname == 'ProjectionSubModeMappingData':
				q['magnification list'] = self.maglistdata
			# This is a forced insert so it is the most recent record
			q.insert(force=True)
			print(('insert %s dbid=%d' % (classname, q.dbid)))

	def validateInput(self, params):
		if len(params) != 3:
			print("Usage import_leginon_cal.py database_hostname camera_cal_json_file")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if not os.path.exists(params[2]):
			raise ValueError('can not find %s to import' % params[2])
		self.jsonfile = params[2]
		digicam_key = '_'.join(self.jsonfile.split('cal_')[1:]).split('.json')[0]
		temhost, temname, cam_host, cameraname = digicam_key.split('+')
		return temhost, temname, cam_host, cameraname

	def getCameraInstrumentData(self, hostname,camname):
		results = leginondata.InstrumentData(hostname=hostname,name=camname).query(results=1)
		if not results:
			print("ERROR: incorrect hostname....")
			r = leginondata.InstrumentData(name=camname).query(results=1)
			if r:
				print(("  Try rename the json file to %s+%s.json instead to match camera host" % (r[0]['hostname'], camname)))
			else:
				msg = "  No %s camera found" % camname
				raise KeyError(msg)

		cam = results[0]
		return cam

	def getTemsByName(self, tem_name):
		results = leginondata.InstrumentData(name=tem_name).query()
		all_tems = []
		for r in results:
			if r['cs']:
				all_tems.append(r)
		return all_tems

	def getTemInstrumentData(self, tem_host, tem_name):
		all_tems = self.getTemsByName(tem_name)
		if len(all_tems) == 1:
			return all_tems[0]
		print((list(map((lambda x: x['hostname']),all_tems))))
		temq = leginondata.InstrumentData(hostname=tem_host,name=tem_name)
		r = temq.query()
		#ptemid = None # tem with pixel calibration is checked first.
		if len(r)==1:
			t = r[0]
			return t
		msg = "  %d tem found matching host %s named %s" % (len(r),tem_host, tem_name) 
		raise KeyError(msg)

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

	def setMagnificationsData(self):
		# see if there is a list from import_leginon_instruments.py
		r = leginondata.MagnificationsData(instrument=self.temdata).query(results=1)
		if r:
			return r[0]
		mags = []
		modes = {}
		for datadict in self.alldata:
			classname = list(datadict.keys())[0]
			kwargs = datadict[classname]
			if classname == 'ProjectionSubModeMappingData':
				if kwargs['name'] not in list(modes.keys()):
					modes[kwargs['name']]=[]
				# assumes that projection submode mapping was inserted in the right order.
				modes[kwargs['name']].append(int(kwargs['magnification']))
		for m in self.sub_mode_order:
			if m in list(modes.keys()):
				mags.extend(modes[m])
		print(('magnifications', mags))
		q = leginondata.MagnificationsData(instrument=self.temdata,magnifications=mags)
		q.insert()
		return q

	def printQuery(self, q):
		print(q)
		return

	def run(self):
		self.readJsonFile(self.jsonfile)
		self.maglistdata = self.setMagnificationsData()
		self.insertAllData()

	def close(self, status):
		if status:
			print("Exit with Error")
			sys.exit(1)

if __name__=='__main__':
	try:
		app = CalibrationJsonLoader(sys.argv)
	except Exception as e:
		print(('ERROR: %s' % e))
		sys.exit(1)
	app.run()
	 
