#!/usr/bin/python -O

import MySQLdb
import sinedon
import apEMAN
import apDisplay
import time

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
			+"LIMIT 10 \n"
		)
	cursor.execute(query)
	results = cursor.fetchall()
	#apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
	if not results:
		apDisplay.printError("Failed to get stack particles")
	return convertSQLtoTree(results)

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
def genProj(alt, az, phi, tilt=False):
	rotcmd = ( "proc3d groel.mrc rotated.mrc rot="
		+str(alt)+","+str(az)+","+str(phi) )
	if tilt is True:
		cmd = "project3d rotated.mrc euler=15,90,-90"
	else:
		cmd = "project3d rotated.mrc euler=0,0,0"


if __name__ == '__main__':
	parttree = getParticles(773)
	for part in parttree:
		print part

