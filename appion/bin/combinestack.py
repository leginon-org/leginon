#!/usr/bin/env python


import os
import sys
### appion
import appionScript
import apStack
import apDisplay
import appionData
import apEMAN
import apProject
import apFile

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
		if self.params['stacks'] and ',' in self.params['stacks']:
			#remember stackids are a list of strings
			stackids = self.params['stacks'].split(',')
			self.params['stackids'] = stackids
		else:
			apDisplay.printError("enter a list of stack ids to combine, e.g. --stackids=11,14,7")
		if self.params['runname'] is None:
			apDisplay.printError("enter a stack run name, e.g. combinestack1")
		if self.params['description'] is None:
			apDisplay.printError("enter a stack description")

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
	
		return


	#=====================
	def commitStack(self, stackid):

		startpart = self.partnum

		stackq = appionData.ApStackData()
		stackq['name'] = self.params['stackfilename']
		stackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		stackq['description'] = self.params['description']+" ... combined stack ids "+str(self.params['stacks'])
		stackq['substackname'] = self.params['runname']
		stackq['project|projects|project'] = apProject.getProjectIdFromStackId(stackid)
		stackq['hidden'] = False

		rinstackdata = apStack.getRunsInStack(stackid)
		for run in rinstackdata:
			rinstackq = appionData.ApRunsInStackData()
			rinstackq['stack']    = stackq
			rinstackq['stackRun'] = run['stackRun']
			rinstackq['project|projects|project'] = run['project|projects|project']
			rinstackq.insert()
				
		stpartsdata = apStack.getStackParticlesFromId(stackid)
		print "inserting "+str(len(stpartsdata))+" particles into DB"
		for particle in stpartsdata:
			stpartq = appionData.ApStackParticlesData()
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


	
