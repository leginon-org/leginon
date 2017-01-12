#!/usr/bin/env python

import os
import multiprocessing

from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apDatabase
from appionlib import appiondata
import leginon.leginondata

def makeStack(tup):
	imgid, selectid = tup
	imgdata = leginon.leginondata.AcquisitionImageData.direct_query(imgid)
	selectdata = appiondata.ApSelectionRunData.direct_query(selectid)
	partq = appiondata.ApParticleData()
	partq[image] = imgdata
	partq[selectionrun] = selectdata
	partdata = partq.query()
	print "Found %d particles"%(len(partdata))
	return

def start_process():
	print 'Starting', multiprocessing.current_process().name

#=====================
#=====================
class QuickStack(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--sessionid", dest="sessionid", type="int",
			help="Session ID", metavar="#")
		self.parser.add_option("--selectid", dest="selectid", type="int",
			help="Particle Selction ID", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['sessionid'] is None:
			apDisplay.printError("Please provide a session id, e.g. --sessionid=15")
		if self.params['selectid'] is None:
			apDisplay.printError("Please provide a Particle Selction id, e.g. --selectid=15")

	#=====================
	def start(self):
		self.imgtree = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		imgidlist = []
		for imgdata in self.imgtree:
			imgidlist.append(imgdata.dbid)
		selectlist = numpy.ones((len(imgidlist)))*self.params['selectid']
		inputs = numpy.hstack(imgidlist, selectlist)

		nproc = 6
		t0 = time.time()
		print "nproc %d"%(nproc)
		p = multiprocessing.Pool(processes=nproc, initializer=start_process)
		p.map(makeStack, inputs)
		p.close()
		p.join()
		p.terminate()
		print "Complete %.3f"%((time.time()-t0)*1)


#=====================
#=====================
if __name__ == '__main__':
	quickstack = QuickStack()
	quickstack.start()
	quickstack.close()

