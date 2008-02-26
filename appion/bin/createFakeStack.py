#!/usr/bin/python -O

import os
import sys
import time
import random
import cPickle
import MySQLdb
import sinedon
import apEMAN
import apDisplay


dbconf = sinedon.getConfig('appionData')
db     = MySQLdb.connect(**dbconf)
cursor = db.cursor()

#=====================
def getParticles(stackid):
	t0 = time.time()
	query = (
		"SELECT \n"
			+"  stpart1.`particleNumber` AS partnum1, \n"
			+"  stpart2.`particleNumber` AS partnum2, \n"
			+"  ROUND(ABS(DEGREES(scoped.`SUBD|stage position|a`))) AS alpha \n"
			+"FROM `ApTiltParticlePairData` AS tiltd \n"

			+"LEFT JOIN `ApStackParticlesData` AS stpart1 \n"
			+"  ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` \n"

			+"LEFT JOIN `ApStackParticlesData` AS stpart2 \n"
			+"  ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` \n"

			+"LEFT JOIN `ApParticleData` AS part1 \n"
			+"  ON stpart1.`REF|ApParticleData|particle` = part1.`DEF_id` \n"

			+"LEFT JOIN dbemdata.`AcquisitionImageData` AS imaged \n"
			+"  ON part1.`REF|leginondata|AcquisitionImageData|image` = imaged.`DEF_id` \n"

			+"LEFT JOIN dbemdata.`ScopeEMData` AS scoped \n"
			+"  ON imaged.`REF|ScopeEMData|scope` = scoped.`DEF_id` \n"

			+"WHERE \n"
			+"      stpart1.`REF|ApStackData|stack` = "+str(stackid)+" \n" 
			+"  AND stpart2.`REF|ApStackData|stack` = "+str(stackid)+" \n" 
			+"ORDER BY stpart1.`particleNumber` ASC \n"
			#+"LIMIT 21 \n"
		)
	cursor.execute(query)
	results = cursor.fetchall()
	#apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
	if not results:
		apDisplay.printError("Failed to get stack particles")
	parttree = convertSQLtoTree(results)
	parttree.sort(compPart)
	return parttree

#=====================
def convertSQLtoTree(results):
	t0 = time.time()
	parttree = []
	for row in results:
		if len(row) < 3:
			apDisplay.printError("delete MySQL cache file and run again")
		try:
			if row[2] < 1.0:
				partpair1 = { 'part1': int(row[0]), 'part2': int(row[1]), 'tilt': False }
				partpair2 = { 'part1': int(row[1]), 'part2': int(row[0]), 'tilt': True }
			else:
				partpair1 = { 'part1': int(row[0]), 'part2': int(row[1]), 'tilt': True }
				partpair2 = { 'part1': int(row[1]), 'part2': int(row[0]), 'tilt': False }
			parttree.append(partpair1)
			parttree.append(partpair2)
		except:
			print row
			apDisplay.printError("bad row entry")			

	apDisplay.printMsg("Converted "+str(len(parttree))+" particles in "+apDisplay.timeString(time.time()-t0))
	return parttree

#=====================
def compPart(a, b):
	if a['part1'] > b['part1']:
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
	alt = int(round(random.random()*90.0,0))
	az = int(round(random.random()*51.43,0))
	phi = int(round(random.random()*360.0,0))
	return (alt, az, phi)

#=====================
def genProj(euler, tilt=False):
	(alt, az, phi) = euler
	rotcmd = ( "proc3d groel.mrc rotated.mrc rot="
		+str(alt)+","+str(az)+","+str(phi) )
	apEMAN.executeEmanCmd(rotcmd, verbose=False, showcmd=False)
	if tilt is True:
		cmd = "project3d rotated.mrc euler=15,90,-90"
	else:
		cmd = "project3d rotated.mrc euler=0,0,0"
	apEMAN.executeEmanCmd(cmd, verbose=False, showcmd=False)

#=====================
def generateProjections(parttree):
	t0 = time.time()
	datafile = "parttree_data-"+str(stackid)+".txt"
	dataf = open(datafile, 'w', 0666)
	count = 0.0
	total = float(len(parttree))
	mult = 0.05
	for part in parttree:
		count += 1.0
		### generate euler
		if not 'euler' in part:
			part['euler'] = randomEuler()
			### set euler for pair
			if part['part2'] < len(parttree) and parttree[part['part2']-1]['part1'] == part['part2']:
				parttree[part['part2']-1]['euler'] = part['euler']
			else:
				apDisplay.printWarning("using slow method for part: "+str(part))
				for pair in parttree:
					if pair['part1'] == part['part2']:
						pair['euler'] = part['euler']
		### save to file
		dataf.write(str(part)+"\n")
		### generate projection
		if count > mult*total:
			sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b"+str(int(100*mult))+"% complete")
			mult += 0.05
			#sys.stderr.write(".")
		genProj(part['euler'], tilt=part['tilt'])
	dataf.close()
	sys.stderr.write("\nwriting to cache file")
	cachefile = "parttree_cache-"+str(stackid)+".pickle"
	cachef = open(cachefile, 'w', 0666)
	cPickle.dump(parttree, cachef)
	cachef.close()
	apDisplay.printMsg("Projected "+str(len(parttree))+" particles in "+apDisplay.timeString(time.time()-t0))

#=====================
#=====================
if __name__ == '__main__':
	stackid = 773
	if os.path.isfile("proj.hed"):
		apDisplay.printWarning("Removing proj.hed and proj.img files")
		time.sleep(2)
		os.remove("proj.hed")
		os.remove("proj.img")
	parttree = getParticles(stackid)
	generateProjections(parttree)



