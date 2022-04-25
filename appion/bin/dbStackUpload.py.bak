#!/usr/bin/env python

#python
import os
import shutil
import random
import numpy
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apStackMeanPlot
from appionlib import apBeamTilt

class dbStackUpload(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --old-stack-id=ID --keep-file=FILE [options]")
		self.parser.add_option("-s", "--old-stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-v", "--new-stack-loc", dest="newstackpath", type="string",
				help="Path to the new stackfile", metavar="PATH")
		self.parser.add_option("-w", "--new-stack-name", dest="newstack",type="string",
				help="filename of the stack", metavar="FILE")
#		self.parser.add_option("-k", "--keep-file", dest="keepfile",
#			help="File listing which particles to keep, EMAN style 0,1,...", metavar="FILE")

		self.parser.add_option("--no-meanplot", dest="meanplot", default=True,
			action="store_false", help="Do not create a mean/stdev plot")
#		self.parser.add_option("--correct-beamtilt", dest="correctbeamtilt", default=False,
#			action="store_true", help="The original stack is sorted")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		
		# creating a keepfile, fixed filename
		self.params['keepfile'] = os.path.join(self.params['newstackpath'],"keepfile.lst")

		#path to the old stack
		oldstack = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		#path to the new stack. the stack path will be provided by the db in the future
		newstack = os.path.join(self.params['newstackpath'], self.params['newstack'])

		#messy way to count the number of particles in a stack
		h = open(newstack, 'r')
		numimg = 0
		while h.read(1024):
			numimg += 1

		#have to use this function to make sure i get the same particle number like in the download
		stackpartdata = apStack.getStackParticlesFromId(self.params['stackid'])
		
		#since the keepfile has to be a proc2d like file, i create a dictionary to transfer the 
		#uniqe particle id into the stack position. I have to decrement 1 to make it count from 0 
		#to numing
		partdict = {}
		dbids = [(part.dbid,part['particleNumber']) for part in stackpartdata]
		for part in dbids:
			partdict[int(part[0])] = int(part[1]-1)

		#writing the keepfile
		f = open(self.params['keepfile'], 'w')
		for i in range(0,numimg):
			partnumber = partdict[int(numpy.memmap(newstack, dtype="float32", offset=i*1024+19*4)[0])]
			f.write('%d\n' % partnumber)
		f.close()

		newcreatestack = os.path.join(self.params['rundir'],self.params['newstack'])
		apStack.makeNewStack(oldstack, newcreatestack, self.params['keepfile'], bad=True)
		apStack.commitSubStack(self.params, self.params['newstack'], sorted=False)
		apStack.averageStack(stack=newcreatestack)
		newstackid = apStack.getStackIdFromPath(newcreatestack)

#=====================
if __name__ == "__main__":
	dbstack = dbStackUpload()
	dbstack.start()
	dbstack.close()

