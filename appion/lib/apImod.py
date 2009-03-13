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

def coarseAlignment(stackdir, processdir, seriesname, commit=False):
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
			'imagestack': os.path.join(stackdir, seriesname+".st"),
			'output': os.path.join(processdir, seriesname+".prexf"),
			'tilts': os.path.join(stackdir, seriesname+".rawtlt"),
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
		writeCommandAndRun(processdir,'xcorr',commands,[inputparams['output'],'xcorr.log'])
		if commit:
			xcorrdata = apTomo.insertImodXcorr(0.0,0.03,0.25,0.05)
			return xcorrdata

def convertToGlobalAlignment(processdir, seriesname):
		"""
$xftoxg
# global fit
0
08aug14f_008.prexf
08aug14f_008.prexg
		"""
		inputparams = {
			'input': os.path.join(processdir, seriesname+".prexf"),
			'output': os.path.join(processdir, seriesname+".prexg"),
		}
		commands = [
			"$xftoxg",
			"# global fit",
			"0",
			inputparams['input'],
			inputparams['output'],
		]
		writeCommandAndRun(processdir,'gcorr',commands,[inputparams['output'],'gcorr.log'])
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

def createAlignedStack(stackdir, processdir, seriesname,bin):
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
			'alignedstack': os.path.join(processdir, seriesname+".ali"),
			'alignment': os.path.join(processdir, seriesname+".prexg"),
			'imagestack': os.path.join(stackdir, seriesname+".st"),
			'bin': bin,
		}
		commands = [
			"$newstack -input "+inputparams['imagestack']+" -output "+inputparams['alignedstack']+" -offset 0,0 -xform "+inputparams['alignment']+" -bin %d" % inputparams['bin'],
			"$mrctaper "+inputparams['alignedstack'],
		]
		writeCommandAndRun(processdir,'newst',commands,[inputparams['alignedstack'],'newst.log'])


def recon3D(stackdir, processdir, seriesname, shape=(2048,2048), thickness=100, invert=False):
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
			'alignedstack': os.path.join(processdir, seriesname+".ali"),
			'tilts': os.path.join(stackdir, seriesname+".rawtlt"),
			'recon': os.path.join(processdir, seriesname+"_full.rec"),
			'scale': 1.0,
			'size': shape,
			'thickness': thickness,
		}
		if invert:
			inputparams['scale'] = -inputparams['scale']
		commands = [
			"$tilt",
			inputparams['alignedstack'],
			inputparams['recon'],
			"FULLIMAGE %d %d" %(shape[1],shape[0]),
			"LOG 0.0",
			"MODE 2",
			"PERPENDICULAR",
			"RADIAL 0.35 0.05",
			"SCALE 0.0 %.1f" %(inputparams['scale']),
			"SUBSETSTART 0 0",
			"THICKNESS %d" % inputparams['thickness'],
			"TILTFILE "+inputparams['tilts'],
			"XAXISTILT 0.0",
		]
		writeCommandAndRun(processdir,'tilt',commands,[inputparams['recon'],'tilt.log'])

def trimVolume(processdir, runname, seriesname, volumename, center, offsetz, size,yzflip=True):
		"""
#	Command for triming reconstructed volume
#
# Tomography reconstruction y and z are flipped
# full tomogram array axes [z,y,x]
# imod full_rec axes [y,z,x]
# center and size axes [x,y,z]
trimvol -x 390,460 -z 477,537 -yz 08aug14f_008_full.rec test.rec
		"""	
		inputparams = {
			'recon': os.path.join(processdir, seriesname+"_full.rec"),
			'subvolume': os.path.join(processdir, runname+"/",volumename+"/",seriesname+"_"+volumename+".rec"),
			'xrange0': max(1,center[0] - size[0]/2),
			'yrange0': max(1,center[1] - size[1]/2),
		}
		if yzflip:
			lookup = {'y':0,'z':1}
		else:
			lookup = {'y':1,'z':0}
		fulltomoheader = mrc.readHeaderFromFile(inputparams['recon'])
		fullshape = fulltomoheader['shape']
		center = list(center)
		center.append(fullshape[lookup['z']]/2+offsetz)
		inputparams['zrange0'] = max(1,center[2] - size[2]/2)
		inputparams['xrange1'] = min(fullshape[2],inputparams['xrange0'] + size[0]-1)
		inputparams['yrange1'] = min(fullshape[lookup['y']],inputparams['yrange0'] + size[1]-1)
		inputparams['zrange1'] = min(fullshape[lookup['z']],inputparams['zrange0'] + size[2]-1)
		if yzflip:
			commands = [
				"$trimvol -x %d,%d -y %d,%d -z %d,%d -yz %s %s"
					% (inputparams['xrange0'],inputparams['xrange1'],
					inputparams['zrange0'],inputparams['zrange1'],
					inputparams['yrange0'],inputparams['yrange1'],
					inputparams['recon'],
					inputparams['subvolume'],
					),
				]
		else:
			commands = [
				"$trimvol -x %d,%d -y %d,%d -z %d,%d %s %s"
					% (inputparams['xrange0'],inputparams['xrange1'],
					inputparams['yrange0'],inputparams['yrange1'],
					inputparams['zrange0'],inputparams['zrange1'],
					inputparams['recon'],
					inputparams['subvolume'],
					),
				]
		writeCommandAndRun(processdir,'trimvol',commands,[inputparams['subvolume'],'trimvol.log'])

def projectFullZ(processdir, runname, seriesname,yzflip=True):
		"""
#	Command for projecting full tomogram to z-axis
#
# Tomography reconstruction y and z are usually flipped
# full tomogram mrc file axes [x,z,y]
# clip average command need [x,y,z]
clip flipyz 09feb18c_002_full.rec temp.mrc
clip avg -2d -iz 0-199 temp.mrc projection.mrc
		"""	
		inputparams = {
			'recon': os.path.join(processdir, seriesname+"_full.rec"),
			'temp': os.path.join(processdir, "temp.rec"),
			'project': os.path.join(processdir, seriesname+"_zproject.mrc"),
		}
		fulltomoheader = mrc.readHeaderFromFile(inputparams['recon'])
		fullshape = fulltomoheader['shape']
		commands = []
		if yzflip:
			lookup = {'y':0,'z':1}
			inputparams['3d'] = inputparams['temp']
			commands.append(
				"$clip flipyz %s %s"
					% (inputparams['recon'],inputparams['temp'],
					)
				)
		else:
			lookup = {'y':1,'z':0}
			inputparams['3d'] = inputparams['recon']
		commands.append(
				"$clip avg -2d -iz %d-%d %s %s"
					% (0,fullshape[lookup['z']]-1,
					inputparams['3d'],inputparams['project'],
					),
			)	
		writeCommandAndRun(processdir,'projectZ',commands,[inputparams['temp'],inputparams['project'],'projectZ.log'])
		return inputparams['project']

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

