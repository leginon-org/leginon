#!/usr/bin/env python

import os
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack

#=====================
#=====================
class UploadISAC(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --jobid=ID [ --commit ]")
		self.parser.add_option("-j", "--jobid", dest="jobid", type="int",
			help="ISAC jobid", metavar="#")

	#=====================
	def checkConflicts(self):
		return

	#=====================
	def setRunDir(self):
		if self.params["jobid"] is not None:
			jobdata = appiondata.ApMaxLikeJobData.direct_query(self.params["jobid"])
			self.params['rundir'] = jobdata['path']['path']
		else:
			self.params['rundir'] = os.path.abspath(".")

	#=====================
	def getMaxLikeJob(self, runparams):
		maxjobq = appiondata.ApMaxLikeJobData()
		maxjobq['runname'] = runparams['runname']
		maxjobq['path'] = appiondata.ApPathData(path=os.path.abspath(runparams['rundir']))
		maxjobq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(runparams['stackid'])
		maxjobq['timestamp'] = self.params['timestamp']
		maxjobdata = maxjobq.query(results=1)
		if not maxjobdata:
			return None
		return maxjobdata[0]

	#=====================
	def insertRunIntoDatabase(self, alignimagicfile, runparams):
		apDisplay.printMsg("Inserting MaxLike Run into DB")

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = runparams['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']+"' and path already exist in database")

		### setup max like run
		maxlikeq = appiondata.ApMaxLikeRunData()
		maxlikeq['runname'] = runparams['runname']
		maxlikeq['run_seconds'] = runparams['runtime']
		#maxlikeq['mask_diam'] = 2.0*runparams['maskrad']
		maxlikeq['fast'] = runparams['fast']
		maxlikeq['fastmode'] = runparams['fastmode']
		maxlikeq['mirror'] = runparams['mirror']
		maxlikeq['student'] = bool(runparams['student'])
		maxlikeq['init_method'] = "xmipp default"
		maxlikeq['job'] = self.getMaxLikeJob(runparams)

		### finish alignment run
		alignrunq['maxlikerun'] = maxlikeq
		alignrunq['hidden'] = False
		alignrunq['runname'] = runparams['runname']
		alignrunq['description'] = runparams['description']
		alignrunq['lp_filt'] = runparams['lowpass']
		alignrunq['hp_filt'] = runparams['highpass']
		alignrunq['bin'] = runparams['bin']

		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = alignimagicfile
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = "part"+self.params['timestamp']+"_average.hed"
		alignstackq['iteration'] = self.lastiter
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq
		### check to make sure files exist
		alignimagicfilepath = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(alignimagicfilepath):
			apDisplay.printError("could not find stack file: "+alignimagicfilepath)
		avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
		if not os.path.isfile(avgmrcfile):
			apDisplay.printError("could not find average mrc file: "+avgmrcfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = apStack.getOnlyStackData(runparams['stackid'])
		alignstackq['boxsize'] = apFile.getBoxSize(alignimagicfilepath)[0]
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		alignstackq['description'] = runparams['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] =  runparams['numpart']

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return

	#=====================
	def insertParticlesIntoDatabase(self, stackid, partlist):
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for partdict in partlist:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refq['refnum'] = partdict['refnum']
			refq['iteration'] = self.lastiter
			refsearch = "part"+self.params['timestamp']+"_ref*"+str(partdict['refnum'])+"*"
			refbase = os.path.splitext(glob.glob(refsearch)[0])[0]
			refq['mrcfile'] = refbase+".mrc"
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			if partdict['refnum']  in self.resdict:
				refq['ssnr_resolution'] = self.resdict[partdict['refnum']]
			reffile = os.path.join(self.params['rundir'], refq['mrcfile'])
			if not os.path.isfile(reffile):
				emancmd = "proc2d "+refbase+".xmp "+refbase+".mrc"
				apEMAN.executeEmanCmd(emancmd, verbose=False)
			if not os.path.isfile(reffile):
				apDisplay.printError("could not find reference file: "+reffile)

			### setup particle
			alignpartq = appiondata.ApAlignParticleData()
			alignpartq['partnum'] = partdict['partnum']
			alignpartq['alignstack'] = self.alignstackdata
			stackpartdata = apStack.getStackParticle(stackid, partdict['partnum'])
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = partdict['xshift']
			alignpartq['yshift'] = partdict['yshift']
			alignpartq['rotation'] = partdict['inplane']
			alignpartq['mirror'] = partdict['mirror']
			alignpartq['ref'] = refq
			alignpartq['spread'] = partdict['spread']

			### insert
			if self.params['commit'] is True:
				inserted += 1
				alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

		return

	#=====================
	def calcResolution(self, partlist, alignimagicfile, apix):
		### group particles by refnum
		reflistsdict = {}
		for partdict in partlist:
			refnum = partdict['refnum']
			partnum = partdict['partnum']
			if not refnum in reflistsdict:
					reflistsdict[refnum] = []
			reflistsdict[refnum].append(partnum)

		### get resolution
		self.resdict = {}
		boxsizetuple = apFile.getBoxSize(alignimagicfile)
		boxsize = boxsizetuple[0]
		for refnum in reflistsdict.keys():
			partlist = reflistsdict[refnum]
			esttime = 3e-6 * len(partlist) * boxsize**2
			apDisplay.printMsg("Ref num %d; %d parts; est time %s"
				%(refnum, len(partlist), apDisplay.timeString(esttime)))

			frcdata = apFourier.spectralSNRStack(alignimagicfile, apix, partlist, msg=False)
			frcfile = "frcplot-%03d.dat"%(refnum)
			apFourier.writeFrcPlot(frcfile, frcdata, apix, boxsize)
			res = apFourier.getResolution(frcdata, apix, boxsize)

			self.resdict[refnum] = res

		return

	#=====================
	#=====================
	def start(self):
		### load parameters
		runparams = self.readRunParameters()

		### align references
		self.alignReferences(runparams)

		### create an aligned stack
		self.createAlignedReferenceStack()

		### read particles
		self.lastiter = self.findLastIterNumber()
		if self.params['sort'] is True:
			self.sortFolder()
		reflist = self.readRefDocFile()
		partlist = self.readPartDocFile(reflist)
		self.writePartDocFile(partlist)

		### create aligned stacks
		alignimagicfile = self.createAlignedStacks(partlist, runparams['localstack'])
		apStack.averageStack(alignimagicfile)

		### calculate resolution for each reference
		apix = apStack.getStackPixelSizeFromStackId(runparams['stackid'])*runparams['bin']
		self.calcResolution(partlist, alignimagicfile, apix)

		### insert into databse
		self.insertRunIntoDatabase(alignimagicfile, runparams)
		self.insertParticlesIntoDatabase(runparams['stackid'], partlist)

		apFile.removeStack(runparams['localstack'], warn=False)
		rmcmd = "/bin/rm -fr partfiles/*"
		apEMAN.executeEmanCmd(rmcmd, verbose=False, showcmd=False)
		apFile.removeFilePattern("partfiles/*")

#=====================
#=====================
if __name__ == '__main__':
	runner = UploadISAC()
	runner.start()
	runner.close()

