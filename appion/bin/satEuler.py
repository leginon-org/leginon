#!/usr/bin/python -O

#python
import sys
import random
import math
import time
import pprint
#site-packages
import numpy
from scipy import ndimage
import MySQLdb
#appion
import appionScript
import apDisplay
import apStack
#sinedon
import sinedon

class satEulerScript(appionScript.AppionScript):
	def onInit(self):
		# connect
		dbconf=sinedon.getConfig('appionData')
		db=MySQLdb.connect(**dbconf)
		# create a cursor
		cursor = db.cursor()

	#=====================
	def getTiltRunIDFromReconID(reconid):
		t0 = time.time()
		query = (
			"SELECT \n"
			+"  part.`REF|ApSelectionRunData|selectionrun` AS tiltrunid \n"
			+"FROM `ApRefinementRunData` as refrun \n"
			+"LEFT JOIN `ApStackParticlesData` AS stackpart \n"
			+"  ON refrun.`REF|ApStackData|stack` = stackpart.`REF|ApStackData|stack` \n"
			+"LEFT JOIN `ApParticleData` AS part \n"
			+"  ON stackpart.`REF|ApParticleData|particle` = part.`DEF_id` \n"
			+"WHERE refrun.`DEF_id` = "+str(reconid)+" \n" 
			+"  LIMIT 1 \n"
		)
		cursor.execute(query)
		numrows = int(cursor.rowcount)
		result = cursor.fetchall()
		apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
		if not result:
			apDisplay.printError("Failed to find tilt run")
		tiltrunid = result[0][0]
		apDisplay.printMsg("selected tilt run: "+str(tiltrunid))
		return tiltrunid

	#=====================
	def getLastIterationFromReconID(reconid):
		t0 = time.time()
		query = (
			"SELECT \n"
			+"  refdata.`iteration` \n"
			+"FROM `ApRefinementData` as refdata \n"
			+"WHERE refdata.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n" 
			+"ORDER BY refdata.`iteration` DESC \n"
			+"LIMIT 1 \n"
		)
		cursor.execute(query)
		numrows = int(cursor.rowcount)
		result = cursor.fetchall()
		apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
		if not result:
			apDisplay.printError("Failed to find any iterations")
		tiltrunid = result[0][0]
		apDisplay.printMsg("selected last iteration: "+str(tiltrunid))
		return tiltrunid

	#=====================
	def analyzeData(reconid, tiltrunid, iteration=1):
		results = getEulersForIteration(reconid, tiltrunid, iteration)
		datastr = "_r"+str(reconid)+"_i"+str(iteration)
		processEulers(results, datastr)

	#=====================
	def getEulersForIteration(reconid, tiltrunid, iteration=1):
		"""
		returns all classdata for a particular refinement iteration
		"""
		t0 = time.time()
		query = (
			"SELECT \n"
				+"  e1.euler1 AS alt1, e1.euler2 AS az1, partclass1.`inplane_rotation` AS phi1, \n"
				+"  e2.euler1 AS alt2, e2.euler2 AS az2, partclass2.`inplane_rotation` AS phi2, \n"
				+"  stpart1.particleNumber AS partnum1, stpart2.particleNumber AS partnum2 \n"
				+"FROM `ApTiltParticlePairData` AS tiltd \n"
				+"LEFT JOIN `ApImageTiltTransformData` as transform \n"
				+"  ON tiltd.`REF|ApImageTiltTransformData|transform`=transform.`DEF_id` \n"
				+"LEFT JOIN `ApStackParticlesData` AS stpart1 \n"
				+"  ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` \n"
				+"LEFT JOIN `ApStackParticlesData` AS stpart2 \n"
				+"  ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` \n"
				+"LEFT JOIN `ApParticleClassificationData` AS partclass1 \n"
				+"  ON partclass1.`REF|ApStackParticlesData|particle` = stpart1.`DEF_id` \n"
				+"LEFT JOIN `ApParticleClassificationData` AS partclass2 \n"
				+"  ON partclass2.`REF|ApStackParticlesData|particle` = stpart2.`DEF_id` \n"
				+"LEFT JOIN `ApEulerData` AS e1 \n"
				+"  ON partclass1.`REF|ApEulerData|eulers` = e1.`DEF_id` \n"
				+"LEFT JOIN `ApEulerData` AS e2 \n"
				+"  ON partclass2.`REF|ApEulerData|eulers` = e2.`DEF_id` \n"
				+"LEFT JOIN `ApRefinementData` AS refd1 \n"
				+"  ON partclass1.`REF|ApRefinementData|refinement` = refd1.`DEF_id` \n"
				+"LEFT JOIN `ApRefinementData` AS refd2 \n"
				+"  ON partclass2.`REF|ApRefinementData|refinement` = refd2.`DEF_id` \n"
				+"WHERE transform.`REF|ApSelectionRunData|tiltrun` = "+str(tiltrunid)+" \n"
				+"  AND refd1.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n" 
				+"  AND refd1.`iteration` = "+str(iteration)+" \n"
				+"  AND refd2.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n" 
				+"  AND refd2.`iteration` = "+str(iteration)+" \n"
				+"ORDER BY stpart1.particleNumber ASC \n"
				#+"LIMIT 300 \n"
			)
		print query
		cursor.execute(query)
		numrows = int(cursor.rowcount)
		result = cursor.fetchall()
		apDisplay.printMsg("Fetched "+str(numrows)+" rows in "+apDisplay.timeString(time.time()-t0))
		return result

	#=====================
	def processEulers(results, datastr):
		f = open("eulerdata"+datastr+".txt", "w")
		k = open("keepfile"+datastr+".lst", "w")
		distlist = []
		keepcount=0
		for i in results:
			r0,r1 = resToEuler(i)
			mat0 = getMatrix3(r0)
			mat1 = getMatrix3(r1)
			dist = calculateDistance(mat0, mat1)
			f.write(str(dist)+"\n")
			distlist.append(dist)
			if abs(dist - 15.0) < 5.0:
				keepcount+=1
				k.write(str(int(i[6]-1))+"\n")
				k.write(str(int(i[7]-1))+"\n")
		f.close()
		k.close()

		freqnumpy = numpy.asarray(distlist, dtype=numpy.float32)
		print "EULER DATA:"
		print "min=",ndimage.minimum(freqnumpy)
		print "max=",ndimage.maximum(freqnumpy)
		print "mean=",ndimage.mean(freqnumpy)
		print "stdev=",ndimage.standard_deviation(freqnumpy)

		f = open("rotdata"+datastr+".txt", "w")
		distlist = []
		for i in results:
			diff = abs(i[2] - i[5])
			if diff > 180.0:
				diff -= 180.0
			f.write(str(diff)+"\n")
			distlist.append(dist)
		f.close()

		freqnumpy = numpy.asarray(distlist, dtype=numpy.float32)
		print "ROTATION DATA:"
		print "min=",ndimage.minimum(freqnumpy)
		print "max=",ndimage.maximum(freqnumpy)
		print "mean=",ndimage.mean(freqnumpy)
		print "stdev=",ndimage.standard_deviation(freqnumpy)

		#return radlist,anglelist,[],[]

	#=====================
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

	#=====================
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

	#=====================
	def calculateDistance(m1,m2):
		r=numpy.dot(m1.transpose(),m2)
		#print r
		trace=r.trace()
		s=(trace-1.0)/2.0
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

	######################################################
	####  ITEMS BELOW WERE SPECIFIED BY AppionScript  ####
	######################################################

	#=====================
	def setupParserOptions(self):
		self.parser.add_option("-r", "--reconid", dest="reconid", type='int',
			help="Reconstruction Run ID", metavar="INT")
		self.parser.add_option("-i", "--iternum", dest="iternum", type='int',
			help="Reconstruction Iteration Number, defaults to last iteration", metavar="INT")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to copy the templates to", metavar="PATH")
		self.parser.add_option("--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.params['reconid'] is reconid:
			apDisplay.printError("Enter a Reconstruction Run ID, e.g. --reconid=243")
		if not self.params['tiltrunid']:
			self.params['tiltrunid'] = getTiltRunIDFromReconID(self.params['reconid'])
		if not self.params['iternum']:
			self.params['iternum'] = getLastIterationFromReconID(self.params['reconid'])
		if not self.params['stackid']:
			self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'])

	#=====================
	def start(self):
		#reconid = 186, 194, 239, 243
		#tiltrunid = 557, 655

		if not self.params['tiltrunid']:
			self.params['tiltrunid'] = getTiltRunIDFromReconID(self.params['reconid'])
		if not self.params['iternum']:
			self.params['iternum'] = getLastIterationFromReconID(self.params['reconid'])
		if not self.params['stackid']:
			self.params['iternum'] = apStack.getStackIdFromRecon(self.params['reconid'])

		### Big slow process
		if self.params['commit'] is True:
			analyzeData(reconid, tiltrunid, iternum)

#=====================
if __name__ == "__main__":
	satEuler = satEulerScript()
	satEuler.start()







