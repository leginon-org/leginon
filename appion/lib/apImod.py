import os
import subprocess
import apDisplay
import apFile
import time
import apTomo
from pyami import mrc

def writeRawtltFile(path,seriesname,tilts):
	rawtltname = os.path.join(path,seriesname+'.rawtlt')
	f = open(rawtltname, 'w')
	for tilt in tilts:
		f.write('%6.2f\n' % (tilt,))
	f.close()

def writeShiftPrexfFile(path, seriesname,xpeaks):
	rawtltname = os.path.join(path,seriesname+'.prexf')
	f = open(rawtltname, 'w')
	tilts = xpeaks.keys()
	tilts.sort()
	f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (1.0,0.0,0.0,1.0,0.0,0.0))
	for tilt in tilts:
		if xpeaks[tilt] is not None:
			f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (1.0,0.0,0.0,1.0,xpeaks[tilt][0],xpeaks[tilt][1]))
	f.close()

def writeTransformPrexfFile(path, seriesname,transforms):
	xfname = os.path.join(path,seriesname+'.prexf')
	f = open(xfname, 'w')
	for transform in transforms:
		if transform is not None:
			f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (
					transform[0,0],transform[0,1],
					transform[1,0],transform[1,1],
					transform[2,0],transform[2,1]))
	f.close()

def coarseAlignment(processpath, seriesname, commit=False):
		"""
#
# TO RUN TILTXCORR
#
$tiltxcorr -StandardInput
InputFile       08aug14f_008.st
OutputFile      08aug14f_008.prexf
TiltFile        08aug14f_008.rawtlt
RotationAngle   0.0
FilterSigma1    0.03
FilterRadius2   0.25
FilterSigma2    0.05

		"""

		inputparams = {
			'imagestack': os.path.join(processpath, seriesname+".st"),
			'output': os.path.join(processpath, seriesname+".prexf"),
			'tilts': os.path.join(processpath, seriesname+".rawtlt"),
		}
		commands = [
			"$tiltxcorr -StandardInput",
			"InputFile	"+inputparams['imagestack'],
			"OutputFile "+inputparams['output'],
			"TiltFile "+inputparams['tilts'],
			"TiltFile "+inputparams['tilts'],
			"RotationAngle   0.0",
			"FilterSigma1    0.03",
			"FilterRadius2   0.25",
			"FilterSigma2    0.05",
		]
		writeCommandAndRun(processpath,'xcorr',commands,[inputparams['output'],'xcorr.log'])
		if commit:
			xcorrdata = apTomo.insertImodXcorr(0.0,0.03,0.25,0.05)
			return xcorrdata

def convertToGlobalAlignment(processpath, seriesname):
		"""
$xftoxg
# global fit
0
08aug14f_008.prexf
08aug14f_008.prexg
		"""
		inputparams = {
			'input': os.path.join(processpath, seriesname+".prexf"),
			'output': os.path.join(processpath, seriesname+".prexg"),
		}
		commands = [
			"$xftoxg",
			"# global fit",
			"0",
			inputparams['input'],
			inputparams['output'],
		]
		writeCommandAndRun(processpath,'gcorr',commands,[inputparams['output'],'gcorr.log'])
		return readTransforms(inputparams['output'])

def readTransforms(filepath):
	file = open(filepath,'r')
	lines = file.readlines()
	transforms = []
	for line in lines:
		cleanlines = line.split('\n')
		items = cleanlines[0].split()
		transforms.append(map((lambda x: float(x)), items))
	return transforms

def createAlignedStack(processpath, seriesname):
		"""
# THIS IS A COMMAND FILE TO MAKE AN ALIGNED STACK FROM THE ORIGINAL STACK
#
####CreatedVersion#### 3.4.4
#
# It assumes that the views are in order in the image stack
#
# The -size argument should be ,, for the full area or specify the desired
# size (e.g.: ,10)
#
# The -offset argument should be 0,0 for no offset, 0,300 to take an area
# 300 pixels above the center, etc.
#
$newstack -input 08aug14f_008.st -output 08aug14f_008.ali -offset 0,0 -xform 08aug14f_
008.xf
$mrctaper 08aug14f_008.ali
		"""
		inputparams = {
			'alignedstack': os.path.join(processpath, seriesname+".ali"),
			'alignment': os.path.join(processpath, seriesname+".prexg"),
			'imagestack': os.path.join(processpath, seriesname+".st"),
		}
		commands = [
			"$newstack -input "+inputparams['imagestack']+" -output "+inputparams['alignedstack']+" -offset 0,0 -xform "+inputparams['alignment'],
			"$mrctaper "+inputparams['alignedstack'],
		]
		writeCommandAndRun(processpath,'newst',commands,[inputparams['alignedstack'],'newst.log'])


