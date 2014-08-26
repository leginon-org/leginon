#!/usr/bin/python -O

#python
import re
import os
import sys
import time
import random
import subprocess
#appion
import leginon.leginondata
from appionlib import testScript
from appionlib import apDisplay
from appionlib import apParticle
from appionlib import apStack
from appionlib import apParam
from appionlib import apFile
from appionlib import apAlignment
from appionlib import apDatabase
from appionlib import appiondata

# Instructions for creating a new automated appion test can be found at: http://ami.scripps.edu/redmine/projects/appion/wiki/Appion_Testing
# Basically, add your test session name to the config.php $TEST_SESSIONS array and copy this file to create a new test class for the session.  

class Test_zz07jul25b(testScript.TestScript):


	#=====================.
	def start(self):
		
		self.setRunDir()
		self.setAppionFlags()
		
		if self.params['commit'] is True:
			self.insertTestRunData()			

		if self.params['uploadimages'] is True:
			self.uploadImages()	

		### Dog Picker
		self.dogPicker()

		### Ace 2
		self.aceTwo(bin=2, blur=10)
		self.aceTwo(bin=2, blur=6)
		self.aceTwo(bin=4)

		### Make stack
		stackname = self.makeStack()

		### Filter stack
		filtstackname = self.filterStack(stackname)
		
		### Maximum likelihood
		maxlikename = self.maxLike(filtstackname)

		### Upload max like
		self.uploadMaxLike(maxlikename)

		### Upload templates
		self.createTemplates(maxlikename)
		return

		### Template pick
		self.templatePick()

		### Make stack
		stackname = self.makeStack()

		### Filter stack
		#filtstackname = self.filterStack(stackname)

		### create PDB model
		self.pdbToModel()

		### Upload model as initial model
		self.uploadModel()

		### Do reconstruction
		### Upload recon
		return

#=====================
if __name__ == "__main__":
	tester = Test_zz07jul25b()
	tester.start()
	tester.close()

