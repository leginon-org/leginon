#!/usr/bin/python -O

#python
import sys
import os
import random
import math
import time
import pprint
#site-packages
import numpy
from scipy import ndimage, stats
import MySQLdb
#appion
import appionScript
import apDisplay
import apStack
import apEulerCalc
import apParam
#sinedon
import sinedon

class satEulerScript(appionScript.AppionScript):
	def __init__(self):
		# connect
		self.dbconf = sinedon.getConfig('appionData')
		self.db     = MySQLdb.connect(**self.dbconf)
		# create a cursor
		self.cursor = self.db.cursor()
		appionScript.AppionScript.__init__(self)

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
		t0 = time.time()
		query = (
			"SELECT \n"
				+"  stpart1.particleNumber AS partnum1, \n"
				+"  e1.euler1 AS alt1, e1.euler2 AS az1, partclass1.`inplane_rotation` AS phi1, \n"
				+"  stpart2.particleNumber AS partnum2, \n"
				+"  e2.euler1 AS alt2, e2.euler2 AS az2, partclass2.`inplane_rotation` AS phi2 \n"
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
				#+"LIMIT 10 \n"
			)
		apDisplay.printMsg("Running MySQL query at "+time.asctime())
		#print query
		self.cursor.execute(query)
		numrows = int(self.cursor.rowcount)
		apDisplay.printMsg("Found "+str(numrows)+" rows in "+apDisplay.timeString(time.time()-t0))
		apDisplay.printMsg("Fetching data at "+time.asctime())
		results = self.cursor.fetchall()
		apDisplay.printMsg("Fetched "+str(numrows)+" rows in "+apDisplay.timeString(time.time()-t0))
		return results

	#=====================
	def convertSQLtoEulerTree(self, results):
		t0 = time.time()
		eulertree = []
		for row in results:
			eulerpair = { 'part1': {}, 'part2': {} }
			eulerpair['part1']['partid'] = int(row[0])
			eulerpair['part1']['euler1'] = float(row[1])
			eulerpair['part1']['euler2'] = float(row[2])
			eulerpair['part1']['euler3'] = float(row[3])

			eulerpair['part2']['partid'] = int(row[4])
			eulerpair['part2']['euler1'] = float(row[5])
			eulerpair['part2']['euler2'] = float(row[6])
			eulerpair['part2']['euler3'] = float(row[7])
			eulertree.append(eulerpair)

		apDisplay.printMsg("Converted "+str(len(eulertree))+" eulers in "+apDisplay.timeString(time.time()-t0))
		return eulertree

	#=====================
	def calcRotationalDifference(self, eulerpair):
		rotdist = abs(eulerpair['part1']['euler3'] - eulerpair['part2']['euler3']) % 360.0
		#if rotdist > 180.0:
		#	rotdist -= 360.0
		return rotdist

	#=====================
	def processEulers(self, eulertree):
		t0 = time.time()
		angdistlist = []
		totdistlist = []
		rotdistlist = []
		for eulerpair in eulertree:
			eulerpair['angdist'] = apEulerCalc.eulerCalculateDistanceSym(eulerpair['part1'],
				eulerpair['part2'], sym='d7', inplane=False)
			eulerpair['totdist'] = apEulerCalc.eulerCalculateDistanceSym(eulerpair['part1'],
				eulerpair['part2'], sym='d7', inplane=True)
			angdistlist.append(eulerpair['angdist'])
			totdistlist.append(eulerpair['totdist'])
			eulerpair['rotdist'] = self.calcRotationalDifference(eulerpair)
			rotdistlist.append(eulerpair['rotdist'])

		self.writeKeepFile(eulertree)
		self.writeScatterFile(eulertree)

		print "EULER ANGLE DATA:"
		myrange = tuple((0,90,5))
		self.analyzeList(angdistlist, myrange, "eulerdata"+self.datastr+".dat")

		print "PLANE ROTATION DATA:"
		myrange = tuple((-180,180,10))
		self.analyzeList(rotdistlist, myrange, "rotdata"+self.datastr+".dat")

		print "TOTAL EULER DATA:"
		myrange = tuple((-180,180,10))
		self.analyzeList(totdistlist, myrange, "totaldata"+self.datastr+".dat")

		apDisplay.printMsg("Processed "+str(len(eulertree))+" eulers in "+apDisplay.timeString(time.time()-t0))

	#=====================
	def writeScatterFile(self, eulertree):
		s = open("scatter"+self.datastr+".dat", "w")
		for eulerpair in eulertree:
			mystr = ( "%3.4f %3.4f\n" % (eulerpair['angdist'], eulerpair['rotdist']) )
			s.write(mystr)
		s.write("&\n")
		s.close()
		return

	#=====================
	def writeKeepFile(self, eulertree):
		#find good particles
		keeplist = []
		for eulerpair in eulertree:
			if abs(eulerpair['angdist'] - 15.0) < 10.0:
				keeplist.append(eulerpair['part1']['partid']-1)
				keeplist.append(eulerpair['part2']['partid']-1)
		#sort
		keeplist.sort()

		#write to file
		k = open("keepfile"+self.datastr+".lst", "w")
		for kid in keeplist:
			k.write(str(kid)+"\n")
		k.close()

		percent = "%3.1f" % (50.0*len(keeplist) / float(len(eulertree)))
		apDisplay.printMsg("Keeping "+str(len(keeplist))+" of "+str(2*len(eulertree))+" ("+percent+"%) eulers")
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
		mymin = float(myrange[0])
		mymax = float(myrange[1])
		mystep = float(myrange[2])

		mynumpy = numpy.asarray(mylist, dtype=numpy.float32)
		print "range=",round(ndimage.minimum(mynumpy),2)," <> ",round(ndimage.maximum(mynumpy),2)
		print " mean=",round(ndimage.mean(mynumpy),2)," +- ",round(ndimage.standard_deviation(mynumpy),2)
		
		#histogram
		bins = []
		mybin = mymin
		while mybin < mymax:
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
				out = ("%3.4f %d\n" % (bins[i] + 2.5, hist[i]) )
				f.write(out)
			f.write("&\n")

	def subStackCmd(self):
		keepfile = os.path.join(self.params['outdir'], "keepfile"+self.datastr+".lst")
		stackdata = apStack.getRunsInStack(self.params['stackid'])

		cmd = ( "subStack.py "
			+" --old-stack-id="+str(self.params['stackid'])
			+" \\\n"+" --keep-file="+keepfile
			+" \\\n"+" --new-stack-name=sub-"+stackdata[0]['stackRun']['stackRunName']
			+" --commit"
			+" --description='xxx xx' \n" )
		print "New subStack.py Command:"
		apDisplay.printColor(cmd, "purple")

	######################################################
	####  ITEMS BELOW WERE SPECIFIED BY AppionScript  ####
	######################################################

	#=====================
	def setupOutputDirectory(self):
		"""
		Overriding appionScript version, this not a kosher thing to do
		"""
		self.datastr = "_r"+str(self.params['reconid'])+"_i"+str(self.params['iternum'])
		self.params['outdir'] =os.path.join(self.params['outdir'], "sat-recon"+str(self.params['reconid']))
		apDisplay.printMsg("Output directory: "+self.params['outdir'])
		apParam.createDirectory(self.params['outdir'])
		os.chdir(self.params['outdir'])

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --reconid=<##> --commit [options]")
		self.parser.add_option("-r", "--reconid", dest="reconid", type='int',
			help="Reconstruction Run ID", metavar="INT")
		self.parser.add_option("-i", "--iternum", dest="iternum", type='int',
			help="Reconstruction Iteration Number, defaults to last iteration", metavar="INT")
		self.parser.add_option("-o", "--outdir", dest="outdir", default=os.path.abspath("."),
			help="Location to copy the templates to", metavar="PATH")
		self.parser.add_option("--tiltrunid", dest="tiltrunid", type='int',
			help="Automatically set", metavar="INT")
		self.parser.add_option("--stackid", dest="stackid", type='int',
			help="Automatically set", metavar="INT")
		self.parser.add_option("-C", "--commit", dest="commit", default=False,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=False,
			action="store_false", help="Do not commit template to database")

	#=====================
	def checkConflicts(self):
		"""
		make sure the necessary parameters are set correctly
		"""
		if not self.params['reconid']:
			apDisplay.printError("Enter a Reconstruction Run ID, e.g. --reconid=243")
		if not self.params['tiltrunid']:
			self.params['tiltrunid'] = self.getTiltRunIDFromReconID(self.params['reconid'])
		if not self.params['iternum']:
			self.params['iternum'] = self.getLastIterationFromReconID(self.params['reconid'])
		if not self.params['stackid']:
			self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'])

	#=====================
	def start(self):
		#reconid = 186, 194, 239, 243
		#tiltrunid = 557, 655
		### Big slow process
		if self.params['commit'] is True:
			t0 = time.time()
			results = self.getEulersForIteration(self.params['reconid'], self.params['tiltrunid'], self.params['iternum'])
			eulertree = self.convertSQLtoEulerTree(results)
			self.processEulers(eulertree)
			apDisplay.printMsg("Total time for "+str(len(eulertree))+" eulers: "+apDisplay.timeString(time.time()-t0))
		else:
			apDisplay.printWarning("Not committing results")
		self.subStackCmd()

#=====================
if __name__ == "__main__":
	satEuler = satEulerScript()
	satEuler.start()







