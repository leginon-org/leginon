#!/usr/bin/env python

#python
import sys
import os
import time
import re
import shutil
import gzip
import urllib
#appion
import appionScript
import apParam
import apFile
import apDisplay
import apDatabase
import apEMAN
import apChimera
import apFile
import appiondata
import apSymmetry

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
		self.parser.add_option("--pdbfile", dest="pdbfile",
			help="PDB file", metavar="STR")
		self.parser.add_option("-r", "--resolution", dest="res", type='float',
			help="Resolution of resulting model (in Angstroms)")
		self.parser.add_option("-a", "--apix", dest="apix", type='float',
			help="Pixel size of model (in Angstroms)")
		self.parser.add_option("-b", "--box", dest="box", type='int',
			help="Box size of model (in Pixels)")
		self.parser.add_option("-u", "--biolunit", dest="bunit", default=False,
			action="store_true", help="Download the biological unit")
		self.parser.add_option("--sym", "--symm", "--symmetry", dest="symmetry",
			help="Symmetry id in the database", metavar="INT")

		self.methods = ( "eman", "spider" )
		self.parser.add_option("--method", dest="method",
			help="Method for PDB to MRC conversion: eman or spider", metavar="METHOD",
			type="choice", choices=self.methods, default="spider" )

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['pdbid'] is None and self.params['pdbfile'] is None:
			apDisplay.printError("specify a PDB id or PDB file")
		if self.params['res'] is None:
			apDisplay.printError("enter a resolution value")
		if self.params['apix'] is None:
			apDisplay.printError("specify a pixel size")
		if self.params['box'] is None:
			apDisplay.printError("specify a box size")
		if self.params['symmetry'] is None:
			apDisplay.printWarning("No symmetry specified using 'c1'")
			self.params['symmetry'] = 'c1'
		self.params['symdata'] = apSymmetry.findSymmetry(self.params['symmetry'])

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
		if self.params['pdbid'] is not None:
			self.params['name'] = self.params['pdbid']+"-"
		else:
			self.params['name'] = os.path.splitext(self.params['pdbfile'])[0]+"-"
		self.params['name'] += str(self.params['apix'])+"-"
		self.params['name'] += str(self.params['res'])+"-"
		self.params['name'] += str(self.params['box'])+".mrc"

	#=====================
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
		densq = appiondata.Ap3dDensityData()
		densq['path'] = appiondata.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = self.params['symdata']
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
		tmpname = os.path.join(self.params['rundir'], tmpname)
		### get pdb from web
		if self.params['pdbid'] is not None:
			pdbfile = self.fetchPDB(tmpname)
		else:
			pdbfile = tmpname+".pdb"
			shutil.copy(self.params['pdbfile'], pdbfile)


		if not os.path.exists(pdbfile):
			apDisplay.printError("Could not retrieve PDB file")

		### create density from pdb
		if self.params['method'] == 'spider':
			volFun.pdb2vol(pdbfile, self.params['apix'], self.params['box'], tmpname)
			if not os.path.isfile(tmpname+".spi"):
				apFile.removeFile(tmpname+".pdb")
				apDisplay.printError("SPIDER could not create density file: "+tmpname+".spi")
			### convert spider to mrc format
			apDisplay.printMsg("converting spider file to mrc")
			emancmd='proc3d %s.spi %s apix=%.4f lp=%.2f norm' % (tmpname, mrcname,
				self.params['apix'], self.params['res'])
			apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
			apFile.removeFile(tmpname+".pdb")
			apFile.removeFile(tmpname+".spi")
		elif self.params['method'] == 'eman':
			emancmd='pdb2mrc %s %s apix=%.4f lp=%.2f box=%d norm' % (pdbfile, mrcname,
				self.params['apix'], self.params['res'], self.params['box'])

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


