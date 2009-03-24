#!/usr/bin/env python

#python
import sys
import os
import time
import re
import shutil
#appion
import appionScript
import apUpload
import apParam
import apFile
import apDisplay
import apDatabase
import urllib
import apEMAN
import apChimera
import apFile
import appionData
import gzip
from apSpider import volFun

class modelFromPDB(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --pdbid=1ohg --resolution=15 --apix=1.63 --box=300 [options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--modelname", dest="name",
			help="Model name", metavar="STR")
		self.parser.add_option("--pdbid", dest="pdbid",
			help="PDB ID", metavar="STR")
		self.parser.add_option("-r", "--resolution", dest="res", type='float',
			help="Resolution of resulting model (in Angstroms)")
		self.parser.add_option("-a", "--apix", dest="apix", type='float',
			help="Pixel size of model (in Angstroms)")
		self.parser.add_option("-b", "--box", dest="box", type='int',
			help="Box size of model (in Pixels)")
		self.parser.add_option("-u", "--biolunit", dest="bunit", default=False,
			action="store_true", help="Download the biological unit")

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['pdbid'] is None:
			apDisplay.printError("specify a PDB id")
		if self.params['res'] is None:
			apDisplay.printError("enter a resolution value")
		if self.params['apix'] is None:
			apDisplay.printError("specify a pixel size")
		if self.params['box'] is None:
			apDisplay.printError("specify a box size")

	#=====================
	def setRunDir(self):
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path,"models","pdb",self.params['runname'])

	#=====================
	def setNewFileName(self, unique=False):
		# set apix, box, and foldname
		self.params['name'] = self.params['pdbid']+"-"
		self.params['name'] += str(self.params['apix'])+"-"
		self.params['name'] += str(self.params['res'])+"-"
		self.params['name'] += str(self.params['box'])+".mrc"

	def fetchPDB(self, tmpname):
		# retrieve pdb from web based on pdb id
		pdbid = self.params['pdbid']+'.pdb'
		# set filename if getting biological unit
		if self.params['bunit'] is True:
			pdbid=self.params['pdbid']+'.pdb1'
		url = "http://www.rcsb.org/pdb/files/%s.gz" % pdbid
		apDisplay.printMsg("retrieving pdb file: %s" %url)
		# uncompress file & save
		outfile = tmpname+".pdb"
		data = urllib.urlretrieve(url)[0]
		g = gzip.open(data,'r').read()
		
		f=open(outfile,'w')
		f.write(g)
		f.close()
		return outfile
	
	#=====================
	def uploadDensity(self, volfile):
		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		#densq['symmetry'] = appionData.ApSymmetryData.direct_query(25)
		densq['pixelsize'] = self.params['apix']
		densq['boxsize'] = self.params['box']
		densq['lowpass'] = self.params['res']
		#densq['highpass'] = self.params['highpasspart']
		#densq['mask'] = self.params['radius']
		densq['description'] = "PDB density from id="+str(self.params['pdbid'])
		densq['resolution'] = self.params['res']
		densq['session'] = self.sessiondata
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['pdbid'] = self.params['pdbid']
		if self.params['commit'] is True:
			densq.insert()
		return 


	#=====================
	def start(self):
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming pdb model: "+self.params['name'], "cyan")

		newmodelpath = os.path.join(self.params['rundir'], self.params['name'])
		mrcname = newmodelpath	

		self.params['basename']=os.path.splitext(newmodelpath)[0]
		### remove '.' from basename for spider
		tmpname = re.sub("\.", "_", self.params['basename'])
		tmpdir = os.path.dirname(tmpname)
		tmpname = os.path.join(self.params['rundir'],tmpname)
		### get pdb from web
		pdbfile = self.fetchPDB(tmpname)

		if not os.path.exists(pdbfile):
			apDisplay.printError("Could not retrieve PDB file")

		### create density from pdb
		volFun.pdb2vol(pdbfile,self.params['apix'],self.params['box'], tmpname)
		
		if not os.path.exists(tmpname+".spi"):
			apFile.removeFile(tmpname+".pdb")
			apDisplay.printError("SPIDER could not create density file: "+tmpname+".spi")

		### convert spider to mrc format
		apDisplay.printMsg("converting spider file to mrc")
		emancmd='proc3d %s.spi %s apix=%f lp=%f norm' % (tmpname, mrcname,
			self.params['apix'], self.params['res'])
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
		apFile.removeFile(tmpname+".pdb")
		apFile.removeFile(tmpname+".spi")

		### chimera imaging
		apChimera.renderSnapshots(mrcname, contour=1.5, zoom=1.0, sym='c1')
		apChimera.renderAnimation(mrcname, contour=1.5, zoom=1.0, sym='c1')

		### upload it
		self.uploadDensity(mrcname)


#=====================
if __name__ == "__main__":
	pdbmodel = modelFromPDB()
	pdbmodel.start()
	pdbmodel.close()

