#!/usr/bin/env python

import os
import sys
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import appionScript

#=====================
#=====================
class NewPicksFromRecon(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("-r", "--reconid", dest="reconid", type="int",
			help="Reconstruction run id", metavar="##")
		self.parser.add_option("-i", "--iternum", dest="iternum", type="int",
			help="Iteration number for reconstruction", metavar="##")
			
	#=====================
	def checkConflicts(self):
		if self.params['reconid'] is None:
			apDisplay.printError("Please provide a recon run id, e.g. --reconid=15")
		if self.params['iternum'] is None:
			refineiterq = appiondata.ApRefineIterData()
			refrun = appiondata.ApRefineRunData.direct_query(self.params['reconid'])
			refineiterq['refineRun'] = refrun
			refiterdata = refineiterq.query()
			lastiter = len(refiterdata)
			refineiterq = appiondata.ApRefineIterData()
			refineiterq['refineRun'] = refrun
			refineiterq['iteration'] = lastiter
			refiterdata = refineiterq.query(results=1)
			if not refiterdata:
				apDisplay.printError("Could not get iteration, please provide a iter num, e.g. --iternum=15")
			self.params['iternum'] = lastiter

	#=====================
	def start(self):
		apDisplay.printMsg("\n\n")
		### get particles
		refrun = appiondata.ApRefineRunData.direct_query(self.params['reconid'])
		refiterq = appiondata.ApRefineIterData()
		refiterq['refineRun'] = refrun
		refiterq['iteration'] = self.params['iternum']
		refiterdatas = refiterq.query(results=1)
		refpartq = appiondata.ApRefineParticleData()
		refpartq['refineIter'] = refiterdatas[0]	
		#this gets lots of data
		refpartdatas = refpartq.query()
		
		### get session
		firstrefpart = refpartdatas[0]
		firstpart = firstrefpart['particle']['particle']
		sessiondata = firstpart['selectionrun']['session']
		
		### create a selection run
		runq = appiondata.ApSelectionRunData()
		for key in firstpart['selectionrun'].keys():
			runq[key] = firstpart['selectionrun'][key]
		runq['name'] = self.params['runname']
		runq['session'] = sessiondata
		pathq = appiondata.ApPathData()
		pathq['path'] = self.params['rundir']
		runq['path'] = pathq
		runq['description'] = ("Corrected particles from refine id %d iter %d and selection %d"
			%(self.params['reconid'], self.params['iternum'], firstpart['selectionrun'].dbid))

		count = 0
		for refpartdata in refpartdatas:
			count += 1
			if count % 10 == 0:
				sys.stderr.write(".")
			partdata = refpartdata['particle']['particle']
			newpartq = appiondata.ApParticleData()
			for key in partdata.keys():
				newpartq[key] = partdata[key]
			newpartq['xcoord'] = partdata['xcoord'] + refpartdata['shiftx']
			newpartq['ycoord'] = partdata['ycoord'] + refpartdata['shifty']
			newpartq['selectionrun'] = runq
			newpartq.insert()
			
		
		

#=====================
#=====================
if __name__ == '__main__':
	newpicks = NewPicksFromRecon()
	newpicks.start()
	newpicks.close()

