import data
import time
import calibration

class AutoFocusCalibration(calibration.Calibration):
	def __init__(self, id, nodelocations):
		calibration.Calibration.__init__(self, id, nodelocations)
		self.axislist = ['x']
		self.defocus = 0.0001
		self.deltadefocus

	def state(self, value, axis):
		return {'beam tilt': {axis: value}}

	def calibrate(self):
		emdata = data.EMData('defocus', {'defocus': self.defocus})
		self.publishRemote(emdata)
		time.sleep(1.0)

		cal1 = calibration.Calibration.calibrate(self)

		emdata = data.EMData('defocus',
			{'defocus': self.defocus + self.deltadefocus})
		self.publishRemote(emdata)
		time.sleep(1.0)

		cal2 = calibration.Calibration.calibrate(self)

		cal = {'autofocus': {}}
		cal['autofocus']['x shift'] = cal2['x shift']['x'] - cal1['x shift']['x'] / self.deltadefocus
		cal['autofocus']['y shift'] = cal2['x shift']['y'] - cal1['x shift']['y'] / self.deltadefocus
		# calibrate needs to take a specific value
		cal['autofocus']['beam tilt'] = cal2['x shift']['value']

		return cal

