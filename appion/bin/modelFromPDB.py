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
import gzip
from apSpider import volFun

class modelFromPDB(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --pdbid=1ohg --resolution=15 --apix=1.63 --box=300 [options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-n", "--modelname", dest="name",
			help="Model name", metavar="STR")
		self.parser.add_option("-p", "--pdbid", dest="pdbid",
			help="PDB ID", metavar="STR")
		self.parser.add_option("-r", "--resolution", dest="res", type='float', default=None,
			help="Resolution of resulting model (in Angstroms)")
		self.parser.add_option("-a", "--apix", dest="apix", type='float', default=None,
			help="Pixel size of model (in Angstroms)")
		self.parser.add_option("-b", "--box", dest="box", type='int', default=None,
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
	def setOutDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['outdir'] = os.path.join(path,"models")

	#=====================
	def setNewFileName(self, unique=False):
		# set apix, box, and foldname
		self.params['name'] = self.params['pdbid']+"-"
		self.params['name'] += str(self.params['apix'])+"-"
		self.params['name'] += str(self.params['res'])+"-"
		self.params['name'] += str(self.params['box'])+".mrc"

	def fetchPDB(self):
		# retrieve pdb from web based on pdb id
		pdbid = self.params['pdbid']+'.pdb'
		# set filename if getting biological unit
		if self.params['bunit'] is True:
			pdbid=self.params['pdbid']+'.pdb1'
		url = "http://www.rcsb.org/pdb/files/%s.gz" % pdbid
		apDisplay.printMsg("retrieving pdb file: %s" %url)
		# uncompress file & save
		outfile = self.params['tmpname']+".pdb"
		data = urllib.urlretrieve(url)[0]
		g = gzip.open(data,'r').read()
		
		f=open(outfile,'w')
		f.write(g)
		f.close()
		return outfile
	
	#=====================
	def start(self):
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming pdb model: "+self.params['name'], "cyan")

		newmodelpath = os.path.join(self.params['outdir'], self.params['name'])
		
		self.params['basename']=os.path.splitext(newmodelpath)[0]
		### remove '.' from basename for spider
		self.params['tmpname'] = re.sub("\.", "_", self.params['basename'])

		### get pdb from web
		pdbfile = self.fetchPDB()

		if not os.path.exists(self.params['tmpname']+'.pdb'):
			apDisplay.printError("Could not retrieve PDB file")

		### create density from pdb
		volFun.pdb2vol(pdbfile,self.params['apix'],self.params['box'],self.params['tmpname'])
		
		if not os.path.exists(self.params['tmpname']+'.spi'):
			os.remove(self.params['tmpname']+".pdb")
			apDisplay.printError("SPIDER could not create density file")
			
		### convert spider to mrc format
		apDisplay.printMsg("converting spider file to mrc")
		emancmd='proc3d %s.spi %s.mrc apix=%f lp=%f norm' % (self.params['tmpname'], self.params['basename'],
								     self.params['apix'], self.params['res'])
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
		os.remove(self.params['tmpname']+".pdb")
		os.remove(self.params['tmpname']+".spi")

#=====================
if __name__ == "__main__":
	pdbmodel = modelFromPDB()
	pdbmodel.start()
	pdbmodel.close()

