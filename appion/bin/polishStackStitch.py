#!/usr/bin/env python

#python
import os
import re
import time
import math
import subprocess
#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apStack
from appionlib import apProject
import sinedon
from pyami import mrc

class stackPolisherScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
#		super(stackPolisher,self).setupParserOptions()
		self.parser.set_usage("Usage: %prog --stackid=ID [options]")

		# appion stack & ddstack ids
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--ddstackid", dest="ddstackid", type="int",
			help="ID for ddstack run to make aligned & polished stack (required)", metavar="INT")

	#=====================
	def checkConflicts(self):
		
		### setup correct database after we have read the project id
		if 'projectid' in self.params and self.params['projectid'] is not None:
			apDisplay.printMsg("Using split database")
			# use a project database
			newdbname = apProject.getAppionDBFromProjectId(self.params['projectid'])
			sinedon.setConfig('appiondata', db=newdbname)
			apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")
		
		# DD processes
		self.dd = apDDprocess.DDStackProcessing()
		print self.dd
	
		# get stack data
		self.stackdata = appiondata.ApStackData.direct_query(self.params['stackid'])
		self.stackparts = apStack.getStackParticlesFromId(self.params['stackid'], msg=True)
		self.sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])
		
		# query image
		qimage = self.stackparts[0]['particle']['image']

		# DD info
		self.dd.setImageData(qimage)
		self.dd.setDDStackRun(self.params['ddstackid'])
		self.ddstackpath = self.dd.getDDStackRun()['path']['path']

	#=====================
	def combine_polished_stacks(self):

		oldmovieid = None
		nmic = 0
		for part in self.stackparts:
			self.dd.setImageData(part['particle']['image'])
			movieid = part['particle']['image'].dbid
			alignpairdata = self.dd.getAlignImagePairData(None,query_source=not self.dd.getIsAligned())
			if alignpairdata is False:
				apDisplay.printWarning('Image not used for nor a result of alignment.')

			if movieid != oldmovieid:
				ddstack = orig_dd_file = alignpairdata['source']['filename']+"_lmbfgs.mrc"
				particlestack = os.path.join(self.params['rundir'], "Particles", ddstack) 
				a = mrc.read(particlestack)
				apDisplay.printMsg("appending stack %s" % ddstack)
				if oldmovieid is None:
					mrc.write(a, "polished.mrc")
				else:
					mrc.append(a, "polished.mrc")
				oldmovieid = movieid
		
	#=====================
	def start(self):
		
		self.combine_polished_stacks()
	
		# Clean up
		apDisplay.printMsg("deleting temporary processing files")

		# Upload results
		#		if self.params['commit'] is True:
		#		apStack.commitPolishedStack(self.params, oldstackparts, newname='start.hed')
        
        
		time.sleep(1)
		return

#=====================
if __name__ == "__main__":
	polisher = stackPolisherScript()
	polisher.start()
	polisher.close()


