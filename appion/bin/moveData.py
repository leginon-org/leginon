#!/usr/bin/env python

import os
import re
import shutil
import MySQLdb
import subprocess
##
import sinedon
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDatabase

#=====================
#=====================
class MoveData(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--session", dest="sessionname",
			help="Session to move data, e.g. --session=10apr16f ", metavar="NAME")
		self.parser.add_option("--basedir", dest="basedir",
			help="Base directory, e.g. --basedir=/ami/data00 ", metavar="PATH")
		return

	#=====================
	def checkConflicts(self):
		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a session name, e.g. --session=10apr16f")
		if self.params['basedir'] is None:
			apDisplay.printError("Please provide a base dir, e.g. --basedir=/ami/data00")
		self.params['basedir'] = os.path.abspath(self.params['basedir'])
		self.appiondir = os.path.join(self.params['basedir'], "appion")
		if not os.path.isdir(self.appiondir):
			apDisplay.printError("Appion directory does not exist")
		self.leginondir = os.path.join(self.params['basedir'], "leginon")
		if not os.path.isdir(self.leginondir):
			apDisplay.printError("Leginon directory does not exist")

	#=====================
	def setRunDir(self):
		#auto set the run directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		path = os.path.abspath(sessiondata['image path'])
		self.params['rundir'] = path

	#=====================
	def onInit(self):
		# connect
		self.dbconf = sinedon.getConfig('appiondata')
		self.db     = MySQLdb.connect(**self.dbconf)
		# create a cursor
		self.cursor = self.db.cursor()

	#=====================
	def changePath(self, oldpath):
		if "/leginon/" in oldpath:
			newpath = re.sub(".*/leginon/", self.leginondir+"/", oldpath)
		elif "/appion/" in oldpath:
			newpath = re.sub(".*/appion/", self.appiondir+"/", oldpath)
		else:
			apDisplay.printError("Could not figure out path: %s"%(oldpath))	
		return newpath

	#=====================
	def updatePath(self, oldpath, newpath):
		updatepathq = ("UPDATE ApPathData SET path='%s', DEF_timestamp=DEF_timestamp WHERE path='%s';"
			%(newpath, oldpath))
		self.cursor.execute(updatepathq)
		if "/leginon/" in oldpath:
			### this is not general
			updatepathq = ("UPDATE dbemdata.SessionData SET `image path`='%s', DEF_timestamp=DEF_timestamp WHERE name='%s';"
				%(newpath, self.params['sessionname']))
			self.cursor.execute(updatepathq)

	#=====================
	def getPathSize(self, path):
		cmd = "du -sk %s"%(path)
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		line = proc.stdout.readline()
		line = line.strip()
		bits = line.split()
		size = int(line.split()[0])
		return size

	#=====================
	def getPaths(self):
		pathlist = []

		### appion paths
		allpathq = ("SELECT path FROM ApPathData WHERE path LIKE '/%/"
			+self.params['sessionname']+"/%'; ")
		self.cursor.execute(allpathq)
		paths = self.cursor.fetchall()
		for item in paths:
			path = item[0]
			pathlist.append(path)

		### leginon paths
		legpathq = ("SELECT `image path` FROM dbemdata.SessionData WHERE name='%s';"
			%(self.params['sessionname']))
		self.cursor.execute(legpathq)
		paths = self.cursor.fetchall()
		for item in paths:
			path = item[0]
			pathlist.append(path)
		return pathlist

	#=====================
	def start(self):
		paths = self.getPaths()
		for oldpath in paths:
			### good path
			if oldpath.startswith(self.params['basedir']):
				apDisplay.printMsg("Skipping: %s"%(oldpath))
				continue

			### make sure old path exists
			if not os.path.isdir(oldpath):
				apDisplay.printError("Major error missing directory: %s"%(oldpath))

			apDisplay.printMsg("Processing: %s"%(oldpath))

			### get new path
			newpath = self.changePath(oldpath)

			### copy files
			shutil.copytree(oldpath, newpath)

			### confirm copy
			oldsize = self.getPathSize(oldpath)
			newsize = self.getPathSize(newpath)			
			if abs(oldsize - newsize) > oldsize*0.001:
				### bigger than 0.1% error
				shutil.rmtree(newpath)
				apDisplay.printError("Different path sizes: %d versus %d for %s"%(oldsize, newsize, newpath))
			apDisplay.printMsg("Good path copy: %d versus %d"%(oldsize,newsize))

			### update database
			self.updatePath(oldpath, newpath)

			### delete old files
			shutil.rmtree(oldpath)


#=====================
#=====================
if __name__ == '__main__':
	movedata = MoveData()
	movedata.start()
	movedata.close()

