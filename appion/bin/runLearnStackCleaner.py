#!/usr/bin/env python

import os
import wx
import learningStackCleaner
from appionlib import apStack
from appionlib import apDisplay
from appionlib import proc2dLib
from appionlib import appionScript
from appionlib import apStackMeanPlot

#=====================
#=====================
class LearningStackCleaner(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-a", "--align-id", dest="alignstackid", type="int",
			help="aligned stack database id", metavar="ID")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None and self.params['alignstackid'] is None:
			apDisplay.printError("Please provide a stack id, e.g. --stackid=15")
		if self.params['description'] is None:
			self.params['description'] = "Learning Stack Cleaner"

	#=====================
	def setRunDir(self):
		### get the path to input stack
		if self.params['stackid'] is not None:
			stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
			stackpath = os.path.abspath(stackdata['path']['path'])
			### go down two directories
			uponepath = os.path.join(stackpath, "..")
			uptwopath = os.path.join(uponepath, "..")
			### add path strings; always add runname to end!!!
			rundir = os.path.join(uptwopath, "example", self.params['runname'])
			self.params['rundir'] = os.path.abspath(rundir)

	#=====================
	def start(self):
		virtualdata = None
		if self.params['stackid'] is not None:
			stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
			stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
			if not os.path.isfile(stackfile):
				apDisplay.printMsg('using virtual data')
				virtualdata = apStack.getVirtualStackParticlesFromId(self.params['stackid'])
				stackfile = virtualdata['filename']
		elif self.params['alignstackid'] is not None:
			raise NotImplementedError
			alignstackdata = apStack.getOnlyStackData(self.params['alignstackid'], msg=False)
			stackfile = os.path.join(alignstackdata['path']['path'], alignstackdata['name'])
			self.params['stackid'] = '??????????' #FIXME

		localstack = os.path.join(self.params['rundir'], self.timestamp+".hed")

		a = proc2dLib.RunProc2d()
		a.setValue('infile',  stackfile)
		a.setValue('outfile', localstack)
		if virtualdata is not None:
			vparts = virtualdata['particles']
			plist = [int(p['particleNumber'])-1 for p in vparts]
			a.setValue('list',plist)
		#run proc2d
		a.run()

		self.app = wx.App()
		self.data = learningStackCleaner.DataClass(stackfile=stackfile)
		self.main = learningStackCleaner.MainWindow(self.data)
		self.main.Show()
		self.app.MainLoop()
		## end app
		
		## finish assigning particles
		self.data.assignRemainingTargets()

		## get the data
		particleAssignments = self.data.particleTarget #dict: key partnum, value assigned class
		# partNum starts at one
		#particleAssignments[partnum] = 1 --> keep
		#particleAssignments[partnum] = 2 --> reject

		###===================================
		### basically run substack.py now:
		###===================================

		## create include list
		includecount = 0
		numpart = len(particleAssignments)
		self.params['keepfile'] = 'emankeepfile.lst'
		keepf = open(self.params['keepfile'], 'w')
		for partnum in range(numpart):
			if particleAssignments.get(partnum, 0) == 1:
				includecount += 1
				#eman numbering starting at zero
				keepf.write('%d\n'%(partnum-1))
		keepf.close()
		apDisplay.printMsg("Including %d of %d particles"%(includecount, numpart))

		## FIXME may break with virtual stacks...

		#new stack path
		oldstackdata = apStack.getOnlyStackData(self.params['stackid'])
		newname = 'clean.hed'
		oldstack = os.path.join(oldstackdata['path']['path'], oldstackdata['name'])
		newstack = os.path.join(self.params['rundir'], newname)
		apStack.checkForPreviousStack(newstack)

		#get number of particles
		self.params['description'] += (
			(" ... cleaned %d particle substack of stackid %d" 
			 %(includecount, self.params['stackid']))
		)
		#create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'], bad=True)

		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")
		apStack.averageStack(stack=newstack)

		if self.params['commit'] is True:
			apStack.commitSubStack(self.params, newname, sorted=False)
			newstackid = apStack.getStackIdFromPath(newstack)
	
			apDisplay.printMsg("creating Stack Mean Plot montage for stackid")
			apStackMeanPlot.makeStackMeanPlot(newstackid)

#=====================
#=====================
if __name__ == '__main__':
	learnstack = LearningStackCleaner()
	learnstack.start()
	learnstack.close()

