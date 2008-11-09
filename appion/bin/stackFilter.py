#!/usr/bin/env python

#python
import os
import shutil
import sys
#appion
import appionScript
import apStack
import apDisplay

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --old-stack-id=ID --keep-file=FILE [options]")
		self.parser.add_option("-s", "--old-stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--minX", dest="minX", type="float",
			help="minimum X value")
		self.parser.add_option("--maxX", dest="maxX", type="float",
			help="maximum X value")
		self.parser.add_option("--minY", dest="minY", type="float",
			help="minimum Y value")
		self.parser.add_option("--maxY", dest="maxY", type="float",
			help="maximum Y value")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description", default="",
			help="Stack description", metavar="TEXT")
		self.parser.add_option("-n", "--new-stack-name", dest="runname",
			help="Run id name", metavar="STR")
		
	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['minX'] is None or self.params['minY'] is None or self.params['maxX'] is None or self.params['maxY'] is None:
			apDisplay.printError("Please define all minX, minY, maxX, maxY")
		if self.params['outdir'] is None:
			self.setOutDir()
			
	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['outdir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		stackparts = apStack.getStackParticlesFromId(self.params['stackid'])
		
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		newname = stackdata['name']
		
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])
		newstack = os.path.join(self.params['outdir'], newname)

	
		slope = (self.params['maxY'] - self.params['minY']) / (self.params['maxX'] - self.params['minX'])
			
		intercept = self.params['minY'] - (slope*self.params['minX'])
		
		print slope
		print intercept
		
		numparticles = 0
		
		self.params['keepfile'] = os.path.join(self.params['outdir'], "keepfile-"+self.timestamp+".list")
		f=open(self.params['keepfile'],'w')
		
		for stackpart in stackparts:
			#print str(stackpart['particleNumber'])+","+ str(stackpart['mean'])+","+str(stackpart['stdev'])
			if stackpart['mean'] > self.params['minX'] and stackpart['mean'] < self.params['maxX']:
				#print str(stackpart['particleNumber'])+","+ str(stackpart['mean'])+","+str(stackpart['stdev'])
				calcY = slope*stackpart['mean']+intercept 
				if calcY > stackpart['stdev']:
					emanpartnum = stackpart['particleNumber']-1
					f.write('%i\n' % emanpartnum)
					numparticles+=1
					
		f.close()
		self.params['description'] +=(
				(" ... %d particle substack of stackid %d" 
				 % (numparticles, self.params['stackid']))
			)

		#create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])
		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")
		apStack.commitSubStack(self.params, newname)
		apStack.averageStack(stack=newstack)

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

