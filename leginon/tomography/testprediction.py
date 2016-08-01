#!/usr/bin/env python
import math
import leginon.tomography.prediction

settings = {
		'phi': 90.0,  #degrees
		'optical_axis': 0.0,  #microns
		'z0': -2,  #microns
	}

class Test(object):
	def __init__(self, settings):
		self.prediction = leginon.tomography.prediction.Prediction()
		self.settings = settings
		self.prediction.fitdata = 4
		self.pixelsize = 5.64e-10
		self.initPredictionParameters(0)
		self.initPredictionParameters(1)
		self.addExistingPositions()

	def initPredictionParameters(self, tiltgroup):
		phi = math.radians(self.settings['phi'])
		optical_axis = self.settings['optical_axis']*(1e-6)/self.pixelsize
		custom_z0 = self.settings['z0']*(1e-6)/self.pixelsize
		params = [phi, optical_axis, custom_z0]

		# specify which tilt group to set value on
		self.prediction.setCurrentTiltGroup(tiltgroup)
		# set values in prediction
		self.prediction.setParameters(tiltgroup,params)
		self.prediction.image_pixel_size = self.pixelsize
		self.prediction.ucenter_limit = 10 #micron
		self.prediction.phi0 = params[0]
		self.prediction.offset0 = params[1]
		self.prediction.z00 = params[2]
		self.prediction.fixed_model = True

	def addTheoreticalPositions(self, positions):
		positions.append([0,math.radians(3.0),{'y':-self.prediction.z00*math.sin(math.radians(3.0)),'x':0},])
		positions.append([0,math.radians(6.0),{'y':-self.prediction.z00*math.sin(math.radians(6.0)),'x':0},])
		positions.append([0,math.radians(9.0),{'y':-self.prediction.z00*math.sin(math.radians(9.0)),'x':0},])
		positions.append([0,math.radians(12.0),{'y':-self.prediction.z00*math.sin(math.radians(12.0)),'x':0},])

	def addRealPositions(self, positions):
		positions.append([0,math.radians(3.0),{'x':0,'y':-92.8},])
		positions.append([0,math.radians(6.0),{'x':-27.9,'y':160.4},])
		positions.append([0,math.radians(9.0),{'x':0,'y':502.4},])
		positions.append([0,math.radians(12.0),{'x':14.0,'y':625.9},])

	def addExistingPositions(self):
		positions=[]
		positions.append([0,math.radians(0.0),{'x':0,'y':0},])
		self.addTheoreticalPositions(positions)

		# add a tilt series to prediction
		self.prediction.newTiltSeries()
		# add a new tilt group in that tilt series
		self.prediction.newTiltGroup()
		# add tilt angles and positions in the tilt group
		for group, tilt, position in positions:
			self.prediction.setCurrentTiltGroup(group)
			self.prediction.addPosition(tilt, position)

	def predict(self, tilt):
		current_tilt_group = self.prediction.getCurrentTiltGroup()
		print current_tilt_group.tilts
		print current_tilt_group.xs
		print current_tilt_group.ys
		predicted_position = self.prediction.predict(tilt)
		print predicted_position

t = Test(settings)
t.predict(math.radians(30))
