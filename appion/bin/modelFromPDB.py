#!/usr/bin/env python

#python
import re
import os
import sys
import time
import gzip
import math
import numpy
import shutil
import urllib
import subprocess
#appion
from appionlib import appionScript
from appionlib import apParam
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apEMAN
from appionlib import apChimera
from appionlib import apFile
from appionlib import appiondata
from appionlib import apSymmetry
from appionlib import apVolume
from appionlib import apPrimeFactor

from appionlib.apSpider import volFun

class modelFromPDB(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --pdbid=1ohg --lowpass=30 --apix=1.63 --box=300 [options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--modelname", dest="name",
			help="Model name", metavar="STR")
		self.parser.add_option("--pdbid", dest="pdbid",
			help="PDB ID", metavar="STR")
		self.parser.add_option("--pdbfile", dest="pdbfile",
			help="PDB file", metavar="STR")
		self.parser.add_option("--res", "--lowpass", dest="lowpass", type='float',
			help="Lowpass filter of PDB model (in Angstroms)")
		self.parser.add_option("--apix", dest="apix", type='float',
			help="Pixel size of model (in Angstroms)")
		self.parser.add_option("--box", "--boxsize", dest="boxsize", type='int',
			help="Box size of model (in Pixels)")
		self.parser.add_option("--mass", dest="mass", type='int',
			help="Mass of model (in kDa)")
		self.parser.add_option("--bunit", "--biolunit", dest="bunit", default=False,
			action="store_true", help="Download the biological unit")
		self.parser.add_option("--sym", "--symm", "--symmetry", dest="symmetry",
			help="Symmetry id in the database", metavar="INT")

		self.parser.add_option("--viper2eman", dest="viper2eman", default=False,
			action="store_true", help="Convert VIPER orientation to EMAN orientation")

		self.methods = ( "eman", "spider" )
		self.parser.add_option("--method", dest="method",
			help="Method for PDB to MRC conversion: eman or spider", metavar="METHOD",
			type="choice", choices=self.methods, default="eman" )

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['pdbid'] is None and self.params['pdbfile'] is None:
			apDisplay.printError("Specify a PDB id or PDB file")
		if self.params['pdbid'] is not None and self.params['pdbfile'] is not None:
			apDisplay.printError("Specify only one of PDB id or PDB file")
		if self.params['pdbfile'] is not None and not os.path.isfile(self.params['pdbfile']):
			apDisplay.printError("PDB file does not exist")
		### PDB is case-insensitve, so make all caps for consistency
		if self.params['pdbid'] is not None:
			self.params['pdbid'] = self.params['pdbid'].upper()

		if self.params['lowpass'] is None:
			apDisplay.printError("Enter a lowpass value")
		if self.params['apix'] is None:
			apDisplay.printError("Specify a pixel size")
		if self.params['lowpass'] < 1.5*self.params['apix']:
			apDisplay.printWarning("Lowpass is less than pixelsize, overriding lp=1.5*apix")
			self.params['lowpass'] = 1.5*self.params['apix']
		if self.params['symmetry'] is None and self.params['pdbfile'] is not None:
			apDisplay.printError("Please specify symmetry group")
		elif self.params['symmetry'] is None:
			apDisplay.printWarning("No symmetry specified using 'c1'")
			self.params['symmetry'] = 'c1'
		self.params['symdata'] = apSymmetry.findSymmetry(self.params['symmetry'])

	#=====================
	def setRunDir(self):
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path, "models/pdb",self.params['runname'])

	#=====================
	def setFileName(self, unique=False):
		if self.params['name'] is None:
			### assign provided name
			if self.params['pdbid'] is not None:
				basename = "pdb%s-%s"%(self.params['pdbid'], self.timestamp)
			else:
				filebase = os.path.splitext(os.path.basename(self.params['pdbfile']))[0]
				basename = "%s-%s"%(filebase, self.timestamp)
		else:
			### clean up provided name
			basename = os.path.splitext(os.path.basename(self.params['name']))[0]
		self.params['name'] = os.path.join(self.params['rundir'], basename)
		apDisplay.printColor("Naming PDB model: "+self.params['name'], "cyan")
		return

	#=====================
	def getPDBMass(self, pdbfile):
		"""
		This is a hack to use pdb2mrc to get the mass
		Probably a better way would be to read PDB directly
		"""
		### res < apix means it will crash
		emancmd = "pdb2mrc %s /dev/null apix=10 res=5 allmdl"%(pdbfile)
		proc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE)
		proc.wait()
		for line in proc.stdout:
			if 'Total Mass' in line:
				sline = line.strip()
				match = re.search('= ([0-9\.]*) Da', sline)
				if match and match.groups():
					### convert mass to kDa
					self.params['mass'] = float(match.groups()[0])/1000.0
		return

	#=====================
	def determineBoxSize(self, pdbfile):
		"""
		Measure the size of the particle and determine a boxsize
		"""
		if self.params['boxsize'] is not None:
			return

		limitsize = apVolume.getPDBDimensions(pdbfile)

		### select double limit for resizing purposes
		boxsize = int(2*limitsize/self.params['apix'])
		while not apPrimeFactor.isGoodPrime(boxsize):
			boxsize += 1

		apDisplay.printMsg("Selected boxsize of %d pixels to bound particle"%(boxsize))
		self.params['boxsize'] = boxsize

	#=====================
	def fetchPDB(self):
		# retrieve pdb from web based on pdb id
		# set filename if getting biological unit
		if self.params['bunit'] is True:
			url = ("http://www.rcsb.org/pdb/files/%s.pdb1.gz"
				%(self.params['pdbid']))
		else:
			url = ("http://www.rcsb.org/pdb/files/%s.pdb.gz"
				%(self.params['pdbid']))
		apDisplay.printMsg("retrieving pdb file: %s" %url)
		pdbfile = self.params['name']+".pdb"

		### download data to memory
		data = urllib.urlretrieve(url)[0]
		### uncompress data
		g = gzip.open(data, 'r').read()
		### dump data to file
		f = open(pdbfile, 'w')
		f.write(g)
		### close up
		f.close()

		return pdbfile

	#=====================
	def fetchPDBXML(self):
		# retrieve pdb XML from web based on pdb id
		url = ("http://www.rcsb.org/pdb/files/%s.xml.gz"
			%(self.params['pdbid']))
		apDisplay.printMsg("retrieving pdb file: %s" %url)

		# uncompress file & save
		xmlfile = self.params['name']+".xml"
		data = urllib.urlretrieve(url)[0]
		g = gzip.open(data,'r').read()
		f = open(xmlfile,'w')
		f.write(g)
		f.close()

		return xmlfile

	#=====================
	def uploadDensity(self, volfile):
		### insert 3d volume density
		densq = appiondata.Ap3dDensityData()
		densq['path'] = appiondata.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = self.params['symdata']
		densq['pixelsize'] = self.params['apix']
		densq['mass'] = self.params['mass']
		densq['boxsize'] = self.params['boxsize']
		densq['lowpass'] = self.params['lowpass']
		#densq['highpass'] = self.params['highpasspart']
		#densq['mask'] = self.params['radius']
		densq['description'] = "PDB id %s density"%(self.params['pdbid'])
		if self.params['mass'] is not None:
			densq['description'] += " with mass of %d kDa"%(self.params['mass'])
		densq['resolution'] = self.params['lowpass']
		densq['session'] = self.sessiondata
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['pdbid'] = self.params['pdbid']
		if self.params['commit'] is True:
			densq.insert()
		return

	#=====================
	def removeModelFlags(self, pdbfile):
		"""
		remove any model flags from PDB
		so all subunits are convert to MRC
		"""
		newpdbfile = self.params['name']+"-nomdl.pdb"
		f = open(pdbfile, "r")
		g = open(newpdbfile, "w")
		for line in f:
			if not (line.startswith("MODEL  ") or line.startswith("ENDMDL")):
				g.write(line)
		f.close()
		g.close()
		return newpdbfile

	#=====================
	def convertPDBtoMRC(self, pdbfile):
		### create density from pdb
		spidername = self.params['name']+".spi"
		mrcname = self.params['name']+".mrc"

		if self.params['method'] == 'spider':
			if self.params['bunit'] is True:
				pdbfile = self.removeModelFlags(pdbfile)
			volFun.pdb2vol(pdbfile, self.params['apix'], self.params['boxsize'], spidername)
			if not os.path.isfile(spidername):
				apDisplay.printError("SPIDER did not create density file: "+spidername)
			### convert spider to mrc format
			apDisplay.printMsg("converting spider file to mrc")
			emancmd='proc3d %s %s apix=%.4f lp=%.2f norm=0,1 origin=0,0,0' % (spidername, mrcname,
				self.params['apix'], self.params['lowpass'])
			apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
			apFile.removeFile(spidername)

		elif self.params['method'] == 'eman':
			mult = 1.0
			### use resolution of mult*apix, because this is slow and lowpass is fast
			emancmd='pdb2mrc %s %s apix=%.4f res=%.2f box=%d center allmdl' % (pdbfile, mrcname,
				self.params['apix'], mult*self.params['apix'], self.params['boxsize'])
			apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
			### lowpass to desired resolution minus the res factor specified
			lp = math.sqrt(self.params['lowpass']**2 - (mult*self.params['apix'])**2)
			emancmd='proc3d %s %s apix=%.4f lp=%.2f norm=0,1 origin=0,0,0' % (mrcname, mrcname,
				self.params['apix'], lp)
			apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

		if self.params['viper2eman'] is True:
			apVolume.viper2eman(mrcname, mrcname, apix=self.params['apix'])

		return mrcname

	#=====================
	def start(self):
		self.setFileName()

		### get pdb from web
		if self.params['pdbid'] is not None:
			pdbfile = self.fetchPDB()
		else:
			pdbfile = self.params['name']+".pdb"
			shutil.copy(self.params['pdbfile'], pdbfile)

		if not os.path.exists(pdbfile):
			apDisplay.printError("Could not retrieve/find PDB file")

		### get mass of PDB structure
		if self.params['mass'] is None:
			self.getPDBMass(pdbfile)

		if self.params['boxsize'] is None:
			self.determineBoxSize(pdbfile)

		### create density from pdb
		mrcname = self.convertPDBtoMRC(pdbfile)
		if not os.path.isfile(mrcname):
			apDisplay.printError("could not create density file: "+mrcname)

		### chimera imaging
		apChimera.renderSnapshots(mrcname, contour=1.5, zoom=1.0, sym=self.params['symdata']['eman_name'])

		### upload it
		self.uploadDensity(mrcname)


#=====================
if __name__ == "__main__":
	pdbmodel = modelFromPDB()
	pdbmodel.start()
	pdbmodel.close()


