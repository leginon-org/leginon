#!/usr/bin/env python
#
import os,sys,re
import time
import math
import shutil
import glob
import cPickle
import tarfile
import subprocess
import string
from EMAN2 import *
from sparx import *
#appion
import sinedon.directq
from appionlib import proc2dLib
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
from appionlib.apImagic import imagicFilters
from appionlib.apImagic import imagicAlignment

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

		self.parser.add_option("--msaproc", dest="msaproc", type="int", default=1,
			help="Number of processor to use for CAN", metavar="#")

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

		### IMAGIC MSA options
		self.parser.add_option("--msaiter", dest="msaiter", type="int", default=50,
			help="number of MSA iterations")
		self.parser.add_option("--numeigen", dest="numeigen", type="int", default=20,
			help="total number of eigen images to calculate")
		self.parser.add_option("--overcorrection", dest="overcorrection", type="float", default=0.8,
			help="overcorrection facter (0-1)")
		self.parser.add_option("--activeeigen", dest="activeeigen", type="int", default=10,
			help="number of active eigen images to use for classification")

		### true/false
		self.parser.add_option("--keep-all", dest="keepall", default=False,
			action="store_true", help="Keep all intermediate node images")
		self.parser.add_option("--premask", dest="premask", default=False,
			action="store_true", help="Mask raw particles before processing")
		self.parser.add_option("--no-mask", dest="nomask", default=False,
			action="store_true", help="Do not apply a mask to the class averages")
		self.parser.add_option("--no-center", dest="nocenter", default=False,
			action="store_true", help="Do not center particles after each iteration")
		self.parser.add_option("--classiter", dest="classiter", default=False,
			action="store_true", help="Perform iterative averaging of class averages")
		self.parser.add_option("--uploadonly", dest="uploadonly", default=False,
			action="store_true", help="Just upload results of completed run")
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert before alignment")

		### choices
		self.mramethods = ("eman","imagic")
		self.parser.add_option("--mramethod", dest="mramethod",
			help="Method for multi-reference alignment", metavar="PACKAGE",
			type="choice", choices=self.mramethods, default="eman")
		self.msamethods = ("can","imagic")
		self.parser.add_option("--msamethod", dest="msamethod",
			help="Method for MSA", metavar="PACKAGE",
			type="choice", choices=self.msamethods, default="can")

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
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		# check for virtual stack
		self.params['virtualdata'] = None
		if not os.path.isfile(stackfile):
			vstackdata = apStack.getVirtualStackParticlesFromId(self.params['stackid'])
			npart = len(vstackdata['particles'])
			self.params['virtualdata'] = vstackdata
		else:
			npart = apFile.numImagesInStack(stackfile)

		if self.params['numpart'] is None:
			self.params['numpart'] = npart
		elif self.params['numpart'] > npart:
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))

		self.boxsize = apStack.getStackBoxsize(self.params['stackid'])
		self.workingboxsize = math.floor(self.boxsize/self.params['bin'])
		if not self.params['mask']:
			self.params['mask'] = (self.boxsize/2)-2
		self.workingmask = math.floor(self.params['mask']/self.params['bin'])
		if self.params['mramethod'] == 'imagic':
			self.imagicroot = apIMAGIC.checkImagicExecutablePath()
			self.imagicversion = apIMAGIC.getImagicVersion(self.imagicroot)

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		uppath = string.replace(uppath,"/jetstor/APPION","")
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

		alignstackq['stack'] = self.stackdata
		alignstackq['boxsize'] = math.floor(self.workingboxsize)
		alignstackq['pixelsize'] = self.stack['apix']*self.params['bin']
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
		apDisplay.printColor("\nPreparing to insert particle alignment data, please wait", "cyan")

		# get path data
		pathq = appiondata.ApPathData()
		pathq['path'] = os.path.abspath(self.params['rundir'])
		pathdata = pathq.query(results=1)
		pathid = pathdata[0].dbid

		# align run id
		alignrunid = self.alignstackdata['alignrun'].dbid

		# get stack particle ids
		stackpdbdict={}
		sqlcmd = "SELECT particleNumber,DEF_id "+ \
			"FROM ApStackParticleData "+ \
			"WHERE `REF|ApStackData|stack`=%i"%(self.params['stackid'])
		results = sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)

		for part in results:
			pnum = int(part['particleNumber'])
			stackpdbdict[pnum]=int(part['DEF_id'])

		apDisplay.printColor("found "+str(len(results))+" particles in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		t0 = time.time()
		apDisplay.printColor("\nInserting class averages into database","cyan")
		# insert reference image data
		reflistvals = []
		for i in range(1,max(partrefdict.values())+1):
			sqlvals="(%i,%i,'%s',%i,%i)"%( \
				i,self.params['currentiter'], \
				os.path.basename(self.params['currentcls'])+".img", \
				alignrunid,pathid)
			reflistvals.append(sqlvals)

		sqlcmd = "INSERT INTO `ApAlignReferenceData` ("+ \
			"`refnum`,`iteration`,`imagicfile`,"+ \
			"`REF|ApAlignRunData|alignrun`,`REF|ApPathData|path`) "
		sqlcmd += "VALUES "+",".join(reflistvals)
		sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)

		# get DEF_ids from inserted references
		refq = appiondata.ApAlignReferenceData()
		refq['iteration'] = self.params['currentiter']
		refq['imagicfile'] = os.path.basename(self.params['currentcls'])+".img"
		refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		refq['alignrun'] = self.alignstackdata['alignrun']
		refresults = refq.query()

		# save DEF_ids to dictionary
		refdbiddict={}
		for ref in refresults:
			refdbiddict[ref['refnum']]=ref.dbid

		apDisplay.printColor("inserted "+str(len(refdbiddict))+" class averages in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		t0 = time.time()
		apDisplay.printColor("\nAssembling database insertion command","cyan")
		partlistvals = []

		for partdict in partlist:
			count += 1
			if count % (len(partlist)/100) == 0:
				pleft = int(float(count)/len(partlist)*100)
				perpart = (time.time()-t0)/count
				tleft = (len(partlist)-count)*perpart
				sys.stderr.write("%3i%% complete, %s left    \r"%(pleft,apDisplay.timeString(tleft)))

			partnum = int(partdict['partnum'])
			refnum = partrefdict[partnum]
			refnum_dbid = refdbiddict[refnum]
			stackpart_dbid = stackpdbdict[partnum]

			sqlvals = "(%i,%i,%i,%s,%s,%s,%i,%s,%i)"%( \
				partdict['partnum'], alignrunid, stackpart_dbid, \
				partdict['xshift'], partdict['yshift'], \
				partdict['inplane'], partdict['mirror'], \
				partdict['cc'],refnum_dbid) 

			partlistvals.append(sqlvals)
		
		sys.stderr.write("100% complete\t\n")

		apDisplay.printColor("Inserting particle information into database","cyan")

		# start big insert cmd
		sqlstart = "INSERT INTO `ApAlignParticleData` (" + \
			"`partnum`,`REF|ApAlignStackData|alignstack`," + \
			"`REF|ApStackParticleData|stackpart`," + \
			"`xshift`,`yshift`,`rotation`,`mirror`," + \
			"`correlation`,`REF|ApAlignReferenceData|ref`) " + \
			"VALUES "

		# break up command into groups of 100K inserts
		# this is a workaround for the max_allowed_packet at 16MB
		n = 100000
		sqlinserts = [partlistvals[i:i+n] \
			for i in range(0, len(partlistvals), n)]

		for sqlinsert in sqlinserts:
			sqlcmd=sqlstart+",".join(sqlinsert)
			sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)

		apDisplay.printColor("\nInserted "+ str(count)+" particles into the database in "
			+ apDisplay.timeString(time.time()-t0), "cyan")

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
			exename = 'can64_mp.exe'
		else:
			exename = 'can32.exe'
		CANexe = apParam.getExecPath(exename, die=True)
		return CANexe

	#=====================
	def runCAN(self):
		numIters = int(self.params['numpart']*self.params['itermult'])
		decrement = self.params['start']-self.params['end']
		if self.params['iter']>0:
			decrement /= float(self.params['iter'])
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
		self.params['currentnumclasses'] = numClasses

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

		# using IMAGIC to align references
		# center the particles
		if self.params['mramethod'] == "imagic":
			#imagic centering doesn't work as well as EMAN's unfortunately
			#cenfile = imagicAlignment.alimass(classname+".hed", maxshift=0.15, ceniter=10, nproc=1)
			aligntime0 = time.time()

			# convert mask to fraction for imagic
			maskfrac = self.workingmask*2/self.workingboxsize

			# don't align references for last iteration
			if self.params['currentiter'] < self.params['iter']:
				if self.params['classiter'] is True:
					emancmd = "e2stacksort.py classes_avg.hed outtmpcls.hdf --simalign=rotate_translate --center --useali --iterative"
					apEMAN.executeEmanCmd(emancmd, verbose=False)
					apFile.removeStack(classname)
					classname = "a"+classname
					# convert hdf back to imagic
					emancmd = "proc2d outtmpcls.hdf %s.hed"%classname
					apEMAN.executeEmanCmd(emancmd, verbose=False)
					apFile.removeStack("outtmpcls.hdf")
				else:
					if self.params['nocenter'] is False and self.params['nomask'] is False:
						emancmd = "proc2d %s.hed %s_cen.hed center"%(classname,classname)
						## try cenalignint
						emancmd = "cenalignint %s.hed"%classname
						apEMAN.executeEmanCmd(emancmd, verbose=False)
						## cenalignint also makes a stack with badly centered avgs 
						if os.path.isfile("bad.hed"):
							emancmd = "proc2d bad.hed ali.hed"
							apEMAN.executeEmanCmd(emancmd, verbose=False)
							apFile.removeStack("bad")
						if self.params['keepall'] is False:
							apFile.removeStack(classname)
						classname = classname+"_cen"
						classname = "ali"

					alifile = imagicAlignment.alirefs(classname, mask=0.99, maxshift=0.1)
					if self.params['keepall'] is False:
						apFile.removeStack(classname)
					classname = alifile

			# mask the classes
			if self.params['nomask'] is False:
				maskfile = imagicFilters.softMask(classname, mask=maskfrac, falloff=0.1)
				if self.params['keepall'] is False:
					apFile.removeStack(classname)
			else:
				maskfile = classname

			# normalize the classes
			classname = imagicFilters.normalize(maskfile, sigma=10.0)
			if self.params['keepall'] is False:
				apFile.removeStack(maskfile)

			apDisplay.printColor("finished alignment in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

		else:
			# for projection matching with EMAN:
			# don't align references for last iteration
			if self.params['currentiter'] < self.params['iter']:
				emancmd = "classalign2 %s.hed 10 keep=100 saveali"%classname
				apEMAN.executeEmanCmd(emancmd, verbose=False)
				apFile.removeStack(classname)
				classname = "a"+classname

			# mask the averages
			emancmd = "proc2d %s.hed %s_mask.hed mask=%i"%(classname,classname,(self.workingmask))
			apEMAN.executeEmanCmd(emancmd, verbose=False)
			apFile.removeStack(classname)
			classname = classname+"_mask"

			# normalize references
			emancmd = "proc2d %s.hed %s_norm.hed norm"%(classname,classname)
			apEMAN.executeEmanCmd(emancmd, verbose=False)
			apFile.removeStack(classname)
			classname = classname+"_norm"

		outputcls = os.path.join(self.params['rundir'],"classes%02i" % self.params['currentiter'])
		# copy normalized particles to run directory
		emancmd = "proc2d %s.hed %s.hed"%(classname,outputcls)
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		apFile.removeStack(classname)

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
			self.workingmask
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
			apFile.removeStack(self.params['alignedstack'])
		self.params['alignedstack']=os.path.abspath("mrastack")
		self.params['alignedstack'] = string.replace(self.params['alignedstack'],"/jetstor/APPION","")

		# remove cls file used for alignment
		os.remove("cls_all.lst")

	#=====================
	def runIMAGICmra(self):
		bfile = "mralign.job"
		outfile = "mrastack"
		apFile.removeStack(outfile)

		f = open(bfile,'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		if self.params['nproc'] > 1:
			f.write("mpirun -np %i -x IMAGIC_BATCH %s/align/mralign.e_mpi << EOF\n" %(self.params['nproc'],self.imagicroot))
			if int(self.imagicversion) != 110119:
				f.write("YES\n")
				f.write("%i\n"%self.params['nproc'])
		else:
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

		# check if there are any rotations stored in the header
		#TEMPORARY HACK
		hasRots=False
		if self.params['currentiter'] > 1:
			hasRots=True

		# don't ask Max shift (during this alignment) for first iteration:
		if hasRots is True:
			f.write("0.2\n")
		f.write("-180,180\n")
		# don't ask rotation (during this alignment) for first iteration:
		if hasRots is True:
			f.write("-180,180\n")
		f.write("MEDIUM\n")
		f.write("0.0,%.2f\n"%(self.workingmask*2/self.workingboxsize))
		f.write("2\n")
		f.write("NO\n")
		f.write("EOF\n")
		f.write("\n")

		### write out alignment parameters to file
		f.write("%s/stand/headers.e <<EOF\n" % self.imagicroot)
		if int(self.imagicversion) < 91120:
			f.write(outfile+"\n")
			f.write("PLT\n")
			f.write("SHIFT\n")
			f.write("outparams.plt\n")
			f.write("*\n")
		else:
			f.write("PLT\n")
			f.write("SHIFT\n")
			f.write(outfile+"\n")
			f.write("outparams.plt\n")
		f.write("EOF\n")
		f.write("touch mra_done.txt\n")
		f.write("exit\n")
		f.close()

		## execute the batch file
		aligntime0 = time.time()
		apEMAN.executeEmanCmd("chmod 755 "+bfile)

		apDisplay.printColor("Running IMAGIC .batch file: %s"%(os.path.abspath(bfile)), "cyan")
		apIMAGIC.executeImagicBatchFile(os.path.abspath(bfile))

		os.remove("mra_done.txt")

		if not os.path.exists(outfile+".hed"):
			apDisplay.printError("ERROR IN IMAGIC SUBROUTINE")
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

		if self.params['currentiter'] > 1:
			apFile.removeStack(self.params['alignedstack'])
		self.params['alignedstack']=os.path.abspath(outfile)
		self.params['alignedstack'] = string.replace(self.params['alignedstack'],"/jetstor/APPION","")

	#=====================
	def runIMAGICmsa(self):
		bfile = "msa.job"
		outfile = "msaout"
		apFile.removeStack(outfile)
		stackfile = self.params['alignedstack']

		# convert mask to fraction for imagic
		maskfrac = self.workingmask*2/self.workingboxsize

		## make an msa mask file
		imagicFilters.mask2D(self.workingboxsize, maskfrac, maskfile='msamask')

		f = open(bfile,'w')
		f.write("#!/bin/csh -f\n")

		f.write("setenv IMAGIC_BATCH 1\n")
		if self.params['msaproc'] > 1:
			f.write("mpirun -np %i -x IMAGIC_BATCH %s/msa/msa.e_mpi << EOF\n" %(self.params['msaproc'],self.imagicroot))
			if int(self.imagicversion) != 110119:
				f.write("YES\n")
				f.write("%i\n"%self.params['msaproc'])
		else:
			f.write("%s/msa/msa.e <<EOF\n" % self.imagicroot)
			if int(self.imagicversion) != 110326:
				f.write("NO\n")
		if int(self.imagicversion) != 110119 and int(self.imagicversion) != 100312:
			f.write("NO\n")
		f.write("FRESH_MSA\n")
		f.write("MODULATION\n")
		f.write("%s\n"%stackfile)
		if int(self.imagicversion) <= 100312:
			f.write("NO\n")
		f.write("msamask\n")
		f.write("eigenim\n")
		if int(self.imagicversion) < 120619:
			f.write("my_pixcoos\n")
			f.write("my_eigenpix\n")
		else:
			f.write("NO\n")
		f.write("%i\n"%self.params['msaiter'])
		f.write("%i\n"%self.params['numeigen'])
		if int(self.imagicversion) >= 120619:
			f.write("1\n")
		f.write("%.02f\n"%self.params['overcorrection'])
		f.write("%s\n"%outfile)
		f.write("EOF\n")

		f.write("touch msa_done.txt\n")
		f.write("exit\n")
		f.close()

		## execute the batch file
		aligntime0 = time.time()
		apEMAN.executeEmanCmd("chmod 755 "+bfile)

		apDisplay.printColor("Running IMAGIC .batch file: %s"%(os.path.abspath(bfile)), "cyan")
		apIMAGIC.executeImagicBatchFile(os.path.abspath(bfile))


		os.remove("msa_done.txt")

		if not os.path.exists(outfile+".plt"):
			apDisplay.printError("ERROR IN IMAGIC SUBROUTINE")
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

		## run classification & class averaging
		self.runIMAGICclassify()

		# align resulting classes
		self.alignClasses()

	#=====================
	def runIMAGICclassify(self):
		bfile = "msaclassify.job"
		outfile = "classes"
		apFile.removeStack(outfile)
		numIters = int(self.params['numpart']*self.params['itermult'])
		decrement = self.params['start']-self.params['end']
		if self.params['iter']>0:
			decrement /= float(self.params['iter'])
		numClasses = self.params['start']-(decrement*self.params['currentiter'])
		stackfile = self.params['alignedstack']
		self.params['currentnumclasses'] = numClasses

		f = open(bfile,'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("%s/msa/classify.e <<EOF\n" % self.imagicroot)
		f.write("IMAGES\n")
		f.write("%s\n"%stackfile)
		f.write("0\n")
		f.write("%i\n"%self.params['activeeigen'])
		f.write("YES\n")
		f.write("%i\n"%numClasses)
		f.write("classes_start\n")
		f.write("EOF\n")

		f.write("%s/msa/classum.e <<EOF\n" % self.imagicroot)
		f.write("%s\n"%stackfile)
		f.write("classes_start\n")
		f.write("%s\n"%outfile)
		f.write("YES\n")
		f.write("NONE\n")
		f.write("0\n")
		if int(self.imagicversion) >= 120619:
			f.write("NONE\n") # Mode of summing statistics
		f.write("EOF\n")

		## make eigenimage stack appion-compatible
		f.write("proc2d eigenim.hed eigenim.hed inplace\n")

		f.write("touch msaclassify_done.txt\n")
		f.write("exit\n")
		f.close()

		## execute the batch file
		aligntime0 = time.time()
		apEMAN.executeEmanCmd("chmod 755 "+bfile)

		apDisplay.printColor("Running IMAGIC .batch file: %s"%(os.path.abspath(bfile)), "cyan")
		apIMAGIC.executeImagicBatchFile(os.path.abspath(bfile))

		os.remove("msaclassify_done.txt")

		if not os.path.exists(outfile+".hed"):
			apDisplay.printError("ERROR IN IMAGIC SUBROUTINE")
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

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
		import operator
		
		directories = []
		members = tarobj.getmembers()

		for tarinfo in members:
			if tarinfo.isdir():
				# Extract directories with a safe mode.
				directories.append(tarinfo)
				tarinfo = copy.copy(tarinfo)
				tarinfo.mode = 0700
			tarobj.extract(tarinfo, ".")

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

		## revert when using python 2.5+
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

		# increment partnum so it starts with 1
		for p in pinfo:
			p['partnum']+=1

		return pinfo

	#=====================
	def readPartIMAGICFile(self):
		## create an array of particle information
		pinfo = []
		# get particle information from imagic file
		alifile = "outparams.plt"
		if not os.path.isfile(alifile):
			apDisplay.printWarning("No IMAGIC alignment file found!  Setting alignment params to 0")
			for pnum in range(1,self.params['numpart']+1):
				pdata = {}
				pdata['partnum'] = pnum
				pdata['inplane'] = 0
				pdata['xshift'] = 0
				pdata['yshift'] = 0
				pdata['cc'] = 0
				pdata['mirror'] = 0
				pinfo.append(pdata)
			return pinfo

		# store contents in array
		f = open(alifile)
		for line in f:
			d = line.strip().split()
			if len(d) < 4:
				continue
			pdata = {}
			numlist = [eval(p) for p in d]

			pdata['partnum'] = numlist[0]
			# imagic rotation is opposite the db
			pdata['inplane'] = -numlist[1]
			# imagic's (y,-x )is db's (x,y)
			pdata['xshift'] = numlist[3]
			pdata['yshift'] = -numlist[2]
			pdata['cc'] = 0
			pdata['mirror'] = 0
			pinfo.append(pdata)
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

		## revert when using python 2.5+
		self.TarExtractall(spitar)
		#spitar.extractall()

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
					pclass[p]=self.sortedAvgDict[refn]
				else:
					apDisplay.printError("particle %i has more than 1 classification,"
						+" classified to reference %i and %i"%(p,pclass[p],refn))
			f.close()
			os.remove(spi)
		return pclass

	#=====================
	def imagicClassificationToDict(self):
		### read the particle classification from IMAGIC
		### save as a dictionary
		pclass = {}
		clslist = "classes_start.cls"
		if not os.path.isfile(clslist):
			apDisplay.printError("no IMAGIC cls file found")

		### cls file has file setup as such:
		### class# #Particles FLOAT
		### INT INT INT	INT INT INT
		### logic is to search for a non-int in the 3rd column,
		### and check that the # particles is correct
		f = open(clslist)
		numps=0
		sofar=0
		refn=0
		for l in f:
			vals = l.strip().split()
			if len(vals) < 1:
				continue
			# check if at a new class
			if len(vals)==3 and not vals[2].isdigit():
				if sofar < numps:
					apDisplay.printError("not enough particles in class %i"%refn)
				refn+=1
				if not int(vals[0])==refn:
					apDisplay.printError("Error reading IMAGIC cls file")
				numps = int(vals[1])
				sofar = 0
				continue
			## now add particles to dictionary
			for p in vals:
				p=int(p)
				if p not in pclass:
					pclass[p]=refn
					sofar+=1
				else:
					apDisplay.printError("particle %i has more than 1 classification,"
						+" classified to reference %i and %i"%(p,pclass[p],refn))
				if sofar > numps:
					apDisplay.printError("too many particles in class %i"%refn)
		return pclass		

	#=====================
	def sortClassAverages(self):
		### sort class averages using cross correlation
		apDisplay.printMsg("Sorting final class averages")

		self.sortedAvgDict = {}
		self.sortedList = []

		out = "sortedcls.hed"
		# read class averages
		d = EMData.read_images(self.params['currentcls']+".hed")
		# set translational search range to tenth of box size
		ts = int(self.workingboxsize*0.1)

		# start with first image
		temp = d[0].copy()
		temp.write_image(out,0)
		del d[0]
		k=1

		# sortlist will keep new list of averages, starting with 1
		self.sortedAvgDict[1]=k
		self.sortedList.append(0)
		# sort the class averages
		while (len(d) > 0):
			maxcit = -111
			# find average with highest CC to previous class
			for i in range(len(d)):
				p1 = peak_search(Util.window(ccf(d[i],temp),ts,ts))
				peak = p1[0][0]
				if (peak > maxcit):
					maxcit = peak
					sx = -int(p1[0][4])
					sy = -int(p1[0][5])
					qi = i
					pnum = d[i].get_attr('IMAGIC.imgnum')
			temp = d[qi].copy()
			temp=rot_shift2D(temp, 0, sx, sy, 0)
			del d[qi]
			temp.write_image(out,k)
			k+=1
			self.sortedAvgDict[pnum]=k
			self.sortedList.append(pnum-1)

		apFile.moveStack(out,self.params['currentcls']+".hed")

		return

	#=====================
	def applySort(self):
		out = "classes_avg.hed"
		# read class averages
		avgfile = os.path.join(self.params['iterdir'],"classes_avg.img")

		# make compatible for eman write
		emancmd = "proc2d %s %s inplace"%(avgfile,avgfile)
		apEMAN.executeEmanCmd(emancmd,verbose=False)

		d = EMData.read_images(avgfile)

		for avgn in self.sortedList:
			d[avgn].write_image(out,-1)
		apFile.removeStack(avgfile)

	#=====================
	def start(self):
		self.insertTopolRepJob()
		self.stack = {}
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		if self.params['virtualdata'] is not None:
			self.stack['file'] = self.params['virtualdata']['filename']
		else:
			self.stack['file'] = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		self.dumpParameters()

		self.params['canexe'] = self.getCANPath()

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")

		a = proc2dLib.RunProc2d()
		a.setValue('infile',self.stack['file'])
		a.setValue('outfile',self.params['localstack'])
		a.setValue('apix',self.stack['apix'])
		a.setValue('bin',self.params['bin'])
		a.setValue('last',self.params['numpart']-1)
		a.setValue('append',False)

		if self.params['lowpass'] is not None and self.params['lowpass'] > 1:
			a.setValue('lowpass',self.params['lowpass'])
		if self.params['highpass'] is not None and self.params['highpass'] > 1:
			a.setValue('highpass',self.params['highpass'])
		if self.params['invert'] is True:
			a.setValue('invert',True)
		if self.params['premask'] is True and self.params['mramethod'] != 'imagic':
			a.setValue('mask',self.params['mask'])

		if self.params['virtualdata'] is not None:
			vparts = self.params['virtualdata']['particles']
			plist = [int(p['particleNumber'])-1 for p in vparts]
			a.setValue('list',plist)

		if self.params['uploadonly'] is not True:
			if os.path.isfile(os.path.join(self.params['rundir'],"stack.hed")):
				self.params['localstack']=os.path.join(self.params['rundir'],"stack.hed")
			else:
				a.run()
			if self.params['numpart'] != apFile.numImagesInStack(self.params['localstack']):
				apDisplay.printError("Missing particles in stack")

			### IMAGIC mask particles before alignment
			if self.params['premask'] is True and self.params['mramethod'] == 'imagic':
				# convert mask to fraction for imagic
				maskfrac = self.workingmask*2/self.workingboxsize
				maskstack = imagicFilters.softMask(self.params['localstack'],mask=maskfrac)
				shutil.move(maskstack+".hed",os.path.splitext(self.params['localstack'])[0]+".hed")
				shutil.move(maskstack+".img",os.path.splitext(self.params['localstack'])[0]+".img")

		origstack = self.params['localstack']
		### find number of processors
#		if self.params['nproc'] is None:
		self.params['nproc'] = apParam.getNumProcessors()

		if self.params['uploadonly'] is not True:
			aligntime = time.time()
			# run through iterations
			for i in range(0,self.params['iter']+1):
				# move back to starting directory
				os.chdir(self.params['rundir'])

				# set up next iteration directory
				self.params['currentiter'] = i
				self.params['iterdir'] = os.path.abspath("iter%02i" % i)
				self.params['iterdir'] = string.replace(self.params['iterdir'],"/jetstor/APPION","")
				if os.path.exists(self.params['iterdir']):
					apDisplay.printError("Error: directory '%s' exists, aborting alignment" % self.params['iterdir'])

				# create directory for iteration
				os.makedirs(self.params['iterdir'])	
				os.chdir(self.params['iterdir'])

				# if at first iteration, create initial class averages 
				if i == 0:
					# first rewrite localstack headers if particles not pre-masked
					if self.params['premask'] is False and self.params['mramethod'] == "imagic":
						imagicFilters.takeoverHeaders(self.params['localstack'],self.params['numpart'],self.workingboxsize)
					self.params['alignedstack'] = os.path.splitext(self.params['localstack'])[0]
					if self.params['msamethod']=='imagic':
						self.runIMAGICmsa()
					else:
						self.runCAN()
					continue

				# using references from last iteration, run multi-ref alignment
				if self.params['mramethod'] == "imagic":
					# rewrite class headers
					imagicFilters.takeoverHeaders(self.params['currentcls'],self.params['currentnumclasses'],self.workingboxsize)
					self.runIMAGICmra()
				else:
					self.runEMANmra()

				# create class averages from aligned stack
				if self.params['msamethod']=='imagic':
					self.runIMAGICmsa()
				else:
					self.runCAN()
			
			aligntime = time.time() - aligntime
			apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		## set upload information params:
		else:
			## get last iteration
			alliters = glob.glob("iter*")
			alliters.sort()

			## get iteration number from iter dir
			self.params['currentiter'] = int(alliters[-1][-2:])
			self.params['iterdir'] = os.path.join(self.params['rundir'],alliters[-1])
			self.params['currentcls'] = "classes%02i"%(self.params['currentiter'])

			## go into last iteration directory
			os.chdir(self.params['iterdir'])
			self.params['alignedstack'] = os.path.abspath("mrastack")
			if os.path.isfile(os.path.join(self.params['rundir'],self.params['currentcls']+".hed")):
				p1 = os.path.join(self.params['rundir'],self.params['currentcls'])
				p2 = os.path.join(self.params['iterdir'],self.params['currentcls'])
				shutil.move(p1+".hed",p2+".hed")
				shutil.move(p1+".img",p2+".img")

		## sort the class averages
		self.sortClassAverages()

		### get particle information from last iteration
		if self.params['mramethod']=='imagic':
			partlist = self.readPartIMAGICFile()
		else:
			partlist = self.readPartEMANFile()
		if self.params['msamethod']=='imagic':
			partrefdict = self.imagicClassificationToDict()
		else:
			partrefdict = self.canClassificationToDict()

		# move back to starting directory
		os.chdir(self.params['rundir'])

		# move aligned stack to current directory for appionweb
		if not os.path.isfile("mrastack.hed"):
			shutil.move(self.params['alignedstack']+".hed","mrastack.hed")
			shutil.move(self.params['alignedstack']+".img","mrastack.img")
			# rewrite header
			if self.params['mramethod'] == "imagic" or self.params['msamethod'] == 'imagic':
				imagicFilters.takeoverHeaders("mrastack",self.params['numpart'],self.workingboxsize)

		# move actual averages to current directory
		if self.params['msamethod']=='can':
			if not os.path.isfile("classes_avg.hed"):
				self.applySort()
			# save actual class averages as refs in database
			self.params['currentcls']="classes_avg"
		
		
		### create an average mrc of final references 
		if not os.path.isfile("average.mrc"):
			apStack.averageStack(stack=self.params['currentcls']+".hed")
			self.dumpParameters()

		### remove the filtered stack
		apFile.removeStack(origstack)

		### save to database
		if self.params['commit'] is True:
			self.insertRunIntoDatabase()
			self.insertParticlesIntoDatabase(partlist, partrefdict)

#=====================
if __name__ == "__main__":
	topRep = TopologyRepScript()
	topRep.start()
	topRep.close()



