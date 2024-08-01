#!/usr/bin/env python
import sys
from leginon import leginondata

class Copier(object):
	def __init__(self, hostname, camname, ht, commit=0):
		results = leginondata.InstrumentData(hostname=hostname,name=camname).query(results=1)
		if not results:
			print("ERROR: incorrect hostname-camera pair....")
			sys.exit()

		self.commit = commit
		self.sourcecam = results[0]
		self.mags = self.getMagnifications()

	def setMatrixType(self,value):
		if not value:
			value = 'stage position'
		self.cal_type = value

	def setReferenceMagnification(self, value):
		self.ref_mag = int(value)
		if self.ref_mag not in self.mags:
			raise ValueError('Reference Mag not found on this TEM')

	def setExcludedMagnifications(self, value):
		bits = value.split(',')
		if not len(bits):
			self.excluded_mags = []
		else:
			if bits[0] == '':
				bits.pop(0)
			self.excluded_mags = list(map((lambda x: int(x)),bits))
		for m in self.excluded_mags:
			if m not in self.mags:
				raise ValueError('%d not found in magnifications on this TEM' % m)

	def run(self):
		caldata = self.getCalibration(self.ref_mag,'MatrixCalibrationData',{'type':self.cal_type})
		if not caldata:
			print('no data found')
			return
		for mag in self.mags:
			if mag > self.ref_mag and mag not in self.excluded_mags:
				self.copyMagDependentCalibration(self.ref_mag, mag,caldata,'matrix') 

	def getMagnifications(self):
		onecaldata = leginondata.MatrixCalibrationData(ccdcamera=self.sourcecam).query(results=1)[0]
		self.temdata = onecaldata['tem']
		magsdata = leginondata.MagnificationsData(instrument=self.temdata).query(results=1)[0]
		return magsdata['magnifications']

	def getPixelSizeCalibrationData(self, mag):
		# PixelSizeCarlibationData
		return self.getCalibration(mag,'PixelSizeCalibrationData')

	def getCalibration(self, mag, attr_name,maps={}):
		q = getattr(leginondata,attr_name)(tem=self.temdata, ccdcamera=self.sourcecam)
		q['magnification'] = mag
		for k in list(maps.keys()):
			q[k]=maps[k]
		results = q.query(results=1)
		if not results:
			print('no calibration found')
			return
		else:
			caldata = results[0]
			return caldata
		
	def copyMagDependentCalibration(self, from_mag, to_mag, from_caldata,key_to_scale):
		attr_name = from_caldata.__class__.__name__
		newdata = getattr(leginondata,attr_name)(initializer=from_caldata)
		if 'magnification' not in list(newdata.keys()):
			return
		if key_to_scale not in list(newdata.keys()):
			return
		print(('From', newdata['magnification'],newdata[key_to_scale]))
		newdata['magnification'] = to_mag
		newdata[key_to_scale] = newdata[key_to_scale]*from_mag/to_mag
		print(('To', newdata['magnification'],newdata[key_to_scale]))
		self.insertDest(newdata)


	def insertDest(self, newdata):
		if self.commit == 1:
			newdata.insert()
			print("Inserted into leginon database")
		else:
			print("Rerun the script with extra option of 1 at the end to insert to database")
		print("")
		return

if __name__ == '__main__':
	if len(sys.argv) < 4:
		print("This program copies existing matrix and stage model calibrations from one mag to another")
		print("Usage copy_mag_cal.py camera_hostname camera_name high_tension <commit>")
		print("high tension is an integer in volts, i.e., 200000")
		print("commit flag, if set to 1 will insert the result to database")
		sys.exit()

	hostname = sys.argv[1]
	camname = sys.argv[2]
	high_tension = int(sys.argv[3])
	if len(sys.argv) == 5:
		commit = int(sys.argv[4])
	else:
		commit = 0

	app = Copier(hostname, camname, high_tension, commit)
	cal_type = input('Enter matrix type [Default: stage position]:')
	app.setMatrixType(cal_type)
	ref_mag = input('Use the matrix at this mag to scale all magnification above it: ')
	app.setReferenceMagnification(ref_mag)
	exclude_mags = input('List mags to exclude the insert, separate by ","')
	app.setExcludedMagnifications(exclude_mags)
	app.run()
	input('hit enter when ready to quit')

