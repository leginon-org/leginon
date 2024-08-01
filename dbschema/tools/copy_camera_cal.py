#!/usr/bin/env python
import sys
from leginon import leginondata


class CopyCameraCal(object):
	def __init__(self, hostname, ht):
		self.hostname = hostname
		self.ht = ht
		try:
			from_cam, to_cam =self.readCameras()
			self.setInstrument(from_cam, to_cam)
		except Exception as e:
			print((e.message))
			self.close()

	def setCommit(self,value):
		self.commit = value

	def readCameras(self):
		cam1 = input('Enter camera name to import from: ')
		cam2 = input('Enter camera name to export to: ')
		if not cam1 or not cam2:
			raise ValueError('Missing a camera name')
		return cam1, cam2

	def setInstrument(self, from_cam, to_cam):
		self.from_camera = self.getInstrumentData(from_cam)
		self.to_camera = self.getInstrumentData(to_cam)
		if to_cam == 'GatanK2Super':
			self.pixelsize_scale = 2
		else:
			self.pixelsize_scale = 1

	def getInstrumentData(self,cam_name):
		results = leginondata.InstrumentData(hostname=self.hostname,name=cam_name).query(results=1)
		if not results:
			print("ERROR: camera not found at host....")
			r = leginondata.InstrumentData(name=cam_name).query(results=1)
			if r:
				print(("  Try one of these instead: %s" % (list(map((lambda x: x['hostname']),r)),)))
				raise ValueError("  %s camera not found" % cam_name)
		camdata = results[0]
		return camdata

	def insertDest(self, newdata):
		if self.commit:
			newdata.insert()
			print("inserted")
		else:
			return

	def confirmTEM(self, temdata):
		answer = input('Is %s the tem hostname coupled with the cameras (y/n) ?' % (temdata['hostname']))
		if answer in 'nN':
			raise ValueError('Wrong tem chosen')

	def run(self):
		high_tension = self.ht
		sourcecam = self.from_camera
		destcam = self.to_camera
		onecaldata = leginondata.MatrixCalibrationData(ccdcamera=sourcecam).query(results=1)[0]
		temdata = onecaldata['tem']
		self.confirmTEM(temdata)
		magsdata = leginondata.MagnificationsData(instrument=temdata).query(results=1)[0]

		#PixelSizeCalibrationData
		for mag in magsdata['magnifications']:
			# PixelSizeCarlibationData
			q = leginondata.PixelSizeCalibrationData(ccdcamera=sourcecam,magnification=mag)
			#q['high tension']=high_tension
			results = q.query(results=1)
			if results:
				caldata = results[0]
				newdata = leginondata.PixelSizeCalibrationData(initializer=caldata)
				newdata['ccdcamera'] = destcam
				pixelsize = caldata['pixelsize']
				pixelsize /= self.pixelsize_scale
				newdata['pixelsize'] = pixelsize
				print(('PixelSizeCalibrationData',newdata['magnification'],newdata['pixelsize']))
				self.insertDest(newdata)

		#StageModelCalibrationData
		for axis in ('x','y'):
			results = leginondata.StageModelCalibrationData(ccdcamera=sourcecam,axis=axis).query(results=1)
			if results:
				newdata = leginondata.StageModelCalibrationData(initializer=results[0])
				newdata['ccdcamera'] = destcam
				print(('StageModelCalibrationData', newdata['period']))
				self.insertDest(newdata)

			for mag in magsdata['magnifications']:
				q = leginondata.StageModelMagCalibrationData(ccdcamera=sourcecam,axis=axis,magnification=mag)
				q['high tension'] = high_tension
				results = q.query(results=1)
				if results:
					newdata = leginondata.StageModelMagCalibrationData(initializer=results[0])
					newdata['ccdcamera'] = destcam
					newdata['mean'] /= self.pixelsize_scale 
					print(('StageModelMagCalibrationData', newdata['magnification'],newdata['mean']))
					self.insertDest(newdata)

		for mag in magsdata['magnifications']:
			# MatrixCarlibationData
			for matrix_type in ('stage position','image shift','defocus','beam shift'):
				q = leginondata.MatrixCalibrationData(ccdcamera=sourcecam,magnification=mag,type=matrix_type)
				q['high tension']=high_tension
				results = q.query(results=1)
				if results:
					caldata = results[0]
					newdata = leginondata.MatrixCalibrationData(initializer=caldata)
					newdata['ccdcamera'] = destcam
					matrix = caldata['matrix']
					matrix /= self.pixelsize_scale
					newdata['matrix'] = matrix
					print(('MatrixCalibrationData', newdata['type'],newdata['magnification'],newdata['matrix'][0,0]))
					self.insertDest(newdata)

	def confirmInsert(self):
		answer = input('Ready to insert ? (y/n/Y/N) ')
		if answer in 'y/Y':
			return True
		else:
			return False

	def close(self):
		print('closing')
		sys.exit()

if __name__=='__main__':
	if len(sys.argv) < 3:
		print("This program copies existing camera matrix and stage model calibrations to another camera at the same plane")
		print("Usage copy_cam_cal.py hostname high_tension")
		print("high tension is an integer in volts, i.e., 200000")
		sys.exit()

	hostname = sys.argv[1]
	high_tension = int(sys.argv[2])

	app = CopyCameraCal(hostname, high_tension)
	app.setCommit(False)
	app.run()
	if app.confirmInsert():
		app.setCommit(True)
		app.run()
	app.close()


