#!/usr/bin/env python

import numpy
from pyami import diffrfun
from leginon import leginondata

class DiffrCalibrator(object):
	'''
	Diffraction parameter calibrator that uses imagedata to select the more
	likely results. Center and camera length calibratable now. Primary use
	is to do all diffraction preset images of the same session.
	'''
	def __init__(self, sessionname):
		self.setSession(sessionname)
		self.logger = None

	def setLogger(self, loggername):
		self.logger = open('diffr_cal_%s.log' % (loggername),'w')
		self.logger.write('nominal_cam_length(mm)\tmeasured_avg(m)\tmeasured_std(m)\tn_samples\n')

	def setSession(self, sessionname):
		r=leginondata.SessionData(name=sessionname).query(results=1)[0]
		self.session = r

	def getImagesAtPreset(self, presetname):
		pq = leginondata.PresetData(session=self.session,name=presetname)
		results=leginondata.AcquisitionImageData(preset=pq).query()
		return results

	def getDiffractionPresetNames(self):
		presetnames = []
		pq = leginondata.PresetData(session=self.session).query()
		for p in pq:
			if p['tem']['name'].startswith('Diffr'):
				if p['name'] not in presetnames:
					presetnames.append(p['name'])
		return presetnames

	def calibrateCameraLengthOnImage(self, image):
		a = image['image']
		ht = image['scope']['high tension']
		cam_psize = image['camera']['pixel size']['x'] # should be the same in x and y.
		image_bin = image['camera']['binning']['x']
		center = (a.shape[0]//2, a.shape[1]//2)
		try:
			cam_lengths, center, radial_values = diffrfun.calibrate(a, ht, cam_psize, image_bin)
		except Exception as e:
			print('Failed %s with %s' % (image['filename'], e))
			return center, []
		#print image['filename'], center, cam_lengths
		return center, cam_lengths

	def isHidden(self, image):
		results = leginondata.ViewerImageStatus(image=image).query()
		for r in results:
			if r['status'] in ('hidden','trash'):
				return True
		return False

	def getStats(self, all_cam_lengths,mag):
		cam_lengths = []
		for cam_length in all_cam_lengths:
			if abs(cam_length*1000 -mag) < mag*0.05:
				cam_lengths.append(cam_length)
		if not cam_lengths:
			print ('No successful calibration at %d mm' % (mag))
			return mag*0.001, 0.0, 0
		n = len(cam_lengths)
		avg_cam_length = numpy.array(cam_lengths).mean()
		std_cam_length_str = ''
		std_cam_length = 0.0
		if len(cam_lengths) > 1:
			std_cam_length = numpy.array(cam_lengths).std()
			std_cam_length_str = '+/-%.3f' % (std_cam_length)
		if self.logger is not None:
			self.logger.write('%d\t%.3f\t%.3f\t%d\n' % (mag, avg_cam_length, std_cam_length, n))
		print('cam_length(m) = %.3f%s (n=%d)' % (avg_cam_length, std_cam_length_str, n))
		return avg_cam_length, std_cam_length, n

	def calibrateCameraLengthAtPreset(self, presetname):
		images = self.getImagesAtPreset(presetname)
		this_mag = None
		cam_lengths = []
		good_image = None
		for image in images:
			if self.isHidden(image):
				continue
			if this_mag is None:
				this_mag = image['scope']['magnification']
			else:
				if image['scope']['magnification'] != this_mag:
					raise ValueError('%s not at %d but at %d' % (image['filename'],this_mag, image['scope']['magnification']))
			good_image = image
			cam_lengths.extend(self.calibrateCameraLengthOnImage(image)[1])
		if this_mag is None:
			# preset has no images, not even hidden ones
			return
		avg_cam_length, std_cam_length, n = self.getStats(cam_lengths, this_mag)
		if n > 0:
			comment = 'std=%.3f (n=%d)' % (std_cam_length, n)
			self.publish(good_image, avg_cam_length, comment)

	def publish(self, good_image, cam_length, comment):
		temdata = good_image['scope']['tem']
		camdata = good_image['camera']['ccdcamera']
		caldata = leginondata.CameraLengthCalibrationData()
		caldata['magnification'] = good_image['scope']['magnification']
		caldata['camera length'] = cam_length
		caldata['comment'] = comment
		caldata['session'] = self.session
		caldata['tem'] = temdata
		caldata['ccdcamera'] = camdata
		caldata.insert()

	def run(self):
		self.setLogger(self.session['name'])
		presetnames = self.getDiffractionPresetNames()
		for pname in presetnames:
			print pname
			self.calibrateCameraLengthAtPreset(pname)
		if self.logger:
			self.logger.close()

if __name__=='__main__':
	app = DiffrCalibrator('g19aug30c')
	app.run()
