#python
import os
import re
import subprocess
import math
import numpy
#appionlib
from appionlib import starFile
from appionlib import apInstrument
from appionlib import apParam
#pyami
from pyami import mrc

def getRelionVersion():
	## no obvious version output info, so tricky
	# first see if relion is loaded:
	if apParam.getExecPath("relion",die=True) is not None:
		# now see if there exists a relion 2.0 function:
		if apParam.getExecPath("relion_helix_toolbox",die=False) is not None:
			return 2.0
		else:
			return 1.4

def readStarFileDataBlock(starfile, datablock):
	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()
	return loopDict


def writeLoopDictToStarFile(loopDict, datablockname, starfilename):

	labels = loopDict[0].keys()
	valueSets = []
	for line in loopDict:
		params = ""
		for p in line.values():
			params += " %s" % p
		valueSets.append(params)
	star = starFile.StarFile(starfilename)
	star.buildLoopFile(datablockname, labels, valueSets)
	star.write()


def excludeClassesFromRelionDataFile(instarfile, datablock, outlist, outstarfile, *classlist):
	### input is Relion data star file, e.g. run1_it025_data.star
	### datablock: The start of a data block is defined by the keyword "data_" followed by an optional string for identification (e.g., "data_images")
	### outputs a list without the particles belonging to excluded classes
	### list is EMAN-style, particle numbering starts with 0 (note that in Relion particle numbering starts with 1)
	### outstarfile is the output star file
	### *classlist can be as many classes as you wish separated by comma, e.g. 1 or 1,3,6; classes are numbered Relion format, starting with 1

	star = starFile.StarFile(instarfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()

	badparts = []
	goodparts = []
	loopDictNew = []
	for i in range(len(loopDict)):
		rlnpart = float(loopDict[i]['_rlnImageName'].split("@")[0]) # starts with 1
		rlnclass = float(loopDict[i]['_rlnClassNumber'])
		bad = False
		badpart = 0
		for c in classlist:
			if float(c) == rlnclass:
				badpart = int(rlnpart)
				bad = True
		if bad is True:
			badparts.append(badpart)
		else:
			goodparts.append(int(rlnpart))
			loopDictNew.append(loopDict[i])
	badparts.sort()
	goodparts.sort()
	f = open(outlist, "w")
	for gp in goodparts:
		f.write("%d\n" % (gp-1)) # EMAN-style numbering, starts with 0
	f.close()
	
	# selected star file parameters, write star file with excluded images
	writeLoopDictToStarFile(loopDictNew, datablock, outstarfile)

def excludeClassesFromRelionDataFile2(starfile, outlist, *classlist):
	### input is Relion data star file, e.g. run1_it025_data.star
	### outputs a list without the particles belonging to excluded classes
	### list is EMAN-style, particle numbering starts with 0 (note that in Relion particle numbering starts with 1)
	### *classlist can be as many classes as you wish separated by comma, e.g. 1 or 1,3,6; classes are numbered Relion format, starting with 1

	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock("data_images")
	loopDict = dataBlock.getLoopDict()

	badparts = []
	goodparts = []
	for i in range(len(loopDict)):
		rlnpart = float(loopDict[i]['_rlnImageName'].split("@")[0]) # starts with 1
		rlnclass = float(loopDict[i]['_rlnClassNumber'])
		bad = False
		badpart = 0
		for c in classlist:
			if float(c) == rlnclass:
				badpart = int(rlnpart)
				bad = True
		if bad is True:
			badparts.append(badpart)
	for i in range(len(loopDict)):
		if (i+1) not in badparts:
			goodparts.append(i+1)
	f = open(outlist, "w")
	for gp in goodparts:
		f.write("%d\n" % (gp-1)) # EMAN-style numbering, starts with 0
	f.close()
	loopDictNew = starFile.LoopBlock
#	loopDictNew = []
	print dir(loopDict), "loop Dict"
	print dir(loopDictNew), "loop Dict New"
	print len(loopDict), "length of loop Dict"
	print loopDict[0]
	for gp in goodparts:
		loopDictNew.append(loopDict[gp-1])
	print len(loopDictNew), "length of loop Dict New"
	dataBlockNew = starFile.DataBlock("data_images")
	dataBlockNew.setLoopBlocks([loopDictNew])
	print dir(dataBlockNew)
	print len(dataBlockNew.loopBlocks)
	star.setDataBlock(dataBlockNew,"data_images")
	dbnew = star.getDataBlock("data_images")
	print dbnew.name, "****"
	print dir(dbnew)
	print len(dbnew.loopBlocks)
	loopDict = dbnew.getLoopDict()
	print len(loopDict)
	star.write("destination.star")

def listFileFromRelionStarFile(starfile, outlist, datablock="data_images"):
	### write out an EMAN-style list file (numbering starts with 0) based on a relion star file with images and image numbers

 	star = starFile.StarFile(starfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()

	allparts = []
	for i in range(len(loopDict)):
		allparts.append(int(loopDict[i]['_rlnImageName'].split("@")[0])) # starts with 1
	allparts.sort()

	f = open(outlist, "w")
	for p in allparts:
		f.write("%d\n" % (p-1)) # EMAN-style numbering, starts with 0
	f.close()

def sortRelionStarFileByParticleNumber(instarfile, outstarfile, datablock="data_images"):
	star = starFile.StarFile(instarfile)
	star.read()
	dataBlock = star.getDataBlock(datablock)
	loopDict = dataBlock.getLoopDict()
	
	partdict = {}
	for i in range(len(loopDict)):
		rlnpart = (int(loopDict[i]['_rlnImageName'].split("@")[0])) # starts with 1
		partdict[rlnpart] = loopDict[i]
	l = sorted(partdict, key=lambda key: partdict[key])
	l.sort()

	# write sorted star file
	loopDictNew = []
	for val in l:
		loopDictNew.append(partdict[val])
	writeLoopDictToStarFile(loopDictNew, datablock, outstarfile)

def getStarFileColumnLabels(starfile):
	# returns array of labels, assuming they are in order
	# and correspond to the data
	labels=[]
	for line in open(starfile):
		l = line.strip().split()
		if line[:4]=="_rln":
			labels.append(l[0])
			continue
		if len(l) > 2:
			return labels

def getColumnFromRelionLine(line,col):
	# return a specified column (starting with 0)
	l = line.strip().split()
	if (len(l)<col or l[:4]=="_rln" or l[0] in ['data_','loop_']):
		return None
	return l[col]
	
def getMrcParticleFilesFromStar(starfile):
	# returns array of mrc files containing particles
	# first get header info
	mrclist = []
	for p in getPartsFromStar(starfile):
		micro = p.split('@')[1]
		# Relion usually uses relative paths, check:
		if micro[0]!="/":
			micro = os.path.join(os.path.dirname(starfile),micro)
		if micro not in mrclist: mrclist.append(micro)
	return mrclist

def getPartsFromStar(starfile):
	# returns array of particles
	labels = getStarFileColumnLabels(starfile)
	namecol = labels.index('_rlnImageName')
	partlist = []
	for line in open(starfile):
		p=getColumnFromRelionLine(line,namecol)
		if p: partlist.append(p)
	return partlist

def writeRelionStarHeader(labels, outstarfile):
	ofile = open(outstarfile,'w')
	ofile.write("\ndata_images\n\nloop_\n")
	ofile.write("\n".join("%s #%i"%(label,index+1) for index,label in enumerate(labels)))
	ofile.write("\n")
	ofile.close()

def writeRelionMicrographsStarHeader(outstarfile,ctfinfo=False):
	labels = ["_rlnMicrographName",
		"_rlnMagnification",
		"_rlnDetectorPixelSize"]
	if ctfinfo is True:
		labels.extend(["_rlnCtfImage",
		"_rlnDefocusU",
		"_rlnDefocusV",
		"_rlnDefocusAngle",
		"_rlnVoltage",
		"_rlnSphericalAberration",
		"_rlnAmplitudeContrast",
		"_rlnCtfFigureOfMerit"])
	writeRelionStarHeader(labels, outstarfile)

def formatCtfForRelion(imgdata,ctfdata,apix):
	"""
	returns array with ctf values required for RELION CTF
	we can't import apDatabase, so supply apix in Angstroms
	"""
	c={}

	#magnification, pixel size
	c['dstep'] = imgdata['camera']['pixel size']['x']*1e6
	c['mag'] = c['dstep']/apix*1e4

	# defoci & angle of astig
	c['defU'] = ctfdata['defocus1']*1.0e10
	c['defV'] = ctfdata['defocus2']*1.0e10
	c['defAngle'] = ctfdata['angle_astigmatism']

	# get kev, CS, ampcontrast
	c['kev'] = imgdata['scope']['high tension']/1000.0
	c['cs'] = apInstrument.getCS(ctfdata)
	c['amp'] = ctfdata['amplitude_contrast']

	# get ctfestimation fig of merit (CC)
	c['cc'] = ctfdata['cross_correlation']
	if c['cc'] is None: c['cc'] = 0

	return c
	
def generateCtfFile(imgname,cs,kev,amp,mag,dstep,defU,defV,defAngle,cc):
	f = open(imgname,'w')
	f.write(" CS[mm], HT[kV], AmpCnst, XMAG, DStep[um]\n")
	f.write(" %4.1f   %6.1f    %4.2f  %8.1f  %7.3f\n"%(cs,kev,amp,mag,dstep))
	f.write("      DFMID1      DFMID2      ANGAST	  CC\n")
	f.write("   %9.2f   %9.2f    %8.2f    %8.5f  Final Values\n"%(defU,defV,defAngle,cc))
	f.close()

def extractParticles(starfile,rootname,boxsize,bin,bgradius,pixlimit,invert,ext,nproc=1,logfile=None):
	relion_version = getRelionVersion()

	relionexe = "`which relion_preprocess"
	if nproc > 1:
		relionexe = "mpirun %s_mpi"%relionexe
	relionexe+= "`"

	relioncmd = "%s"%relionexe
	if relion_version < 2:
		relioncmd+= " --o %s --mic_star %s"%(rootname,starfile)
	else:
		relioncmd+= " --part_star %s.star --i %s"%(rootname,starfile)
		relioncmd+= " --coord_dir %s"%(os.path.abspath("."))
	relioncmd+= " --coord_suffix %s --extract"%(ext)
	relioncmd+= " --extract_size %i"%boxsize
	if bin is not None:
		relioncmd+=" --scale %i"%(int(boxsize/bin))
	relioncmd+= " --norm --bg_radius %i"%(bgradius)
	if pixlimit is not None:
		pixlimit=abs(pixlimit)
		relioncmd+= " --white_dust %.1f --black_dust %.1f"%(pixlimit,pixlimit)
	if invert is True:
		relioncmd+= " --invert_contrast"
	if logfile:
		logf = open(logfile,'w')
		logf.write(relioncmd)
		logf.close()
	subprocess.Popen(relioncmd, shell=True).wait()

def replaceNaNImageInStack(stackfile, outfile=None):
	'''
	Relion 2D classification sometimes give NaN array in reference
	image stack where it should be zeros.  This function checks 
	and replace them if needed.  See Issue #4396
	'''
	h = mrc.readHeaderFromFile(stackfile)
	nz = h['nz']
	badz = []
	if not outfile:
		outfile = stackfile
	for i in range(nz):
		a = mrc.read(stackfile, i)
		if math.isnan(a[0,0]):
			badz.append(i)
	if badz:
		a = mrc.read(stackfile)
		zeros = numpy.zeros((a.shape[1],a.shape[2]))
		for i in badz:
			a[i,:,:] = zeros
		mrc.write(a, outfile)
		mrc.update_file_header(outfile, h)
	return len(badz)

def adjustPartDict(relionpartdict, reflist):
	'''
	For the particle defined in relionpartdict, adjust its shift/rotation 
	parameters by the shift/rotation parameters in reflist at its assigned
	class.
	'''
	refnum = int(relionpartdict['_rlnClassNumber'])
	refdict = reflist[refnum-1]
	#APPION uses shift, mirror, clockwise rotate system for 2D alignment
	#In order for Appion to get the parameters right, we have to do the mirror operation first.
	particleNumber = int(re.sub("\@.*$", "", relionpartdict['_rlnImageName']))
	xshift = 1.0*float(relionpartdict['_rlnOriginX'])+refdict['xshift']
	yshift = -1.0*float(relionpartdict['_rlnOriginY'])+refdict['yshift']
	inplane = wrap360(float(relionpartdict['_rlnAnglePsi'])+refdict['inplane'])
	newpartdict = {
		'partnum': particleNumber,
		'xshift': xshift,
		'yshift': yshift,
		'inplane': inplane,
		'refnum': refnum,
		'mirror': True, #not available in RELION, but must be True to correct alignments
		'spread': float(relionpartdict['_rlnMaxValueProbDistribution']), #check for better
	}
	if particleNumber < 10:
		print "%03d -- %.1f -- %s"%(particleNumber, newpartdict['inplane'], relionpartdict['_rlnAnglePsi'])
	return newpartdict

def wrap360(theta):
	f = theta % 360
	if f > 180:
		f = f - 360.0
	return f

