import leginon.leginondata
from leginon.acq import setImageFilename

class TiltSeries(object):
	def __init__(self, node, settings, session, preset, target, emtarget, save_tracking=False):
		self.node = node
		self.dataclass = leginon.leginondata.TiltSeriesData
		self.imagedataclass = leginon.leginondata.AcquisitionImageData
		self.settings = settings
		self.session = session
		# TODO: fix me
		self.queue = None
		self.list = None
		self.preset = preset
		self.target = target
		self.emtarget = emtarget
		self.image_counter = 0
		self.current_image_filename = None
		self.save_tracking = save_tracking

	def save(self):
		dataq = self.dataclass(session=self.session)
		old_tilt_series_data = dataq.query()
		if len(old_tilt_series_data) > 0:	
			if old_tilt_series_data[0]['number'] is not None:
				series_number = 1 + old_tilt_series_data[0]['number']
			else:
				# old series has no number
				series_number = 1 + len(old_tilt_series_data)
		else:
			# new session has no tilt_series_data
			series_number = 1
		initializer = {
			'session': self.session,
			'tilt min': self.settings['tilt min'],
			'tilt max': self.settings['tilt max'],
			'tilt start': self.settings['tilt start'],
			'tilt step': self.settings['tilt step'],
			'tilt order': self.settings['tilt order'],
			'number':	series_number,
		}
		tilt_series_data = self.dataclass(initializer=initializer)
		tracking_tilt_series_data = self.dataclass(initializer=initializer)

		tilt_series_data['is_tracking'] = False
		tracking_tilt_series_data['is_tracking'] = True
		self.node.publish(tilt_series_data, database=True, dbforce=True)
		if self.save_tracking:
			self.node.publish(tracking_tilt_series_data, database=True, dbforce=True)

		self.tilt_series_data = tilt_series_data
		self.tracking_tilt_series_data = tracking_tilt_series_data

	def _constructImageData(self, cam_image_data):
		# store EMData to DB to prevent referencing errors
		self.node.publish(cam_image_data['scope'], database=True)
		self.node.publish(cam_image_data['camera'], database=True)

		tilt_series_image_data = self.imagedataclass(initializer=cam_image_data)
		tilt_series_image_data['queue'] = self.queue
		tilt_series_image_data['list'] = self.list
		tilt_series_image_data['preset'] = self.preset
		tilt_series_image_data['label'] = self.node.name
		tilt_series_image_data['target'] = self.target
		tilt_series_image_data['emtarget'] = self.emtarget
		tilt_series_image_data['phase plate'] = self.node.pp_used
		# TODO: put in seperate data
		#tilt_series_image_data['shift'] = None
		tilt_series_image_data['tilt series'] = self.tilt_series_data
		tilt_series_image_data['version'] = 0
		tilt_series_image_data.attachPixelSize()
		return tilt_series_image_data

	def saveImage(self, cam_image_data):
		tilt_series_image_data = self._constructImageData(cam_image_data)
		setImageFilename(tilt_series_image_data)

		# HACK: fix me
		tilt_series_image_data['filename'] += '_%03d' % (self.image_counter + 1)
		self.current_image_filename = tilt_series_image_data['filename']


		self.node.publish(tilt_series_image_data, database=True)
		# publish image event for image count
		self.node.publish(tilt_series_image_data, pubevent=True)
		self.node.publishStats(tilt_series_image_data)

		self.image_counter += 1

		return tilt_series_image_data

	def saveTrackingImage(self, cam_image_data, tracking_preset):
		"""
		Saving tracking image under a separate tilt series at the
		same number.
		"""
		new_image_data = self._constructImageData(cam_image_data)
		new_image_data['preset'] = tracking_preset
		new_image_data['tilt series'] = self.tracking_tilt_series_data
		new_image_data['filename'] = self.current_image_filename + '_track'
		self.node.publish(new_image_data, database=True)
		self.node.publishStats(new_image_data)

