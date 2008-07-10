import data
import instrument
from acquisition import setImageFilename

class TiltSeries(object):
	def __init__(self, node, settings, session, preset, target, emtarget):
		self.node = node
		self.dataclass = data.TiltSeriesData
		#self.imagedataclass = data.TiltSeriesImageData
		self.imagedataclass = data.AcquisitionImageData
		self.settings = settings
		self.session = session
		# TODO: fix me
		self.queue = None
		self.list = None
		self.preset = preset
		self.target = target
		self.emtarget = emtarget
		self.image_counter = 0

	def save(self):
		initializer = {
			'session': self.session,
			'tilt min': self.settings['tilt min'],
			'tilt max': self.settings['tilt max'],
			'tilt start': self.settings['tilt start'],
			'tilt step': self.settings['tilt step'],
		}
		tilt_series_data = self.dataclass(initializer=initializer)

		self.node.publish(tilt_series_data, database=True, dbforce=True)

		self.tilt_series_data = tilt_series_data

	def saveImage(self, image_data):
		# store EMData to DB to prevent referencing errors
		self.node.publish(image_data['scope'], database=True)
		self.node.publish(image_data['camera'], database=True)

		tilt_series_image_data = self.imagedataclass(initializer=image_data)
		tilt_series_image_data['queue'] = self.queue
		tilt_series_image_data['list'] = self.list
		tilt_series_image_data['preset'] = self.preset
		tilt_series_image_data['target'] = self.target
		tilt_series_image_data['emtarget'] = self.emtarget
		# TODO: put in seperate data
		#tilt_series_image_data['shift'] = None
		tilt_series_image_data['tilt series'] = self.tilt_series_data
		tilt_series_image_data['version'] = 0

		setImageFilename(tilt_series_image_data)

		# HACK: fix me
		tilt_series_image_data['filename'] += '_%03d' % (self.image_counter + 1)

		self.node.publish(tilt_series_image_data, database=True)
		self.node.publishStats(tilt_series_image_data)

		self.image_counter += 1

		return tilt_series_image_data

