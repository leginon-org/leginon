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
import appionData
import apRecon
import urllib
import apEMAN
import gzip

class modelFromEMDB(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --emdbid=1122 --resolution=15 --apix=1.63 --box=300 [options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--modelname", dest="name",
			help="Model name", metavar="STR")
		self.parser.add_option("-e", "--emdbid", dest="emdbid", type="int",
			help="EMDB ID", metavar="#")
		self.parser.add_option("-r", "--resolution", dest="res", type='float',
			help="Resolution of resulting model (in Angstroms)")
		self.parser.add_option("-a", "--apix", dest="apix", type='float',
			help="Pixel size of model (in Angstroms)")
		self.parser.add_option("-b", "--box", dest="box", type='int',
			help="Box size of model (in Pixels)")

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['emdbid'] is None:
			apDisplay.printError("specify a emdb id")
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
		self.params['rundir'] = os.path.join(path,"models","emdb",self.params['runname'])

	#=====================
	def setNewFileName(self, unique=False):
		# set apix, box, and foldname
		self.params['name'] = str(self.params['emdbid'])+"-"
		self.params['name'] += str(self.params['apix'])+"-"
		self.params['name'] += str(self.params['res'])+"-"
		self.params['name'] += str(self.params['box'])+".mrc"

	#=====================
	def getOriginalApixFromEMDB(self, emdbid):
		# retrieve emdb from web based on emdb id
		xmlurl = ( "ftp://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-%d/header/emd-%d.xml"
			%(emdbid, emdbid) )

		apDisplay.printMsg("retrieving emdb apix: "+xmlurl)
		# uncompress file & save
		data = urllib.urlopen(xmlurl)
		goodlines = []
		for line in data:
			sline = line.strip()
			if re.search("pixel", sline):
				goodlines.append(sline)
		for line in goodlines:
			a = re.search(" units=\"A\">([0-9\.]+)<\/pixel", line)
			if a:
				apix = float(a.groups()[0])
				break
		apDisplay.printMsg("file has a pixel size of "+str(round(apix,2))+" A/pix")
		if apix < 0.3:
			apDisplay.printError("could not get appropriate pixel size")
		return apix

	#=====================
	def fetchEMDB(self, emdbid, outfile):
		# retrieve emdb from web based on emdb id
		mapurl = ( "ftp://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-%d/map/emd_%d.map.gz"
			%(emdbid, emdbid) )
		apDisplay.printMsg("retrieving emdb file: "+mapurl)
		# uncompress file & save
		data = urllib.urlretrieve(mapurl)[0]
		g = gzip.open(data,'r').read()
		f=open(outfile,'w')
		f.write(g)
		f.close()
		if not os.path.exists(outfile):
			apDisplay.printError("Could not retrieve EMDB file")
		size = apFile.fileSize(outfile)
		apDisplay.printMsg("downloaded file of size "+str(round(size/1024.0,1))+"k")

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
		densq['description'] = "EMDB density from id="+str(self.params['emdbid'])
		densq['resolution'] = self.params['res']
		densq['session'] = self.sessiondata
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['emdbid'] = self.params['emdbid']
		if self.params['commit'] is True:
			densq.insert()
		return 

	#=====================
	def start(self):
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming emdb model: "+self.params['name'], "cyan")

		newmodelpath = os.path.join(self.params['rundir'], self.params['name'])
		
		ccp4name = newmodelpath+".ccp4"
		mrcname = newmodelpath+".mrc"

		### get emdb from web
		emdbfile = self.fetchEMDB(self.params['emdbid'], ccp4name)

		### create density from emdb
		origapix = self.getOriginalApixFromEMDB(self.params['emdbid'])
		scale = origapix/self.params['apix']
		emancmd = ("proc3d "+ccp4name+" "+mrcname+
			(" scale=%f clip=%d,%d "%(scale, self.params['box'], self.params['box'])))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
		apFile.removeFile(ccp4name)

		### lowpass filter
		emancmd = ("proc3d "+mrcname+" "+mrcname+
			(" apix=%f lp=%f origin=0,0,0 norm "%(self.params['apix'], self.params['res'])))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

		### chimera imaging
		apRecon.renderSnapshots(mrcname, self.params['res'], None, 
			1.5, 1.0, self.params['apix'], 'c1', self.params['box'], False)

		### upload it
		self.uploadDensity(mrcname)


#=====================
if __name__ == "__main__":
	emdbmodel = modelFromEMDB()
	emdbmodel.start()
	emdbmodel.close()

