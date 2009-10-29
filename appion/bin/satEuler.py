#!/usr/bin/env python

#python
import os
import sys
import math
import time
import glob
import pprint
import random
import cPickle
import subprocess
#appion
import appionScript
import apDisplay
import apStack
import apEulerCalc
import apParam
import apSymmetry
import appiondata
#sinedon
import sinedon
#site-packages
import numpy
from pyami import mrc, quietscipy
from scipy import ndimage, stats
import MySQLdb

class satEulerScript(appionScript.AppionScript):
	def __init__(self):
		"""
		Need to connect to DB server before moving forward
		"""
		self.cursor = None
		appionScript.AppionScript.__init__(self)
		if self.cursor is None:
			# connect
			self.dbconf = sinedon.getConfig('appiondata')
			self.db     = MySQLdb.connect(**self.dbconf)
			# create a cursor
			self.cursor = self.db.cursor()


	#=====================
	def getTiltRunIDFromReconID(self, reconid):
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
		#print query
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		#apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
		if not result:
			apDisplay.printError("Failed to find tilt run")
		tiltrunid = result[0][0]
		apDisplay.printMsg("selected tilt run: "+str(tiltrunid))
		return tiltrunid

	#=====================
	def getLastIterationFromReconID(self, reconid):
		t0 = time.time()
		query = (
			"SELECT \n"
			+"  refdata.`iteration` \n"
			+"FROM `ApRefinementData` as refdata \n"
			+"WHERE refdata.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n"
			+"ORDER BY refdata.`iteration` DESC \n"
			+"LIMIT 1 \n"
		)
		self.cursor.execute(query)
		result = self.cursor.fetchall()
		#apDisplay.printMsg("Fetched data in "+apDisplay.timeString(time.time()-t0))
		if not result:
			apDisplay.printError("Failed to find any iterations")
		tiltrunid = result[0][0]
		apDisplay.printMsg("selected last iteration: "+str(tiltrunid))
		return tiltrunid

	#=====================
	def getEulersForIteration(self, reconid, tiltrunid, iteration=1):
		"""
		returns all classdata for a particular refinement iteration
		"""
		#get mirror and good/bad
		t0 = time.time()
		query = (
			"SELECT \n"
				+"  stpart1.particleNumber AS partnum1, \n"
				+"  stpart1.`DEF_id` AS dbid1, \n"
				+"  partclass1.`euler1` AS alt1, partclass1.`euler2` AS az1, partclass1.`euler3` AS phi1, \n"
				+"  partclass1.`mirror` AS mirror1, partclass1.`thrown_out` AS reject1, \n"
				+"  stpart2.particleNumber AS partnum2, \n"
				+"  stpart2.`DEF_id` AS dbid2, \n"
				+"  partclass2.`euler1` AS alt2, partclass2.`euler2` AS az2, partclass2.`euler3` AS phi2, \n"
				+"  partclass2.`mirror` AS mirror2, partclass2.`thrown_out` AS reject2 \n"
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
				#+"LIMIT 10 \n"
			)
		#print query

		cachefile = "mysql_cache-recon"+str(reconid)+"-iter"+str(iteration)+".pickle"
		if not os.path.isfile(cachefile):
			apDisplay.printColor("Running MySQL query at "+time.asctime(), "yellow")
			self.cursor.execute(query)
			numrows = int(self.cursor.rowcount)
			apDisplay.printMsg("Found "+str(numrows)+" rows in "+apDisplay.timeString(time.time()-t0))
			apDisplay.printMsg("Fetching data at "+time.asctime())
			results = self.cursor.fetchall()
			cachef = open(cachefile, 'w', 0666)
			cPickle.dump(results, cachef)
		else:
			apDisplay.printColor("Using cached MySQL query data at "+time.asctime(), "cyan")
			cachef = open(cachefile, 'r')
			results = cPickle.load(cachef)
		cachef.close()
		apDisplay.printMsg("Fetched "+str(len(results))+" rows in "+apDisplay.timeString(time.time()-t0))

		#convert to tree form
		eulertree = self.convertSQLtoEulerTree(results)

		if len(eulertree) < 10:
			print query
			apDisplay.printError("Failed to get euler angles")

		return eulertree

	#=====================
	def convertSQLtoEulerTree(self, results):
		t0 = time.time()
		eulertree = []
		for row in results:
			if len(row) < 11:
				apDisplay.printError("delete MySQL cache file and run again")
			try:
				eulerpair = { 'part1': {}, 'part2': {} }
				eulerpair['part1']['partid'] = int(row[0])
				eulerpair['part1']['dbid']   = int(row[1])
				eulerpair['part1']['euler1'] = float(row[2])
				eulerpair['part1']['euler2'] = float(row[3])
				eulerpair['part1']['euler3'] = float(row[4])
				eulerpair['part1']['mirror'] = self.nullOrValue(row[5])
				eulerpair['part1']['reject'] = self.nullOrValue(row[6])
				eulerpair['part1']['tilt']   = apStack.getStackParticleTilt(eulerpair['part1']['dbid'])

				eulerpair['part2']['partid'] = int(row[7])
				eulerpair['part2']['dbid']   = int(row[8])
				eulerpair['part2']['euler1'] = float(row[9])
				eulerpair['part2']['euler2'] = float(row[10])
				eulerpair['part2']['euler3'] = float(row[11])
				eulerpair['part2']['mirror'] = self.nullOrValue(row[12])
				eulerpair['part2']['reject'] = self.nullOrValue(row[13])
				eulerpair['part2']['tilt']   = apStack.getStackParticleTilt(eulerpair['part2']['dbid'])
				eulertree.append(eulerpair)
			except:
				print row
				apDisplay.printError("bad row entry")

		apDisplay.printMsg("Converted "+str(len(eulertree))+" eulers in "+apDisplay.timeString(time.time()-t0))
		return eulertree

	#=====================
	def getEulersForIteration2(self, reconid, tiltrunid, stackid, iteration=1):
		"""
		returns all classdata for a particular refinement iteration
		"""
		#get mirror and good/bad
		t0 = time.time()

		cachefile = "mysql_cache-recon"+str(reconid)+"-iter"+str(iteration)+".pickle"
		if os.path.isfile(cachefile):
			apDisplay.printColor("Using cached MySQL query data at "+time.asctime(), "cyan")
			cachef = open(cachefile, 'r')
			eulertree = cPickle.load(cachef)
			cachef.close()
			apDisplay.printMsg("\nFetched "+str(len(eulertree))+" rows in "+apDisplay.timeString(time.time()-t0))
			return eulertree

		query = (
			"SELECT \n"
				+"  tiltd.`REF|ApParticleData|particle1` AS partnum1, \n"
				+"  tiltd.`REF|ApParticleData|particle2` AS partnum2 \n"
				+"FROM `ApTiltParticlePairData` AS tiltd \n"
				+"LEFT JOIN `ApImageTiltTransformData` as transform \n"
				+"  ON tiltd.`REF|ApImageTiltTransformData|transform` = transform.`DEF_id` \n"
				+"LEFT JOIN `ApStackParticlesData` AS stpart1 \n"
				+"  ON stpart1.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle1` \n"
				+"LEFT JOIN `ApStackParticlesData` AS stpart2 \n"
				+"  ON stpart2.`REF|ApParticleData|particle` = tiltd.`REF|ApParticleData|particle2` \n"
				+"WHERE \n"
				#+"  transform.`REF|ApSelectionRunData|tiltrun` = "+str(tiltrunid)+" \n"
				#+"AND \n"
				+"  stpart1.`REF|ApStackData|stack` = "+str(stackid)+" \n"
				+"AND \n"
				+"  stpart2.`REF|ApStackData|stack` = "+str(stackid)+" \n"
				#+"LIMIT 50 \n"
			)
		#print query
		apDisplay.printColor("Getting all particles via MySQL query at "+time.asctime(), "yellow")
		self.cursor.execute(query)
		numrows = int(self.cursor.rowcount)
		results = self.cursor.fetchall()
		apDisplay.printMsg("Fetched "+str(len(results))+" rows in "+apDisplay.timeString(time.time()-t0))

		if len(results) < 3:
			print query
			apDisplay.printError("No tilt pairs found in this stackid="+str(stackid))

		t0 = time.time()
		eulertree = []
		apDisplay.printColor("Getting individual particle info at "+time.asctime(), "yellow")
		count = 0
		for row in results:
			count += 1
			if count % 500 == 0:
				sys.stderr.write(".")
			eulerpair = { 'part1': {}, 'part2': {} }
			partid1 = int(row[0])
			partid2 = int(row[1])
			query = (
				"SELECT \n"
					+"  stpart.`particleNumber` AS partnum, \n"
					+"  stpart.`DEF_id` AS dbid, \n"
					+"  partclass.`euler1` AS alt, partclass.`euler2` AS az, partclass.`euler3` AS phi, \n"
					+"  partclass.`mirror` AS mirror, partclass.`thrown_out` AS reject \n"
					+"FROM `ApStackParticlesData` AS stpart \n"
					+"LEFT JOIN `ApParticleClassificationData` AS partclass \n"
					+"  ON partclass.`REF|ApStackParticlesData|particle` = stpart.`DEF_id` \n"
					+"LEFT JOIN `ApRefinementData` AS refd \n"
					+"  ON partclass.`REF|ApRefinementData|refinement` = refd.`DEF_id` \n"
					+"WHERE "
					+"  stpart.`REF|ApParticleData|particle` = "+str(partid1)+" \n"
					+"AND \n"
					+"  refd.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n"
					+"AND \n"
					+"  refd.`iteration` = "+str(iteration)+" \n"
					+"LIMIT 1 \n"
			)
			#print query
			self.cursor.execute(query)
			row = self.cursor.fetchone()
			if not row:
				continue
			eulerpair['part1']['partid'] = int(row[0])
			eulerpair['part1']['dbid']   = int(row[1])
			eulerpair['part1']['euler1'] = float(row[2])
			eulerpair['part1']['euler2'] = float(row[3])
			eulerpair['part1']['euler3'] = float(row[4])
			eulerpair['part1']['mirror'] = self.nullOrValue(row[5])
			eulerpair['part1']['reject'] = self.nullOrValue(row[6])
			eulerpair['part1']['tilt']   = apStack.getStackParticleTilt(eulerpair['part1']['dbid'])
			query = (
				"SELECT \n"
					+"  stpart.`particleNumber` AS partnum, \n"
					+"  stpart.`DEF_id` AS dbid, \n"
					+"  partclass.`euler1` AS alt, partclass.`euler2` AS az, partclass.`euler3` AS phi, \n"
					+"  partclass.`mirror` AS mirror, partclass.`thrown_out` AS reject \n"
					+"FROM `ApStackParticlesData` AS stpart \n"
					+"LEFT JOIN `ApParticleClassificationData` AS partclass \n"
					+"  ON partclass.`REF|ApStackParticlesData|particle` = stpart.`DEF_id` \n"
					+"LEFT JOIN `ApRefinementData` AS refd \n"
					+"  ON partclass.`REF|ApRefinementData|refinement` = refd.`DEF_id` \n"
					+"WHERE "
					+"  stpart.`REF|ApParticleData|particle` = "+str(partid2)+" \n"
					+"AND \n"
					+"  refd.`REF|ApRefinementRunData|refinementRun` = "+str(reconid)+" \n"
					+"AND \n"
					+"  refd.`iteration` = "+str(iteration)+" \n"
					+"LIMIT 1 \n"
			)
			#print query
			self.cursor.execute(query)
			row = self.cursor.fetchone()
			if not row:
				continue
			eulerpair['part2']['partid'] = int(row[0])
			eulerpair['part2']['dbid']   = int(row[1])
			eulerpair['part2']['euler1'] = float(row[2])
			eulerpair['part2']['euler2'] = float(row[3])
			eulerpair['part2']['euler3'] = float(row[4])
			eulerpair['part2']['mirror'] = self.nullOrValue(row[5])
			eulerpair['part2']['reject'] = self.nullOrValue(row[6])
			eulerpair['part2']['tilt']   = apStack.getStackParticleTilt(eulerpair['part2']['dbid'])
			eulertree.append(eulerpair)
			#end loop
		cachef = open(cachefile, 'w', 0666)
		cPickle.dump(eulertree, cachef)
		cachef.close()
		apDisplay.printMsg("\nFetched "+str(len(eulertree))+" rows in "+apDisplay.timeString(time.time()-t0))
		return eulertree



	#=====================
	def nullOrValue(self, val):
		if val is None:
			return 0
		else:
			return 1

	#=====================
	def calc3dRotationalDifference(self, eulerpair):
		e1 = { "euler1": eulerpair['part1']['euler1'],
			"euler2": eulerpair['part1']['euler2'],
			"euler3": eulerpair['part1']['euler3'] }
		e2 = { "euler1": eulerpair['part1']['euler1'],
			"euler2": eulerpair['part1']['euler2'],
			"euler3": eulerpair['part2']['euler3'] }
		rotdist = apEulerCalc.eulerCalculateDistanceSym(e1, e2, sym=self.params['symmname'], inplane=True)
		return rotdist

	#=====================
	def calc2dRotationalDifference(self, eulerpair):
		rotdist = (eulerpair['part1']['euler3'] - eulerpair['part2']['euler3']) % 360.0
		#With EMAN data the next line shouldn't be done
		#if rotdist > 180.0:
		#	rotdist -= 360.0
		return rotdist

	#=====================
	def processEulers(self, eulertree):
		t0 = time.time()
		angdistlist = []
		totdistlist = []
		rotdistlist = []
		t0 = time.time()
		apDisplay.printMsg("Begin processing "+str(len(eulertree))+" euler distances")
		count = 0
		for eulerpair in eulertree:
			count += 1
			if count % 500 == 0:
				sys.stderr.write(".")
			eulerpair['angdist'] = apEulerCalc.eulerCalculateDistanceSym(eulerpair['part1'],
				eulerpair['part2'], sym=self.params['symmname'], inplane=False)
			eulerpair['totdist'] = apEulerCalc.eulerCalculateDistanceSym(eulerpair['part1'],
				eulerpair['part2'], sym=self.params['symmname'], inplane=True)
			eulerpair['rotdist'] = self.calc2dRotationalDifference(eulerpair)
			### ignore rejected particles
			#if eulerpair['part1']['reject'] == 0 or eulerpair['part2']['reject'] == 0:
			#print eulerpair['part1']['mirror'],eulerpair['part2']['mirror'],eulerpair['totdist']
			angdistlist.append(eulerpair['angdist'])
			totdistlist.append(eulerpair['totdist'])
			rotdistlist.append(eulerpair['rotdist'])
		apDisplay.printMsg("Processed "+str(len(eulertree))+" eulers in "
			+apDisplay.timeString(time.time()-t0))

		self.writeRawDataFile(eulertree)
		self.writeKeepFiles(eulertree)
		self.writeScatterFile(eulertree)

		print "ANGLE EULER DATA:"
		#D-symmetry goes to 90, all other 180
		self.analyzeList(angdistlist, tuple((0,None,self.params['stepsize'])), "angdata"+self.datastr+".dat")

		print "PLANE ROTATION DATA:"
		self.analyzeList(rotdistlist, tuple((None,None,self.params['stepsize'])), "rotdata"+self.datastr+".dat")

		print "TOTAL EULER DATA:"
		#D-symmetry goes to 90, all other 180
		self.analyzeList(totdistlist, tuple((0,None,self.params['stepsize'])), "totaldata"+self.datastr+".dat")

		apDisplay.printMsg("Processed "+str(len(eulertree))+" eulers in "+apDisplay.timeString(time.time()-t0))

	#=====================
	def writeScatterFile(self, eulertree):
		"""
		write:
			(1) rotation angle diff in radians
			(2) tilt angle diff in degrees
		for xmgrace display
		"""
		s = open("scatter"+self.datastr+".agr", "w")
		s.write("@g0 type Polar\n")
		s.write("@with g0\n")
		s.write("@    world 0, 0, "+str(round(2.0*math.pi,6))+", 30\n")
		s.write("@    xaxis  tick major "+str(round(2.0*math.pi/7.0,6))+"\n")
		s.write("@    xaxis  tick major grid on\n")
		s.write("@    xaxis  tick major linestyle 6\n")
		s.write("@    yaxis  tick major 15.0\n")
		s.write("@    yaxis  tick minor ticks 2\n")
		s.write("@    yaxis  tick major grid on\n")
		s.write("@    yaxis  tick minor grid on\n")
		s.write("@    yaxis  tick minor linewidth 0.5\n")
		s.write("@    yaxis  tick minor linestyle 4\n")
		s.write("@    frame linestyle 0\n")
		s.write("@    s0 symbol size 0.14\n")
		s.write("@    s0 line type 0\n")
		s.write("@    s0 symbol fill color 2\n")
		s.write("@target G0.S0\n")
		for eulerpair in eulertree:
			if (eulerpair['part1']['mirror'] + eulerpair['part2']['mirror']) % 2 == 1:
				mystr = ( "%3.8f %3.8f\n" % (eulerpair['rotdist']*math.pi/180.0, eulerpair['angdist']) )
				s.write(mystr)
		s.write("&\n")
		s.close()
		return

	#=====================
	def writeRawDataFile(self, eulertree):
		#write to file
		rawfile = "rawdata"+self.datastr+".dat"
		apDisplay.printMsg("Writing raw data to file: "+rawfile)
		r = open(rawfile, "w")
		r.write("p1-id\tp1-e1\tp1-e2\tp1-e3\tmirror\treject\t"
			+"p2-id\tp2-e1\tp2-e2\tp2-e3\tmirror\treject\t"
			+"ang-dist\trot-dist\ttotal-dist\n")
		for eulerpair in eulertree:
			mystr = (
				str(eulerpair['part1']['partid'])+"\t"+
				str(round(eulerpair['part1']['euler1'],2))+"\t"+
				str(round(eulerpair['part1']['euler2'],2))+"\t"+
				str(round(eulerpair['part1']['euler3'],2))+"\t"+
				str(eulerpair['part1']['mirror'])+"\t"+
				str(eulerpair['part1']['reject'])+"\t"+
				str(eulerpair['part2']['partid'])+"\t"+
				str(round(eulerpair['part2']['euler1'],2))+"\t"+
				str(round(eulerpair['part2']['euler2'],2))+"\t"+
				str(round(eulerpair['part2']['euler3'],2))+"\t"+
				str(eulerpair['part2']['mirror'])+"\t"+
				str(eulerpair['part2']['reject'])+"\t"+
				str(round(eulerpair['angdist'],2))+"\t"+
				str(round(eulerpair['rotdist'],2))+"\t"+
				str(round(eulerpair['totdist'],2))+"\n"
			)
			r.write(mystr)
		r.close()
		return

	#=====================
	def writeKeepFiles(self, eulertree):
		#find good particles
		totkeeplist = []
		totbadlist = []
		notiltkeeplist = []
		angkeeplist = []
		skippair = 0
		for eulerpair in eulertree:
			if eulerpair['part1']['reject'] == 1 and eulerpair['part2']['reject'] == 1:
				skippair += 1
				continue
			goodtot = (abs(eulerpair['totdist'] - self.params['angle']) < self.params['cutrange'])
			badtot = (abs(eulerpair['totdist'] - self.params['angle']) > 3*self.params['cutrange'])
			goodang = (abs(eulerpair['angdist'] - self.params['angle']) < self.params['cutrange'])
			if goodtot:
				if eulerpair['part1']['tilt'] < eulerpair['part2']['tilt']:
					notiltkeeplist.append(eulerpair['part1']['partid']-1)
				else:
					notiltkeeplist.append(eulerpair['part2']['partid']-1)
				totkeeplist.append(eulerpair['part1']['partid']-1)
				totkeeplist.append(eulerpair['part2']['partid']-1)
			if badtot:
				totbadlist.append(eulerpair['part1']['partid']-1)
				totbadlist.append(eulerpair['part2']['partid']-1)
			if goodang:
				angkeeplist.append(eulerpair['part1']['partid']-1)
				angkeeplist.append(eulerpair['part2']['partid']-1)
		apDisplay.printMsg("skipped "+str(skippair)+" double bad pairs")
 		#sort
		totkeeplist.sort()
		notiltkeeplist.sort()
		angkeeplist.sort()
		totbadlist.sort()

		### write to file
		k = open("keeplist-tot"+self.datastr+".lst", "w")
		for kid in totkeeplist:
			k.write(str(kid)+"\n")
		k.close()

		### write to file
		k = open("keeplist-notilt"+self.datastr+".lst", "w")
		for kid in notiltkeeplist:
			k.write(str(kid)+"\n")
		k.close()

		### write to file
		#k = open("keeplist-ang"+self.datastr+".lst", "w")
		#for kid in angkeeplist:
		#	k.write(str(kid)+"\n")
		#k.close()

		### write to file
		k = open("badlist-tot"+self.datastr+".lst", "w")
		for kid in totbadlist:
			k.write(str(kid)+"\n")
		k.close()

		percent = "%3.1f" % (50.0*len(totkeeplist) / float(len(eulertree)))
		apDisplay.printMsg("Total Keeping "+str(len(totkeeplist))+" of "+str(2*len(eulertree))+" ("+percent+"%) eulers")
		percent = "%3.1f" % (50.0*len(angkeeplist) / float(len(eulertree)))
		apDisplay.printMsg("Angle Keeping "+str(len(angkeeplist))+" of "+str(2*len(eulertree))+" ("+percent+"%) eulers")
		return

	#=====================
	def analyzeList(self, mylist, myrange=(0,1,1), filename=None):
		"""
		histogram2(a, bins) -- Compute histogram of a using divisions in bins

		Description:
		   Count the number of times values from array a fall into
		   numerical ranges defined by bins.  Range x is given by
		   bins[x] <= range_x < bins[x+1] where x =0,N and N is the
		   length of the bins array.  The last range is given by
		   bins[N] <= range_N < infinity.  Values less than bins[0] are
		   not included in the histogram.
		Arguments:
		   a -- 1D array.  The array of values to be divied into bins
		   bins -- 1D array.  Defines the ranges of values to use during
		         histogramming.
		Returns:
		   1D array.  Each value represents the occurences for a given
		   bin (range) of values.
		"""
		#hist,bmin,minw,err = stats.histogram(mynumpy, numbins=36)
		#print hist,bmin,minw,err,"\n"
		if len(mylist) < 2:
			apDisplay.printWarning("Did not write file not enough rows ("+str(filename)+")")
			return

		if myrange[0] is None:
			mymin = float(math.floor(ndimage.minimum(mylist)))
		else:
			mymin = float(myrange[0])
		if myrange[1] is None:
			mymax = float(math.ceil(ndimage.maximum(mylist)))
		else:
			mymax = float(myrange[1])
		mystep = float(myrange[2])

		mynumpy = numpy.asarray(mylist, dtype=numpy.float32)
		print "range=",round(ndimage.minimum(mynumpy),2)," <> ",round(ndimage.maximum(mynumpy),2)
		print " mean=",round(ndimage.mean(mynumpy),2)," +- ",round(ndimage.standard_deviation(mynumpy),2)

		#histogram
		bins = []
		mybin = mymin
		while mybin <= mymax:
			bins.append(mybin)
			mybin += mystep
		bins = numpy.asarray(bins, dtype=numpy.float32)
		apDisplay.printMsg("Creating histogram with "+str(len(bins))+" bins")
		hist = stats.histogram2(mynumpy, bins=bins)
		#print bins
		#print hist
		if filename is not None:
			f = open(filename, "w")
			for i in range(len(bins)):
				out = ("%3.4f %d\n" % (bins[i] + mystep/2.0, hist[i]) )
				f.write(out)
			f.write("&\n")

	#=====================
	def subStackCmd(self):
		keepfile = os.path.join(self.params['rundir'], "keeplist-tot"+self.datastr+".lst")
		stackdata = apStack.getRunsInStack(self.params['stackid'])

		cmd = ( "subStack.py "
			+" --projectid="+str(self.params['projectid'])
			+" --old-stack-id="+str(self.params['stackid'])
			+" --commit"
			+" \\\n --keep-file="+keepfile
			+" \\\n --new-stack-name=sub-"+stackdata[0]['stackRun']['stackRunName']
			+" \\\n --description='sat from recon "+str(self.params['reconid'])
			+" iter "+str(self.iternum)
			+" with angle "+str(self.params['angle'])
			+" +/- "+str(self.params['cutrange'])
			+"' \n" )
		print "New subStack.py Command:"
		apDisplay.printColor(cmd, "purple")

	#=====================
	def satAverageCmd(self):
		keepfile = os.path.join(self.params['rundir'], "keeplist-tot"+self.datastr+".lst")
		newname = "recon%d_cut%d_iter%d.hed" % (self.params['reconid'], self.params['cutrange']*10, self.iternum)
		cmd = ( "satAverage.py "
			+" --projectid="+str(self.params['projectid'])
			+" --reconid="+str(self.params['reconid'])
			+" \\\n --mask=62 --iter="+str(self.iternum)
			+" \\\n --stackname="+newname
			+" \\\n --keep-list="+keepfile
			+" \n" )
		print "New satAverage.py Command:"
		apDisplay.printColor(cmd, "purple")

	#=====================
	def runSatAverage(self):
		keepfile = os.path.join(self.params['rundir'], "keeplist-tot"+self.datastr+".lst")
		newname = "recon%d_cut%d_iter%d.hed" % (self.params['reconid'], self.params['cutrange']*10, self.iternum)
		volname = "recon%d_cut%d_iter%d.%da.mrc"% (self.params['reconid'], self.params['cutrange']*10, self.iternum, self.iternum)
		volfile = os.path.join(self.params['rundir'], "volumes", volname)
		if os.path.isfile(volfile):
			apDisplay.printMsg("Skipping sat average, volume exists")
			return
		cmd = ( "satAverage.py "
			+" --projectid="+str(self.params['projectid'])
			+" --reconid="+str(self.params['reconid'])
			+" \\\n --mask=40 --iter="+str(self.iternum)
			+" \\\n --stackname="+newname
			+" \\\n --keep-list="+keepfile
			+" \n" )
		print "New satAverage.py Command:"
		apDisplay.printColor(cmd, "purple")
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()
		return

	#=====================
	def medianVolume(self):
		volpath = os.path.join(self.params['rundir'], "volumes/*a.mrc")
		mrcfiles = glob.glob(volpath)
		volumes = []
		for filename in mrcfiles:
			if os.path.isfile(filename):
				print filename
				vol = mrc.read(filename)
				print vol.shape
				volumes.append(vol)
		volarray = numpy.asarray(volumes, dtype=numpy.float32)
		medarray = numpy.median(volarray, axis=0)
		medfile = os.path.join(self.params['rundir'], "volumes/medianVolume.mrc")
		print medfile
		print medarray.shape
		mrc.write(medarray, medfile)

		apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])

		uploadcmd = ( ("uploadModel.py --projectid=%d --session=%s --file=%s "
				+"--apix=%.3f --sym=%s --name=satmedian-recon%d.mrc")
			%(self.params['projectid'], sessiondata['name'], medfile, 
				apix, self.params['symmname'], self.params['reconid']) )
		apDisplay.printColor(uploadcmd, "purple")

	######################################################
	####  ITEMS BELOW WERE SPECIFIED BY AppionScript  ####
	######################################################

	#=====================
	def setProcessingDirName(self):
		self.processdirname = os.path.join(self.functionname, "sat-recon"+str(self.params['reconid']))

	#=====================
	def setRunDir(self):
		"""
		this function only runs if no rundir is defined at the command line
		"""
		refdata = appiondata.ApRefinementRunData.direct_query(self.params['reconid'])
		if not refdata:
			apDisplay.printError("reconid "+str(self.params['reconid'])+" does not exist in the database")
		refpath = refdata['path']['path']
		rundir = os.path.join(refpath, "../../satEuler/sat-recon%d"%(self.params['reconid']))
		self.params['rundir'] = os.path.abspath(rundir)

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --reconid=<##> --commit [options]")
		self.parser.add_option("-r", "--reconid", dest="reconid", type='int',
			help="Reconstruction Run ID", metavar="INT")
		self.parser.add_option("--tiltrunid", dest="tiltrunid", type='int',
			help="Automatically set", metavar="INT")
		self.parser.add_option("--stackid", dest="stackid", type='int',
			help="Automatically set", metavar="INT")
		self.parser.add_option("-s", "--stepsize", dest="stepsize", type='float', default=1.0,
			help="Histogram step size in degrees, default=1.0", metavar="FLOAT")
		self.parser.add_option("-c", "--cutrange", dest="cutrange", type='float', default=5.0,
			help="Keep list cut range, default=5.0 ==> 15 +- 5 ==> 10 -- 20", metavar="FLOAT")
		self.parser.add_option("-a", "--angle", dest="angle", type='float', default=15.0,
			help="Ideal angle in degrees, default=15.0", metavar="FLOAT")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if self.cursor is None:
			# connect
			self.dbconf = sinedon.getConfig('appiondata')
			self.db     = MySQLdb.connect(**self.dbconf)
			# create a cursor
			self.cursor = self.db.cursor()
		if not self.params['reconid']:
			apDisplay.printError("Enter a Reconstruction Run ID, e.g. --reconid=243")
		if not self.params['tiltrunid']:
			self.params['tiltrunid'] = self.getTiltRunIDFromReconID(self.params['reconid'])
		self.params['symmetry'] = apSymmetry.getSymmetryFromReconRunId(self.params['reconid'])
		self.params['symmname'] = self.params['symmetry']['eman_name']
		if not self.params['stackid']:
			self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'])

	#=====================
	def start(self):
		#reconid = 186, 194, 239, 243
		#tiltrunid = 557, 655
		### Big slow process
		lastiter = self.getLastIterationFromReconID(self.params['reconid'])
		if self.params['commit'] is True:
			self.iternum = lastiter
			while self.iternum > 0:
				self.datastr = "_r"+str(self.params['reconid'])+"_i"+str(self.iternum)
				apDisplay.printColor("\n====================", "green")
				apDisplay.printColor("Iteration %d"%(self.iternum), "green")
				t0 = time.time()
				eulertree = self.getEulersForIteration2(self.params['reconid'], self.params['tiltrunid'],
					self.params['stackid'], self.iternum)
				#eulertree = self.getEulersForIteration(self.params['reconid'], self.params['tiltrunid'],
				#	self.iternum)
				self.processEulers(eulertree)
				self.runSatAverage()
				apDisplay.printMsg("Total time for "+str(len(eulertree))+" eulers: "+apDisplay.timeString(time.time()-t0))
				self.iternum-=1
		else:
			apDisplay.printWarning("Not committing results")
		self.subStackCmd()
		self.medianVolume()
		#self.satAverageCmd()

#=====================
if __name__ == "__main__":
	satEuler = satEulerScript()
	satEuler.start()
	satEuler.close()








