#!/usr/bin/env python

#python
import os
import shutil
import random
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apStackMeanPlot
from appionlib import apBeamTilt

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --old-stack-id=ID --keep-file=FILE [options]")
		self.parser.add_option("-s", "--old-stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")

		self.parser.add_option("-k", "--keep-file", dest="keepfile",
			help="File listing which particles to keep, EMAN style 0,1,...", metavar="FILE")

		self.parser.add_option("--first", dest="first", type="int",
			help="First Particle to include")
		self.parser.add_option("--last", dest="last", type="int",
			help="Last Particle to include")

		self.parser.add_option("--split", dest="split", type="int", default=1,
			help="Number of files into which the stack will be split")
		
		self.parser.add_option("--random", dest="random", type="int",
            help="Number of random particles into the stack")

		self.parser.add_option("--exclude", dest="exclude",
			help="EMAN style classes to EXCLUDE in the new stack (0,5,8)", metavar="0,1,...")
		self.parser.add_option("--include", dest="include",
			help="EMAN style classes to INCLUDE in the new stack (0,2,7)", metavar="0,1,...")

		self.parser.add_option("--no-meanplot", dest="meanplot", default=True,
			action="store_false", help="Do not create a mean/stdev plot")
		self.parser.add_option("--correct-beamtilt", dest="correctbeamtilt", default=False,
			action="store_true", help="The original stack is sorted")
		self.parser.add_option("--sorted", dest="sorted", default=False,
			action="store_true", help="The original stack is sorted")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		numpart = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")

		### have first but not last
		if self.params['first'] is not None and self.params['last'] is None:
			if self.params['random'] is not None:
				apDisplay.printError("Random function can't combine with range of the stack")
			self.params['last'] = numpart
		elif self.params['first'] is None and self.params['last'] is not None:
			if self.params['random'] is not None:
				apDisplay.printError("Random function can't combine with range of the stack")
			self.params['first'] = 0

		if self.params['last'] is None:
			self.params['last'] = numpart

		if self.params['random'] > numpart or self.params['last'] > numpart:
			apDisplay.printError("Requesting too many particles from stack, max %d"%(numpart))

		if self.params['first'] is None and self.params['split'] == 1:
			if self.params['keepfile'] is None and self.params['exclude'] is None and self.params['include'] is None and self.params['random'] is None:
				apDisplay.printError("Please define either keepfile, exclude or include")
			elif self.params['keepfile']:
				self.params['keepfile'] = os.path.abspath(self.params['keepfile'])
				if not os.path.isfile(self.params['keepfile']):
					apDisplay.printError("Could not find keep file: "+self.params['keepfile'])
		if self.params['keepfile'] and (self.params['exclude'] is not None or self.params['include'] is not None):
			apDisplay.printError("Please define only either keepfile, exclude or include")
		if self.params['exclude'] and (self.params['keepfile'] is not None or self.params['include'] is not None):
			apDisplay.printError("Please define only either keepfile, exclude or include")
		if self.params['include'] and (self.params['exclude'] is not None or self.params['keepfile'] is not None):
			apDisplay.printError("Please define only either keepfile, exclude or include")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		# if exclude or include lists are not defined...
		if self.params['exclude'] is None and self.params['include'] is None:
			# if first and last are specified, create a file
			if self.params['first'] is not None and self.params['last'] is not None:
				stp = str(self.params['first'])
				enp = str(self.params['last'])
				fname = 'sub'+str(self.params['stackid'])+'_'+stp+'-'+enp+'.lst'
				self.params['keepfile'] = os.path.join(self.params['rundir'],fname)
				apDisplay.printMsg("Creating keep list: "+self.params['keepfile'])
				f=open(self.params['keepfile'],'w')
				for i in range(self.params['first'],self.params['last']+1):
					f.write('%d\n' % (int(i)-1))
				f.close()
				# generate the random list by giving number and create the file
			elif self.params['random'] is not None:
				#numOfRandomParticles = str(self.params['random'])
				#fname = 'random'+str(self.params['stackid'])+'_'+numOfRandomParticles+'.lst'
				fname = "random%d_%d.lst"%(self.params['stackid'], self.params['random'])
				self.params['keepfile'] = os.path.join(self.params['rundir'],fname)
				apDisplay.printMsg("Creating keep list: "+self.params['keepfile'])
				# create a file
				f=open(self.params['keepfile'],'w')
				# generate a random sequence by giving size
				randomList = random.sample(xrange(self.params['last']), self.params['random'])
				randomList.sort()
				for partnum in randomList:
					f.write('%d\n' % partnum)
				f.close()				
				
			# if splitting, create files containing the split values
			elif self.params['split'] > 1:
				num = apStack.getNumberStackParticlesFromId(self.params['stackid'])
				for i in range(self.params['split']):
					fname = 'sub'+str(self.params['stackid'])+'.'+str(i+1)+'.lst'
					self.params['keepfile'] = os.path.join(self.params['rundir'],fname)
					apDisplay.printMsg("Creating keep list: "+self.params['keepfile'])
					f = open(self.params['keepfile'],'w')
					for p in range(num):
						if (p % self.params['split'])-i==0:
							f.write('%i\n' % p)
					f.close()
			# otherwise, just copy the file
			elif not os.path.isfile(os.path.basename(self.params['keepfile'])):
				shutil.copy(self.params['keepfile'], os.path.basename(self.params['keepfile']))

		# if either exclude or include lists is defined
		elif self.params['exclude'] or self.params['include']:
			
			### list of particles to be excluded
			excludelist = []
			if self.params['exclude'] is not None:
				excludestrlist = self.params['exclude'].split(",")
				for excld in excludestrlist:
					excludelist.append(int(excld.strip()))
			apDisplay.printMsg("Exclude list: "+str(excludelist))

			### list of particles to be included
			includelist = []
			if self.params['include'] is not None:
				includestrlist = self.params['include'].split(",")
				for incld in includestrlist:
					includelist.append(int(incld.strip()))		
			apDisplay.printMsg("Include list: "+str(includelist))


		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		newname = stackdata['name']

		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

		#if include or exclude list is given...			
		if self.params['include'] is not None or self.params['exclude'] is not None:
		
			#old stack size
			stacksize = apStack.getNumberStackParticlesFromId(self.params['stackid'])

			includeParticle = []
			excludeParticle = 0

			for partnum in range(stacksize):
				if includelist and partnum in includelist:
					includeParticle.append(partnum)
				elif excludelist and not partnum in excludelist:
					includeParticle.append(partnum)
				else:
					excludeParticle += 1
			includeParticle.sort()
		
			### write kept particles to file
			self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
			apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
			kf = open(self.params['keepfile'], "w")
			for partnum in includeParticle:
				kf.write(str(partnum)+"\n")
			kf.close()		

			#get number of particles
			numparticles = len(includeParticle)
			if excludelist:
				self.params['description'] += ( " ... %d particle substack of stackid %d" 
				% (numparticles, self.params['stackid']))
			elif includelist:
				self.params['description'] += ( " ... %d particle substack of stackid %d" 
				% (numparticles, self.params['stackid']))	
		
		ogdescr = self.params['description']
		for i in range(self.params['split']):
			### always do this, if not splitting split=1
			sb = os.path.splitext(stackdata['name'])
			if self.params['first'] is not None and self.params['last'] is not None:
				newname = sb[0]+'.'+str(self.params['first'])+'-'+str(self.params['last'])+sb[-1]
			elif self.params['random'] is not None:
				newname = "%s-random%d%s"%(sb[0], self.params['random'], sb[-1])
			elif self.params['split'] > 1:
				fname = 'sub'+str(self.params['stackid'])+'.'+str(i+1)+'.lst'
				self.params['keepfile'] = os.path.join(self.params['rundir'],fname)
				newname = sb[0]+'.'+str(i+1)+'of'+str(self.params['split'])+sb[-1]
			newstack = os.path.join(self.params['rundir'], newname)
			apStack.checkForPreviousStack(newstack)

			#get number of particles
			f = open(self.params['keepfile'], "r")
			numparticles = len(f.readlines())
			f.close()
			self.params['description'] = ogdescr
			self.params['description'] += (
				(" ... %d particle substack of stackid %d" 
				 % (numparticles, self.params['stackid']))
			)
			#if splitting, add to description
			if self.params['split'] > 1:
				self.params['description'] += (" (%i of %i)" % (i+1, self.params['split']))

			#create the new sub stack
			if not self.params['correctbeamtilt']:
				apStack.makeNewStack(oldstack, newstack, self.params['keepfile'], bad=True)
			else:
				apBeamTilt.makeCorrectionStack(self.params['stackid'], oldstack, newstack)
			if not os.path.isfile(newstack):
				apDisplay.printError("No stack was created")
			apStack.commitSubStack(self.params, newname, sorted=False)
			apStack.averageStack(stack=newstack)
			newstackid = apStack.getStackIdFromPath(newstack)
			if self.params['meanplot'] is True:
				apDisplay.printMsg("creating Stack Mean Plot montage for stackid")
				apStackMeanPlot.makeStackMeanPlot(newstackid)

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

