import os
import time
import subprocess
from leginon import calibrationclient

class GctffindClient(object):
	def __init__(self, node):
		self.acename = 'gctffind'
		self.aceexe = 'gctffind'
		self.node = node
		self.logger = node.logger

	def runFromImageData(self, imagedata, amp_contrast=0.07, fieldsize=512, phase_search=(0,0)):
		mrcpath=os.path.join(imagedata['session']['image path'],imagedata['filename']+'.mrc')
		return self._runMrcPathWithImageData(mrcpath, imagedata, amp_contrast, fieldsize, phase_search)

	def runArrayWithImageData(self, a, imagedata, amp_contrast=0.07, fieldsize=512, phase_search=(0,0)):
		mrcpath='temp.mrc'
		return self._runMrcPathWithImageData(mrcpath, imagedata, amp_contrast, fieldsize, phase_search)

	def _runMrcPathWithImageData(self, mrcpath, imagedata, amp_contrast=0.07, fieldsize=512, phase_search=(0,0)):
		pcalclient = calibrationclient.PixelSizeCalibrationClient(self.node)
		psize = imagedata_pixel_size = pcalclient.getImagePixelSize(imagedata)['x']
		inputparams={}
		inputparams['input']=mrcpath
		inputparams['pow_output']='%s-pow.mrc' % imagedata['filename']
		inputparams['ctf_output']='%s.mrc.ctf.txt' % imagedata['filename']
		inputparams['cs']=imagedata['scope']['tem']['cs']*1000 # in mm
		inputparams['volts']=imagedata['scope']['high tension'] # in volts
		inputparams['apix']=psize*1e10 # in angstrum
		inputparams['fieldsize'] = fieldsize
		inputparams['amplitude_contrast'] = amp_contrast #use appion ctfvalues key name
		if min(phase_search) < max(phase_search):
			inputparams['min_phase_shift'] = min(phase_search) # in degrees
			inputparams['max_phase_shift'] = max(phase_search)
		cmd = self.makeCommand(inputparams)
		self.logger.info("run %s on %s" % (self.acename, imagedata['filename']))
		self.run(cmd, inputparams['ctf_output'])
		self.ctfvalues = self.readResult(inputparams['ctf_output'])
		self.ctfvalues.update(inputparams)
		os.remove(inputparams['ctf_output'])
		return self.ctfvalues

	def makeCommand(self, inputparams):
		### make standard input for GCtffind
		command_input_list = [ self.aceexe,
			"-InMrc %s" % inputparams['input'],
			"-OutMrc %s" % inputparams['pow_output'],
			"-OutCtf %s" % inputparams['ctf_output'],
			"-Cs %.1f" % inputparams['cs'],
			"-kV %d" % (inputparams['volts']/1000,),
			"-PixSize %.3f" % inputparams['apix'],
			"-TileSize %d" % inputparams['fieldsize'],
			"-AmpContrast %.4f" % inputparams['amplitude_contrast'],
		]
		if 'min_phase_shift' in inputparams.keys() and 'max_phase_shift' in inputparams.keys():
			command_input_list.append(
				"-ExtPhase %.1f %.1f" % (inputparams['min_phase_shift'],inputparams['max_phase_shift'])
			)
		return ' '.join(command_input_list)

	def readResult(self, ctf_output):
		f= open(ctf_output, 'r')
		lines = f.read().split('\n')
		# second line has the data
		l = lines[1]
		data = list(filter(lambda x: len(x)>0,l.split(' ')))
		dfmin = float(data[2])
		dfmax = float(data[3])
		azimuth = float(data[4])
		extphase = float(data[5])
		score = float(data[6])
		return {'defocus1':dfmin, 'defocus2':dfmax, 'angle_astigmatism':azimuth, 'extra_phase_shift':extphase, 'confidence':score}

	def run(self, commandline, ctf_output):
		### run ace
		print(commandline)
		t0 = time.time()
		aceoutf = open('%s.log' % self.acename,'w')
		aceerrf = open('%s.err' % self.acename,'w')
		#aceproc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
		aceproc = subprocess.Popen(commandline, shell=True)
		#aceproc = subprocess.Popen(commandline, shell=True)
		aceproc.wait()
		aceoutf.close()
		aceerrf.close()

		### check if ace worked
		if not os.path.isfile(ctf_output):
			self.logger.warning("%s did not run" % self.acename)

