import os
import math
import subprocess
import shutil
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apFile
import time
from appionlib import apTomo
from pyami import mrc

def writeRawtltFile(path,seriesname,tilts):
	rawtltname = os.path.join(path,seriesname+'.rawtlt')
	f = open(rawtltname, 'w')
	for tilt in tilts:
		f.write('%6.2f\n' % (tilt,))
	f.close()

def linkStackRawtltFiles(stackdir,processdir,seriesname):
	for ext in ('st','rawtlt'):
		filename = seriesname+'.'+ext
		source = os.path.join(stackdir,filename)
		destination = os.path.join(processdir,filename)
		apFile.safeSymLink(source, destination)

def readShiftPrexgFile(path, seriesname):
	prexgname = os.path.join(path,seriesname+'.prexg')
	f = open(prexgname, 'r')
	lines = f.readlines()
	shifts = []
	for line in lines:
		cleanline = line.strip('\n')
		items = cleanline.split()
		shifts.append({'x':-float(items[-2]),'y':-float(items[-1])})
	f.close()
	return shifts

def writeShiftPrexfFile(path, seriesname,xpeaks):
	rawtltname = os.path.join(path,seriesname+'.prexf')
	f = open(rawtltname, 'w')
	for xpeak in xpeaks:
		if xpeak is not None:
			f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (1.0,0.0,0.0,1.0,-xpeak['x'],-xpeak['y']))
	f.close()

def writeTransformFile(path, seriesname,transforms,ext='prexf'):
	xfname = os.path.join(path,seriesname+'.'+ext)
	f = open(xfname, 'w')
	for transform in transforms:
		if transform is not None:
			# work on either form of the transform matrix
			if transform[0,2] or transform[1,2]:
				shiftx = transform[0,2]
				shifty = transform[1,2]
			else:
				shiftx = transform[2,0]
				shifty = transform[2,1]
			f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (
					transform[0,0],transform[0,1],
					transform[1,0],transform[1,1],
					shiftx,shifty))
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
			'alignment': os.path.join(processdir, seriesname+".xf"),
			'imagestack': os.path.join(stackdir, seriesname+".st"),
			'bin': bin,
		}
		if not os.path.exists(inputparams['alignment']):
			inputparams['alignment'] = os.path.join(processdir, seriesname+".prexg")
		commands = [
			"$newstack -input "+inputparams['imagestack']+" -output "+inputparams['alignedstack']+" -offset 0,0 -xform "+inputparams['alignment']+" -bin %d" % inputparams['bin'],
			"$mrctaper "+inputparams['alignedstack'],
		]
		writeCommandAndRun(processdir,'newst',commands,[inputparams['alignedstack'],'newst.log'])


def recon3D(stackdir, processdir, seriesname, shape=(2048,2048), thickness=100, invert=False, excludelist=[]):
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
EXCLUDELIST 11,12
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
		comfilename = writeTiltCom(processdir,inputparams['alignedstack'],inputparams['recon'],inputparams['tilts'],shape,inputparams['thickness'],0.0,0.0,(0,inputparams['scale']),excludelist)

		runCommand(processdir,'tilt',comfilename,[inputparams['recon'],'tilt.log'])

def writeTiltCom(processdir,align_file,recon_file,tilt_file,imageshape,thickness=100,offset=0.0,xaxistilt=0.0,scale=(0,250.0),excludelist=[]):
		commands = [
			"$tilt",
			align_file,
			recon_file,
			"FULLIMAGE %d %d" %(imageshape[1],imageshape[0]),
			"LOG 0.0",
			"MODE 2",
			"OFFSET %.1f" % offset,
			"PERPENDICULAR",
			"AdjustOrigin",
			"RADIAL 0.35 0.05",
			"SCALE %.1f %.1f" % scale,
			"SUBSETSTART 0 0",
			"THICKNESS %d" % (thickness),
			"TILTFILE %s" % tilt_file,
			"XAXISTILT %.1f" % xaxistilt,
		]
		if len(excludelist):
			commands.append("EXCLUDELIST2 "+ ','.join(map((lambda x: str(x+1)),excludelist))) 
		return writeCommand(processdir,'tilt',commands)

def createETomoBoundaryModelEDF(processdir, templatedir, seriesname, sample_thickness,pixelsize):
	template = open(os.path.join(templatedir,'etomo.edf.template'),'r')
	lines = template.readlines()
	template.close()
	outfile = open(os.path.join(processdir,'%s.edf' % (seriesname)),'w')
	for i,line in enumerate(lines):
		if 'Setup.DatasetName' in line:
			lines[i] = 'Setup.DatasetName=%s\n' % seriesname
		if 'Setup.PixelSize' in line:
			lines[i] = 'Setup.PixelSize=%.3f\n' % (pixelsize*1e9)
		if 'Setup.First.sample.THICKNESS' in line:
			lines[i] = 'Setup.First.sample.THICKNESS=%d\n' % (sample_thickness)
	outfile.writelines(lines)
	outfile.close()

