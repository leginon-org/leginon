#!/usr/bin/env python

#python
import sys
import os
import time
import re
import shutil
import MySQLdb
#appion
import appionScript
import apStack
import apDisplay
import apEMAN
import apFile
import sinedon

class tiltStackAlign(appionScript.AppionScript):
	def __init__(self):
		"""
		Need to connect to DB server before moving forward
		"""
		# connect
		self.dbconf = sinedon.getConfig('appionData')
		self.db     = MySQLdb.connect(**self.dbconf)
		# create a cursor
		self.cursor = self.db.cursor()
		appionScript.AppionScript.__init__(self)

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --notstackid=1239 --tiltstackid=1240")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-t", "--tiltstackid", dest="tiltstackid",
			help="Tilted stack id", metavar="ID")
		self.parser.add_option("-n", "--notstackid", dest="notstackid",
			help="Untilted stack id", metavar="ID")
		self.parser.add_option("-r", "--runname", dest="runname",
			help="Name for aligned stack run", metavar="STR")

	#=====================
	def checkConflicts(self):
		if self.params['tiltstackid'] is None:
			apDisplay.printError("Enter a tilted stack ID")
		if self.params['notstackid'] is None:
			apDisplay.printError("Enter a untilted stack ID")
		if self.params['runname'] is None:
			apDisplay.printError("Enter run name")

	#=====================
	def setOutDir(self):
		self.tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])
		stackpath = self.tiltstackdata['path']['path']
		self.params['outdir'] = os.path.abspath(os.path.join(stackpath, "../alignedstacks", self.params['runname']))

	#=====================
	def getPartcileLists(self):
		#first query
		query1 = self.queryParticles(swap=False)
		self.cursor.execute(query1)
		results1 = self.cursor.fetchall()

		#swap particle1 and particle2 in ApTiltParticlePairData
		query2 = self.queryParticles(swap=True)
		self.cursor.execute(query2)
		results2 = self.cursor.fetchall()

		parttree = self.parseResults(results1, results2)
		return parttree

	#=====================
	def parseResults(self, results1, results2):
		parttree = []
		for result in results1:
			partdict = {}
			partdict['not'] = int(result[0])
			partdict['tilt'] = int(result[1])
			parttree.append(partdict)
		for result in results2:
			partdict = {}
			partdict['not'] = int(result[0])
			partdict['tilt'] = int(result[1])
			parttree.append(partdict)
		apDisplay.printMsg("found "+str(len(parttree))+" particle pairs")
		return parttree

	#=====================
	def queryParticles(self, swap=False):
		query = (
			"SELECT "
			+"	stpart1.`particleNumber` AS partnum1, "
			+"	stpart2.`particleNumber` AS partnum2 "
			+"FROM `ApTiltParticlePairData` AS tiltd "
		)
		if swap is True:
			query += (
				"LEFT JOIN `ApStackParticlesData` AS stpart1 "
				+"	ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` "
				+"LEFT JOIN `ApStackParticlesData` AS stpart2 "
				+"	ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` "
			)
		else:
			query += (
				"LEFT JOIN `ApStackParticlesData` AS stpart1 "
				+"	ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` "
				+"LEFT JOIN `ApStackParticlesData` AS stpart2 "
				+"	ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` "
			)
		query += (
			"WHERE "
			+"	stpart1.`REF|ApStackData|stack` = "+str(self.params['notstackid'])+" "
			+"AND "
			+"	stpart2.`REF|ApStackData|stack` = "+str(self.params['tiltstackid'])+" "
			+"ORDER BY "
			+"	stpart1.`particleNumber` ASC "
			+";"
		)
		#print query
		return query

	#=====================
	def makeNewStacks(self, parttree):
		### untilted stack
		self.notstackdata = apStack.getOnlyStackData(self.params['notstackid'])
		notstackfile = os.path.join(self.notstackdata['path']['path'], self.notstackdata['name'])
		newnotstack = os.path.join(self.params['outdir'], "notstack.hed")
		if os.path.isfile(newnotstack):
			apFile.removeStack(newnotstack)

		### tilted stack
		if not self.tiltstackdata:
			self.tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])
		tiltstackfile = os.path.join(self.tiltstackdata['path']['path'], self.tiltstackdata['name'])
		newtiltstack = os.path.join(self.params['outdir'], "tiltstack.hed")
		if os.path.isfile(newtiltstack):
			apFile.removeStack(newtiltstack)

		count = 0
		for partdict in parttree:
			count += 1
			if count % 20 == 0:
				print count,"particles"
			### get particle numbers
			emannotnum = partdict['not']-1
			emantiltnum = partdict['tilt']-1
			### untilted stack		
			emancmd = "proc2d %s %s first=%d last=%d "%(notstackfile,newnotstack,emannotnum,emannotnum)
			apEMAN.executeEmanCmd(emancmd, showcmd=False)
			### tilted stack
			emancmd = "proc2d %s %s first=%d last=%d "%(tiltstackfile,newtiltstack,emantiltnum,emantiltnum)
			apEMAN.executeEmanCmd(emancmd, showcmd=False)


	#=====================
	def start(self):
		parttree = self.getPartcileLists()
		self.makeNewStacks(parttree)

#=====================
if __name__ == "__main__":
	tiltstacks = tiltStackAlign()
	tiltstacks.start()
	tiltstacks.close()

