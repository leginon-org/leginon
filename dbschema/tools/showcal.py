#!/usr/bin/env python
import sys
from leginon import leginondata
'''
	This program shows sql statement required to insert calibrations
	into leginon database of dest_database_host based on the existing
	calibration on the source_database_host.  The latter is in sinedon.cfg
	Usage: showcal.py source_database_hostname source_camera_hosthame camera_name
'''
pixelsize_scale = 1

def convertStringToSQL(value):
	if value is None:
		return 'Null'
	else:
		return "'"+value+"'"

class ShowCalibrationQuery(object):
	def __init__(self,params):
		self.validateInput(params)
		self.inputNewDBInfo()

	def validateInput(self, params):
		if len(params) != 4:
			print("Usage showcal.py source_database_hostname source_camera_hosthame camera_name")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		self.sourcecam = self.getSourceCameraInstrumentData(params[2],params[3])

	def inputNewDBInfo(self):
		'''
		Tem, Cam and session ids to put in the insertion query.  This means that a session must
		be created first on the same instrument in the new db before this script is run.
		'''
		answer = input("You need to create a session with the new database where these calibrations\n are inserted into.\n Press Y/y if ready.")
		if answer not in ('Y','y'):
			self.close(1)
		self.new_temid = int(input('TEM instrument Id ?'))
		self.new_camid = int(input('Digital Camera instrument Id ?'))
		self.new_sessionid = int(input('Session Id ?'))

	def getSourceCameraInstrumentData(self, from_hostname,from_camname):
		results = leginondata.InstrumentData(hostname=from_hostname,name=from_camname).query(results=1)
		if not results:
			print("ERROR: incorrect hostname....")
			r = leginondata.InstrumentData(name=from_camname).query(results=1)
			if r:
				print(("  Try %s instead" % r[0]['hostname']))
			else:
				print(("  No %s camera found" % from_camname))
			sys.exit()

		sourcecam = results[0]
		return sourcecam

	def printQuery(self, q):
		print(q)
		return

	def getMags(self):
		onecaldata = leginondata.MatrixCalibrationData(ccdcamera=self.sourcecam).query(results=1)[0]
		temdata = onecaldata['tem']
		print((temdata.dbid, temdata))
		magsdata = leginondata.MagnificationsData(instrument=temdata).query(results=1)[0]
		return magsdata['magnifications']

	def printPixelSizeCalibrationQueries(self, mags):
		#PixelSizeCalibrationData
		for mag in mags:
			results = leginondata.PixelSizeCalibrationData(ccdcamera=self.sourcecam,magnification=mag).query(results=1)
			if results:
				newdata = leginondata.PixelSizeCalibrationData(initializer=results[0])
				insertq = "insert into `PixelSizeCalibrationData` (`REF|SessionData|session`,magnification,pixelsize,comment,`REF|InstrumentData|tem`,`REF|InstrumentData|ccdcamera`) values (%d,%d,%e,'%s',%d,%d);" % (self.new_sessionid,newdata['magnification'],newdata['pixelsize'],newdata['comment'],self.new_temid,self.new_camid)
				self.printQuery(insertq)

	def printStageModelCalibrationQueries(self, mags):
		#StageModelCalibrationData
		for axis in ('x','y'):
			results = leginondata.StageModelCalibrationData(ccdcamera=self.sourcecam,axis=axis).query(results=1)
			if results:
				newdata = leginondata.StageModelCalibrationData(initializer=results[0])
				insertq = "insert into `StageModelCalibrationData` (`REF|SessionData|session`,`axis`,`period`,`ARRAY|a|1_1`,`ARRAY|b|1_1`,`label`,`REF|InstrumentData|tem`,`REF|InstrumentData|ccdcamera`) values (%d,'%s',%e,%e,%e,'%s',%d,%d);" % (self.new_sessionid,newdata['axis'],newdata['period'],newdata['a'][0][0],newdata['b'][0][0],newdata['label'],self.new_temid,self.new_camid)
				self.printQuery(insertq)

			for mag in mags:
				q = leginondata.StageModelMagCalibrationData(ccdcamera=self.sourcecam,axis=axis,magnification=mag)
				results = q.query(results=1)
				if results:
					newdata = results[0]
					insertq = "insert into `StageModelMagCalibrationData` (`REF|SessionData|session`,`angle`,`axis`,`mean`,`high tension`,`label`,`REF|instrumentData|tem`,`REF|InstrumentData|ccdcamera`,`magnification`) values (%d,%e,'%s',%e,%d,'%s',%d,%d,%d);" % (self.new_sessionid,newdata['angle'], newdata['axis'],newdata['mean'],newdata['high tension'],newdata['label'],self.new_temid,self.new_camid,mag)
					self.printQuery(insertq)


	def printMatrixCalibrationQueries(self, mags, probe):
		for mag in mags:
			# MatrixCarlibationData
			for matrix_type in ('stage position','image shift','defocus','beam shift'):
				q = leginondata.MatrixCalibrationData(ccdcamera=self.sourcecam,magnification=mag,type=matrix_type, probe=probe)
				results = q.query(results=1)
				if results:
					caldata = results[0]
					newdata = leginondata.MatrixCalibrationData(initializer=caldata)
					q = "insert into `MatrixCalibrationData` (`REF|SessionData|session`, `type`,`magnification`, `ARRAY|matrix|1_1`,`ARRAY|matrix|1_2`,`ARRAY|matrix|2_1` , `ARRAY|matrix|2_2` , `REF|InstrumentData|tem` , `REF|InstrumentData|ccdcamera`,`high tension`,`probe`) values (%d,'%s',%d,%e,%e,%e,%e,%d,%d,%d,%s);" % (self.new_sessionid,newdata['type'],newdata['magnification'],newdata['matrix'][0][0],newdata['matrix'][0][1],newdata['matrix'][1][0],newdata['matrix'][1][1],self.new_temid,self.new_camid,newdata['high tension'],convertStringToSQL(newdata['probe']))
					self.printQuery(q)

	def run(self):
		mags = self.getMags()
		#print self.sourcecam.dbid
		#print mags
		self.printPixelSizeCalibrationQueries(mags)
		self.printStageModelCalibrationQueries(mags)
		for p in ('micro','nano'):
			self.printMatrixCalibrationQueries(mags,p)

		input('hit enter when ready to quit')

	def close(self, status):
		if status:
			print("Exit with Error")
			sys.exit(1)

if __name__=='__main__':
	app = ShowCalibrationQuery(sys.argv)
	app.run()
	 
