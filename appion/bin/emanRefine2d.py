#!/usr/bin/env python

import os
import sys
import time
import math
import glob
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apParam
from appionlib import apFile
from appionlib import apEMAN
from appionlib import appiondata

#=====================
#=====================
class Refine2dScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		### refine2d options
		self.parser.add_option("--num-iter", dest="numiter", type="int", default=8,
			help="Number of iterations to perform", metavar="#")
		self.parser.add_option("--num-classes", dest="numclasses", type="int", default=50,
			help="Number of classes to create", metavar="#")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="Stack id to align", metavar="#")

		### stack preparation options
		self.parser.add_option("--lp", "--lowpass", dest="lowpass", type="float",
			help="Low pass filter to apply to stack before processing in Angstroms",
			metavar="#.#")		
		self.parser.add_option("--hp", "--highpass", dest="highpass", type="float",
			help="High pass filter to apply to stack before processing in Angstroms",
			metavar="#.#")		
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning to apply to stack before processing", metavar="#")
		self.parser.add_option("--num-part", dest="numpart", type="int",
			help="Number of particles to align from stack", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("Please provide a stack id, e.g. --stackid=15")
		if self.params['runname'] is None:
			apDisplay.printError("Please provide a run name id, e.g. --runname=refine1")
		if self.params['description'] is None:
			apDisplay.printError("Please provide a description, e.g. --description='something'")
		### get number of particles in stack
		numpart = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		if self.params['numpart'] is None:
			self.params['numpart'] = numpart
		elif self.params['numpart'] > numpart:
			apDisplay.printError("Requested number of particles (%d) is greater than the number of particles in the stack (%d)"%(self.params['numpart'], numpart))

	#=====================
	def setRunDir(self):
		"""
		This function is only run, if --rundir is not defined on the commandline
		"""
		### get the path to input stack
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		### good idea to set absolute path,
		stackpath = os.path.abspath(stackdata['path']['path'])
		### same thing in one step
		rundir = os.path.join(stackpath, "../../align", self.params['runname'])
		### good idea to set absolute path,
		### cleans up 'path/stack/stack1/../../example/ex1' -> 'path/example/ex1'
		self.params['rundir'] = os.path.abspath(rundir)

	#=====================
	def determineClassOwnership(self):
		"""
		reads ptcl2orig.lst and cls000#.lst 
		to determine which particles belong to which class
		"""
		ptclf = open('ptcl2orig.lst', 'r')
		count = 0
		### mapping original location -> final location
		orig2finalmap = {}
		### mapping final location -> original location
		final2origmap = {}
		for line in ptclf:
			sline = line.strip()
			if sline[0] == "#":
				continue
			pieces = sline.split()
			num = int(pieces[0])
			orig2finalmap[num] = count
			final2origmap[count] = num
			count += 1
		ptclf.close()

		### determine ownership
		clsfiles = glob.glob("cls*.lst")
		clsfiles.sort()
		classnum = 1
		classmapping = {}
		particlemapping = {}
		for clsfile in clsfiles:
			classf = open(clsfile, "r")
			classlist = []
			for line in classf:
				sline = line.strip()
				if sline[0] == "#":
					continue
				pieces = sline.split()
				partnum = int(pieces[0])
				origpartnum = final2origmap[partnum]
				classlist.append(origpartnum)
				particlemapping[origpartnum] = classnum
			### filled class list
			classmapping[classnum] = classlist
			classnum += 1

		### return class ownership
		return particlemapping

	#=====================
	def commitToDatabase(self):
		"""
		insert the results into the database
		"""
		### expected result for an alignment run:
		### 1. aligned particle stack in IMAGIC
		### 2. rotation, shift, and quality parameters for each particle
		### 3. which particles belongs to which class
		### 4. stack file with the class averages
		
		alignedstack = os.path.join(self.params['rundir'], "ptcl.hed")
		refstack = os.path.join(self.params['rundir'], "iter.final.hed")
		averagemrc = os.path.join(self.params['rundir'], "average.mrc")
		apStack.averageStack(alignedstack, averagemrc)
		particlemapping = self.determineClassOwnership()

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+runparams['runname']
				+"' and path already exisclassmappingt in database")

		### setup eman refine2d run
		emanrefinetwodq = appiondata.ApEMANRefine2dRunData()
		emanrefinetwodq['runname'] = self.params['runname']
		emanrefinetwodq['run_seconds'] = time.time() - self.t0
		emanrefinetwodq['num_iters'] = self.params['numiter']
		emanrefinetwodq['num_classes'] = self.params['numclasses']

		### finish alignment run
		alignrunq['refine2drun'] = emanrefinetwodq
		alignrunq['hidden'] = False
		alignrunq['runname'] = self.params['runname']
		alignrunq['description'] = self.params['description']
		alignrunq['lp_filt'] = self.params['lowpass']
		alignrunq['hp_filt'] = self.params['highpass']
		alignrunq['bin'] = self.params['bin']

		### setup alignment stackalignimagicfile
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = os.path.basename(alignedstack)
		alignstackq['avgmrcfile'] = os.path.basename(averagemrc)
		alignstackq['refstackfile'] = os.path.basename(refstack)
		alignstackq['iteration'] = self.params['numiter']
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
			apDisplay.printErrrefqor("could not find reference stack file: "+refstackfile)

		### continue setting values
		alignstackq['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		alignstackq['boxsize'] = apFile.getBoxSize(alignimagicfilepath)[0]
		alignstackq['pixelsize'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])*self.params['bin']
		alignstackq['description'] = self.params['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] = apFile.numImagesInStack(alignimagicfilepath)

		### inserting particles and references
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for emanpartnum in range(self.params['numpart']):
			partnum = emanpartnum+1
			if partnum % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refnum = particlemapping[emanpartnum]
			refq['refnum'] = refnum
			refq['iteration'] = self.params['numiter']
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = alignrunq

			### TODO: create mrc file
			#refq['mrcfile'] = refbase+".mrc"
			#reffile = os.path.join(self.params['rundir'], refq['mrcfile'])
			#if not os.path.isfile(reffile):
			#	emancmd = "proc2d "+refstack+".xmp "+refstack+".mrc"
			#	apEMAN.executeEmanCmd(emancmd, verbose=False)
			#if not os.path.isfile(reffile):
			#	apDisplay.printError("could not find reference file: "+reffile)

			### TODO: get resolution
			#refq['ssnr_resolution'] = TODO

			### setup particle
			alignpartq = appiondata.ApAlignParticleData()
			alignpartq['partnum'] = partnum
			alignpartq['alignstack'] = alignstackq
			stackpartdata = apStack.getStackParticle(self.params['stackid'], partnum)
			alignpartq['stackpart'] = stackpartdata
			### TODO: get the alignment parameters
			#alignpartq['xshift'] = partdict['xshift']
			#alignpartq['yshift'] = partdict['yshift']
			#alignpartq['rotation'] = partdict['inplane']
			#alignpartq['mirror'] = partdict['mirror']
			alignpartq['ref'] = refq
			### TODO: get the score
			#alignpartq['score'] = partdict['score']

			### insert
			if self.params['commit'] is True:
				alignpartq.insert()

		return

	#=====================
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
				
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		original_stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		filtered_stackfile = os.path.join(self.params['rundir'], self.timestamp+".hed")
		apFile.removeStack(filtered_stackfile, warn=False)
		apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		boxsize = apStack.getStackBoxsize(self.params['stackid'])

		emancmd = "proc2d %s %s apix=%.3f "%(original_stackfile, filtered_stackfile, apix)
		if self.params['lowpass'] is not None:
			emancmd += " lp=%.3f "%(self.params['lowpass'])
		if self.params['highpass'] is not None:
			emancmd += " hp=%.3f "%(self.params['highpass'])
		if self.params['bin'] is not None and self.params['bin'] > 1:
			## determine a multiple of the bin that is divisible by 2 and less than the boxsize
			clipsize = int(math.floor(boxsize/float(self.params['bin']*2)))*2*self.params['bin']
			emancmd += " shrink=%d clip=%d,%d "%(self.params['bin'], clipsize, clipsize)		
		emancmd += " last=%d "%(self.params['numpart']-1)
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)

		### confirm that it worked
		if self.params['numpart'] != apFile.numImagesInStack(filtered_stackfile):
			apDisplay.printError("Missing particles in stack")

		nproc = apParam.getNumProcessors()

		### run the refine2d.py
		emancmd = ("refine2d.py --iter=%d --ninitcls=%d --proc=%d %s"
				%(self.params['numiter'], self.params['numclasses'],
				nproc, filtered_stackfile,)
			)
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)
		
		self.commitToDatabase()

#=====================
#=====================
if __name__ == '__main__':
	refscript = Refine2dScript()
	refscript.start()
	refscript.close()

