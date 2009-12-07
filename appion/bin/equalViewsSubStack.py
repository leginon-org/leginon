#!/usr/bin/env python

#builtin
import os
import sys
import time
#appion
import appionScript
import apDisplay
import appiondata
import apStack

#===================
class EqualViews(appionScript.AppionScript):
	#===================
	def setupParserOptions(self):
		self.parser.add_option("--reconid", dest="reconid", type="int",
			help="Reconstruction run database id, e.g. --reconid=12", metavar="#")
		self.parser.add_option("--iternums", dest="iternums",
			help="List of iterations to use, e.g. --iternums=2,3,4", metavar="#")
		self.parser.add_option("--mincount", dest="mincount", type="int", default=1,
			help="Minimum number of particles, e.g. --mincount=10", metavar="#")

	#===================
	def checkConflicts(self):
		if self.params['reconid'] is None:
			apDisplay.printError("Please provide recon id, e.g. --reconid=12")
		self.reconrundata = appiondata.ApRefinementRunData.direct_query(self.params['reconid'])
		if self.params['iternums'] is None:
			apDisplay.printError("Please provide a list of iterations to use, e.g. --iternums=2,3,4")
		try:
			striternums = self.params['iternums'].strip().split(",")
			self.iternums = []
			for i in striternums:
				self.iternums.append(int(i))
		except:
			apDisplay.printError("Unable to parse list of iterations, e.g. --iternums=2,3,4")

	#===================
	def setRunDir(self):
		reconrunpath = self.reconrundata['path']['path']
		self.params['rundir'] = os.path.abspath(os.path.join(reconrunpath, "../../stacks", self.params['runname']))

	#===================
	def start(self):
		partdict = {}
		partlist = []
		### get Euler angles for each particle
		for iternum in self.iternums:
			### get recon iter data
			reconiterq = appiondata.ApRefinementData()
			reconiterq['refinementRun'] = self.reconrundata
			reconiterq['iteration'] = iternum
			reconiterdata = reconiterq.query(results=1)[0] #this should be unique

			### get particle data
			reconpartq = appiondata.ApParticleClassificationData()
			reconpartq['refinement'] = reconiterdata
			apDisplay.printMsg("Querying for particles at "+time.asctime())
			reconpartdatas = reconpartq.query()

			### group particle data
			for partdata in reconpartdatas:
				partnum = partdata['particle']['particleNumber']
				if not partnum in partlist:
					partlist.append(partnum)
				partdict[(partnum, iternum)] = partdata

		### run through particles and check Euler angles
		partlist.sort()
		eulerdict = {}
		eulercount = {}
		reject = 0
		for partnum in partlist:
			e1d = {}
			e2d = {}
			for iternum in self.iternums:
				if not (partnum, iternum) in partdict:
					continue
				partdata = partdict[(partnum, iternum)]
				euler1 = "%.2f"%(partdata['euler1'])
				if not euler1 in e1d:
					e1d[euler1] = 1
				else:
					e1d[euler1] += 1
				euler2 = "%.2f"%(partdata['euler2'])
				if not euler2 in e2d:
					e2d[euler2] = 1
				else:
					e2d[euler2] += 1
				#print partnum, euler1, euler2
			counts = [(val,key) for key,val in e1d.items()]
			e1count, euler1 = max(counts)
			counts = [(val,key) for key,val in e2d.items()]
			e2count, euler2 = max(counts)

			# reject indeterminant particles
			if e2count < 2 or e1count < 2:
				reject += 1
				continue

			### group particles by their Euler angles
			if not (euler1,euler2) in eulerdict:
				eulerdict[(euler1,euler2)] = []
				eulercount[(euler1,euler2)] = 0
			eulerdict[(euler1,euler2)].append(partnum)
			eulercount[(euler1,euler2)] += 1

		print "Rejected %d particles"%(reject)

		values = eulercount.values()
		values.sort()
		print values

		### run through Euler angles and count particles
		counts = [(val,key) for key,val in eulercount.items()]
		mincount, val = min(counts)
		self.params['mincount'] = max(self.params['mincount'], mincount)
		#print "Keeping %d of %d particles"%(mincount*len(eulercount.keys()), len(partlist))
		print "Keeping %d of %d particles"%(self.params['mincount']*len(eulercount.keys()), len(partlist))

		keeplist = []
		for key in eulerdict.keys():
			eulerpartlist = eulerdict[key]
			if len(partlist) < self.params['mincount']:
				keeplist.extend(eulerpartlist)
			else:
				keeplist.extend(eulerpartlist[:self.params['mincount']])
		keeplist.sort()
		print "Keeping %d of %d particles"%(len(keeplist), len(partlist))

		#need to set keepfile for commitSubStack
		self.params['keepfile'] = os.path.join(self.params['rundir'], "equalviews.lst")
		f = open(self.params['keepfile'], "w")
		for partnum in keeplist:
			f.write("%d\n"%(partnum-1))
		f.close()

		### make a new stack using the keep particles
		oldstackdata = self.reconrundata['stack']

		oldstack = os.path.join(oldstackdata['path']['path'], oldstackdata['name'])
		newstack = os.path.join(self.params['rundir'], "start.hed")
		apStack.makeNewStack(oldstack, newstack, listfile=self.params['keepfile'], remove=True)
		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")
		self.params['stackid'] = oldstackdata.dbid #need to set stackid for commitSubStack
		apStack.commitSubStack(self.params, "start.hed")
		apStack.averageStack(stack=newstack)

if __name__ == '__main__':

	eqview = EqualViews()
	eqview.start()
	eqview.close()
