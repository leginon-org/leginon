#!/usr/bin/env python
#
import os
import re
import time
import sys
import math
import subprocess
import shlex
import leginon.leginondata
import copy
import numpy
#appion
from appionlib import appionScript
from appionlib import appionLoop2
from appionlib import apHelicalParams
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apParam
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata
from appionlib import apProject
from appionlib import apXmipp
from appionlib import apChimera
from appionlib import apRecon
from appionlib import apEMAN


#=====================
#=====================

class HipScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--session", dest="sessionname", type="str",
			help="Session name", metavar="NAME")
		self.parser.add_option("--mandir", dest="mandir", type="str",
			help="Directory containing mandatory files", metavar="DIR")
		self.parser.add_option("-s", "--id", "--stackid", dest="stackid", type="int",
			help="Stack ID", metavar="ID")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of filament segments to use", metavar="#")
		self.parser.add_option("--rep-len", dest="replen", type="int",
			help="Helical repeat length (in Angstroms)", metavar="#")
		self.parser.add_option("--subunits", dest="subunits", type="int",
			help="Number of subunits in one helical repeat", metavar="#")
		self.parser.add_option("--diam", dest="diameter", type="int",
			help="Outer diameter of the filament (in Angstroms)", metavar="#")
		self.parser.add_option("--diam-inner", dest="diaminner", type="int",
			help="Inner diameter of the filament (in Angstroms)", metavar="#")
		self.parser.add_option("--xlngth", dest="xlngth", type="int",
			help="Filament segment length (in pixels)", metavar="#")
		self.parser.add_option("--yht2", dest="yht2", type="int",
			help="Filament box height prior to alignments (in pixels)", metavar="#")
		self.parser.add_option("--pad-val", dest="padval", type="int",
			help="Value to pad the filament box to (in pixels)", metavar="#")
		self.parser.add_option("--res-cut", dest="rescut", type="int",
			help="Phase residual cutoff", metavar="#")
		self.parser.add_option("--fil-val", dest="filval", type="int",
			help="Lowpass filter value", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="str",
			help="Binning factor", metavar="#")
		self.parser.add_option("--conchg", dest="cont", type="str",
			help="Will a contrast change be applied, yes or no", metavar="CHOICE")
		self.parser.add_option("--prehip", dest="prehip", type="str",
			help="Is prehip needed to set up input files, yes or no", metavar="CHOICE")
		self.parser.add_option("--rise", dest="rise", type="float",
			help="Rise distance between protein subunits", metavar="#")
		self.parser.add_option("--twist", dest="twist", type="float",
			help="Twist angle between protein subunits", metavar="#")
		self.parser.add_option("--ll1", dest="ll1", type="int",
			help="(1,0) Layer line", metavar="#")
		self.parser.add_option("--bo1", dest="bo1", type="int",
			help="(1,0) Bessel Order", metavar="#")
		self.parser.add_option("--ll2", dest="ll2", type="int",
			help="(0,1) Layer line", metavar="#")
		self.parser.add_option("--bo2", dest="bo2", type="int",
			help="(0,1) Bessel Order", metavar="#")
		self.parser.add_option("--nfold", dest="nfold", type="int",
			help="Order of the symmetry axis", metavar="#")
		self.parser.add_option("--maxll", dest="maxll", type="int",
			help="Maximum layer line to include", metavar="#")
		self.parser.add_option("--maxbo", dest="maxbo", type="int",
			help="Maximum bessel order to include", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("Stack id was not defined")
		if self.params['mandir'] is None:
			apDisplay.printError("Directory containing mandatory files was not defined")
		if self.params['description'] is None:
			apDisplay.printError("Run description was not defined")
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)
			apDisplay.printWarning("Number of particles not defined, processing full stack")
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])+" than available "+str(apFile.numImagesInStack(stackfile)))
		if self.params['replen'] is None:
			apDisplay.printError("Helical repeat was not defined")
		if self.params['subunits'] is None:
			apDisplay.printError("Number of subunits was not defined")
		if self.params['diameter'] is None:
			apDisplay.printError("Filament diameter was not defined")
		if self.params['diaminner'] is None:
			apDisplay.printError("Inner filament diameter was not defined")
		if self.params['rescut'] is None:
			apDisplay.printError("Phase residual cutoff was not defined")
		if self.params['filval'] is None:
			apDisplay.printError("Filter value was not defined")
		if self.params['bin'] is None:
			self.params['bin'] = 1
			apDisplay.printWarning("Binning factor was not defined, binning by one")
		if self.params['cont'] is None:
			apDisplay.printError("Must specify if a contrast change is needed")
		if self.params['prehip'] is None:
			apDisplay.printError("Must specify if prehip needs to be executed or not")
		step = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.params['step'] = step
		onerep = math.floor(self.params['replen'] / step)
		calcyht2 = math.floor(self.params['diameter'] / step)
		boxsize = apStack.getStackBoxsize(self.params['stackid'])
		self.params['boxsize'] = boxsize
		if self.params['xlngth'] < onerep:
			apDisplay.printError("Filament segment length can not be less than one helical repeat")
		if self.params['xlngth'] > boxsize:
			apDisplay.printError("Filament segment length can not be greater than stack box size")
		if self.params['yht2'] < calcyht2:
			apDisplay.printError("Filament box height can not be less than filament diameter")
		if self.params['padval'] < self.params['xlngth']:
			apDisplay.printError("Pad value can not be less than the filament segment length")
		if not self.checkval(self.params['yht2']):
			apDisplay.printError("Filament box height must be a power of two")
		if not self.checkval(self.params['padval']):
			apDisplay.printError("Pad value must be a power of two")

	#=====================
	def setRunDir(self):
		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a sessionname or run directory")
		else:
			print self.params['sessionname']
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		path = os.path.join(path, self.processdirname, self.params['runname'])
		self.params['rundir'] = path

	#=====================
	def checkval(self, x):
		temp = x
		while temp > 2.0:
			temp = (temp / 2.0)
		if temp == 2.0:
			return True
		else:
			return False

	#=====================
	def getimageData(self):
		sessionname = self.params['sessionname']
		sessionq = leginon.leginondata.SessionData(name=sessionname)
		imageq = leginon.leginondata.AcquisitionImageData(session=sessionq)  
		firstimage = imageq.query(results=1) 
		imgpath = firstimage[0]['session']['image path']
		self.params['imgpath'] = imgpath
		volts = firstimage[0]['scope']['high tension'] 
		self.params['volts'] = volts
		mag = firstimage[0]['scope']['magnification']
		defocus = abs(firstimage[0]['scope']['defocus'])*1000000
		xdim = firstimage[0]['camera']['dimension']['x'] ###just for reference now
		ydim = firstimage[0]['camera']['dimension']['y'] ###just for reference now

	#=====================
	def writeParams(self):
		self.getimageData()
		finalparams = {}
		finalparams.update(apHelicalParams.setupParams())
		finalparams.update(self.params)
		step = self.params['step']
		diameter = self.params['diameter']
		diaminner = self.params['diaminner']
		replen = self.params['replen']
		padval = self.params['padval']
		finalparams.update(apHelicalParams.calculateParams(step, diameter, diaminner, replen, padval))
		filename = os.path.join(self.params['rundir'], "phoelix_params")
		f = open(filename, 'w')
		for (k, v) in finalparams.items():
			f.write("set %s = %s\n" % (k, v))
		f.close()
	#=====================
	def writeLLBO1(self):
		filename = os.path.join(self.params['mandir'], "llbo.tmp")
		filename2 = os.path.join(self.params['mandir'], "llbo.txt")
		f = open(filename, 'w')
		f2 = open(filename2, 'w')

		rise = self.params['rise']
		twist = self.params['twist']
		replen = self.params['replen']
		nfold = self.params['nfold']
		maxbo = self.params['maxbo']
		maxll = self.params['maxll']
		
		subunits = math.ceil(replen/rise)
		if twist < 0:
			turns = math.floor((twist * subunits)/360)
		else:
			turns = math.ceil((twist * subunits)/360)
		print "subunits=", subunits, "turns=", turns

		print>>f, 0, 0
		print>>f2, "ll= ", 0, "bo= ", 0
		i = 1
		stop = maxll + 1
		while i <= stop:
			j = -1*maxbo
			while j <= maxbo:
				test = ((nfold * i) + (turns * j))
				if test%subunits == 0:
					bo = j
					ll = i
					print>>f, ll, bo
					print>>f2, "ll= ", ll, "bo= ", bo
					j = j+1
				else:	
					j = j+1
			i = i +1

	#=====================
	def writeLLBO2(self):
		filename = os.path.join(self.params['mandir'], "llbo.tmp")
		filename2 = os.path.join(self.params['mandir'], "llbo.txt")
		f = open(filename, 'w')
		f2 = open(filename2, 'w')

		ll1 = self.params['ll1']
		bo1 = self.params['bo1']
		ll2 = self.params['ll2']
		bo2 = self.params['bo2']

		print>>f, 0, 0
		print>>f2, "ll= ", 0, "bo= ", 0

		i = 0
		startll = ll1 - (ll2 * 5)
		startbo = bo1 - (bo2 * 5)
		lla = startll
		boa = startbo
		subdict = []
		while lla <= 200:
			lla = startll + (ll2 * i)
			boa = startbo + (bo2 * i)
			ll = lla
			bo = boa
			j = 0
			while bo < 2*self.params['maxbo'] and bo > -2*self.params['maxbo']:
				ll = lla + (ll1 * j)
				bo = boa + (bo1 * j)
				if ll > 0 and ll <= self.params['maxll'] and bo >= -1*self.params['maxbo'] and bo <= self.params['maxbo']:
					print>>f, ll, bo
					print>>f2, "ll= ", ll, "bo= ", bo
				if bo == 0:
					subdict.append(ll)
				j = j+1
			i = i+1

		i = 0
		startll = 0
		startbo = 0
		lla = startll
		boa = startbo
		while lla <= 200 and lla >= -1*ll1:
			lla = startll - (ll1 * i)
			boa = startbo - (bo1 * i)
			ll = lla
			bo = boa
			j = 0
			while bo < 2*self.params['maxbo'] and bo > -2*self.params['maxbo']:
				ll = lla + (ll2 * j)
				bo = boa + (bo2 * j)
				if ll > 0 and ll <= self.params['maxll'] and bo >= -1*self.params['maxbo'] and bo <= self.params['maxbo']:
					print>>f, ll, bo
					print>>f2, "ll= ", ll, "bo= ", bo
				if bo == 0:
					subdict.append(ll)
				j = j+1
			i = i+1

		f.close()
		f2.close()
		subunits = subdict[0]

	#=====================
	def putFilesInStack(self):
		selfile = os.path.join(self.params['rundir'], "selfile.list")
		stackfile = os.path.join(self.params['rundir'], "start.hed")
		apXmipp.gatherSingleFilesIntoStack(selfile, stackfile, filetype="mrc")
		return stackfile

	#==================
	def getResolutionData(self, avgpath, iternum):
		evenvol = os.path.join(avgpath, "avglist3_%dp1.mrc"%(self.params['rescut']))
		oddvol = os.path.join(avgpath, "avglist3_%dp2.mrc"%(self.params['rescut']))
		evenhed = os.path.join(avgpath, "avglist3_%dp1.hed"%(self.params['rescut']))
		oddhed = os.path.join(avgpath, "avglist3_%dp2.hed"%(self.params['rescut']))
		emancmd1 = 'proc3d %s %s' % (evenvol, evenhed)
		apEMAN.executeEmanCmd(emancmd1, verbose=True)
		emancmd2 = 'proc3d %s %s' % (oddvol, oddhed)
		apEMAN.executeEmanCmd(emancmd2, verbose=True)
		fscfile = 'fsc.eotest.%d'%(iternum)
		fscpath = os.path.join(avgpath, fscfile)
		emancmd3 = 'proc3d %s %s fsc=%s' % (evenhed, oddhed, fscpath)
		apEMAN.executeEmanCmd(emancmd3, verbose=True)

		if not os.path.isfile(fscpath):
			apDisplay.printWarning("Could not find FSC file: "+fscpath)
			return None
		f = open(fscpath, 'r')
		xy = f.readlines()
		lines = len(xy)
		boxsize = (lines * 2.0)
		f.close()
		# calculate the resolution:
		halfres = apRecon.calcRes(fscpath, boxsize, self.params['step'])
		apDisplay.printColor("FSC 0.5 Resolution of %.3f Angstroms"%(halfres), "cyan")

		# save to database
		resq=appiondata.ApResolutionData()
		resq['half'] = halfres
		resq['fscfile'] = fscpath

		return resq

	#==================
	def getRMeasureData(self, volumeDensity):
		volPath = os.path.join(self.params['rundir'], volumeDensity)
		if not os.path.exists(volPath):
			apDisplay.printWarning("R Measure failed, volume density not found: "+volPath)
			return None

		resolution = apRecon.runRMeasure(self.params['step'], volPath)
		if resolution is None:
			return None

		rmesq = appiondata.ApRMeasureData()
		rmesq['volume']=os.path.basename(volumeDensity)
		rmesq['rMeasure']=resolution
		print rmesq
		return rmesq

	#=====================
	def insertHipRunData(self):
		HipRun = appiondata.ApHipRunData()
		HipRun['runname'] = self.params['runname']
		HipRun['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		HipRun['description'] = self.params['description']
		HipRun['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		HipRun['session'] = sessiondata
		HipRun['apix'] = self.params['step']
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		HipRun['stack'] = self.stackdata
		if self.params['commit'] is True:
			HipRun.insert()
		else:
			print HipRun
		self.params['HipRunID'] = HipRun.dbid
		print "self.params['HipRunID']",self.params['HipRunID']
		self.params['HipRun'] = HipRun
		return HipRun

	#=====================
	def getHipRunData(self):
		HipRun = appiondata.ApHipRunData()
		HipRun['runname'] = self.params['runname']
		HipRun['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		HipRun['description'] = self.params['description']
		HipRun['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		HipRun['session'] = sessiondata
		HipRun['apix'] = self.params['step']
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		HipRun['stack'] = self.stackdata
		return HipRun

	#=====================
	def insertHipParamsData(self):
		HipParams = appiondata.ApHipParamsData()
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		HipParams['session'] = sessiondata
		HipParams['hipRun'] = self.params['HipRun']
		HipParams['numpart'] = self.params['numpart']
		HipParams['replen'] = self.params['replen']
		HipParams['diam'] = self.params['diameter']
		HipParams['diaminner'] = self.params['diaminner']
		HipParams['subunits'] = self.params['subunits']
		HipParams['xlngth'] = self.params['xlngth']
		HipParams['yht2'] = self.params['yht2']
		HipParams['padval'] = self.params['padval']
		HipParams['rescut'] = self.params['rescut']
		HipParams['filval'] = self.params['filval']
		HipParams['strong'] = os.path.join(self.params['rundir'], "strong.sa")
		HipParams['range'] = os.path.join(self.params['rundir'], "range.sa")
		HipParams['llbo'] = os.path.join(self.params['rundir'], "llbo.sa")
		HipParams['final_stack'] = os.path.join(self.params['rundir'], "start.hed")
		if self.params['commit'] is True:
			HipParams.insert()	
		else:
			print HipParams
		self.params['HipParamsID'] = HipParams.dbid
		print "self.params['HipParamsID']",self.params['HipParamsID']
		return

	#=====================
	def insertHipIterData(self):
		for i in range(3):
			iternum = i+1
			apDisplay.printColor("\nUploading iteration %d of %d\n"%(iternum, 3), "green")
			HipIter = appiondata.ApHipIterData()
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			HipIter['session'] = sessiondata
			if iternum == 1:
				avgpath = os.path.join(self.params['rundir'], "avgsnif1")
				HipIter['chop1'] = os.path.join(avgpath, "chop1.dek")
			elif iternum == 2:
				avgpath = os.path.join(self.params['rundir'], "avgsnif1/avgsnif2")
				HipIter['chop2'] = os.path.join(avgpath, "chop2.dek")
			elif iternum == 3:
				avgpath = os.path.join(self.params['rundir'], "avgsnif1/avgsnif2/avg3")
			volumeMrcFile = os.path.join(avgpath, "avglist3_%dp.mrc"%(self.params['rescut']))
			apChimera.filterAndChimera(volumeMrcFile, res=10, apix=self.params['step'], chimtype='snapshot', contour=1.0, zoom=1, sym='c9', silhouette=True)

			HipIter['hipRun'] = self.params['HipRun']
			HipIter['iteration'] = iternum
			HipIter['iterpath'] = avgpath
			HipIter['volumeDensity'] = volumeMrcFile
			HipIter['resolution'] = self.getResolutionData(avgpath, iternum)
			HipIter['rMeasure'] = self.getRMeasureData(volumeMrcFile)
			HipIter['cutfit1'] = os.path.join(avgpath, "cutfit1.dek")
			HipIter['cutfit2'] = os.path.join(avgpath, "cutfit2.dek")
			HipIter['cutfit3'] = os.path.join(avgpath, "cutfit3.dek")
			HipIter['avglist_file'] = os.path.join(avgpath, "avglist3_%dp.list"%(self.params['rescut']))
			f = open(HipIter['avglist_file'], 'r')
			lines = f.readlines()
			f.close()
			HipIter['final_numpart'] = len(lines) 
			HipIter['asymsu'] = int(((self.params['boxsize']*self.params['step'])/self.params['replen'])*self.params['subunits']*len(lines))
			HipIter['avg_file'] = os.path.join(avgpath, "avglist3_%dp.avg"%(self.params['rescut']))
			HipIter['map_file'] = os.path.join(avgpath, "avglist3_%dp.map"%(self.params['rescut']))
			HipIter['mrc_file'] = os.path.join(avgpath, "avglist3_%dp.mrc"%(self.params['rescut']))
			HipIter['ll_file'] = os.path.join(avgpath, "pll.list")
			HipIter['op_file'] = os.path.join(avgpath, "pop.list")
			HipIter['output_file'] = os.path.join(avgpath, "avglist3_%dp.OUTPUT"%(self.params['rescut']))
			if self.params['commit'] is True:
				HipIter.insert()	
			else:
				print HipIter
			self.params['HipIterID'] = HipIter.dbid
			print "self.params['HipIterID']",self.params['HipIterID']
		return

	#=====================
	def insertHipParticleData(self):
		self.particleNumber = 0
		alldir = os.listdir(self.params['rundir'])
		ems_list = []
		for file in alldir:
			if re.search(".ems.out", file):
				ems_list.append(file)
		ems_list.sort()

		avgdir = os.listdir(os.path.join(self.params['rundir'],"avgsnif1/avgsnif2/avg3"))
		fhlxavg_list = []	
		for file in avgdir:
			if re.search("f.hlxavg_dek", file):
				fhlxavg_list.append(file)
		fhlxavg_list.sort()

		nhlxavg_list = []	
		for file in avgdir:
			if re.search("n.hlxavg_dek", file):
				nhlxavg_list.append(file)
		nhlxavg_list.sort()

		for i in range(len(ems_list)):
			filename = ems_list[i]
			### Will the filenames always be part000000.ext with apXmipp.breakStackIntoSingleFiles??  This is a risky way to get the file prefix. Find a better way!
			self.filep = filename[0:10]
			self.particleNumber += 1
			HipParticle = appiondata.ApHipParticleData()
			HipParticle['hipRun'] = self.params['HipRun']

			for file in fhlxavg_list:
				if re.search(self.filep, file):
					f = open(os.path.join(self.params['rundir'], "avgsnif1/avgsnif2/avg3", file), 'r')
					lines = f.readlines()
					keyline = lines[2]
					pzr_list = keyline.split()
					f.close()
					HipParticle['far_phi'] = pzr_list[2]
					HipParticle['far_z'] = pzr_list[3]
					HipParticle['far_rscale'] = pzr_list[4]
					HipParticle['far_ampscale'] = lines[-1]
			for file in nhlxavg_list:
				if re.search(self.filep, file):
					f = open(os.path.join(self.params['rundir'], "avgsnif1/avgsnif2/avg3", file), 'r')
					lines = f.readlines()
					keyline = lines[2]
					pzr_list = keyline.split()
					f.close()
					HipParticle['ner_phi'] = pzr_list[2]
					HipParticle['ner_z'] = pzr_list[3]
					HipParticle['ner_rscale'] = pzr_list[4]
					HipParticle['ner_ampscale'] = lines[-1]
			f = open(ems_list[i], 'r')
			lines = f.readlines()
			lastline = lines[-1]
			tsr_list = lastline.split()
			f.close()
			sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
			HipParticle['session'] = sessiondata
			HipParticle['filename'] = self.filep
			HipParticle['stack'] = self.stackdata
			HipParticle['mrc_file'] = os.path.join(self.params['rundir'], self.filep + ".mrc")
			HipParticle['s_file'] = os.path.join(self.params['rundir'], self.filep + ".s")
			HipParticle['dft_file'] = os.path.join(self.params['rundir'], self.filep + ".dft")
			HipParticle['colb_file'] = os.path.join(self.params['rundir'], self.filep + ".colb")
			HipParticle['ner_file'] = os.path.join(self.params['rundir'], self.filep + ".ner")
			HipParticle['far_file'] = os.path.join(self.params['rundir'], self.filep + ".far")
			HipParticle['fft_file'] = os.path.join(self.params['rundir'], self.filep + ".fft")
			self.stackrundata = appiondata.ApStackRunData()
			HipParticle['stackRun'] = self.stackrundata
			HipParticle['particleNumber'] = self.particleNumber
			HipParticle['tilt'] = tsr_list[0]
			HipParticle['shift'] = tsr_list[1]
			HipParticle['resid'] = tsr_list[2]
			HipParticledata = HipParticle.query(results=1)
			if HipParticledata:
				apDisplay.printError("trying to insert a duplicate particle")
			if self.params['commit'] is True:
				HipParticle.insert()
			self.params['HipParticleID'] = HipParticle.dbid
			print "self.params['HipParticleID']",self.params['HipParticleID']
		return
	#=====================
	def start(self):
		self.writeParams()
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackpath = os.path.abspath(stackdata['path']['path']) 
		stackfile = os.path.join(stackpath, "start.hed")
		self.params['localstack'] = os.path.join(stackpath, self.timestamp+".hed")
		proccmd = "proc2d "+stackfile+" "+self.params['localstack']+" apix="+str(self.params['step'])
		if self.params['bin'] > 1:
			proccmd += " shrink=%d"%int(self.params['bin'])
		proccmd += " last="+str(self.params['numpart']-1)
		apParam.runCmd(proccmd, "EMAN", verbose=True)
		if self.params['numpart'] != apFile.numImagesInStack(self.params['localstack']):
			apDisplay.printError("Missing particles in stack")
		apXmipp.breakupStackIntoSingleFiles(self.params['localstack'], filetype="mrc")
		if self.params['prehip'] == "yes":
			if self.params['rise'] is not None:
				self.writeLLBO1()
			elif self.params['ll1'] is not None:
				self.writeLLBO2()
			elif self.params['rise'] is None and self.params['ll1'] is None:
				apDisplay.printError("You must specify either rise and twist or (1,0) and (0,1) layer lines to run preHIP")
			apDisplay.printMsg("now running s_prehip to set up input files")
			apDisplay.printMsg("Make sure the layer line/bessel order assignment is correct. If it is not, you may need to adjust some of the input variables.")
			cmd = "s_prehip"
			proc = subprocess.Popen(cmd)
			proc.wait()
		else:
			apDisplay.printMsg("now running s_hip2: Phoelix programs")
			cmd = "s_hip2"
			proc = subprocess.Popen(cmd)
			proc.wait()
			#apParam.runCmd(cmd, package="Phoelix")
			self.putFilesInStack()
			self.insertHipRunData()
			self.insertHipParamsData()
			self.insertHipIterData()
			self.insertHipParticleData()



#=====================
if __name__ == "__main__":
	hip = HipScript()
	hip.start()
