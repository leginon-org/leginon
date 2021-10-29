#/usr/bin/env python
import math
from leginon import leginondata

class TiltCtfUploader(object):
	def __init__(self):
		self.filepath = raw_input('filepath ? ')
		self.tilt_ref = 0.0 # radians
		self.tilt0 = 0.0

	def run(self):
		lines = self.readCtfData(self.filepath)
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

	def _parse(self, l):
		bits = l.split('\t')
		image_id = int(bits[0])
		def1 = float(bits[2])
		def2 = float(bits[3])
		avg_def = (def1+def2)/2
		imagedata = leginondata.AcquisitionImageData().direct_query(image_id)
		alpha = imagedata['scope']['stage position']['a']*180.0/math.pi
		alpha_degrees = round(alpha,2)
		return alpha_degrees, avg_def

	def parseCtfData(self, lines):
		ctfdict = {}
		for l in lines[1:]:
			alpha_degrees, avg_def = self._parse(l)
			if abs(float(alpha_degrees)-self.tilt_ref*180.0/math.pi) < 0.5:
				def0 = avg_def
				self.tilt0 = alpha_degrees*math.pi/180.0
			alpha_degress, avg_def = self._parse(l)
			avg_def = avg_def - def0
			if alpha_degrees not in ctfdict:
				ctfdict[alpha_degrees] = []
			ctfdict[alpha_degrees].append(avg_def)
		alpha_keys = ctfdict.keys()
		alpha_keys.sort()
		ctfs = []
		for k in alpha_keys:
			ctfdict[k] = sum(ctfdict[k])/float(len(ctfdict[k]))
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
