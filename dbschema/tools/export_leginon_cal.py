#!/usr/bin/env python
import sys
from leginon import leginondata
from pyami import jsonfun
'''
	This program export a json file required to insert calibrations
	into another leginon database, typically on a different host.
	It can be run as a daily calibration backup in case of database
	problem.
	Usage: export_leginon_cal.py source_database_hostname source_camera_hosthame camera_name
'''
pixelsize_scale = 1

class CalibrationJsonMaker(jsonfun.DataJsonMaker):
	def __init__(self,params):
		super(CalibrationJsonMaker,self).__init__(leginondata)
		try:
			self.validateInput(params)
		except ValueError, e:
			print "Error: %s" % e.message
			self.close(1)

	def validateInput(self, params):
		if len(params) != 4:
			print "Usage export_leginon_cal.py source_database_hostname source_camera_hosthame camera_name"
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		self.cam = self.getSourceCameraInstrumentData(params[2],params[3])
		self.tem = self.getSourceTemInstrumentData(self.cam)

	def getSourceCameraInstrumentData(self, from_hostname,from_camname):
		kwargs = {'hostname':from_hostname,'name':from_camname}
		q = self.makequery('InstrumentData',kwargs)
		result = self.research(q,True)
		if not result:
			print "ERROR: incorrect hostname...."
			r = leginondata.InstrumentData(name=from_camname).query(results=1)
			if r:
				raise ValueError("Try %s instead" % result['hostname'])
			else:
				raise ValueError("  No %s camera found" % from_camname)
			sys.exit()

		sourcecam = result
		return sourcecam

	def getSourceTemInstrumentData(self, sourcecam):
		'''
		Get the most recent TEM connected to the camera that has PixelSizeCalibration
		'''
		allcaldata = leginondata.PixelSizeCalibrationData(ccdcamera=sourcecam).query()
		if not allcaldata:
			raise ValueError('no tem linked with the camera')
		temids = []
		for c in allcaldata:
			if c['tem'].dbid not in temids:
				temids.append(c['tem'].dbid)
		for id in temids:
			tem = leginondata.InstrumentData().direct_query(id)
			answer = raw_input('Gather calibration associated with tem  %s on host %s ? (Y/y or N/n)' % (tem['name'], tem['hostname']))
			if answer.lower() in 'y':
				temdata = tem
				break
		try:		
			print "Using tem id=%d on %s named %s" % (temdata.dbid, temdata['hostname'], temdata['name'])
			return temdata
		except:
			raise ValueError('no tem selected with the camera')

	def getMags(self):
		magsdata = leginondata.MagnificationsData(instrument=self.tem).query(results=1)[0]
		return magsdata['magnifications']

	def printPixelSizeCalibrationQueries(self, mags):
		#PixelSizeCalibrationData
		for mag in mags:
			results = leginondata.PixelSizeCalibrationData(ccdcamera=self.cam,magnification=mag).query(results=1)
			if results:
				print 'Adding PixeSize at %dx = %.3e' % (mag, results[0]['pixelsize'])
				self.publish(results)

	def printStageModelCalibrationQueries(self, mags):
		#StageModelCalibrationData
		for axis in ('x','y'):
			results = leginondata.StageModelCalibrationData(tem=self.tem,ccdcamera=self.cam,axis=axis).query(results=1)
			if results:
				print 'StageModel', axis
				self.publish(results)

			for mag in mags:
				q = leginondata.StageModelMagCalibrationData(tem=self.tem, ccdcamera=self.cam,axis=axis,magnification=mag)
				results = q.query(results=1)
				if results:
					print 'StageModelMag', axis, mag
					self.publish(results)

	def printMatrixCalibrationQueries(self, mags, probe):
		for mag in mags:
			# MatrixCarlibationData
			for matrix_type in ('stage position','image shift','defocus','beam shift'):
				# stage position is not probe dependent
				if matrix_type == 'defocus' and probe is None:
					continue
				if matrix_type != 'defocus' and probe is not None:
					continue
				q = leginondata.MatrixCalibrationData(tem=self.tem, ccdcamera=self.cam,magnification=mag,type=matrix_type, probe=probe)
				results = q.query(results=1)
				if results:
					print 'Matrix', matrix_type, probe, mag
					self.publish(results)

	def run(self):
		mags = self.getMags()
		#print self.cam.dbid
		#print mags
		self.printPixelSizeCalibrationQueries(mags)
		self.printStageModelCalibrationQueries(mags)
		for p in (None,'micro','nano'):
			self.printMatrixCalibrationQueries(mags,p)
		json_filename = '%s+%s+%s.json' % (self.tem['name'],self.cam['hostname'],self.cam['name'])
		self.writeJsonFile(json_filename)

	def close(self, status=0):
		if status:
			print "Exit with Error"
			sys.exit(1)
		raw_input('hit enter when ready to quit')

if __name__=='__main__':
	app = CalibrationJsonMaker(sys.argv)
	app.run()
	app.close()
	 
