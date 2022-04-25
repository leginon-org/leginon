#!/usr/bin/env python
#
import os
import re
import sys
import time
import glob
import math
import numpy
import string
import subprocess
import shutil
#appion
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apEulerCalc
from appionlib import apFile
from appionlib import apParam
from appionlib import apImagicFile
from pyami import spider, mrc, mem
from appionlib.apSpider import operations

#======================
#======================
def convertStackToXmippData(instack, outdata, maskpixrad, boxsize, numpart=None):
	"""
	From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Img2Data

	This program applies a mask to a set of images. 
	This set is given by a selfile. 
	After applying the mask the result is storaged as a vector in the following format:
		The first line indicates the dimension of the vectors and the number of vectors.
		The rest of the lines are the feature vectors. 
		Each line is a vector and each column is a vectors' component (pixels values inside the mask). 
	"""
	apDisplay.printMsg("Convert stack file to Xmipp data file")
	maskfile = "circlemask.spi"
	operations.createMask(maskfile, maskpixrad, boxsize)
	partlistdocfile = breakupStackIntoSingleFiles(instack, numpart=numpart)
	convertcmd = "xmipp_convert_img2data -i %s -mask %s -o %s"%(partlistdocfile, maskfile, outdata)
	proc = subprocess.Popen(convertcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
	proc.wait()
	outfilesize = apFile.fileSize(outdata)
	partfilesize = apFile.fileSize(partlistdocfile)
	if outfilesize < 2*partfilesize:
		apDisplay.printError("Outdata conversion did not work, data file smaller than docfile, %s < %s"
			%(apDisplay.bytes(outfilesize), apDisplay.bytes(partfilesize)))
	apFile.removeFilePattern("partfiles/*")

	return outdata

#======================
#======================
def convertXmippDataToStack(indata, outstack, maskpixrad):
	"""
	From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Img2Data

	This program applies a mask to a set of images. 
	This set is given by a selfile. 
	After applying the mask the result is storaged as a vector in the following format:
		The first line indicates the dimension of the vectors and the number of vectors.
		The rest of the lines are the feature vectors. 
		Each line is a vector and each column is a vectors' component (pixels values inside the mask). 
	"""
	convertcmd = "xmipp_convert_data2img "

#======================
#======================
#======================
#======================
class breakUpStack(apImagicFile.processStack):
	#===============
	def preLoop(self):
		self.dirnum = 0
		if self.stepsize > 4096:
			numchucks = math.ceil(self.numpart/4096.0)
			self.stepsize = int(self.numpart/numchucks)
		self.numdir = math.ceil(self.numpart/float(self.stepsize))
		self.message("Splitting %d particles into %d folders with %d particles per folder"
			%(self.numpart, self.numdir, self.stepsize))
		self.partdocf = open(self.partdocfile, "w")

	#===============
	def processStack(self, stackarray):
		self.dirnum += 1
		self.partdir = os.path.join(self.rootdir, "%03d"%(self.dirnum))
		apParam.createDirectory(self.partdir, warning=False)
		for partarray in stackarray:
			self.processParticle(partarray)
			self.index += 1 #you must have this line in your loop

	#===============
	def processParticle(self, partarray):
		if self.filetype == "mrc":
			partfile = os.path.join(self.partdir, "part%06d.mrc"%(self.index))
			mrc.write(partarray, partfile)
		else:
			partfile = os.path.join(self.partdir, "part%06d.spi"%(self.index))
			try:
				spider.write(partarray, partfile)
			except:
				print partarray
				apDisplay.printWarning("failed to write spider file for part index %d"%(self.index))
				print partarray.shape
				spider.write(partarray, partfile)
		self.partdocf.write(os.path.abspath(partfile)+" 1\n")

	#===============
	def postLoop(self):
		self.partdocf.close()

#======================
#======================
def breakupStackIntoSingleFiles(stackfile, partdir="partfiles", numpart=None, filetype="spider"):
	"""
	takes the stack file and creates single spider files ready for processing
	"""
	apDisplay.printColor("Breaking up spider stack into single files, this can take a while", "cyan")
	apParam.createDirectory(partdir)
	partdocfile = "partlist.sel"

	### setup
	breaker = breakUpStack()
	if numpart is not None:
		breaker.numpart = numpart
	breaker.rootdir = partdir
	breaker.filetype = filetype
	breaker.partdocfile = partdocfile

	### make particle files
	breaker.start(stackfile)

	return partdocfile

#======================
#======================
def gatherSingleFilesIntoStack(selfile, stackfile, filetype="spider"):
	"""
	takes a selfile and creates an EMAN stack
	"""
	selfile = os.path.abspath(selfile)
	stackfile = os.path.abspath(stackfile)
	if stackfile[-4:] != ".hed":
		apDisplay.printWarning("Stack file does not end in .hed")
		stackfile = stackfile[:-4]+".hed"

	apDisplay.printColor("Merging files into a stack, this can take a while", "cyan")

	starttime = time.time()

	if not os.path.isfile(selfile):
		apDisplay.printError("selfile does not exist: "+selfile)

	### Process selfile
	fh = open(selfile, 'r')
	filelist = []
	for line in fh:
		sline = line.strip()
		if sline:
			args=sline.split()
			if (len(args)>1):
				filename = args[0].strip()
				filelist.append(filename)
	fh.close()

	### Set variables
	boxsize = apFile.getBoxSize(filelist[0])
	partperiter = int(1e9/(boxsize[0]**2)/16.)
	if partperiter > 4096:
		partperiter = 4096
	apDisplay.printMsg("Using %d particle per iteration"%(partperiter))
	numpart = len(filelist)
	if numpart < partperiter:
		partperiter = numpart

	### Process images
	imgnum = 0
	stacklist = []
	stackroot = stackfile[:-4]
	### get memory in kB
	startmem = mem.active()
	while imgnum < len(filelist):
		filename = filelist[imgnum]
		index = imgnum % partperiter
		if imgnum % 100 == 0:
			sys.stderr.write(".")
			#sys.stderr.write("%03.1fM %d\n"%((mem.active()-startmem)/1024., index))
			if mem.active()-startmem > 2e6:
				apDisplay.printWarning("Out of memory")
		if index < 1:
			#print "img num", imgnum
			### deal with large stacks, reset loop
			if imgnum > 0:
				sys.stderr.write("\n")
				stackname = "%s-%d.hed"%(stackroot, imgnum)
				apDisplay.printMsg("writing single particles to file "+stackname)
				stacklist.append(stackname)
				apFile.removeStack(stackname, warn=False)
				apImagicFile.writeImagic(stackarray, stackname, msg=False)
				perpart = (time.time()-starttime)/imgnum
				apDisplay.printColor("part %d of %d :: %.1fM mem :: %s/part :: %s remain"%
					(imgnum+1, numpart, (mem.active()-startmem)/1024. , apDisplay.timeString(perpart), 
					apDisplay.timeString(perpart*(numpart-imgnum))), "blue")
			stackarray = []
		### merge particles
		if filetype == "mrc":
			partimg = mrc.read(filename)
		else:
			partimg = spider.read(filename)
		stackarray.append(partimg)
		imgnum += 1

	### write remaining particles to file
	sys.stderr.write("\n")
	stackname = "%s-%d.hed"%(stackroot, imgnum)
	apDisplay.printMsg("writing particles to file "+stackname)
	stacklist.append(stackname)
	apImagicFile.writeImagic(stackarray, stackname, msg=False)

	### merge stacks
	apFile.removeStack(stackfile, warn=False)
	apImagicFile.mergeStacks(stacklist, stackfile)
	print stackfile
	filepart = apFile.numImagesInStack(stackfile)
	if filepart != numpart:
		apDisplay.printError("number merged particles (%d) not equal number expected particles (%d)"%
			(filepart, numpart))
	for stackname in stacklist:
		apFile.removeStack(stackname, warn=False)

	### summarize
	apDisplay.printColor("merged %d particles in %s"%(imgnum, apDisplay.timeString(time.time()-starttime)), "cyan")

#======================
#======================
def createSubFolders(partdir, numpart, filesperdir):
	i = 0
	dirnum = 0
	while i < numpart:
		dirnum += 1
		apParam.createDirectory(os.path.join(partdir, str(dirnum)), warning=False)
		i += filesperdir
	return dirnum

#======================
#======================
def locateXmippProtocol(protocolname):
	### get Xmipp directory
	proc = subprocess.Popen('which xmipp_protocols',
		shell=True,stdout=subprocess.PIPE)
	stdout_value = proc.communicate()[0]
	i = stdout_value.find("bin/xmipp_protocols");
	if (i==-1):
		apDisplay.printError("Cannot locate Xmipp protocol %s" % (protocolname));
	XmippDir=stdout_value[0:i]

	### make sure protocolname is given correctly
	if re.search(".py", protocolname):
		protocolname = re.sub(".py", "", protocolname)
	protocolname_new = protocolname+".py"
	p = os.path.join(XmippDir, "protocols", protocolname_new)
	if os.path.isfile(p):
		return p
	else:
		apDisplay.printError("Cannot locate Xmipp protocol %s" % p)

#======================
#======================
def particularizeProtocol(protocolIn, parameters, protocolOut):
	'''
	standard function to modify an Xmipp protocol (e.g. xmipp_protocols_projmatch.py or xmipp_protocols_ml3d.py).
	Requires 3 inputs: (1) the full path to the protocol name in the Xmipp bin directory, (2) all parameters particular
	the protocol in a dictionary format, with all keys filled in and matching all variables in the protocolIn file, (3)
	the full path to the output protocol in the run directory.
	'''
	fileIn = open(protocolIn)
	fileOut = open(protocolOut,'w')
	endOfHeader=False
	for line in fileIn:
		if not line.find("{end-of-header}")==-1:
			endOfHeader=True
		if endOfHeader:
			fileOut.write(line)
		else:
			for key in parameters.keys():
				if not re.match('^'+key,line) is None:
					line=key+'='+repr(parameters[key])+'\n'
					break
			fileOut.write(line)
	fileIn.close()
	fileOut.close()

def searchTwoLineTextsInFile(filepath,texts):
	if len(texts) > 2:
		apDisplay.printError('searchTwoLineTextsInFile can only handle two texts')
	fileIn = open(filepath)
	lines = fileIn.readlines()
	fileIn.close()
	maskline_index=None
	for l,line in enumerate(lines):
		if texts[0] in line:
			print 'candidate line:',line
			print len(texts)
			if len(texts) == 1:
				maskline_index=l
			elif len(texts) == 2 and texts[1] in lines[l+1]:
				maskline_index=l
	return maskline_index

def fixReferenceMakingInRefineOnlyProtocol(protocol):
	tmp_protocol = protocol+'.tmp'
	fileIn = open(protocol)
	fileOut = open(tmp_protocol,'w')
	maskline_index=searchTwoLineTextsInFile(protocol,['# Mask reference volume','execute_mask'])
	# Making masklines
	lines = fileIn.readlines()
	fileIn.close()
	masklines = []
	masklines.append('          if _iteration_number == 1:\n')
	if maskline_index is not None:
		for m in range(10):
			masklines.append('  '+lines[maskline_index+m])
		masklines.append('          else:\n')
		masklines.append('            shutil.move(os.path.join("../Iter_%d" % (_iteration_number-1), "Iter_%d_reference_volume.vol" % (_iteration_number-1)), os.path.join("../Iter_%d" % (_iteration_number), "Iter_%d_reference_volume.vol" % (_iteration_number)))\n')
		outlines = lines[:maskline_index]
		outlines.extend(masklines)
		outlines.extend(lines[maskline_index+10:])
	else:
		outlines = lines
	fileOut.writelines(outlines)
	fileOut.close()
	return tmp_protocol

def removeBadFilterInRefineOnlyProtocol(protocol):
	tmp_protocol = protocol+'.tmp'
	fileIn = open(protocol)
	fileOut = open(tmp_protocol,'w')
	maskline_index=searchTwoLineTextsInFile(protocol,['globalFourierMaxFrequencyOfInterest=filter_at_given_resolution'])
	print 'global',maskline_index
	# Making masklines
	lines = fileIn.readlines()
	fileIn.close()
	masklines = []
	masklines.append('          if self._DoReconstruction:\n')
	if maskline_index is not None:
		masklines.append('  '+lines[maskline_index])
		outlines = lines[:maskline_index]
		outlines.extend(masklines)
		outlines.extend(lines[maskline_index+1:])
	else:
		outlines = lines
	fileOut.writelines(outlines)
	fileOut.close()
	return tmp_protocol

def fixRefineOnlyProtocol(template_protocol,protocol):
	'''
	protocol version specific function to modify Xmipp protocol so that multiple iteration of refine-only will run
	'''
	shutil.copy(template_protocol,protocol)
	temp_protocol = fixReferenceMakingInRefineOnlyProtocol(protocol)
	shutil.move(temp_protocol,protocol)
	tmp_protocol = removeBadFilterInRefineOnlyProtocol(protocol)
	shutil.move(temp_protocol,protocol)

#======================
#======================	
def convertXmippEulersToEman(phi, theta, psi,mirror=False):
	return apEulerCalc.convertXmippEulersToEman(phi, theta, psi, mirror)

def convertEmanEulersToXmipp(alt, az, psi):
	''' reverse of convertXmippEulersToEman '''
	phi = math.fmod((az-90), 360.0)
	theta = alt
	psi = math.fmod((psi+90), 360.0)
	return phi, theta, psi
	
#======================	
#=====================

class filePathModifier:
	#=====================
	def common_prefix(self, c1, c2):
		if not c1 and c2: return
		for i, c in enumerate(c1):
			if c != c2[i]:
				return c1[:i]
		return c1

	#=====================
	def common_suffix(self, c1, c2):
		return self.common_prefix(c1[::-1], c2[::-1])[::-1]

	#=====================
	def findUncommonPathPrefix(self, path1, path2):
		''' usefule when transfering sel and doc files from one file system to another '''
		prefix1 = re.sub(self.common_suffix(path1, path2), "", path1)
		prefix2 = re.sub(self.common_suffix(path1, path2), "", path2)
		return os.path.abspath(prefix1), os.path.abspath(prefix2)
		
	#=====================
	def checkSelOrDocFileRootDirectory(self, sel_doc_file, old_rootdir, new_rootdir):
		''' necessary when files are transferred from one file system to another, e.g., the root directory on Garibaldi is different from that on Guppy'''

		try:
			f = open(sel_doc_file, "r")
		except:
			apDisplay.printWarning("Unable to open file: %s" % sel_doc_file)
			return
		lines = f.readlines()
		newlines = []
		f.close()
			
		### replace old root directory with new root directory	
		count = 0
		for line in lines:
			if re.search(old_rootdir, line):
				newline = re.sub(old_rootdir, new_rootdir, line)
				count += 1
			else: 
				newline = line
			newlines.append(newline)
		if count > 0:
			apDisplay.printMsg("changing root directory from %s to %s in %s" % (old_rootdir, new_rootdir, sel_doc_file))
			f = open(sel_doc_file, "w")
			f.writelines(newlines)
			f.close()
		return
		
#=====================
#=====================
def checkSelOrDocFileRootDirectoryInDirectoryTree(directory, remote_basedir, local_basedir):
	''' 
	used to change all the root directories in Xmipp .sel, .doc, and .ctfdat files recursively, e.g:
	from /ddn/people/dlyumkis/appion/11jan11a/recon to /ami/data00/appion/11jan11a/recon
	'''
	
	if remote_basedir != local_basedir:
		modifier = filePathModifier()
		remote_root, local_root = modifier.findUncommonPathPrefix(remote_basedir, local_basedir)
		print "remote cluster root path is: ", remote_root
		print "local cluster root path is: ", local_root
			
		### modify all .sel and .doc files using old_rootdir (remote_root) and new_rootdir (local_root) arguments
		matches = []
		for root, dirs, files in os.walk(directory):
			for file in files:
				if file.endswith('.sel') or file.endswith('.doc') or file.endswith('.ctfdat'):
					matches.append(os.path.join(root,file))
		for match in matches: 
			modifier.checkSelOrDocFileRootDirectory(match, remote_root, local_root)

#=====================
#=====================
def compute_stack_of_class_averages_and_reprojections(dir, selfile, refvolume, docfile, boxsize, resultspath, timestamp, iteration, reference_number=1, extract=False):
	''' takes Xmipp single files, doc and sel files in routine, creates a stack of class averages in the results directory '''
	
	workingdir = os.getcwd()
	os.chdir(dir)
	if dir.endswith("/"):
		dir = dir[:-1]
	head, tail = os.path.split(dir)
	
	### remove "lastdir" component from selfile (created by Xmipp program), then extract header information to docfile
	f = open(selfile, "r")
	lines = f.readlines()
	newlines = [re.sub(str(tail)+"/", "", line) for line in lines]
	f.close()
	f = open(selfile[:-4]+"_new.sel", "w")
	f.writelines(newlines)
	f.close()
	if extract is True:
		extractcmd = "xmipp_header_extract -i %s.sel -o %s.doc" % (selfile[:-4], docfile[:-4])
		apParam.runCmd(extractcmd, "Xmipp")

	### create a projection params file and project the volume along identical Euler angles
	f = open("paramfile.descr", "w")
	f.write("%s\n" % refvolume)
	f.write("tmpproj 1 xmp\n")
	f.write("%d %d\n" % (boxsize, boxsize))
	f.write("%s rot tilt psi\n" % docfile)
	f.write("NULL\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.close()
	projectcmd = "xmipp_project -i paramfile.descr"
	apParam.runCmd(projectcmd, "Xmipp")
	
	### get order of projections in docfile
	d = open(docfile, "r")
	lines = d.readlines()[1:]
	d.close()
	projfile_sequence = []
	for i, l in enumerate(lines):
		if i % 2 == 0:
			filename = os.path.basename(l.split()[1])
			projfile_sequence.append(filename)
		else: pass
		
	### create stack of projections and class averages
	projections = glob.glob("tmpproj**xmp")
	projections.sort()
	if len(projections) != len(projfile_sequence):
		apDisplay.printWarning("number of projections does not match number of classes")
	stackarray = []
	stackname = os.path.join(resultspath, "proj-avgs_%s_it%.3d_vol%.3d.hed" % (timestamp, iteration, reference_number))
	for i in range(len(projections)):
		stackarray.append(spider.read(projections[i]))
		stackarray.append(spider.read(projfile_sequence[i]))
	apImagicFile.writeImagic(stackarray, stackname, msg=False)
	
	### remove unnecessary files
	for file in glob.glob("tmpproj*"):
		apFile.removeFile(file)
	os.chdir(workingdir)

	return 

#======================
#======================

def importProtocolPythonFile(protocolscript, rundir):
	''' finds protocol python file in directory, protocolscript passed without .py extension, e.g. xmipp_protocol_ml3d '''

	try:
		if not rundir in sys.path:
			sys.path.append(os.path.abspath(rundir))
		p = __import__(protocolscript)		
	except ImportError, e:
		print e, "cannot open protocol script, trying to open backup file"
		try:
			for root, dirs, files in os.walk(rundir):
				for name in files:
					if re.match(str(protocolscript+"_backup.py"), name):
						if not root in sys.path:
							sys.path.append(root)				
			p = __import__(protocolscript+"_backup")
		except ImportError, e:
			print e, "cannot open backup protocol file"
			apDisplay.printError("could not find protocol file: %s ... try uploading as an external refinement" % protocolscript)
	return p

#======================
#======================

def convertSymmetryNameForPackage(inputname):
	'''
	hedral symmetry key is of possible name, value is that of this package
	'''
	# (5 3 2) EMAN and (2 5 3) crowther icos would have been converted into (2 3 5) 3dem orientation during the preparation
	xmipp_hedral_symm_names = {'oct':'O','icos (2 3 5) viper/3dem':'I1','icos (2 5 3) crowther':'I1','icos (5 3 2) eman':'I1'}
	inputname = inputname.lower()
	if inputname[0] in ('c','d') or inputname in xmipp_hedral_symm_names.values():
		symm_name = inputname.lower().split()[0]
	elif inputname in xmipp_hedral_symm_names.keys():
		symm_name = xmipp_hedral_symm_names[inputname]
	else:
		symm_name = inputname.upper()
		apDisplay.printWarning("unknown symmetry name conversion. Use it directly as %s" % symm_name)
	return symm_name

#=======================
#=======================
def calculate_equivalent_Eulers_without_flip(phi, theta, psi):
	return apEulerCalc.calculate_equivalent_XmippEulers_without_flip(phi, theta, psi)

#=======================
#=======================
def removeMirrorFromDocfile(docfile_old, docfile_new):
	''' removes mirroring operation from docfile and outputs a new docfile '''

	### read info
	particles, header = readDocfile(docfile_old, returnheader=True)
	dfn = open(docfile_new, "w")

	### update header
	headinfo = header.strip().split()
	dfn.write(" ; Headerinfo columns: rot (1), tilt (2), psi (3), Xoff (4), Yoff (5), Ref (6)")
	if len(headinfo) > 16:
		count = 7
		restheader = headinfo[17:]
		for i in range(len(restheader)/2):
			dfn.write(", %s (%d)" % (restheader[i*2], count))
			count += 1
	dfn.write("\n")
	### modify Eulers and write to new docfile
	for partnum, params in particles.iteritems():
		dfn.write(" ; %s\n" % params['filename'])
		p = params['values']
		phi = float(p[2])
		theta = float(p[3])
		psi = float(p[4])
		flip = bool(float(p[8]))
		if flip is True:
			phi, theta, psi = calculate_equivalent_Eulers_without_flip(phi, theta, psi)
		dfn.write("%5d%2d %11.5f%11.5f%11.5f%11.5f%11.5f%12.5f" \
			% (float(p[0]), float(p[1])-1, phi, theta, psi, float(p[5]), float(p[6]), float(p[7])))
		if len(p) > 9:
			for param in p[9:]:
				dfn.write("%11.5f" % float(param))
		dfn.write("\n")
	dfn.close()
	return
	
def readSelfile(selfile):
	''' returns a list of filenames '''
	f = open(selfile, "r")
	lines = f.readlines()
	f.close()
	split = [l.strip().split() for l in lines]
	filenames = [s[0] for s in split]
	return filenames

#=======================
#=======================
def readDocfile(docfile, returnheader=False):
	''' returns a nested dictionary: key=particle number (starts with 0), value=dictionary: {'values':[allvals], 'filename':'name'} '''
	f = open(docfile, "r")
	l = f.readlines()
	f.close()
	header = l[0]
	lines = l[1:]
	splitl = [l.strip().split() for l in lines]
	d = {}
	for i in range(len(splitl)/2):
		filename = splitl[i*2][1]
		m = re.search('part[0-9]{6}', filename)
		partnum = int(float(m.group(0)[-6:]))
		vals = splitl[i*2+1]
		d[partnum] = {'filename':filename, 'values':vals}
	if returnheader is True:
		return d, header
	else:
		return d

def selFileToList(selfile, list):
	''' reads selfile, writes sorted list of numbers, eman style '''
	f = open(selfile, "r")
	lines = f.readlines()
	f.close()
	split = [l.strip().split() for l in lines]
	filenames = [s[0] for s in split]
	fileorder = []
	for file in filenames:
		match = re.match('[A-Za-z]+([0-9]+)\.[A-Za-z]+', file.split('/')[-1])
		if (match):
			filenumber=int(match.groups()[0])
			fileorder.append(filenumber)
	f = open(list, "w")
	for n in fileorder:
		f.write("%d\n" % n)
	f.close()
