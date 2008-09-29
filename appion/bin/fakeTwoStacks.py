#!/usr/bin/env python

import os
import sys
import time
import random
import cPickle
import MySQLdb
import sinedon
import shutil
import appionScript
import apStack
import apEMAN
import apFile
import apDisplay



dbconf = sinedon.getConfig('appionData')
db     = MySQLdb.connect(**dbconf)
cursor = db.cursor()

#=====================
def getParticles(notstackid, tiltstackid):
	cachefile = "parttree-"+str(notstackid)+"_"+str(tiltstackid)+".cache"
	if os.path.isfile(cachefile):
		cachef = open(cachefile, "r")
		parttree = cPickle.load(cachef)
		cachef.close()
		return parttree

	t0 = time.time()
	query = (
		"SELECT \n"
			+"  stpart1.`particleNumber` AS partnum1, \n"
			+"  stpart1.`REF|ApStackData|stack` AS stackid1, \n"
			+"  DEGREES(scoped1.`SUBD|stage position|a`) AS alpha1, \n"
			+"  stpart2.`particleNumber` AS partnum2, \n"
			+"  stpart2.`REF|ApStackData|stack` AS stackid2, \n"
			+"  DEGREES(scoped2.`SUBD|stage position|a`) AS alpha2 \n"

			+"FROM `ApTiltParticlePairData` AS tiltd \n"

			+"LEFT JOIN `ApStackParticlesData` AS stpart1 \n"
			+"  ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` \n"
			+"LEFT JOIN `ApParticleData` AS part1 \n"
			+"  ON stpart1.`REF|ApParticleData|particle` = part1.`DEF_id` \n"
			+"LEFT JOIN dbemdata.`AcquisitionImageData` AS imaged1 \n"
			+"  ON part1.`REF|leginondata|AcquisitionImageData|image` = imaged1.`DEF_id` \n"
			+"LEFT JOIN dbemdata.`ScopeEMData` AS scoped1 \n"
			+"  ON imaged1.`REF|ScopeEMData|scope` = scoped1.`DEF_id` \n"

			+"LEFT JOIN `ApStackParticlesData` AS stpart2 \n"
			+"  ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` \n"
			+"LEFT JOIN `ApParticleData` AS part2 \n"
			+"  ON stpart2.`REF|ApParticleData|particle` = part2.`DEF_id` \n"
			+"LEFT JOIN dbemdata.`AcquisitionImageData` AS imaged2 \n"
			+"  ON part2.`REF|leginondata|AcquisitionImageData|image` = imaged2.`DEF_id` \n"
			+"LEFT JOIN dbemdata.`ScopeEMData` AS scoped2 \n"
			+"  ON imaged2.`REF|ScopeEMData|scope` = scoped2.`DEF_id` \n"

			+"WHERE \n"
			+"     ( ( stpart1.`REF|ApStackData|stack` = "+str(notstackid)+" \n" 
			+"      OR stpart1.`REF|ApStackData|stack` IS NULL ) \n" 
			+"   AND ( stpart2.`REF|ApStackData|stack` = "+str(tiltstackid)+" \n"
			+"      OR stpart2.`REF|ApStackData|stack` IS NULL ) )\n" 
			+"  OR ( ( stpart1.`REF|ApStackData|stack` = "+str(tiltstackid)+" \n" 
			+"      OR stpart1.`REF|ApStackData|stack` IS NULL ) \n" 
			+"   AND ( stpart2.`REF|ApStackData|stack` = "+str(notstackid)+" \n" 
			+"      OR stpart2.`REF|ApStackData|stack` IS NULL ) )\n" 
			+"ORDER BY stpart1.`particleNumber` ASC \n"
			#+"LIMIT 21 \n"
		)
	apDisplay.printMsg("particle query at "+time.asctime())
	cursor.execute(query)
	results = cursor.fetchall()
	if not results:
		apDisplay.printError("Failed to get stack particles")
	apDisplay.printMsg("Fetched "+str(len(results))+" data pairs in "+apDisplay.timeString(time.time()-t0))
	parttree = convertSQLtoTree(results, notstackid)
	parttree.sort(compPart)

	### save to file
	cachef = open(cachefile, "w")
	cPickle.dump(parttree, cachef)
	cachef.close()

	for part in parttree:
		if part['part2'] is None:
			print part
	print ""
	print ""

	return parttree

