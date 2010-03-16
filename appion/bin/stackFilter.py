#!/usr/bin/env python

#python
import os
import shutil
import sys
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apStackMeanPlot

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --old-stack-id=ID --keep-file=FILE [options]")
		self.parser.add_option("-s", "--old-stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--minx", dest="minx", type="float",
			help="minimum X value")
		self.parser.add_option("--maxx", dest="maxx", type="float",
			help="maximum X value")
		self.parser.add_option("--miny", dest="miny", type="float",
			help="minimum Y value")
		self.parser.add_option("--maxy", dest="maxy", type="float",
			help="maximum Y value")
		
	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['minx'] is None or self.params['miny'] is None or self.params['maxx'] is None or self.params['maxy'] is None:
			apDisplay.printError("Please define all minx, miny, maxx, maxy")
			
	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		stackparts = apStack.getStackParticlesFromId(self.params['stackid'])
		
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		newname = stackdata['name']
		
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['rundir'], newname)

		# calculate slop and intercept from the four points given	
		slope = (self.params['maxy'] - self.params['miny']) / (self.params['maxx'] - self.params['minx'])
		intercept = self.params['miny'] - (slope*self.params['minx'])
		
#		print slope
#		print intercept
		
		numparticles = 0
		
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
		f=open(self.params['keepfile'],'w')
		
		for stackpart in stackparts:
			#print str(stackpart['particleNumber'])+","+ str(stackpart['mean'])+","+str(stackpart['stdev'])
			if stackpart['mean'] > self.params['minx'] and stackpart['mean'] < self.params['maxx']:
				#print str(stackpart['particleNumber'])+","+ str(stackpart['mean'])+","+str(stackpart['stdev'])
				calcY = slope*stackpart['mean']+intercept 
				if calcY >= stackpart['stdev']:
					emanpartnum = stackpart['particleNumber']-1
					f.write('%i\n' % emanpartnum)
					numparticles+=1
					
		f.close()
		self.params['description'] +=(
				(" ... %d particle substack of stackid %d" 
				 % (numparticles, self.params['stackid']))
			)

		#create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'], bad=True)
		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")
		apStack.commitSubStack(self.params, newname, oldstackparts=stackparts)
		apStack.averageStack(stack=newstack)

		# stack mean plot
		newstackid = apStack.getStackIdFromPath(newstack)
		apDisplay.printMsg("creating Stack Mean Plot montage for stackid")
		apStackMeanPlot.makeStackMeanPlot(newstackid)

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