def getETomoExcludeTiltNumber(processdir):
	values = getETomoParam(processdir,'tilt.com',['EXCLUDELIST ','EXCLUDELIST2 '])
	excludenumbers = set([])
	for value in values:
		bits = value.split(',')
		excludenumbers = excludenumbers.union(bits)
	return ','.join(excludenumbers)

def getETomoThickness(processdir,seriesname):
	values = getETomoParam(processdir,'tilt.com',['THICKNESS '])
	if len(values) != 1:
		apDisplay.printError('Tomogram Thickness not found')
	return int(values[0])

def getETomoBin(processdir,seriesname):
	edfname = '%s.edf' % (seriesname) 
	values = getETomoParam(processdir,edfname,['Setup.TomoGenBinningA=','Setup.FinalStackBinningA='])
	bin = 1
	for value in values:
		bin *= int(value)
	return bin

def getSubTomoBoundary(processdir,seriesname,axis):
	'''
	Get the start and end coordinate at a particular axis.
	The definition of origin may or may not apply to tomograms
	generated outside imod.
	'''
	fulltomopath = os.path.join(processdir,seriesname+'_full.rec')
	subtomopath = os.path.join(processdir,seriesname+'.rec')
	fullheader = mrc.readHeaderFromFile(fulltomopath)
	subheader = mrc.readHeaderFromFile(subtomopath)

	lenkey = axis+'len'
	originkey = axis+'origin'
	mkey = 'm'+axis
	# There is a rotation around x-axis in full tomogram
	fullorigin = {'xorigin':fullheader['xorigin'],'yorigin':fullheader['zorigin'],'zorigin':fullheader['yorigin']}
	fullm = {'mx':fullheader['mx'],'my':fullheader['mz'],'mz':fullheader['my']}
	# full and sub tomo should have the same pixelsize
	pixelsize = subheader[lenkey] / subheader[mkey]
	if axis != 'z':
		start = int((fullorigin[originkey] - subheader[originkey]) / pixelsize)
	else:
		# z origin is defined different from x and y
		start = -int((fullorigin[originkey] + subheader[originkey]) / pixelsize) + int(fullm[mkey])
	end = start + int(subheader[mkey])
	return (start,end)

def getImodZShift(processdir):
	shift_str = getETomoParam(processdir,'tilt.com',['SHIFT'])[0]
	bits = shift_str.split(' ')
	return float(bits[-1])
		
def getETomoParam(processdir, filename, searchkeys):
	paramfile = open(os.path.join(processdir,filename),'r')
	lines = paramfile.readlines()
	paramfile.close()
	values = []
	for line in lines:
		for key in searchkeys:
			if key in line:
				bits = line.split(key)
				values.append(bits[-1][:-1])
	return values

def writeETomoNewstComTemplate(processdir, seriesname):
	'''
	etomo needs this template to continue after sampling.
	It also only understand local files.
	'''
	inputparams = {
		'alignedstack': seriesname+".ali",
		'alignment': seriesname+".xf",
		'imagestack': seriesname+".st",
		'bin': 1,
	}
	commands = [
		"$newstack -input "+inputparams['imagestack']+" -output "+inputparams['alignedstack']+" -offset 0,0 -xform "+inputparams['alignment']+" -bin %d" % inputparams['bin'],
		"$mrctaper "+inputparams['alignedstack'],
		"$if (-e ./savework) ./savework",
	]
	writeCommand(processdir,'newst',commands)

def makeFilesForETomoSampleRecon(processdir, stackdir,aligndir, templatedir, seriesname, thickness, pixelsize,yspacing,has_rotation=False):
	'''
	Make or link local files required by etomo to redo sampling, creating tomopitch model, and reconstruct the volume.
	'''
	# etomo status file
	createETomoBoundaryModelEDF(processdir,templatedir,seriesname,thickness,pixelsize)
	# required by remaking sample tomograms inside etomo
	if has_rotation:
		apDisplay.printWarning('eTomo wants to regenerate global alignment from non-rotated local alignment.  This alignment with rotation will not work right')
	else:
		# prexf file is generated from database values if this function is called from tomomaker.  It is better not to change it if exists.
		prexf = seriesname+".prexf"
		alignprexf = os.path.join(aligndir,prexf)
		localprexf = os.path.join(processdir,prexf)
		apFile.safeCopy(alignprexf,localprexf)
		writeETomoNewstComTemplate(processdir, seriesname)
		rawtltname = '%s.rawtlt' % (seriesname)
		shutil.copy(os.path.join(stackdir,rawtltname),os.path.join(processdir,rawtltname))
	# required by tomopitch model making
	tomopitchname = 'tomopitch.com'
	imodcomdir = os.path.join(os.environ['IMOD_DIR'],'com')
	tomopitchpath = os.path.join(processdir,tomopitchname)
	shutil.copy(os.path.join(imodcomdir,tomopitchname),tomopitchpath)
	apFile.replaceUniqueLinePatternInTxtFile(tomopitchpath,'SpacingInY','SpacingInY\t%.1f\n' % yspacing)
	
	# required by "Final Aligned Stack" step
	stackname = '%s.st' % (seriesname)
	apFile.safeSymLink(os.path.join(stackdir,stackname),os.path.join(processdir,stackname))

