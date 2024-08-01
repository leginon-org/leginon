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
	def __init__(self,params, interactive=False):
		self.interactive = interactive
		super(CalibrationJsonMaker,self).__init__(leginondata)
		self.tem = None
		self.cam = None
		try:
			self.validateInput(params)
		except ValueError as e:
			print(("Error: %s" % e))
			if interactive:
				self.close(1)

	def validateInput(self, params):
		if len(params) < 4:
			print("Usage export_leginon_cal.py source_database_hostname source_camera_hosthame camera_name (source_tem_name)")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		self.cam = self.getSourceCameraInstrumentData(params[2],params[3])
		if len(params) > 4:
			tem_name = params[4]
		else:
			tem_name = None
		print(("TEM_NAME::::::", tem_name))
		self.tem = self.getSourceTemInstrumentData(self.cam, tem_name)

	def getSourceCameraInstrumentData(self, from_hostname,from_camname):
		kwargs = {'hostname':from_hostname,'name':from_camname}
		q = self.makequery('InstrumentData',kwargs)
		result = self.research(q,True)
		if not result:
			print("ERROR: incorrect hostname....")
			r = leginondata.InstrumentData(name=from_camname).query(results=1)
			if r:
				raise ValueError("Try %s instead" % r[0]['hostname'])
			else:
				raise ValueError("  No %s camera found" % from_camname)
			sys.exit()

		sourcecam = result
		return sourcecam

	def getSourceTemInstrumentData(self, sourcecam, sourcetem_name=None):
		'''
		Get TEM connected to the camera that has PixelSizeCalibration or CameraLengthCalibration (diffraction tem)
		'''
		allcaldata = leginondata.PixelSizeCalibrationData(ccdcamera=sourcecam).query()
		allcaldata.extend(leginondata.CameraLengthCalibrationData(ccdcamera=sourcecam).query())
		if not allcaldata:
			raise ValueError('no tem linked with the camera')
		temids = []
		print('******')
		print(sourcetem_name)
		# gather tems of the sourcetem_name that has such calibrations
		for c in allcaldata:
			if c['tem'] and c['tem'].dbid not in temids:
				if sourcetem_name and c['tem']['name']!=sourcetem_name:
					continue
				temids.append(c['tem'].dbid)
		# There should only be one entry
		temdata = None
		for tid in temids:
			tem = leginondata.InstrumentData().direct_query(tid)
			if len(temids) == 1:
				temdata = tem
			else:
				# more than one possibility
				answer = input('Gather calibration associated with tem  %s on host %s ? (Y/y or N/n)' % (tem['name'], tem['hostname']))
				if answer.lower() in 'y':
					temdata = tem
					break
		try:		
			print(("Using tem id=%d on %s named %s" % (temdata.dbid, temdata['hostname'], temdata['name'])))
			return temdata
		except AttributeError:
			raise ValueError('no tem selected with the camera %s:%s' % (sourcecam['hostname'],sourcecam['name']))

	def getMags(self):
		magsdata = leginondata.MagnificationsData(instrument=self.tem).query(results=1)[0]
		return magsdata['magnifications']

	def printMagSubmodeMap(self):
		magsdata = leginondata.MagnificationsData(instrument=self.tem).query(results=1)[0]
		q = leginondata.ProjectionSubModeMappingData()
		q['magnification list'] = magsdata
		results = q.query()
		if results:
			for r in results:
				print(('Adding Submode Mag at %dx = %s' % (r['magnification'], r['name'])))
			self.publish(results)

	def printPixelSizeCalibrationQueries(self, mags):
		#PixelSizeCalibrationData
		for mag in mags:
			results = leginondata.PixelSizeCalibrationData(ccdcamera=self.cam,magnification=mag).query(results=1)
			if results:
				print(('Adding PixeSize at %dx = %.3e' % (mag, results[0]['pixelsize'])))
				self.publish(results)

	def printCameraLengthCalibrationQueries(self, mags):
		#CameraLengthCalibrationData
		for mag in mags:
			results = leginondata.CameraLengthCalibrationData(ccdcamera=self.cam,magnification=mag).query(results=1)
			if results:
				print(('Adding CameraLength at %d mm = %.3e' % (mag, results[0]['camera length'])))
				self.publish(results)

	def printStageModelCalibrationQueries(self, mags):
		#StageModelCalibrationData
		for axis in ('x','y'):
			results = leginondata.StageModelCalibrationData(tem=self.tem,ccdcamera=self.cam,axis=axis).query(results=1)
			if results:
				print(('StageModel', axis))
				self.publish(results)

			for mag in mags:
				q = leginondata.StageModelMagCalibrationData(tem=self.tem, ccdcamera=self.cam,axis=axis,magnification=mag)
				results = q.query(results=1)
				if results:
					print(('StageModelMag', axis, mag))
					self.publish(results)

	def printMatrixCalibrationQueries(self, mags, probe):
		probe_dependent = ('defocus','image-shift coma','image-shift stig','image-shift defocus')
		for mag in mags:
			# MatrixCarlibationData
			for matrix_type in ('stage position','image shift','defocus','beam shift','image-shift coma','image-shift stig','image-shift defocus'):
				# stage position is not probe dependent
				if matrix_type in probe_dependent and probe is None:
					continue
				if matrix_type not in probe_dependent and probe is not None:
					continue
				q = leginondata.MatrixCalibrationData(tem=self.tem, ccdcamera=self.cam,magnification=mag,type=matrix_type, probe=probe)
				results = q.query(results=1)
				if results:
					print(('Matrix', matrix_type, probe, mag))
					self.publish(results)

	def printCameraSensitivityQueries(self):
		#CameraSensitivity
		results = leginondata.CameraSensitivityCalibrationData(ccdcamera=self.cam).query(results=1)
		if results:
			print('Adding Camera Sensitivity')
			self.publish(results)

	def printEucentricFocusQueries(self, mags, probe):
		# EucentricFocus in both micro and nano probe mode
		for mag in mags:
			results = leginondata.EucentricFocusData(tem=self.tem, magnification=mag, probe=probe).query(results=1)
			if results:
				print(('Adding Eucentric Focus for %d mag and %s probe' % (mag, probe)))
				self.publish(results)

	def printRotationCenterQueries(self, mags, probe):
		# RotationCenter in both micro and nano probe mode
		for mag in mags:
			results = leginondata.RotationCenterData(tem=self.tem, magnification=mag, probe=probe).query(results=1)
			if results:
				print(('Adding Rotation Center for %d mag and %s probe' % (mag, probe)))
				self.publish(results)

	def printImageRotationCalibrationQueries(self, mags, probe):
		# Image Rotation in both micro and nano probe mode
		for mag in mags:
			results = leginondata.ImageRotationCalibrationData(tem=self.tem, ccdcamera=self.cam, magnification=mag, probe=probe).query(results=1)
			if results:
				print(('Adding Image Rotation for %d mag and %s probe' % (mag, probe)))
				self.publish(results)

	def printImageScaleAdditionCalibrationQueries(self, mags, probe):
		# ImageScaleAddition in both micro and nano probe mode
		for mag in mags:
			results = leginondata.ImageScaleAdditionCalibrationData(tem=self.tem, ccdcamera=self.cam, magnification=mag, probe=probe).query(results=1)
			if results:
				print(('Adding Image Scale Addition for %d mag and %s probe' % (mag, probe)))
				self.publish(results)

	def printPPBeamTiltRotationQuery(self, probe):
		results = leginondata.PPBeamTiltRotationData(tem=self.tem, probe=probe).query(results=1)
		if results:
			print(('Adding Phase Plate Beam Tilt Rotation for %s probe' % (probe)))
			self.publish(results)

	def printPPBeamTiltVectorsQuery(self, probe):
		results = leginondata.PPBeamTiltVectorsData(tem=self.tem, probe=probe).query(results=1)
		if results:
			print(('Adding Phase Plate Beam Tilt Vectors for %s probe' % (probe)))
			self.publish(results)

	def printBeamSizeQuery(self, probe):
		if probe is None:
			return
		q = leginondata.BeamSizeCalibrationData(tem=self.tem)
		q['probe mode'] = probe
		results = q.query()
		if results:
			all_types = []
			newest_type_results = []
			for r in results:
				key = '%d-%d' % (r['c2 size'],r['spot size'])
				if key not in all_types:
					all_types.append(key)
					newest_type_results.append(r)
			print(('Adding BeamSizeCalibration for %s probe' % (probe)))
			self.publish(newest_type_results)

	def run(self):
		if not self.tem:
			return
		mags = self.getMags()
		print((self.cam.dbid))
		if not mags:
			print('Need magnifications to export')
			self.close(1)
		self.printMagSubmodeMap()
		self.printPixelSizeCalibrationQueries(mags)
		self.printCameraLengthCalibrationQueries(mags)
		self.printCameraSensitivityQueries()
		self.printStageModelCalibrationQueries(mags)
		for p in (None,'micro','nano'):
			self.printMatrixCalibrationQueries(mags,p)
			self.printImageRotationCalibrationQueries(mags,p)
			self.printImageScaleAdditionCalibrationQueries(mags,p)
			self.printEucentricFocusQueries(mags,p)
			self.printRotationCenterQueries(mags,p)
			self.printPPBeamTiltVectorsQuery(p)
			self.printPPBeamTiltRotationQuery(p)
			self.printBeamSizeQuery(p)
		json_filename = 'cal_%s+%s+%s+%s.json' % (self.tem['hostname'],self.tem['name'],self.cam['hostname'],self.cam['name'])
		self.writeJsonFile(json_filename)

	def close(self, status=0):
		if status:
			print("Exit with Error")
			sys.exit(1)
		if self.interactive:
			input('hit enter when ready to quit')

if __name__=='__main__':
	app = CalibrationJsonMaker(sys.argv, interactive=False)
	app.run()
	app.close()
	 
