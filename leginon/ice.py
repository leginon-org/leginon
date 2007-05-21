import math

min_intensity = 0.000001
inf = 1e300

class IceCalculator(object):
	def __init__(self, i0=None):
		self.i0 = i0

	def set_i0(self, i0):
		self.i0 = i0

	def get_intensity(self, thickness):
		return self.i0 / math.exp(thickness)

	def get_thickness(self, intensity):
		if intensity > self.i0:
			intensity = self.i0
		if intensity < min_intensity:
			intensity = min_intensity
		return math.log(self.i0 / intensity)

	def get_stdev_thickness(self, stdev_intensity, mean_intensity):
		if stdev_intensity >= mean_intensity:
			std = inf
		else:
			std = math.log(mean_intensity / (mean_intensity-stdev_intensity))
		return std

	def get_stdev_intensity(self, stdev_thickness, mean_thickness):
		### figure this out later
		pass
