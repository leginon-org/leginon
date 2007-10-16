#!/usr/bin/python -O

import MySQLdb
import math
import numpy
from scipy import ndimage
import random
import time
import pprint
import apDisplay
import sys

# connect
db = MySQLdb.connect(host="cronus4.scripps.edu", user="usr_object", passwd="", db="dbappiondata")
# create a cursor
cursor = db.cursor()


def getEulersForIteration(reconid, tiltrunid, iteration=1):
	"""
	returns all classdata for a particular refinement iteration
	"""
	t0 = time.time()
	query = (
		"SELECT \n"
			#+"	tiltd.`REF|ApParticleData|particle1` AS p1, \n"
			#+"	tiltd.`REF|ApParticleData|particle2` AS p2, \n"
			#+"	refd1.`iteration`, refd1.`REF|ApRefinementRunData|refinementRun` AS refRun1, \n"
			#+"	refd2.`iteration`, refd2.`REF|ApRefinementRunData|refinementRun` AS refRun2, \n"
			+"	e1.euler1 AS alt1, e1.euler2 AS az1, partclass1.`inplane_rotation` AS phi1, \n"
			+"	e2.euler1 AS alt2, e2.euler2 AS az2, partclass2.`inplane_rotation` AS phi2 \n"
			+"FROM `ApTiltParticlePairData` AS tiltd \n"
			+"LEFT JOIN `ApImageTiltTransformData` as transform \n"
			+"	ON tiltd.`REF|ApImageTiltTransformData|transform`=transform.`DEF_id` \n"
			+"LEFT JOIN `ApStackParticlesData` AS stpart1 \n"
			+"	ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` \n"
			+"LEFT JOIN `ApStackParticlesData` AS stpart2 \n"
			+"	ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` \n"
			+"LEFT JOIN `ApParticleClassificationData` AS partclass1 \n"
			+"	ON partclass1.`REF|ApStackParticlesData|particle` = stpart1.`DEF_id` \n"
			+"LEFT JOIN `ApParticleClassificationData` AS partclass2 \n"
			+"	ON partclass2.`REF|ApStackParticlesData|particle` = stpart2.`DEF_id` \n"
			+"LEFT JOIN `ApEulerData` AS e1 \n"
			+"	ON partclass1.`REF|ApEulerData|eulers` = e1.`DEF_id` \n"
			+"LEFT JOIN `ApEulerData` AS e2 \n"
			+"	ON partclass2.`REF|ApEulerData|eulers` = e2.`DEF_id` \n"
			+"LEFT JOIN `ApRefinementData` AS refd1 \n"
			+"	ON partclass1.`REF|ApRefinementData|refinement` = refd1.`DEF_id` \n"
			+"LEFT JOIN `ApRefinementData` AS refd2 \n"
			+"	ON partclass2.`REF|ApRefinementData|refinement` = refd2.`DEF_id` \n"
			+"WHERE transform.`REF|ApSelectionRunData|tiltrun` = "+str(tiltrunid)+" \n"
			+"	AND refd1.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n" 
			+"	AND refd1.`iteration` = "+str(iteration)+" \n"
			+"	AND refd2.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n" 
			+"	AND refd2.`iteration` = "+str(iteration)+" \n"
			#+"	AND tiltd.`REF|ApParticleData|particle1` = 14234108 \n"
			#+"LIMIT 300 \n"
		)

	print query

	cursor.execute(query)
	numrows = int(cursor.rowcount)
	print "Found ",numrows," rows"
	apDisplay.printMsg("Found data in "+apDisplay.timeString(time.time()-t0))

	result = cursor.fetchall()
	apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))

	#pprint.pprint(result)
	"""
	for i in result:
		for j in i:
			sys.stderr.write(str(round(j,2))+", ")
		sys.stderr.write("\n")
	"""

	f = open("eulerdata"+str(iteration)+".txt", "w")
	distlist = []
	for i in result:
		r0,r1 = resToEuler(i)
		#print r0
		#print r1
		mat0 = getMatrix3(r0)
		mat1 = getMatrix3(r1)
		dist = calculateDistance(mat0, mat1)
		#print mat0
		#print mat1
		f.write(str(dist)+"\n")
		distlist.append(dist)
		#print "dist=",dist
	f.close()

	freqnumpy = numpy.asarray(distlist, dtype=numpy.int32)
	#print(freqlist)
	print "EULER DATA:"
	print "min=",ndimage.minimum(freqnumpy)
	print "max=",ndimage.maximum(freqnumpy)
	print "mean=",ndimage.mean(freqnumpy)
	print "stdev=",ndimage.standard_deviation(freqnumpy)

	f = open("rotdata"+str(iteration)+".txt", "w")
	distlist = []
	for i in result:
		diff = abs(i[2] - i[5])
		if diff > 180.0:
			diff -= 180.0
		f.write(str(diff)+"\n")
		distlist.append(dist)
		#print "dist=",dist
	f.close()

	freqnumpy = numpy.asarray(distlist, dtype=numpy.int32)
	#print(freqlist)
	print "ROTATION DATA:"
	print "min=",ndimage.minimum(freqnumpy)
	print "max=",ndimage.maximum(freqnumpy)
	print "mean=",ndimage.mean(freqnumpy)
	print "stdev=",ndimage.standard_deviation(freqnumpy)

	#return radlist,anglelist,[],[]

