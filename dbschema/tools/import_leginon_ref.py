#!/usr/bin/env python
import sys
import os

from leginon import leginondata, session, leginonconfig
from pyami import jsonfun, mrc, fileutil
'''
	This program creates sql statement and insert the references
	into leginon database of dest_database_host based on the existing
	references previously exported.  The dest_database_host is in sinedon.cfg
	Usage: import_leginon_ref.py dest_database_hostname tem_camera_ref.json
	Requirements: InstrumentData
'''

def convertStringToSQL(value):
	if value is None:
		return 'Null'
	else:
		return "'"+value+"'"

class ReferenceJsonLoader(jsonfun.DataJsonLoader):
	def __init__(self,params):
		tem_hostname, tem_name, cam_hostname, camera_name = self.validateInput(params)
		print((tem_hostname, tem_name))
		super(ReferenceJsonLoader,self).__init__(leginondata)
		self.data = {}
		self.setSessionData()
		self.ccddata = self.getCameraInstrumentData(cam_hostname,camera_name)
		self.temdata = self.getTemInstrumentData(tem_hostname,tem_name)
		self.data['camera'] = None
		self.data['scope'] = None
		self.data['corrector plan'] = None
		self.data['bright'] = None
		self.data['dark'] = None

	def addKnownData(self, q):
		if 'ccdcamera' in list(q.keys()):
			q['ccdcamera'] = self.ccddata
		if 'tem' in list(q.keys()):
			q['tem'] = self.temdata
		q['session'] = self.session
		for k in list(self.data.keys()):
			# don't want to associate corrector plan with others
			if k in list(q.keys()) and k not in ('corrector plan',):
				q[k] = self.data[k]
		if 'image' in list(q.keys()) and 'filename' in list(q.keys()):
			mrc_name = q['filename']+'.mrc'
			if not os.path.exists(mrc_name):
				raise ValueError('%s does not exist.' % mrc_name)
			q['image'] = mrc.read(mrc_name)
		return q

	def insertClass(self, classname, datadict):
		if datadict is None:
			return None
		datadict = self.addKnownData(datadict)
		q = self.makequery(classname,datadict)
		if 'Plan' in classname:
			# JsonLoader treats list of list as array. convert to lists here.
			for name in ('bad_pixels','bad_rows','bad_cols'):
				if hasattr(datadict[name],'tolist'):
					datalist = datadict[name].tolist()
				else:
					# behavior not consistent.  Cover the case we get list here.
					datalist = datadict[name]
				q[name] = datalist
		info = 'inserting  %s ' % (classname,)
		if 'filename' in list(datadict.keys()):
			info += 'saving %dx%d %s.mrc in %s' % (datadict['camera']['dimension']['x'],datadict['camera']['dimension']['y'],datadict['filename'], self.session['name'])
		print(info)
		# This is a forced insert so it is the most recent record
		q.insert(force=False)
		return q

	def insertAllData(self):
		for datadict in self.alldata:
			self.data = {}
			if 'NormImageData' in list(datadict.keys()):
				self.processNormImageData(datadict)
			if 'CorrectorPlanData' in list(datadict.keys()):
				self.processCorrectorPlanData(datadict)

	def processNormImageData(self, datadict):
		# processing  NormImageData
		classname = 'NormImageData'
		kwargs = datadict[classname]
		# process camdata, scopedata
		# export does not go further than child so the reference to InstrumentData
		# is not in the keys and the import script won't insert if no key
		# add instrument as key
		kwargs['camera']['ccdcamera'] = None
		self.data['camera'] = self.insertClass('CameraEMData', kwargs['camera'])
		# add instrument as key
		kwargs['scope']['tem'] = None
		self.data['scope'] = self.insertClass('ScopeEMData', kwargs['scope'])
		if kwargs['dark']:
			kwargs['dark']['image'] = None
			self.data['dark'] = self.insertClass('DarkImageData', kwargs['dark'])
		if kwargs['bright']:
			kwargs['bright']['image'] = None
			self.data['bright'] = self.insertClass('BrightImageData', kwargs['bright'])
		self.data['norm'] = self.insertClass('NormImageData', kwargs)

	def processCorrectorPlanData(self, datadict):
			# processing  CorrectorPlanData
			classname = 'CorrectorPlanData'
			if classname in list(datadict.keys()):
				kwargs = datadict[classname]
				# add instrument as key
				kwargs['camera']['ccdcamera'] = None
				self.data['camera'] = self.insertClass('CameraEMData', kwargs['camera'])
				self.data['corrector plan'] = self.insertClass('CorrectorPlanData', kwargs)

	def validateInput(self, params):
		if len(params) != 3:
			print("Usage import_leginon_ref.py database_hostname camera_ref_json_file")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if not os.path.exists(params[2]):
			raise ValueError('can not find %s to import' % params[2])
		self.jsonfile = params[2]
		digicam_key = self.jsonfile.split('ref_')[-1].split('.json')[0]
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
				print(("  No %s camera found" % camname))
			sys.exit()

		cam = results[0]
		return cam

	def getTemsByHostAndName(self, tem_hostname, tem_name):
		results = leginondata.InstrumentData(hostname=tem_hostname, name=tem_name).query()
		all_tems = []
		for r in results:
			if r['cs']:
				all_tems.append(r)
		return all_tems

	def getTemInstrumentData(self, tem_hostname, tem_name):
		all_tems = self.getTemsByHostAndName(tem_hostname,tem_name)
		if len(all_tems) == 1:
			return all_tems[0]
		print((list(map((lambda x: x['hostname']),all_tems))))
		temq = leginondata.InstrumentData(hostname=tem_hostname, name=tem_name)
		r = leginondata.PixelSizeCalibrationData(tem=temq, ccdcamera=self.ccddata).query(results=1)
		ptemid = None # tem with pixel calibration is checked first.
		if r:
			t = r[0]['tem']
			answer = input(' Is %s %s the tem to import ? Y/y/N/n ' % (t['hostname'], t['name']))
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
			answer = (input(' Is %s %s the tem to import ? Y/y/N/n ' % (t['hostname'], t['name']))
			if answer.lower() == 'y':
				return t
		print("  No tem found")
		sys.exit()

	def setSessionData(self):
		# find administrator user
		ur = leginondata.UserData(username='administrator').query()
		if ur:
			admin_user = ur[0]
		else:
			# do not process without administrator.
			print(" Need administrator user to import")
			self.close(True)
		try:
			self.session = session.createReferenceSession(admin_user, None)
		except Exception as e:
			raise
			print(("Error setting session: %s" % (e)))
		fileutil.mkdirs(self.session['image path'])

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
	app = ReferenceJsonLoader(sys.argv)
	app.run()
	 
