#/usr/bin/env python
import math
from leginon import leginondata

class TiltCtfUploader(object):
	"""
	upload Tilt series Ctf as calibration of Tilt Defocus.  The input
	file is either Appion CTF data from its export or AreTomo3 ctf estimation.
	"""
	def __init__(self):
		self.filepath = input('filepath ? ')
		self.is_aretomo3 = input('Is AreTomo3 output ? (Y/N)').lower() == 'y'
		self.tilt_ref = 0.0 # radians
		self.tilt0 = 0.0

	def run(self):
		lines = self.readCtfData(self.filepath)
		if self.is_aretomo3:
			self.image = self.getFirstAreTomo3ImageData(lines[1])
		else:
			self.image = self.getFirstImageData(lines[1])
		alphas, ctfs = self.parseCtfData(lines)
		self.saveAlphaCtfs(alphas, ctfs)

	def readCtfData(self, filepath):
		f = open(filepath,'r')
		lines = f.readlines()
		f.close()
		return lines

	def getFirstImageData(self, line):
		bits = line.split('\t')
		image_id = int(bits[0])
		imagedata = leginondata.AcquisitionImageData().direct_query(image_id)
		if abs(imagedata['scope']['stage position']['a']-self.tilt_ref) > math.radians(0.5):
			raise ValueError('ctfdata must starts from %.2f degrees' % self.tilt_ref)
		return imagedata

	def getFirstAreTomo3ImageData(self, line):
		image_id =  int(input('most negative tilt ImageData ID= '))
		imagedata = leginondata.AcquisitionImageData().direct_query(image_id)
		return imagedata

	def _parse(self, l):
		if self.is_aretomo3:
			separator = ' '
			offset = 0
		else:
			separator = '\t'
			offset = 1
		bits = l.split(separator)
		bits = list(filter(lambda x: x!='', bits))
		def1 = float(bits[1+offset])
		def2 = float(bits[1+offset])
		avg_def = (def1+def2)/2
		return avg_def

	def parseCtfData(self, lines):
		ctfdict = {}
		datasize = len(lines)-1
		halfsize = datasize // 2
		q = leginondata.AcquisitionImageData()
		q['tilt series'] = self.image['tilt series']
		all_images = q.query()
		if len(all_images) != len(lines[1:]):
			raise ValueError('Image number and ctf data not matching')
		# Aretomo3 results always from negative to positive
		if self.is_aretomo3:
			alpha_images = {}
			for image in all_images:
				alpha_degrees = image['scope']['stage position']['a']*180.0/math.pi
				# high precision so all are unique
				alpha_key = alpha_degrees
				if alpha_key in alpha_images.keys():
					alpha_degrees += 0.0001
				alpha_images[alpha_degrees] = image
			alpha_keys = list(alpha_images.keys())
			# aretomo output always starts from negative tilt
			alpha_keys.sort()
			images_in_line_order = list(map((lambda x:alpha_images[x]), alpha_keys))
			scale = 1e-10 # defocus in angstroms
		else:
			# appion ctfdata export is sorted by image id in ascending order.
			all_images.reverse()
			images_in_line_order = all_images 
			scale = 1
		# create alpha_degrees keys and averged defocus values
		for i,l in enumerate(lines[1:]):
			alpha_degrees = images_in_line_order[i]['scope']['stage position']['a']*180.0/math.pi
			alpha_degrees = round(alpha_degrees,2)
			avg_def = self._parse(l)
			if abs(float(alpha_degrees)-self.tilt_ref*180.0/math.pi) < 0.5:
				self.def0 = avg_def
				self.tilt0 = alpha_degrees*math.pi/180.0
			avg_def = self._parse(l)
			if alpha_degrees not in ctfdict:
				ctfdict[alpha_degrees] = []
			ctfdict[alpha_degrees].append(avg_def*scale)
		alpha_keys = list(ctfdict.keys())
		alpha_keys.sort()
		ctfs = []
		for k in alpha_keys:
			# use initial tilt as reference.
			# bidirectional sequential tilt series have two values at the initial tilt.
			# Averaging them.
			ctfdict[k] = sum(ctfdict[k])/float(len(ctfdict[k])) -self.def0*scale
			ctfs.append(ctfdict[k])
		return alpha_keys, ctfs

	def saveAlphaCtfs(self, alphas, ctfs):
		q = leginondata.TiltDefocusCalibrationData(session=self.image['session'],tem=self.image['scope']['tem'])
		q['tilts'] = list(map((lambda x: math.radians(x)),alphas))
		q['defocus deltas'] = ctfs
		q['reference tilt'] = self.tilt0
		q.insert()

if __name__=='__main__':
	app = TiltCtfUploader()
	app.run()
