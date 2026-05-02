"""
GCTFFIND handling functions used by both leginon and appion
"""
import os
import time
import subprocess

def makeCommand(ace_exe, inputparams):
	### make standard input for GCtffind
	command_input_list = [ ace_exe,
		"-InMrc %s" % inputparams['input'],
		"-OutMrc %s" % inputparams['pow_output'],
		"-OutCtf %s" % inputparams['ctf_output'],
		"-Cs %.1f" % inputparams['cs'],
		"-kV %d" % (inputparams['volts']/1000,),
		"-PixSize %.3f" % inputparams['apix'],
		"-TileSize %d" % inputparams['fieldsize'],
		"-AmpContrast %.4f" % inputparams['amplitude_contrast'],
		"-AstRange %.3f" % inputparams['astig'],
	]
	if 'min_phase_shift' in inputparams.keys() and 'max_phase_shift' in inputparams.keys():
		command_input_list.append(
			"-ExtPhase %.1f %.1f" % (inputparams['min_phase_shift'],inputparams['max_phase_shift'])
		)
	return ' '.join(command_input_list)

def run(commandline, acename, ctf_output):
	### run ace
	t0 = time.time()
	aceoutf = open('%s.log' % acename,'w')
	aceerrf = open('%s.err' % acename,'w')
	# passing stdout stderr does not always work
	#aceproc = subprocess.Popen(commandline, shell=True, stdout=aceoutf, stderr=aceerrf)
	aceproc = subprocess.Popen(commandline, shell=True)
	aceproc.wait()
	aceoutf.close()
	aceerrf.close()

	if not os.path.isfile(ctf_output):
		raise RuntimeError('%s did not run' % acename)

def readResult(ctf_output):
	f= open(ctf_output, 'r')
	lines = f.read().split('\n')
	# second line has the data
	l = lines[1]
	data = list(filter(lambda x: len(x)>0,l.split(' ')))
	dfmin = float(data[2]) * 1e-10 #meters
	dfmax = float(data[3]) * 1e-10 #meters
	azimuth = float(data[4]) #degrees
	extphase = float(data[5]) #degrees
	score = float(data[6]) #relative 0-1
	return {'defocus1':dfmin, 'defocus2':dfmax, 'angle_astigmatism':azimuth, 'extra_phase_shift':extphase, 'confidence':score}