def sampleRecon(stackdir, processdir, aligndir, seriesname, samplesize=10, sampleoffset=0.66, thickness=100, excludelist=[]):
	inputparams = {
		'alignedstack': seriesname+".ali",
		'xf': seriesname+".xf",
		'rawtilts': os.path.join(stackdir, seriesname+".rawtlt"),
		'tilts': os.path.join(seriesname+".tlt"),
		'tiltstack': os.path.join(stackdir, seriesname+".st"),
		'recon': seriesname+"_full.rec",
		'scale': 250.0,
		'thickness': thickness,
	}
	alignxf = os.path.join(aligndir, seriesname+".xf")
	linkxf = inputparams['xf']
	files_to_copy = [(alignxf,linkxf),(inputparams['rawtilts'],inputparams['tilts'])]
	for filepair in files_to_copy:
		apFile.safeCopy(filepair[0],filepair[1])
	st_shape = apFile.getMrcFileShape(inputparams['tiltstack'])
	# shape is in (z, y, x) size for imod is in (x,y)
	inputparams['size']=(st_shape[2],st_shape[1])
	total_tilts = st_shape[0]
	if samplesize == 'all' or samplesize > total_tilts:
		samplesize = total_tilts
	# calculate sampletilt range that reduces the process time
	sampletilt_start = max(int((total_tilts - samplesize)/2.0),1)
	sampletilt_end = min(sampletilt_start + samplesize - 1,total_tilts)
	# calculate the 3 offsets
	sampleoffset = int (st_shape[1] * sampleoffset / 2.0)
	st_y_center = int (st_shape[1] / 2.0)
	sampleoffsets = {'mid':0,'top':sampleoffset,'bot':(-1)*sampleoffset}
	# write basic tilt.com without processdir
	comfilename = writeTiltCom(processdir,inputparams['alignedstack'],inputparams['recon'],inputparams['tilts'],inputparams['size'],inputparams['thickness'],0.0,0.0,(0,inputparams['scale']),excludelist)
	# make commandlines
	commands = []
	for key in sampleoffsets.keys():
		commands.extend([
			'$newstack -size ,%d -offset 0,%d -xf %s %s %s' % (total_tilts,sampleoffsets[key],inputparams['xf'],inputparams['tiltstack'],inputparams['alignedstack']),
			'$sampletilt %d %d %d %s %s.rec tilt.com' % (sampletilt_start,sampletilt_end,sampleoffsets[key]+st_y_center,seriesname,key)
		])
	writeCommandAndRun(processdir,'sample',commands,[inputparams['alignedstack'],'sample.log'])

