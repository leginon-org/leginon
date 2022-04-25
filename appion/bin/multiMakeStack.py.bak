#!/usr/bin/env python

#python
import sys
import math
import subprocess
import sinedon.directq
#appion
from appionlib import apDisplay
from appionlib import apParticle
from appionlib import apDatabase
from appionlib import appionScript
#pyami
from pyami import primefactor

class MulitStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
		self.parser.add_option("-s", "--selectionid", dest="selectionid", type="int",
			help="Selection database id", metavar="ID")

	#=====================
	def checkConflicts(self):
		if self.params['selectionid'] is None:
			apDisplay.printError("selectionid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("stack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("stack base name was not defined")

	#=====================
	def getLabelsForSelectionId(self):
		sqlquery = ("SELECT label, count(DEF_id) AS `count` FROM ApParticleData "
			+(" WHERE `REF|ApSelectionRunData|selectionrun` = %d "%(self.params['selectionid']))
			+" AND label IS NOT NULL GROUP BY label; ")
		results = sinedon.directq.complexMysqlQuery('appiondata', sqlquery)
		labels = []
		for mydict in results:
			label = mydict['label']
			labels.append(label)
		return labels

	#=====================
	def makeStack(self, boxsize, label, stackname):
		"""
		makestack2.py \
			--single=start.hed --no-invert --normalize-method=edgenorm \
			--rundir=/emg/data/appion/16jul07t05a/stacks/stack1 --preset=upload \
		"""
		stackcmd = "makestack2.py "
		stackcmd += " --boxsize=%d --label='%s' --runname=%s "%(boxsize, label, stackname)
		stackcmd += " --description='multi stack from label %s' "%(label)
		stackcmd += " --selectionid=%d "%(self.params['selectionid'])
		stackcmd += " --projectid=%d "%(self.params['projectid'])
		stackcmd += " --expid=%d "%(self.params['expid'])
		stackcmd += " --no-rejects --no-wait --continue --jobtype=makestack2 --commit "

		proc = subprocess.Popen(stackcmd, shell=True)
		proc.communicate()

	#=====================
	def start(self):
		partdata = apParticle.getOneParticleFromSelectionId(self.params['selectionid'])
		imgdata = partdata['image']
		apix = apDatabase.getPixelSize(imgdata)
		
		labels = self.getLabelsForSelectionId()
		for label in labels:
			if label.startswith("diam"):
				labelsize = float(label[4:])
				minboxsize = math.ceil(labelsize / apix * 3.1)
				boxsize = primefactor.getNextEvenPrime(minboxsize)
				stackname = label.replace("diam", "mstack")
			self.makeStack( boxsize, label, stackname )


#=====================
if __name__ == "__main__":
	multiStack = MulitStackScript()
	multiStack.start()
	multiStack.close()

