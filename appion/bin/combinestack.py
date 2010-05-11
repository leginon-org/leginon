#!/usr/bin/env python


import os
import re
import sys
### appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apEMAN
from appionlib import apProject
from appionlib import apFile

#=====================
#=====================
class combineStackScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --name=<name> --stacks=<int>,<int>,<int>  "
			+"--description='<text>' --commit [options]")
		self.parser.add_option("--stacks", dest="stacks",
			help="list of stack ids to combine, e.g. --stackids=11,14,7", metavar="LIST")
		self.parser.add_option("--stack-filename", dest="stackfilename", default="start.hed",
			help="Name of stack file name, e.g. start.hed", metavar="start.hed")

	#=====================
	def checkConflicts(self):
		if self.params['runname'] is None:
			apDisplay.printError("enter a stack run name, e.g. combinestack1")
		if self.params['description'] is None:
			apDisplay.printError("enter a stack description")

		if self.params['stacks'] and ',' in self.params['stacks']:
			#remember stackids are a list of strings
			stackids = self.params['stacks'].split(',')
			self.params['stackids'] = stackids
		else:
			apDisplay.printError("enter a list of stack ids to combine, e.g. --stackids=11,14,7")

		### check to make sure all pixel and box size are the same
		self.newboxsize = None
		self.newpixelsize = None
		for stackidstr in self.params['stackids']:
			if not re.match("^[0-9]+$", stackidstr):
				apDisplay.printError("Stack id '%s' is not an integer"%(stackidstr))
			stackid = int(stackidstr)
			boxsize = apStack.getStackBoxsize(stackid, msg=False)
			pixelsize = apStack.getStackPixelSizeFromStackId(stackid, msg=False)
			apDisplay.printMsg("Stack id: %d\tBoxsize: %d\tPixelsize: %.3f"%(stackid, boxsize, pixelsize))
			if self.newboxsize is None:
				self.newboxsize = boxsize
			if self.newpixelsize is None:
				self.newpixelsize = pixelsize
			if boxsize != self.newboxsize:
				apDisplay.printError("Trying to combine stacks with different box sizes")
			if abs(pixelsize - self.newpixelsize) > 0.01:
				apDisplay.printError("Trying to combine stacks with different pixel sizes")

	#=====================
	def setRunDir(self):
		stackid = int(self.params['stackids'][-1])
		stackdata = apStack.getOnlyStackData(stackid, msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def appendToStack(self, stackdata):
		addfile  = os.path.join( stackdata['path']['path'], stackdata['name'] )

		addnumpart = apFile.numImagesInStack(addfile)
		orignumpart = apFile.numImagesInStack(self.combinefile)

		cmd = "proc2d "+addfile+" "+self.combinefile
		apDisplay.printMsg("adding "+str(addnumpart)+" particles to "+str(orignumpart)+" particles")
		apEMAN.executeEmanCmd(cmd, verbose=True, showcmd=True)

		newnumpart = apFile.numImagesInStack(self.combinefile)

		apDisplay.printMsg("added "+str(addnumpart)+" particles from stackid="+str(stackdata.dbid)+" to "
			+str(orignumpart)+" particles giving a new combined stack of "+str(newnumpart)+" particles")

		if addnumpart + orignumpart < newnumpart:
			apDisplay.printError("Error in stack merging, too few particles added")

		return

	#=====================
	def commitStack(self, stackid):

		startpart = self.partnum

		stackq = appiondata.ApStackData()
		oldstackdata = apStack.getOnlyStackData(stackid)
		stackq['name'] = self.params['stackfilename']
		stackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		stackq['description'] = self.params['description']+" ... combined stack ids "+str(self.params['stacks'])
		stackq['substackname'] = self.params['runname']
		stackq['hidden'] = False
		stackq['pixelsize'] = self.newpixelsize*1e-10
		stackq['boxsize'] = self.newboxsize

		rinstackdata = apStack.getRunsInStack(stackid)
		for run in rinstackdata:
			rinstackq = appiondata.ApRunsInStackData()
			rinstackq['stack']    = stackq
			rinstackq['stackRun'] = run['stackRun']
			rinstackq.insert()

		stpartsdata = apStack.getStackParticlesFromId(stackid)
		apDisplay.printMsg("inserting "+str(len(stpartsdata))+" particles into DB")
		for particle in stpartsdata:
			stpartq = appiondata.ApStackParticleData()
			stpartq['particleNumber'] = self.partnum
			stpartq['stack']    = stackq
			stpartq['stackRun'] = particle['stackRun']
			stpartq['particle'] = particle['particle']
			stpartq.insert()
			self.partnum += 1
			if self.partnum % 1000 == 0:
				sys.stderr.write(".")
		sys.stderr.write("\n")

		apDisplay.printMsg("commited particles "+str(startpart)+"-"+str(self.partnum))

		return

	#=====================
	def start(self):
		### universal particle counter
		self.partnum = 1

		### final stack file
		self.combinefile = os.path.join( self.params['rundir'], self.params['stackfilename'] )
		if os.path.isfile(self.combinefile):
			apDisplay.printError("A stack with name "+self.params['stackfilename']+" and path "
				+self.params['rundir']+" already exists.")

		### loop through stacks
		for stackstr in self.params['stackids']:
			stackid = int(stackstr)

			### get stack data
			stackdata = apStack.getOnlyStackData(stackid)

			### append particle to stack file
			self.appendToStack(stackdata)

			if self.params['commit'] is True:
				### insert stack data
				apDisplay.printColor("inserting new stack particles from stackid="+str(stackid), "cyan")
				self.commitStack(stackid)
			else:
				apDisplay.printWarning("not committing data to database")

		apStack.averageStack(stack=self.combinefile)


#=====================
if __name__ == "__main__":
	combineStack = combineStackScript()
	combineStack.start()
	combineStack.close()