def recon3D(processpath, seriesname,thickness=100,invert=False):
		"""
# Command file to run Tilt
#
####CreatedVersion#### 3.4.4
#
# RADIAL specifies the frequency at which the Gaussian low pass filter begins
#   followed by the standard deviation of the Gaussian roll-off
#
# LOG takes the logarithm of tilt data after adding the given value
#
$tilt
08aug14f_008.ali
08aug14f_008_full.rec
FULLIMAGE 512 512
LOG 0.0
MODE 2
PERPENDICULAR
RADIAL 0.35 0.05
SCALE 1.39 500.0
SUBSETSTART 0 0
THICKNESS 100
TILTFILE 08aug14f_008.tlt
XAXISTILT 0.0
DONE

		"""
		inputparams = {
			'alignedstack': os.path.join(processpath, seriesname+".ali"),
			'tilts': os.path.join(processpath, seriesname+".rawtlt"),
			'recon': os.path.join(processpath, seriesname+"_full.rec"),
			'scale': 500.0,
			'thickness': thickness,
		}
		if invert:
			inputparams['scale'] = -inputparams['scale']
		commands = [
			"$tilt",
			inputparams['alignedstack'],
			inputparams['recon'],
			"FULLIMAGE 512 512",
			"LOG 0.0",
			"MODE 2",
			"PERPENDICULAR",
			"RADIAL 0.35 0.05",
			"SCALE 1.39 -500.0",
			"SUBSETSTART 0 0",
			"THICKNESS "+inputparams['thickness'],
			"TILTFILE "+inputparams['tilts'],
			"XAXISTILT 0.0",
		]
		writeCommandAndRun(processpath,'tilt',commands,[inputparams['recon'],'tilt.log'])

def trimVolume(processpath, runname, seriesname, volumename, center, size):
		"""
#	Command for triming reconstructed volume
#
# Tomography reconstruction y and z are flipped
trimvol -x 390,460 -z 477,537 -yz 08aug14f_008_full.rec test.rec
		"""	
		inputparams = {
			'recon': os.path.join(processpath, seriesname+"_full.rec"),
			'subvolume': os.path.join(processpath, runname+"/",volumename+"/",seriesname+"_"+volumename+".rec"),
			'xrange0': max(1,1+center[0] - size[0]/2),
			'zrange0': max(1,1+center[1] - size[1]/2),
		}
		fulltomo = mrc.read(inputparams['recon'])
		fullshape = fulltomo.shape
		inputparams['xrange1'] = min(fullshape[2],1+inputparams['xrange0'] + size[0])
		# y and z can be flip so use x dimension as limit
		inputparams['zrange1'] = min(fullshape[0],1+inputparams['zrange0'] + size[1])

		commands = [
			"$trimvol -x %d,%d -z %d,%d -yz %s %s"
				% (inputparams['xrange0'],inputparams['xrange1'],
				inputparams['zrange0'],inputparams['zrange1'],
				inputparams['recon'],
				inputparams['subvolume'],
				),
		]
		writeCommandAndRun(processpath,'trimvol',commands,[inputparams['subvolume'],'trimvol.log'])

def writeCommandAndRun(path,comname, commands, outputlist):		
		### make standard input for ctftilt
		commandlines = map((lambda x: x+"\n"), commands)
		comname = os.path.join(path,comname)
		comfile = open(comname+".com", "w")
		comfile.writelines(commandlines)
		comfile.close()
		os.system('chmod 755 '+comname+'.com')
		comfile = open(comname+".com", "r")
		for output in outputlist:
			if os.path.isfile(output):
				# clean up output before running
				apFile.removeFile(output)

		t0 = time.time()
		apDisplay.printMsg("running "+comname+" at "+time.asctime())
		proc = subprocess.Popen("submfg "+comname+".com", shell=True)
		proc.wait()
		comfile.close()

		apDisplay.printMsg(comname+" completed in "+apDisplay.timeString(time.time()-t0))

