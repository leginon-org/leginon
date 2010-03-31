#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
import gzip
import shutil
import urllib
#appion
from appionlib import appionScript
from appionlib import apParam
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apSymmetry
from appionlib import appiondata
from appionlib import apChimera
from appionlib import apEMAN
from appionlib import apVolume


class modelFromEMDB(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --emdbid=1122 --lowpass=15 --sym=c1 [options]")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--modelname", dest="name",
			help="Model name", metavar="STR")
		self.parser.add_option("-e", "--emdbid", dest="emdbid", type="int",
			help="EMDB ID", metavar="#")
		self.parser.add_option("-l", "--lowpass", dest="lowpass", type='float',
			help="Low pass filter (in Angstroms)")
		self.parser.add_option("--sym", "--symm", "--symmetry", dest="symmetry",
			help="Symmetry id in the database", metavar="INT")

		self.parser.add_option("--viper2eman", dest="viper2eman", default=False,
			action="store_true", help="Convert VIPER orientation to EMAN orientation")

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['emdbid'] is None:
			apDisplay.printError("specify a emdb id")
		if self.params['symmetry'] is None:
			#apSymmetry.printSymmetries()
			apDisplay.printError("Enter a symmetry group, e.g. --symm=c1")
		self.params['symdata'] = apSymmetry.findSymmetry(self.params['symmetry'])

	#=====================
	def setRunDir(self):
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path, "models/emdb", self.params['runname'])

	#=====================
	def setFileName(self):
		if self.params['name'] is None:
			### assign provided name
			basename = "emdb%s-%s"%(self.params['emdbid'], self.timestamp)
		else:
			### clean up provided name
			basename = os.path.splitext(os.path.basename(self.params['name']))[0]
		self.params['name'] = os.path.join(self.params['rundir'], basename)
		apDisplay.printColor("Naming EMDB model: "+self.params['name'], "cyan")
		return

	#=====================
	def getXMLInfoFromEMDB(self, emdbid):
		# retrieve emdb from web based on emdb id
		xmlurl = ( "ftp://ftp.ebi.ac.uk/pub/databases/emdb/structures/EMD-%d/header/emd-%d.xml"
			%(emdbid, emdbid) )

		apDisplay.printMsg("retrieving emdb XML file: "+xmlurl)
		# uncompress file & save
		data = urllib.urlopen(xmlurl)
		goodlines = []
		massline = None
		for line in data:
			sline = line.strip()
			if re.search("pixel", sline):
				goodlines.append(sline)
			if re.search("molWtTheo", sline):
				massline = sline

		### parse pixel info lines
		for line in goodlines:
			a = re.search(" units=\"A\">([0-9\.]+)<\/pixel", line)
			if a:
				apix = float(a.groups()[0])
				break
		apDisplay.printMsg("file has a pixel size of %.3f A/pix"%(apix))
		if apix < 0.3:
			apDisplay.printError("could not get appropriate pixel size")
		self.apix = apix
		
		# try and get the mass
		if massline is not None:
			#print "Mass: ", massline
			b = re.search(" units=\"(.*)\">([0-9\.]+)<\/", massline)
			if b:
				unit = b.groups()[0].lower()
				mass = float(b.groups()[1])
				#print mass, unit
				if unit == "mda":
					mass *= 1000
				elif unit == "da":
					mass /= 1000
				self.mass = mass
			apDisplay.printMsg("file has a mass of %.1f kDa"%(self.mass))

		return

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
		densq = appiondata.Ap3dDensityData()
		densq['path'] = appiondata.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = self.params['symdata']
		#densq['symmetry'] = appiondata.ApSymmetryData.direct_query(25)
		densq['pixelsize'] = self.apix
		densq['mass'] = self.mass
		densq['boxsize'] = apFile.getBoxSize(volfile)[0]
		densq['lowpass'] = self.params['lowpass']
		#densq['highpass'] = self.params['highpasspart']
		#densq['mask'] = self.params['radius']
		densq['description'] = "EMDB id %d density"%(self.params['emdbid'])
		if self.mass is not None:
			densq['description'] += " with mass of %d kDa"
		densq['resolution'] = self.params['lowpass']
		densq['session'] = self.sessiondata
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['emdbid'] = self.params['emdbid']
		if self.params['commit'] is True:
			densq.insert()
		return

	#=====================
	def start(self):
		self.apix = None
		self.mass = None
		self.setFileName()

		mrcname = self.params['name']+".mrc"
		ccp4name = self.params['name']+".ccp4"

		### get emdb from web
		emdbfile = self.fetchEMDB(self.params['emdbid'], ccp4name)

		### create density from emdb
		self.getXMLInfoFromEMDB(self.params['emdbid'])
		emancmd = ("proc3d "+ccp4name+" "+mrcname)
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
		apFile.removeFile(ccp4name)

		if self.params['viper2eman'] is True:
			apVolume.viper2eman(mrcname, mrcname, apix=self.apix)

		### lowpass filter, do both atan2 and Gaussian filter to sum up to requested lowpass
		### total lowpass = sqrt( lp1^2 + lp2^2 )
		lp = self.params['lowpass']/math.sqrt(2.0)
		emancmd = ("proc3d "+mrcname+" "+mrcname+
			(" apix=%.3f tlp=%.2f lp=%.2f origin=0,0,0 norm=0,1 "%(self.apix, lp, lp)))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

		if self.mass is not None:
			apChimera.setVolumeMass(mrcname, apix=self.apix, mass=self.mass)

		### chimera imaging
		apChimera.renderSnapshots(mrcname, contour=1.0, zoom=1.0, sym=self.params['symdata']['eman_name'])

		### upload it
		self.uploadDensity(mrcname)


#=====================
if __name__ == "__main__":
	emdbmodel = modelFromEMDB()
	emdbmodel.start()
	emdbmodel.close()