#=====================
def convertSQLtoTree(results, notstackid):
	t0 = time.time()
	parttree = []
	minpartnum1 = 1e6
	minpartnum2 = 1e6
	count = 0
	for row in results:
		if len(row) < 6:
			apDisplay.printError("delete MySQL cache file and run again")

		try:
			partnum1 = intOrNone(row[0])
			stackid1 = intOrNone(row[1])
			angle1   = floatOrNone(row[2])
			partnum2 = intOrNone(row[3])
			stackid2 = intOrNone(row[4])
			angle2   = floatOrNone(row[5])
			if partnum1 and partnum1 < minpartnum1:
				minpartnum1 = partnum1
			if partnum2 and partnum2 < minpartnum2:
				minpartnum2 = partnum2
			if partnum1 is not None and partnum2 is not None:
				if stackid1 == notstackid:
					partpair1 = { 'part1': partnum1, 'part2': -partnum2, 'stackid1': stackid1, 'stackid2': stackid2, 'tilt': False }
					partpair2 = { 'part1': -partnum2, 'part2': partnum1, 'stackid1': stackid2, 'stackid2': stackid1, 'tilt': True }
				else:
					partpair1 = { 'part1': -partnum1, 'part2': partnum2, 'stackid1': stackid1, 'stackid2': stackid2, 'tilt': True }
					partpair2 = { 'part1': partnum2, 'part2': -partnum1, 'stackid1': stackid2, 'stackid2': stackid1, 'tilt': False }
			elif partnum1 is not None:
				if stackid1 == notstackid:
					partpair1 = { 'part1': partnum1, 'part2': None, 'stackid1': stackid1, 'stackid2': None, 'tilt': False }
				else:
					partpair1 = { 'part1': -partnum1, 'part2': None, 'stackid1': stackid1, 'stackid2': None, 'tilt': True }
			elif partnum2 is not None:
				if stackid2 == notstackid:
					partpair2 = { 'part1': partnum2, 'part2': None, 'stackid1': stackid2, 'stackid2': None, 'tilt': False }
				else:
					partpair2 = { 'part1': -partnum2, 'part2': None, 'stackid1': stackid2, 'stackid2': None, 'tilt': True }

			if partnum1 is not None:	
				parttree.append(partpair1)
				count += 1
			if partnum2 is not None:
				parttree.append(partpair2)
				count += 1
		except:
			print count, row
			apDisplay.printError("bad row entry")			
	print count, minpartnum1, minpartnum2
	apDisplay.printMsg("Converted "+str(len(parttree))+" particles in "+apDisplay.timeString(time.time()-t0))
	return parttree

#=====================
def whichIsTilted(angle1, angle2):
	if angle1 is None and abs(angle2) > 10:
		return 2
	if angle2 is None and abs(angle1) > 10:
		return 1
	if abs(angle1) > abs(angle2):
		return 1
	return 2

#=====================
def intOrNone(item):
	if item:
		return int(item)
	return None	

#=====================
def floatOrNone(item):
	if item:
		return float(item)
	return 0.0	

#=====================
def compPart(a, b):
	if a['part1'] and b['part1'] and abs(a['part1']) > abs(b['part1']):
		return 1
	else:
		return -1

#=====================
def randomEuler():
	"""
	alt = int(round(random.random()*180.0,0))
	az = int(round(random.random()*360.0,0))
	phi = int(round(random.random()*360.0,0))
	"""
	#alt = int(round(random.random()*90.0,0))
	alt = 0
	#az = int(round(random.random()*51.43,0))
	az = 0
	#phi = int(round(random.random()*360.0,0))
	phi = int(round(random.random()*6.0,0))*60
	return (alt, az, phi)



