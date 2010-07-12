#!/usr/bin/env python
#
import os,sys
import time
import math
import shutil
import glob
import cPickle
import tarfile
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apParam
from appionlib import apEMAN
from appionlib import appiondata
from appionlib import apProject
from appionlib.apSpider import operations
from appionlib import apIMAGIC
from appionlib import apImagicFile

#=====================
#=====================
class TopologyRepScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID --start=# --end=# [options]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="Number of processor to use", metavar="ID#")

		self.parser.add_option("--clip", dest="clipsize", type="int",
			help="Clip size in pixels (reduced box size)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")
		self.parser.add_option("-i", "--iter", dest="iter", type="int", default=20,
			help="Number of iterations", metavar="#")
		self.parser.add_option("--start", dest="start", type="int",
			help="number of classes to create in first iteration")
		self.parser.add_option("--end", dest="end", type="int",
			help="number of classes to create in last iteration")
		self.parser.add_option("--mask", dest="mask", type='int', metavar="#",
			help="radius of circular mask to apply in pixels (default=(boxsize/2)-2)")
		self.parser.add_option("--itermult", dest="itermult", type="float", metavar="FLOAT", default=10.0,
			help="multiplier for determining number of times data will be presented to the network. Number of particles in your stack will by multiplied by this value to determine # of iterations")
		self.parser.add_option("--learn", dest="learn", type="float", metavar="FLOAT", default=0.01,
			help="direct learning rate - fraction that closest unit image will be moved toward presented data, 0.01 suggested for cryo, higher for neg stain")
		self.parser.add_option("--ilearn", dest="ilearn", type="float", metavar="FLOAT", default=0.0005,
			help="indirect learning rate - fraction that connection unit images will be moved should be lower than direct rate")
		self.parser.add_option("--age", dest="maxage", type="int", metavar="INT", default=25,
			help="number of iterations an edge connecting two units can be unused before it's discarded")

		### choices
		self.mramethods = ("eman","imagic")
		self.parser.add_option("--mramethod", dest="mramethod",
			help="Method for multi-reference alignment", metavar="PACKAGE",
			type="choice", choices=self.mramethods, default="eman")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['start'] is None:
			apDisplay.printError("a number of starting classes was not provided")
		if self.params['end'] is None:
			apDisplay.printError("a number of ending classes was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))

		boxsize = apStack.getStackBoxsize(self.params['stackid'])
		self.clipsize = int(math.floor(boxsize/float(self.params['bin']*2)))*2
		if self.params['clipsize'] is not None:
			if self.params['clipsize'] >= self.clipsize:
				apDisplay.printError("requested clipsize is too big %d > %d"
					%(self.params['clipsize'],self.clipsize))
			self.clipsize = self.params['clipsize']
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)
		if not self.params['mask']:
			self.params['mask'] = (self.clipsize/2)-2
		if self.params['mramethod'] == 'imagic':
			self.imagicroot = apIMAGIC.checkImagicExecutablePath()
			self.imagicversion = apIMAGIC.getImagicVersion(self.imagicroot)

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = "topolrep-"+self.timestamp+"-params.pickle"
		pf = open(paramfile, "w")
		cPickle.dump(self.params, pf)
		pf.close()

	#=====================
	def insertTopolRepJob(self):
		topoljobq = appiondata.ApTopolRepJobData()
		topoljobq['runname'] = self.params['runname']
		topoljobq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		topoljobdatas = topoljobq.query(results=1)
		if topoljobdatas:
			alignrunq = appiondata.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			alignrundata = alignrunq.query(results=1)
			if topoljobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		topoljobq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		topoljobq['timestamp'] = self.timestamp
		topoljobq['finished'] = False
		topoljobq['hidden'] = False
		if self.params['commit'] is True:
			topoljobq.insert()
		self.params['topoljob'] = topoljobq
		return

	#=====================
	def insertRunIntoDatabase(self):
		apDisplay.printMsg("Inserting Topology Rep Run into DB")

		### set up alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' and path already exist in database")

		### set up topology rep run
		toprepq = appiondata.ApTopolRepRunData()
		toprepq['runname'] = self.params['runname']
		toprepq['mask'] = self.params['mask']
		toprepq['itermult'] = self.params['itermult']
		toprepq['learn'] = self.params['learn']
		toprepq['ilearn'] = self.params['ilearn']
		toprepq['age'] = self.params['maxage']
		toprepq['mramethod'] = self.params['mramethod']
		toprepq['job'] = self.params['topoljob']

		### finish alignment run
		alignrunq['topreprun'] = toprepq
		alignrunq['hidden'] = False
		alignrunq['runname'] = self.params['runname']
		alignrunq['description'] = self.params['description']
		alignrunq['lp_filt'] = self.params['lowpass']
		alignrunq['hp_filt'] = self.params['highpass']
		alignrunq['bin'] = self.params['bin']
		### set up alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = "mrastack.hed"
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = os.path.basename(self.params['currentcls'])+".hed"
		alignstackq['iteration'] = self.params['currentiter']
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq

		### check to make sure files exist
		imagicfile = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find stack file: "+imagicfile)
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)

		alignstackq['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		alignstackq['boxsize'] = math.floor(apStack.getStackBoxsize(self.params['stackid'])/self.params['bin'])
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])*self.params['bin']
		alignstackq['description'] = self.params['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  self.params['numpart']

		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

	#=====================
	def insertParticlesIntoDatabase(self, partlist, partrefdict):
		# insert particle alignment information into database
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")

			### set up reference
			refq = appiondata.ApAlignReferenceData()
			## get reference number from partrefdict
			refq['refnum'] = partrefdict[int(partdict['partnum'])+1]
			refq['iteration'] = self.params['currentiter']
			refq['imagicfile'] = os.path.basename(self.params['currentcls'])+".img"
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			reffile = os.path.join(self.params['rundir'], refq['imagicfile'])
			if not os.path.isfile(reffile):
				apDisplay.printError("could not find reference file: "+reffile)

			### set up particle
			alignpartq = appiondata.ApAlignParticleData()
			## EMAN particles start with 0, database starts at 1
			alignpartq['partnum'] = partdict['partnum'] + 1
			alignpartq['alignstack'] = self.alignstackdata
			stackpartdata = apStack.getStackParticle(self.params['stackid'], partdict['partnum']+1)
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['rotation'] = partdict['inplane']
			alignpartq['mirror'] = partdict['mirror']
			alignpartq['correlation'] = partdict['cc']
			alignpartq['ref'] = refq

			### insert
			if self.params['commit'] is True:
				inserted += 1
				alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

	#=====================
	def writeTopolRepLog(self, text):
		f = open("topolrep.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def getCANPath(self):
		unames = os.uname()
		if unames[-1].find('64') >= 0:
			exename = 'can64.exe'
		else:
			exename = 'can32.exe'
		CANexe = apParam.getExecPath(exename, die=True)
		return CANexe

	#=====================
	def runCAN(self):
		numIters = int(self.params['numpart']*self.params['itermult'])
		decrement = (self.params['start']-self.params['end'])/float(self.params['iter'])
		numClasses = self.params['start']-(decrement*self.params['currentiter'])
		stackfile = self.params['alignedstack']
		canopts = " %s classes %i %.3f %.5f %i %i" % (
			stackfile,
			numIters,
			self.params['learn'],
			self.params['ilearn'],
			self.params['maxage'],
			numClasses
		)
		cancmd = self.params['canexe']+canopts
		apDisplay.printMsg("running CAN:")
		apDisplay.printMsg(cancmd+"\n")
		self.writeTopolRepLog(cancmd)
		apEMAN.executeEmanCmd(cancmd, verbose=True, showcmd=True)

		# check that CAN ran properly
		if not os.path.exists('classes.hed'):
			apDisplay.printError("CAN did not create an output stack, check CAN functionality")

		# tar spider files
		spitar = tarfile.open("cls.spi.tar","w")
		spifiles = glob.glob("classes_class_*.spi")
		for spif in spifiles:
			spitar.add(spif)
		spitar.close()
		# remove class files
		for spif in spifiles:
			os.remove(spif)

		# align resulting classes
		self.alignClasses()
		
	#=====================
	def alignClasses(self):
		classname = "classes"

		# mask the averages
		emancmd = "proc2d %s.hed %s_mask.hed mask=%i"%(classname,classname,(self.params['mask']/self.params['bin']))
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		os.remove(classname+".hed")
		os.remove(classname+".img")
		classname = classname+"_mask"
		
		# don't align references for last iteration - classalign2 doesn't save rotations & shifts
		if self.params['currentiter'] < self.params['iter']:
			# align the references to each other
			emancmd = "classalign2 %s.hed 10 keep=100 saveali"%classname
			apEMAN.executeEmanCmd(emancmd, verbose=False)
			os.remove(classname+".hed")
			os.remove(classname+".img")
			classname = "a"+classname

		# normalize references
		emancmd = "proc2d %s.hed %s_norm.hed norm"%(classname,classname)
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		os.remove(classname+".hed")
		os.remove(classname+".img")
		classname = classname+"_norm"

		outputcls = os.path.join(self.params['rundir'],"classes%02i" % self.params['currentiter'])
		shutil.move(classname+".hed",outputcls+".hed")
		shutil.move(classname+".img",outputcls+".img")
		self.params['currentcls'] = outputcls

	#=====================
	def runEMANmra(self):
		# set up cls files
		emancmd = "proc2d %s.hed cls mraprep" %self.params['currentcls']
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		# run EMAN projection matching
		emancmd = "classesbymra %s %s.hed mask=%i split imask=-1 logit=1 sep=1 phase" %(
			self.params['localstack'],
			self.params['currentcls'],
			self.params['mask']
		)
		if self.params['nproc'] > 1:
			apEMAN.executeRunpar(emancmd, self.params['nproc'])
		else:
			apEMAN.executeEmanCmd(emancmd, verbose=True)

		# create stack of aligned particles
		# first get list of cls files
		clslist=glob.glob('cls*.lst')
		clslist.sort()
		emantar = tarfile.open("cls.eman.tar","w")
		clsarray = [[]for i in range(self.params['numpart'])]
		for cls in clslist:
			f = open(cls)
			lines = f.readlines()
			f.close()
			for l in range(1,len(lines)):
				d=lines[l].strip().split()
				if len(d) < 4:
					continue
				part = int(d[0])
				stack = d[1]
				cc = float(d[2][:-1])
				(rot,x,y,mirror) = d[3].split(',')
				clsarray[part]=[part,stack,cc,float(rot),float(x),float(y),int(mirror)]
			# for tarring cls files
			emantar.add(cls)
		emantar.close()

		# remove eman cls####.lst files
		for cls in clslist:
			os.remove(cls)

		# create a new cls file with all particles
		f = open("cls_all.lst","w")
		f.write("#LST\n")
		for p in clsarray:
			f.write("%i\t%s\t%.2f,  %.6f,%.3f,%.3f,%i\n" % (p[0],p[1],p[2],p[3],p[4],p[5],p[6]))
		f.close()

		# create aligned particles
		apEMAN.alignParticlesInLST("cls_all.lst","mrastack.hed")

		if self.params['currentiter'] > 1:
			os.remove(self.params['alignedstack']+".hed")
			os.remove(self.params['alignedstack']+".img")
		self.params['alignedstack']=os.path.abspath("mrastack")

		# remove cls file used for alignment
		os.remove("cls_all.lst")

	#=====================
	def runIMAGICmra(self):
		bfile = "mralign.csh"
		outfile = "mrastack"
		if os.path.exists(outfile+".hed"):
			os.remove(outfile+".hed")
		if os.path.exists(outfile+".img"):
			os.remove(outfile+".img")

		f = open(bfile,'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("%s/align/mralign.e <<EOF\n" % self.imagicroot)
		f.write("NO\n")
		f.write("FRESH\n")
		f.write("ALL\n")
		# 091120 or higher version 4D options:
		if int(self.imagicversion) >= 91120:
			f.write("ALIGNMENT\n")
			f.write("ALL\n")
		f.write("ROTATION_FIRST\n")
		f.write("CCF\n")
		f.write(self.params['alignedstack']+"\n")
		f.write(outfile+"\n")
		f.write(os.path.splitext(self.params['localstack'])[0]+"\n")
		f.write(self.params['currentcls']+"\n")
		f.write("NO_FILTER\n")
		# lower than 091120 version of imagic asks for mirrors:
		if int(self.imagicversion) < 91120:
			f.write("NO\n")
		f.write("0.31\n")
		# don't ask Max shift (during this alignment) for first iteration:
		if self.params['currentiter'] > 1:
			f.write("0.2\n")
		f.write("-180,180\n")
		# don't ask rotation (during this alignment) for first iteration:
		if self.params['currentiter'] > 1:
			f.write("-180,180\n")
		f.write("MEDIUM\n")
		f.write("0.0,0.8\n")
		f.write("2\n")
		f.write("NO\n")
		f.write("EOF\n")
		f.write("\n")

		### write out alignment parameters to file
		f.write("%s/stand/headers.e <<EOF\n" % self.imagicroot)
		f.write(outfile+"\n")
		f.write("PLT\n")
		f.write("INDEX\n")
		f.write("116;117;118;104;107\n") ### rotation, shiftx, shifty, ccc, reference num
		f.write("outparams.plt\n")
		f.write("EOF\n")
		f.close()

		## execute the batch file
		aligntime0 = time.time()
		apEMAN.executeEmanCmd("chmod 775 "+bfile)

		apDisplay.printColor("Running IMAGIC .batch file: %s"%(os.path.abspath(bfile)), "cyan")
		apIMAGIC.executeImagicBatchFile(os.path.abspath(bfile))

		if not os.path.exists(outfile+".hed"):
			apDisplay.printError("ERROR IN IMAGIC SUBROUTINE")
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

		if self.params['currentiter'] > 1:
			os.remove(self.params['alignedstack']+".hed")
			os.remove(self.params['alignedstack']+".img")
		self.params['alignedstack']=os.path.abspath(outfile)

	#=====================
	def TarExtractall(self, tarobj):
		"""
		Function introduced in python 2.5 and is not available in python 2.4
		Copied and modified from python 2.6 code 
		Delete this when we move to python 2.5 code - Neil

		Extract all members from the archive to the current working
		directory and set owner, modification time and permissions on
		directories afterwards. `path' specifies a different directory
		to extract to. `members' is optional and must be a subset of the
		list returned by getmembers().
		"""
		import copy
		
		directories = []
		members = tarobj.getmembers()

		for tarinfo in members:
			if tarinfo.isdir():
				# Extract directories with a safe mode.
				directories.append(tarinfo)
				tarinfo = copy.copy(tarinfo)
				tarinfo.mode = 0700
			tarobj.extract(tarinfo, path)

		# Reverse sort directories.
		directories.sort(key=operator.attrgetter('name'))
		directories.reverse()

		# Set correct owner, mtime and filemode on directories.
		for tarinfo in directories:
			dirpath = os.path.join(".", tarinfo.name)
			tarobj.chown(tarinfo, dirpath)
			tarobj.utime(tarinfo, dirpath)
			tarobj.chmod(tarinfo, dirpath)

	#=====================
	def readPartEMANFile(self):
		# get particle information from lst file
		# first untar the cls file
		clstarf = "cls.eman.tar"
		if not os.path.isfile(clstarf):
			apDisplay.printError("no EMAN cls tar file found")
		clstar = tarfile.open(clstarf)
		self.TarExtractall(clstar)
		#clstar.extractall()
		clstar.close()
		clsfiles = glob.glob("cls*.lst")
		if not clsfiles:
			apDisplay.printError("EMAN did not create cls####.lst files")

		clsfiles.sort()

		# store contents of each lst file in array
		pinfo = []
		for cls in clsfiles:
			# get reference number from lst file name
			p = apEMAN.emanLSTtoArray(cls)
			if p is not None:
				pinfo += p
			os.remove(cls)
		# sort the array by particle number
		pinfo.sort(key = lambda adict: adict['partnum'])

		return pinfo

	#=====================
	def readPartIMAGICFile(self):
		# get particle information from imagic file
		alifile = "outparams.plt"
		if not os.path.isfile(alifile):
			apDisplay.printError("no IMAGIC alignment file found")

		# store contents in array
		f = open(alifile)
		pinfo = []
		pnum = 0
		for line in f:
			d = line.strip().split()
			if len(d) < 5:
				continue
			pdata = {}
			numlist = [eval(p) for p in d]

			pdata['partnum'] = pnum
			# imagic rotation is opposite the db
			pdata['inplane'] = -numlist[0]
			# imagic's (y,-x )is db's (x,y)
			pdata['xshift'] = numlist[2]
			pdata['yshift'] = -numlist[1]
			pdata['cc'] = numlist[3]
			pdata['mirror'] = 0
			pinfo.append(pdata)
			pnum += 1
		f.close()	

		return pinfo

	#=====================
	def canClassificationToDict(self):
		### read the particle classification results from CAN
		### output in spider format & save as a dictionary
		pclass = {}
		spitarf = "cls.spi.tar"
		if not os.path.isfile(spitarf):
			apDisplay.printError("no SPIDER cls tar file found")
		spitar = tarfile.open(spitarf)
		spitar.extractall()
		spitar.close()
		spifiles = glob.glob("classes_class_*.spi")
		if not spifiles:
			apDisplay.printError("CAN did not create SPIDER cls files")
		
		spifiles.sort()

		# store classification in dictionary, defined by particle number
		for spi in spifiles:
			## get ref number from class file name
			refn=int(os.path.splitext(spi)[0][-4:])
			f = open(spi)
			for l in f:
				if l[:2] == ' ;':
					continue
				spidict = operations.spiderInLine(l)
				p = int(spidict['floatlist'][0])
				if p not in pclass:
					pclass[p]=refn
				else:
					apDisplay.printError("particle %i has more than 1 classification,"
						+" classified to reference %i and %i"%(p,pclass[p],refn))
			f.close()
			os.remove(spi)
		return pclass

	#=====================
	def start(self):
		self.insertTopolRepJob()
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.dumpParameters()

		self.params['canexe'] = self.getCANPath()

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")
		proccmd = "proc2d "+self.stack['file']+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		if self.params['bin'] > 1 or self.params['clipsize'] is not None:
			clipsize = int(self.clipsize)*self.params['bin']
			proccmd += " shrink=%d clip=%d,%d edgenorm"%(self.params['bin'],clipsize,clipsize)
		proccmd += " last="+str(self.params['numpart']-1)
		if self.params['highpass'] is not None and self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		apEMAN.executeEmanCmd(proccmd, verbose=True)
		if self.params['numpart'] != apFile.numImagesInStack(self.params['localstack']):
			apDisplay.printError("Missing particles in stack")

		### find number of processors
		if self.params['nproc'] is None:
			self.params['nproc'] = apParam.getNumProcessors()

		aligntime = time.time()
		# run through iterations
		for i in range(0,self.params['iter']+1):
			# move back to starting directory
			os.chdir(self.params['rundir'])

			# set up next iteration directory
			self.params['currentiter'] = i
			self.params['iterdir'] = os.path.abspath("iter%02i" % i)
			if os.path.exists(self.params['iterdir']):
				apDisplay.printError("Error: directory '%s' exists, aborting alignment" % self.params['iterdir'])

			# create directory for iteration
			os.makedirs(self.params['iterdir'])	
			os.chdir(self.params['iterdir'])

			# if at first iteration, create initial class averages 
			if i == 0:
				self.params['alignedstack'] = os.path.splitext(self.params['localstack'])[0]
				self.runCAN()
				continue

			# using references from last iteration, run multi-ref alignment
			if self.params['mramethod'] == "imagic":
				# first check headers
				apImagicFile.setImagic4DHeader(self.params['localstack'])
				apImagicFile.setImagic4DHeader(self.params['alignedstack'])
				apImagicFile.setImagic4DHeader(self.params['currentcls'])
				self.runIMAGICmra()
			else:
				self.runEMANmra()

			# create class averages from aligned stack
			self.runCAN()
			
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### get particle information from last iteration
		if self.params['mramethod']=='imagic':
			partlist = self.readPartIMAGICFile()
		else:
			partlist = self.readPartEMANFile()
		partrefdict = self.canClassificationToDict()

		# move back to starting directory
		os.chdir(self.params['rundir'])

		# move aligned stack to current directory
		shutil.move(self.params['alignedstack']+".hed",".")
		shutil.move(self.params['alignedstack']+".img",".")

		### create an average mrc of final references 
		apStack.averageStack(stack=self.params['currentcls']+".hed")
		self.dumpParameters()

		# move actual averages to current directory
		shutil.move(os.path.join(self.params['iterdir'],"classes_avg.hed"),".")
		shutil.move(os.path.join(self.params['iterdir'],"classes_avg.img"),".")
		# save actual class averages as refs in database
		self.params['currentcls']="classes_avg"
		
		### save to database
		self.insertRunIntoDatabase()
		self.insertParticlesIntoDatabase(partlist, partrefdict)

#=====================
if __name__ == "__main__":
	topRep = TopologyRepScript(True)
	topRep.start()
	topRep.close()



