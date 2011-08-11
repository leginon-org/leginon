#!/usr/bin/env python


import os
import re
import sys
import shutil
import numpy
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
class dbStackDownload(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --runname=<name> --stack=<int>  "
			+"--description='<text>' --commit [options] --package=<packagename>")
		self.parser.add_option("--stackid", dest="stackid",
			help="which stack should be downloaded", metavar="LIST")
		self.parser.add_option("--stack-filename", dest="stackfilename", default="start.hed",
			help="Name of stack file name, e.g. start.hed", metavar="start.hed")

	#=====================
	def checkConflicts(self):
		if self.params['runname'] is None:
			apDisplay.printError("enter a stack run name, e.g. dbstackdownload")
		if self.params['description'] is None:
			apDisplay.printError("enter a stack description")

		if self.params['stackid'] is None:
			apDisplay.printError("enter a stackid for download")


	#=====================
	def setRunDir(self):
		stackid = int(self.params['stackid'])
		#stackdata = apStack.getOnlyStackData(stackid, msg=False)
		stackdata = apStack.getOnlyStackData(stackid)
		print "stackdata: ", stackdata
		path = stackdata['path']['path']
		#substitude the stacks with dbstacks folder
		uppath = os.path.dirname(os.path.abspath(path))[:-6]+"dbstacks"
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

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
		### final stack file
		self.dbstackfile = os.path.join( self.params['rundir'], self.params['stackfilename'] )
		if os.path.isfile(self.dbstackfile):
			apDisplay.printError("A stack with name "+self.params['stackfilename']+" and path "
				+self.params['rundir']+" already exists.")

		#self.stackid = int(self.params['stackid'])
		#self.stackdata = apStack.getOnlyStackData(self.stackid)

		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		originalstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		#self.dbstackfile #new file
		shutil.copyfile(originalstack,self.dbstackfile)
		shutil.copyfile(originalstack[:-3]+"img",self.dbstackfile[:-3]+"img")
		
		stackpartdata = apStack.getStackParticlesFromId(self.params['stackid'])
		dbids = [part.dbid for part in stackpartdata]

		for i,id in enumerate(dbids):
			numpy.memmap(self.dbstackfile, dtype="float32", offset=i*1024+19*4)[0] = id




#=====================
if __name__ == "__main__":
	dbStackDownload = dbStackDownload()
	dbStackDownload.start()
	dbStackDownload.close()