def resToEuler(res):
	first = {}
	first['euler1'] = float(res[0])
	first['euler2'] = float(res[1])
	first['euler3'] = float(res[2])
	second = {}
	second['euler1'] = float(res[3])
	second['euler2'] = float(res[4])
	second['euler3'] = float(res[5])
	return first,second

def getMatrix3(eulerdata):
	#math from http://mathworld.wolfram.com/EulerAngles.html
	#appears to conform to EMAN conventions - could use more testing
	#tested by independently rotating object with EMAN eulers and with the
	#matrix that results from this function
	phi = round(eulerdata['euler2']*math.pi/180,2) #eman az,  azimuthal
	the = round(eulerdata['euler1']*math.pi/180,2) #eman alt, altitude
	psi = 0.0
	#psi = round(eulerdata['euler3']*math.pi/180,2) #eman phi, inplane_rotation

	m=numpy.zeros((3,3), dtype=numpy.float32)
	m[0,0] =  math.cos(psi)*math.cos(phi) - math.cos(the)*math.sin(phi)*math.sin(psi)
	m[0,1] =  math.cos(psi)*math.sin(phi) + math.cos(the)*math.cos(phi)*math.sin(psi)
	m[0,2] =  math.sin(psi)*math.sin(the)
	m[1,0] = -math.sin(psi)*math.cos(phi) - math.cos(the)*math.sin(phi)*math.cos(psi)
	m[1,1] = -math.sin(psi)*math.sin(phi) + math.cos(the)*math.cos(phi)*math.cos(psi)
	m[1,2] =  math.cos(psi)*math.sin(the)
	m[2,0] =  math.sin(the)*math.sin(phi)
	m[2,1] = -math.sin(the)*math.cos(phi)
	m[2,2] =  math.cos(the)
	return m

def calculateDistance(m1,m2):
	r=numpy.dot(m1.transpose(),m2)
	#print r
	trace=r.trace()
	s=(trace-1)/2.0
	if int(round(abs(s),7)) == 1:
		#print "here"
		return 0
	else:
		#print "calculating"
		theta=math.acos(s)
		#print 'theta',theta
		t1=abs(theta/(2*math.sin(theta)))
		#print 't1',t1 
		t2 = math.sqrt(pow(r[0,1]-r[1,0],2)+pow(r[0,2]-r[2,0],2)+pow(r[1,2]-r[2,1],2))
		#print 't2',t2, t2*180/math.pi
		d = t1 * t2
		#print 'd',d
		return d*180.0/math.pi


if __name__ == "__main__":
	#getEulersForIteration(reconid, tiltrunid, iteration=1):
	for i in (8,5,7):
		getEulersForIteration(186, 557, i)