class fakeStackScript(appionScript.AppionScript):
	#######################################################
	#### ITEMS BELOW CAN BE SPECIFIED IN A NEW PROGRAM ####
	#######################################################

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stackid=<session> --commit [options]")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to copy the templates to", metavar="PATH")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")
		self.parser.add_option("--stack1", dest="stack1", type="int",
			help="ID for untilted particle stack", metavar="INT")
		self.parser.add_option("--stack2", dest="stack2", type="int",
			help="ID for tilted particle stack", metavar="INT")
		self.parser.add_option("--runid", "-r", dest="runid", default=self.timestamp,
			help="Run ID name, e.g. --runid=run1", metavar="NAME")
		self.parser.add_option("--density", "-d", dest="density", 
			default="/ami/data13/appion/06jul12a/refine/logsplit2/run55351/threed.20a.mrc",
			help="density file, e.g. --density=groel.mrc", metavar="NAME")

	#=====================
	def checkConflicts(self):
		if self.params['stack1'] is None:
			apDisplay.printError("enter a untilted stack ID, e.g. --stack1=773")
		if self.params['stack2'] is None:
			apDisplay.printError("enter a tilted stack ID, e.g. --stack2=774")
		if self.params['runid'] is None:
			apDisplay.printError("enter a run ID, e.g. --runid=run1")

	#=====================
	def setProcessingDirName(self):
		self.processdirname = self.functionname

	#=====================
	def setOutDir(self):
		#auto set the output directory
		stackdata = apStack.getOnlyStackData(self.params['stack1'], msg=False)
		path = os.path.abspath(stackdata['path']['path'])
		path = os.path.dirname(path)
		self.params['outdir'] = os.path.join(path, "faketwostack", self.params['runid'])

	#=====================
	def checksizes(self):
		newnots = apFile.numImagesInStack(self.params['notstack'])
		newtilts = apFile.numImagesInStack(self.params['tiltstack'])
		stackdata1 = apStack.getOnlyStackData(self.params['stack1'], msg=False)
		stackpath1 = os.path.join(stackdata1['path']['path'], stackdata1['name'])
		oldnots = apFile.numImagesInStack(stackpath1)
		stackdata2 = apStack.getOnlyStackData(self.params['stack2'], msg=False)
		stackpath2 = os.path.join(stackdata2['path']['path'], stackdata2['name'])
		oldtilts = apFile.numImagesInStack(stackpath2)
		if newtilts != oldtilts:
			apDisplay.printWarning("tilted stack are different sizes: %d vs. %d part"%(newtilts,oldtilts))
		else:
			apDisplay.printMsg("tilted stack are the sames sizes: %d part"%(newtilts))
		if newnots != oldnots:
			apDisplay.printWarning("untilted stack are different sizes: %d vs. %d part"%(newnots,oldnots))
		else:
			apDisplay.printMsg("untilted stack are the sames sizes: %d part"%(newnots))

	#=====================
	def generateProjections(self, parttree, density):
		t0 = time.time()

		datafile = "parttree_data-"+str(self.timestamp)+".txt"
		dataf = open(datafile, 'w', 0666)
		count = 0.0
		tilts = 0
		nots = 0
		total = float(len(parttree))
		mult = 0.00
		for part in parttree:
			count += 1.0

			### have we generated an euler yet?
			if not 'euler' in part:
				### generate euler
				part['euler'] = randomEuler()
				### set euler for pair, so we use the same one later
				for pair in parttree:
					if pair['part1'] == part['part2']:
						pair['euler'] = part['euler']

			### log to particle file
			dataf.write(str(part)+"\n")
			if count > mult*total:
				for i in range(25):
					sys.stderr.write("\b\b\b")
				sys.stderr.write(str(int(100*mult))+"% complete")
				if count > 10:
					esttime = float(time.time()-t0)*(total/count-1.0)
					sys.stderr.write(", time: "+apDisplay.timeString(esttime))
				mult += 0.01

			### generate projection
			self.genProj(part['euler'], density, tilt=part['tilt'])
			if part['tilt'] is False:
				nots += 1
			else:
				tilts += 1

		dataf.close()
		print "tilts=",tilts,"nots=",nots
		apDisplay.printMsg("Projected "+str(len(parttree))+" particles in "+apDisplay.timeString(time.time()-t0))

	#=====================
	def genProj(self, euler, density, tilt=False):
		(alt, az, phi) = euler
		rotcmd = ( "proc3d "+density+" rotated.mrc rot="
			+str(alt)+","+str(az)+","+str(phi) )
		apEMAN.executeEmanCmd(rotcmd, verbose=False, showcmd=False)
		if tilt is True:
			cmd = "project3d rotated.mrc out="+self.params['tiltstack']+" euler=55,90,-90"
		else:
			cmd = "project3d rotated.mrc out="+self.params['notstack']+" euler=0,0,0"
		apEMAN.executeEmanCmd(cmd, verbose=False, showcmd=False)

	#=====================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		self.params['notstack'] = os.path.join(self.params['outdir'], "notstack-"+self.timestamp+".hed")
		self.params['tiltstack'] = os.path.join(self.params['outdir'], "tiltstack-"+self.timestamp+".hed")

		apFile.removeStack(self.params['notstack'])
		apFile.removeStack(self.params['tiltstack'])

		parttree = getParticles(self.params['stack1'], self.params['stack2'])

		### copy density file
		if not os.path.isfile(self.params['density']):
			apDisplay.printError("cannot find file: "+self.params['density'])
		density = self.timestamp+".mrc"
		shutil.copy(self.params['density'], density)

		self.generateProjections(parttree, density)

		### double check sizes
		self.checksizes()


#=====================
#=====================
if __name__ == '__main__':
	fakestack = fakeStackScript()
	fakestack.start()
	fakestack.close()