def trimVolume(processdir, runname, seriesname, volumename, center, offsetz, size,rotx=True):
		"""
#	Command for triming reconstructed volume
#
# Full Tomography reconstruction is X,Z,Y need to rotate around x
# full tomogram array axes [z,y,x]
# imod full_rec axes [y,z,x]
# center and size axes [x,y,z]
trimvol -x 390,460 -z 477,537 -rx 08aug14f_008_full.rec test.rec
		"""	
		inputparams = {
			'recon': os.path.join(processdir, seriesname+"_full.rec"),
			'subvolume': os.path.join(processdir, runname+"/",volumename+"/",seriesname+"_"+volumename+".rec"),
			'xrange0': max(1,center[0] - size[0]/2),
			'yrange0': max(1,center[1] - size[1]/2),
		}
		if rotx:
			lookup = {'y':0,'z':1}
		else:
			lookup = {'y':1,'z':0}
		fullshape = apFile.getMrcFileShape(inputparams['recon'])
		center = list(center)
		center.append(fullshape[lookup['z']]/2+offsetz)
		inputparams['zrange0'] = max(1,center[2] - size[2]/2)
		inputparams['xrange1'] = min(fullshape[2],inputparams['xrange0'] + size[0]-1)
		inputparams['yrange1'] = min(fullshape[lookup['y']],inputparams['yrange0'] + size[1]-1)
		inputparams['zrange1'] = min(fullshape[lookup['z']],inputparams['zrange0'] + size[2]-1)
		if rotx:
			commands = [
				"$trimvol -x %d,%d -y %d,%d -z %d,%d -rx %s %s"
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

def transformVolume(volumepath,operation):
		"""
#	Command for transform tomogram
# for example, flipyz flip y and z axis (transpose, and results in handness change)
# clip flipyz 09feb18c_002_full.rec temp.mrc
# clip rotx 09feb18c_002_full.rec temp.mrc
		"""	
		volumedir = os.path.dirname(volumepath)
		volumefilename = os.path.basename(volumepath)
		transformedfilename = volumefilename+"."+operation
		inputparams = {
			'recon': os.path.join(volumedir, volumefilename),
			'out': os.path.join(volumedir, transformedfilename),
		}
		commands = []
		inputparams['3d'] = inputparams['out']
		commands.append(
			"$clip %s %s %s"
				% (operation,inputparams['recon'],inputparams['out'],
				)
			)
		writeCommandAndRun(volumedir,operation,commands,[inputparams['out'],operation+'.log'])
		return os.path.join(volumedir,transformedfilename)

def pad(volumepath,originalshape,finalshape,bin=1,order='XZY'):
	# This padding is only in x and y direction symmetrically and assume
	# XYZ order of the full tomogram
	volumedir = os.path.dirname(volumepath)
	volumefilename = os.path.basename(volumepath)
	padfilename = volumefilename+".pad"
	padpath = os.path.join(volumedir, padfilename)
	inputparams = {
		'in': os.path.join(volumedir, volumefilename),
		'out': padpath,
		'padwidth': 
			{'X':(finalshape[1]/bin - originalshape[1]) / 2,
				'Y':(finalshape[0]/bin - originalshape[0]) / 2,
				'Z':0
			},
	}
	padstring = ""
	for axis in order:
		padstring += "%d " % (inputparams['padwidth'][axis])
	commands = [
		"$taperoutvol",
		inputparams['in'],
		inputparams['out'],
		"/",
		padstring
	]
	writeCommandAndRun(volumedir,'volumepad',commands,[inputparams['out'],'volumepad.log'])
	return padpath

def projectFullZ(processdir, runname, seriesname,bin=1,rotx=True,flipyz=False):
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
		fullshape = apFile.getMrcFileShape(inputparams['recon'])
		commands = []
		if rotx or flipyz:
			op = ''
			if rotx:
				op += ' rotx'
			if flipyz:
				op += ' flipyz'
			lookup = {'y':0,'z':1}
			inputparams['3d'] = inputparams['temp']
			commands.append(
				"$clip"+op+" %s %s"
					% (inputparams['recon'],inputparams['temp'],
					)
				)
		else:
			lookup = {'y':1,'z':0}
			inputparams['3d'] = inputparams['recon']
		# limit slices for projection to 200 to save time.
		zcenter = int(fullshape[lookup['z']] / 2)
		zstart = max(0,zcenter - 100)
		zend = min(fullshape[lookup['z']]-1,zcenter + 99)
		commands.append(
				"$clip avg -2d -iz %d-%d %s %s"
					% (zstart,zend,
					inputparams['3d'],inputparams['project'],
					),
			)	
		writeCommandAndRun(processdir,'projectZ',commands,[inputparams['temp'],inputparams['project'],'projectZ.log'])
		if bin > 1:
			# unbin the projection
			a = mrc.read(inputparams['project'])
			b = apImage.scaleImage(a,bin)
			mrc.write(b,inputparams['project'])
		return inputparams['project']

def writeCommand(path,comname, commands):		
		### make standard input for ctftilt
		commandlines = map((lambda x: x+"\n"), commands)
		comfilename = comname+".com"
		comfilepath = os.path.join(path,comfilename)
		comfile = open(comfilepath, "w")
		comfile.writelines(commandlines)
		comfile.close()
		proc = subprocess.Popen('chmod 755 '+comfilepath, shell=True)
		proc.wait()
		return comfilename

def writeCommandAndRun(path,comname, commands, outputlist):		
		comfilename = writeCommand(path,comname,commands)
		runCommand(path,comname, comfilename, outputlist)

def runCommand(path,comname, comfilename, outputlist):
		# change directory because submfg can not handle long path name in front of the command to run
		currentdir = os.getcwd()
		os.chdir(path)
		for output in outputlist:
			if os.path.isfile(output):
				# clean up output before running
				apFile.removeFile(output)

		t0 = time.time()
		apDisplay.printMsg("running "+comname+" at "+time.asctime())
		proc = subprocess.Popen("submfg "+comfilename, shell=True)
		proc.wait()

		apDisplay.printMsg(comname+" completed in "+apDisplay.timeString(time.time()-t0))
		os.chdir(currentdir)

