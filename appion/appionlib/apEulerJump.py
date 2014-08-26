#!/usr/bin/python -O

### python
import sys
import os
import re
import time
### numpy
import numpy
### db
import sinedon
import MySQLdb
### appion
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apEulerCalc
from appionlib import appiondata
from appionlib import apSymmetry

class ApEulerJump(object):
	#=====================
	def __init__(self):
		"""
		Need to connect to DB server before moving forward
		"""
		### get db config info
		self.dbconf = sinedon.getConfig('appiondata')
		### connect
		self.db     = MySQLdb.connect(**self.dbconf)
		self.db.autocommit(True)
		### create a cursor
		self.cursor = self.db.cursor()
		### keep sinedon version too
		self.jumperror = False


	#=====================
	def calculateEulerJumpsForEntireRecon(self, reconrunid, stackid=None, sym=None, multimodelrunid=None):
		if sym is None:
			sym = self.getSymmetry(reconrunid)
		if re.match("^icos", sym.lower()):
			apDisplay.printWarning("Processing Icos symmetry "+sym)
		if not re.match("^[cd][0-9]+$", sym.lower()) and not re.match("^icos", sym.lower()):
			apDisplay.printError("Cannot calculate euler jumps for symmetry: "+sym)
			return
		### get stack particles
		if stackid is None:
			stackid = apStack.getStackIdFromRecon(reconrunid, msg=False)
		stackparts = apStack.getStackParticlesFromId(stackid)
		stackparts.sort(self.sortStackParts)
		numparts = len(stackparts)
		### start loop
		t0 = time.time()
		medians = []
		count = 0
		miscount = 0
		for stackpart in stackparts:
			count += 1
			if multimodelrunid is None:
				jumpdata = self.getEulerJumpData(reconrunid, stackpartid=stackpart.dbid, stackid=stackid, sym=sym)
			else:
				jumpdata = self.getEulerJumpData(reconrunid, stackpartid=stackpart.dbid, stackid=stackid, sym=sym, multimodelrunid=multimodelrunid)
			if jumpdata is None:
				if miscount < 25:
					continue
				else:
					break
			medians.append(jumpdata['median'])
			if count % 500 == 0:
				timeremain = (time.time()-t0)/(count+1)*(numparts-count)
				print ("particle=% 5d; median jump=% 3.2f, remain time= %s" % (stackpart['particleNumber'], jumpdata['median'],
					apDisplay.timeString(timeremain)))
		if len(medians) > 0:
			### print stats
			apDisplay.printMsg("complete "+str(len(stackparts))+" particles in "+apDisplay.timeString(time.time()-t0))
			print "-- median euler jumper stats --"
			medians = numpy.asarray(medians, dtype=numpy.float32)
			print ("mean/std :: "+str(round(medians.mean(),2))+" +/- "
				+str(round(medians.std(),2)))
			print ("min/max  :: "+str(round(medians.min(),2))+" <> "
				+str(round(medians.max(),2)))
		else:
			apDisplay.printWarning("no Euler jumpers inserted into the database, make sure that the angles are read by the recon uploader")			
		return

	#=====================
	def sortStackParts(self, a, b):
		if a['particleNumber'] > b['particleNumber']:
			return 1
		else:
			return -1

	#=====================
	def getEulerJumpData(self, reconrunid,  stackpartnum=None, stackpartid=None, stackid=None, sym='d7', multimodelrunid=None):
		if stackpartnum is None and stackpartid is None:
			apDisplay.printError("please provide either stackpartnum or stackpartid")
		if stackpartid is None:
			stackpartid = self.getStackPartID(stackpartnum, reconrunid, stackid)
		### check DB first for data
		if multimodelrunid is None:
			jumpdata = self.getJumpDataFromDB(stackpartid, reconrunid=reconrunid)
		else:
			jumpdata = self.getJumpDataFromDB(stackpartid, multimodelrunid=multimodelrunid)
		if jumpdata is not None:
			return jumpdata
		### need to calculate the jump
		if multimodelrunid is None:
			jumpdata = self.calculateJumpData(stackpartid, reconrunid=reconrunid, sym=sym)
		else:
			jumpdata = self.calculateJumpData(stackpartid, multimodelrunid=multimodelrunid, sym=sym)
		if jumpdata is None:
			### No jump data for particle stackpartid
			if self.jumperror is False:
				self.jumperror = True
				if multimodelrunid is None:
					id = reconrunid
				else:
					id = multimodelrunid
				apDisplay.printWarning("Could not get or calculate jump data for stackpartid="
					+str(stackpartid)+" and reconrunid=%d" % id)
			return None
		### insert into DB
		if multimodelrunid is None:
			self.insertJumpIntoDB(stackpartid, jumpdata, reconrunid=reconrunid)
		else:
			self.insertJumpIntoDB(stackpartid, jumpdata, multimodelrunid=multimodelrunid)
		return jumpdata

	###########################################
	#### ITEMS BELOW ARE FOR INTERNAL USE ONLY ####
	###########################################

	#=====================
	def insertJumpIntoDB(self, stackpartid, jumpdata, reconrunid=None, multimodelrunid=None):
		if reconrunid is None and multimodelrunid is None:
			return None
		else:
			if multimodelrunid is None:
				#refinerundata=appiondata.ApRefineRunData.direct_query(reconid)
				ejumpq = appiondata.ApEulerJumpData()
				ejumpq['particle'] = appiondata.ApStackParticleData.direct_query(stackpartid)
				ejumpq['refineRun'] = appiondata.ApRefineRunData.direct_query(reconrunid)
				for key in ('median', 'mean', 'stdev', 'min', 'max'):
					ejumpq[key] = jumpdata[key]
				ejumpq.insert()
			else:
				ejumpq = appiondata.ApEulerJumpData()
				ejumpq['particle'] = appiondata.ApStackParticleData.direct_query(stackpartid)
				ejumpq['multiModelRefineRun'] = appiondata.ApMultiModelRefineRunData.direct_query(multimodelrunid)
				for key in ('median', 'mean', 'stdev', 'min', 'max'):
					ejumpq[key] = jumpdata[key]
				ejumpq.insert()				

	#=====================
	def getJumpDataFromDB(self, stackpartid, reconrunid=None, multimodelrunid=None):
		if reconrunid is None and multimodelrunid is None:
			return None
		elif reconrunid is not None and multimodelrunid is None:
			jumpq = appiondata.ApEulerJumpData()
			jumpq['particle'] = appiondata.ApStackParticleData.direct_query(stackpartid)
			jumpq['refineRun'] = appiondata.ApRefineRunData.direct_query(reconrunid)
			jumpdatas = jumpq.query(results=1)
			if not jumpdatas:
				return None
			return jumpdatas[0]
		elif reconrunid is None and multimodelrunid is not None:
			jumpq = appiondata.ApEulerJumpData()
			jumpq['particle'] = appiondata.ApStackParticleData.direct_query(stackpartid)
			jumpq['multiModelRefineRun'] = appiondata.ApMultiModelRefineRunData.direct_query(multimodelrunid)
			jumpdatas = jumpq.query(results=1)
			if not jumpdatas:
				return None
			return jumpdatas[0]
		else:
			return None

	#=====================
	def getStackPartID(self, stackpartnum, reconrunid, stackid=None):
		if stackid is None:
			stackid = apStack.getStackIdFromRecon(reconrunid, msg=False)

		stackpartq = appiondata.ApStackParticleData()
		stackpartq['stack'] = appiondata.ApStackData.direct_query(stackid)
		stackpartq['particleNumber'] = stackpartnum
		stackpartdata = stackpartq.query(results=1)

		if not stackpartdata:
			apDisplay.printError("Failed to get Stack Particle ID for Number "+str(partnum))
		return stackpartdata[0].dbid

	#=====================
	def calculateJumpData(self, stackpartid, reconrunid=None, multimodelrunid=None, sym='d7'):
		if reconrunid is None and multimodelrunid is None:
			return None
		else:
			#apDisplay.printMsg("calculating jump data for "+str(stackpartid))
			jumpdata = {}
			if multimodelrunid is None:
				eulers = self.getEulersForParticle(stackpartid, reconrunid)
			else:
				eulers = self.getEulersForParticle_MMrun(stackpartid, multimodelrunid)
			if eulers is None:
				return None
			eulers.sort(self.sortByIteration)
			distances = []
			for i in range(len(eulers)-1):
				#calculate distance (in degrees) for D7 symmetry
				dist = apEulerCalc.eulerCalculateDistanceSym(eulers[i], eulers[i+1], sym=sym, inplane=True)
				distances.append(dist)
				#f.write('%3.3f\t' % (dist))
			distarray = numpy.asarray(distances, dtype=numpy.float32)
			jumpdata['median'] = numpy.median(distarray)
			jumpdata['mean'] = distarray.mean()
			jumpdata['stdev'] = distarray.std()
			jumpdata['min'] = distarray.min()
			jumpdata['max'] = distarray.max()

			return jumpdata

	#=====================
	def sortByIteration(self, a, b):
		if a['iteration'] > b['iteration']:
			return 1
		else:
			return -1


	#=====================
	def getSymmetry(self, reconrunid, msg=True):
		"""
		get the symmetry from the last iteration of a refinement
		"""
		symmdata = apSymmetry.getSymmetryFromReconRunId(reconrunid, msg)
		symmname = symmdata['eman_name']
		return symmname

	#=====================
	def getEulersForParticleSinedon(self, stackpartid, reconrunid):
		"""
		returns all classdata for a particular particle and refinement
		"""
		refrundata = appiondata.ApRefineRunData.direct_query(reconrunid)
		stackpartdata = appiondata.ApStackParticleData.direct_query(stackpartid)

		refmentq = appiondata.ApRefineIterData()
		refmentq['refineRun'] = refrundata

		particledata = stackpartdata
		partclassq = appiondata.ApRefineParticleData()
		partclassq['particle'] = particledata
		partclassq['refineIter']  = refmentq
		partclassdata = partclassq.query()

		eulertree = []
		for data in partclassdata:
			try:
				euler = {}
				euler['stackpartid'] = int(data['particle'].dbid)
				euler['euler1'] = float(data['euler1'])
				euler['euler2'] = float(data['euler2'])
				euler['euler3'] = float(data['euler3'])
				euler['mirror'] = self.nullOrValue(data['mirror'])
				euler['reject'] = self.nullOrValue(data['refine_keep'])
				euler['iteration'] = int(data['refineIter']['iteration'])
				eulertree.append(euler)
			except:
				print euler
				import pprint
				pprint.pprint(data)
				apDisplay.printError("bad data entry")
		return eulertree

	#=====================
	def getEulersForParticle(self, stackpartid, reconrunid, stackid=None):
		"""
		returns euler data for a particular particle and refinement
		"""
		query = (
			"SELECT \n"
			+"  stackpart.`DEF_id` AS alt, \n"
			+"  partclass.`euler1` AS alt, \n"
			+"  partclass.`euler2` AS az, \n"
			+"  partclass.`euler3` AS phi, \n"
			+"  partclass.`mirror` AS mirror, \n"
			+"  partclass.`refine_keep` AS refine_keep, \n"
			+"  ref.`iteration` AS iteration \n"
			+"FROM `ApStackParticleData` as stackpart \n"
			+"LEFT JOIN `ApRefineParticleData` AS partclass \n"
			+"  ON partclass.`REF|ApStackParticleData|particle` = stackpart.`DEF_id` \n"
			+"LEFT JOIN `ApRefineIterData` AS ref \n"
			+"  ON partclass.`REF|ApRefineIterData|refineIter` = ref.`DEF_id` \n"
			+"WHERE \n"
			+"  stackpart.`DEF_id` = "+str(stackpartid)+" \n"
			+"AND \n"
			+"  ref.`REF|ApRefineRunData|refineRun` = "+str(reconrunid)+" \n"
		)
		self.cursor.execute(query)
		results = self.cursor.fetchall()
		if not results:
			### this particle was not used in the recon
			return None
		eulertree = self.convertSQLtoEulerTree(results)
		return eulertree

	#=====================
	def getEulersForParticle_MMrun(self, stackpartid, multimodelrunid):
		"""
		returns euler data for a particular particle and refinement	in multi-model case
		NOTE: particles can jump between individual refinements (i.e. references) in multi-model refinement. 
		Therefore, the query is constructed without the use of ApRefineRunData table
		"""
	
		query = (
			"SELECT \n"
			+"stackpart.`DEF_id` AS alt, \n"
			+"partclass.`euler1` AS alt, \n"
			+"partclass.`euler2` AS az, \n"
			+"partclass.`euler3` AS phi, \n"
			+"partclass.`mirror` AS mirror, \n"
			+"partclass.`refine_keep` AS refine_keep, \n"
			+"iter.`iteration` AS iteration \n"
			+"FROM `ApStackParticleData` as stackpart \n"
			+"LEFT JOIN `ApRefineParticleData` AS partclass \n"
			+"	ON partclass.`REF|ApStackParticleData|particle` = stackpart.`DEF_id` \n"
			+"LEFT JOIN `ApMultiModelRefineRunData` AS mmrun \n"
			+"	ON partclass.`REF|ApMultiModelRefineRunData|multiModelRefineRun` = mmrun.`DEF_id` \n"
			+"LEFT JOIN `ApRefineIterData` AS iter \n"
			+"	ON partclass.`REF|ApRefineIterData|refineIter` = iter.`DEF_id` \n"
			+"WHERE \n"
			+"	stackpart.`DEF_id` = "+str(stackpartid)+" \n"
			+"AND \n"
			+"	partclass.`REF|ApMultiModelRefineRunData|multiModelRefineRun` = "+str(multimodelrunid)+" \n"
		)
		self.cursor.execute(query)
		results = self.cursor.fetchall()
		if not results:
			### this particle was not used in the recon
			return None
		eulertree = self.convertSQLtoEulerTree(results)
		return eulertree

	#=====================
	def convertSQLtoEulerTree(self, results):
		eulertree = []
		for row in results:
			try:
				euler = {}
				euler['stackpartid'] = int(row[0])
				euler['euler1'] = float(row[1])
				euler['euler2'] = float(row[2])
				euler['euler3'] = float(row[3])
				euler['mirror'] = self.nullOrValue(row[4])
				euler['reject'] = not self.nullOrValue(row[5])
				euler['iteration'] = int(row[6])
				eulertree.append(euler)
			except:
				apDisplay.printError("bad row entry")
		return eulertree

	#=====================
	def nullOrValue(self, val):
		if val is None:
			return 0
		else:
			return 1


#==================
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: ./apEulerJump.py reconid [sym]\n\te.g. ./apEulerJump.py 418"
		sys.exit(1)
	reconrunid = int(sys.argv[1].strip())
	if len(sys.argv) > 2:
		sym = sys.argv[2].strip()
	else:
		sym=None
	a = ApEulerJump()
	a.calculateEulerJumpsForEntireRecon(reconrunid, sym=sym)



