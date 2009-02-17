#!/usr/bin/env python

#python
import os
import shutil
import time
import numpy
#appion
import appionScript
import apStack
import apFile
import apParam
import apXmipp
import apImagicFile
import apDisplay
import apEMAN
import apImage
from apSpider import operations

class centerStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--maxshift", dest="maxshift", type="int",
			help="Maximum shift", metavar="#")
		self.parser.add_option("--new-stack-name", dest="runname",
			help="Run name", metavar="STR")

		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int", default=50,
			help="Low pass filter radius (in Angstroms) not applied to final particles", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int", default=1000,
			help="High pass filter radius (in Angstroms) not applied to final particles", metavar="#")

		### true/false
		self.parser.add_option("-M", "--mirror", dest="mirror", default=False,
			action="store_true", help="Use mirror method")
		self.parser.add_option("--no-mirror", dest="mirror", default=False,
			action="store_false", help="Do NOT use rotate method")
		self.parser.add_option("--rotate", dest="rotate", default=False,
			action="store_true", help="Use rotate method")
		self.parser.add_option("--no-rotate", dest="rotate", default=False,
			action="store_false", help="Do NOT use rotate method")

		### choices
		self.convergemodes = ( "normal", "fast", "slow" )
		self.parser.add_option("--converge", dest="converge",
			help="Convergence criteria mode", metavar="MODE", 
			type="choice", choices=self.convergemodes, default="normal" )

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		if oldstack[-4:] == ".hed":
			oldstack = oldstack[:-4]+".img"
		stacksize = apFile.fileSize(oldstack)/1024.0/1024.0
		if stacksize > 1200:
			apDisplay.printError("Stack is too large to read "+str(round(stacksize,1))+" MB")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def writeXmippLog(self, text):
		f = open("xmipp.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def runMaxlike(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")
		proccmd = "proc2d "+stackfile+" "+self.params['localstack']+" apix="+str(apix)
		if self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		apEMAN.executeEmanCmd(proccmd, verbose=True)

		### convert stack into single spider files
		self.partlistdocfile = apXmipp.breakupStackIntoSingleFiles(self.params['localstack'])

		### setup Xmipp command
		aligntime = time.time()
		xmippopts = ( " "
			+" -i "+os.path.join(self.params['rundir'], self.partlistdocfile)
			+" -nref 1 "
			+" -iter 10 "
			+" -o "+os.path.join(self.params['rundir'], "part"+self.timestamp)
			+" -fast -C 1e-18 "
		)
		### angle step
		if self.params['rotate'] is True:
			xmippopts += " -psi_step 90 "
		else:
			xmippopts += " -psi_step 360 "
		### convergence criteria
		if self.params['converge'] == "fast":
			xmippopts += " -eps 5e-3 "
		elif self.params['converge'] == "slow":
			xmippopts += " -eps 5e-8 "
		else:
			xmippopts += " -eps 5e-5 "
		### mirrors
		if self.params['mirror'] is True:
			xmippopts += " -mirror "
		if self.params['maxshift'] is not None:
			xmippopts += " -max_shift %d "%(self.params['maxshift'])


		### use single processor
		xmippexe = apParam.getExecPath("xmipp_ml_align2d", die=True)
		xmippcmd = xmippexe+" "+xmippopts
		self.writeXmippLog(xmippcmd)
		apEMAN.executeEmanCmd(xmippcmd, verbose=True, showcmd=True)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### create a quick mrc
		emancmd = "proc2d part"+self.timestamp+"_ref000001.xmp average.mrc"
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apFile.removeStack(self.params['localstack'])
		apFile.removeFilePattern("partfiles/*")


	#=====================
	def writeFakeKeepFile(self, numpart):
		"""
		This method keeps all particles
		"""
		self.params['keepfile'] = os.path.join(self.params['rundir'], "allparticles.lst")
		f = open(self.params['keepfile'], "w")
		for partnum in range(numpart):
			f.write("%d\n"%(partnum))
		f.close()
			
	#=====================
	def readPartDocFile(self):
		partlist = []
		docfile = "part"+self.timestamp+".doc"
		if not os.path.isfile(docfile):
			apDisplay.printError("could not find doc file "+docfile+" to read particle angles")
		f = open(docfile, "r")
		mininplane = 360.0
		for line in f:
			if line[:2] == ' ;':
				continue
			spidict = operations.spiderInLine(line)
			partdict = self.spidict2partdict(spidict)
			if partdict['inplane'] < mininplane:
				mininplane = partdict['inplane']
			partlist.append(partdict)
		apDisplay.printMsg("minimum inplane: "+str(mininplane))
		for partdict in partlist:
			partdict['inplane'] = partdict['inplane']-mininplane
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(partlist))+" particles")
		return partlist

	#=====================
	def spidict2partdict(self, spidict):
		partdict = {
			'partnum': int(spidict['row']),
			'inplane': float(spidict['floatlist'][2]),
			'xshift': float(spidict['floatlist'][3]),
			'yshift': float(spidict['floatlist'][4]),
			'refnum': int(spidict['floatlist'][5]),
			'mirror': bool(spidict['floatlist'][6]),
			'spread': float(spidict['floatlist'][7]),
		}
		return partdict

	#=====================
	def createAlignedStacks(self, partlist):
		stackid = self.params['stackid']
		stackdata = apStack.getOnlyStackData(stackid)
		origstackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		imagesdict = apImagicFile.readImagic(origstackfile)
		i = 0
		t0 = time.time()
		apDisplay.printMsg("rotating and shifting particles at "+time.asctime())
		alignstack = []
		while i < len(partlist):
			partimg = imagesdict['images'][i]
			partdict = partlist[i]
			partnum = i+1
			#print partnum, partdict, partimg.shape
			if partdict['partnum'] != partnum:
				apDisplay.printError("particle shifting "+str(partnum)+" != "+str(partdict))
			xyshift = (partdict['xshift'], partdict['yshift'])
			alignpartimg = apImage.rotateThenShift(partimg, rot=partdict['inplane'], 
				shift=xyshift, mirror=partdict['mirror'])
			alignstack.append(alignpartimg)
			i += 1
		apDisplay.printMsg("rotate then shift %d particles in %s"%(i,apDisplay.timeString(time.time()-t0)))
		alignstackarray = numpy.asarray(alignstack)
		self.alignimagicfile = "alignstack.hed"
		apImagicFile.writeImagic(alignstackarray, self.alignimagicfile)

	#=====================
	def start(self):
		### new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

		### make sure that old stack is numbered
		alignedstack = os.path.join(self.params['rundir'], 'alignstack.hed')
		apStack.checkForPreviousStack(alignedstack)

		### run centering algorithm
		self.runMaxlike()

		### create aligned stacks
		partlist = self.readPartDocFile()
		stackfile = self.createAlignedStacks(partlist)
		if not os.path.isfile(alignedstack):
			apDisplay.printError("No stack was created")

		### get number of particles
		numpart = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		self.writeFakeKeepFile(numpart)
		self.params['description'] += (
			" ... %d maxlike centered substack id %d" 
			% (numpart, self.params['stackid']))
		
		apStack.commitSubStack(self.params, newname='alignstack.hed', centered=True)
		apStack.averageStack(stack=alignedstack)

#=====================
if __name__ == "__main__":
	cenStack = centerStackScript()
	cenStack.start()
	cenStack.close()

