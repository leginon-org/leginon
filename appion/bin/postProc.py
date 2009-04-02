#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

import os
import sys
import re
import appionScript

import apParam
import apDisplay
import apEMAN
import apVolume
import apFile
import apUpload
import apDatabase
import apChimera

#===========================
def insert3dDensity(params):
	apDisplay.printMsg("commiting density to database")
	symdata=appionData.ApSymmetryData.direct_query(params['sym'])
	if not symdata:
		apDisplay.printError("no symmetry associated with this id\n")		
	params['syminfo'] = symdata
	modq=appionData.Ap3dDensityData()
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	modq['session'] = sessiondata
	modq['path'] = appionData.ApPathData(path=os.path.abspath(params['rundir']))
	modq['name'] = params['name']
	modq['resolution'] = params['res']
	modq['symmetry'] = symdata
	modq['pixelsize'] = params['apix']
	modq['boxsize'] = params['box']
	modq['description'] = params['description']
	modq['lowpass'] = params['lp']
	modq['highpass'] = params['hp']
	modq['mask'] = params['mask']
	modq['imask'] = params['imask']
	if params['reconid'] is not None:
		iterdata = appionData.ApRefinementData.direct_query(params['reconid'])
		if not iterdata:
			apDisplay.printError("this iteration was not found in the database\n")
		modq['iterid'] = iterdata
	### if ampfile specified
	if params['ampfile'] is not None:
		(ampdir, ampname) = os.path.split(params['ampfile'])
		modq['ampPath'] = appionData.ApPathData(path=os.path.abspath(ampdir))
		modq['ampName'] = ampname
		modq['maxfilt'] = params['maxfilt']
	modq['handflip'] = params['yflip']
	modq['norm'] = params['norm']
	modq['invert'] = params['invert']
	modq['hidden'] = False
	filepath = os.path.join(params['rundir'], params['name'])
	modq['md5sum'] = apFile.md5sumfile(filepath)
	if params['commit'] is True:
		modq.insert()
	else:
		apDisplay.printWarning("not commiting model to database")

#=====================
#=====================
class PostProcScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with density (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-f", "--file", dest="file",
			help="Filename of the density", metavar="FILE")
		self.parser.add_option("--amp", dest="ampfile",
			help="Filename of the amplitude file", metavar="FILE")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Density pixel size in Angstroms per pixel", metavar="FLOAT")
		self.parser.add_option("--lp", dest="lp", type="float",
			help="Low pass filter value (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--hp", dest="hp", type="float",
			help="High pass filter value (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--mask", dest="mask", type="float",
			help="Radius of outer mask (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--imask", dest="imask", type="float",
			help="Radius of inner mask (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--maxfilt", dest="maxfilt", type="float",
			help="filter limit to which data will adjusted (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--res", dest="res", type="float",
			help="resolution of the reconstruction (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("-y", "--yflip", dest="yflip", default=False,
			action="store_true", help="Flip the handedness of the density")
		self.parser.add_option("-i", "--invert", dest="invert", default=False,
			action="store_true", help="Invert the density values")
		self.parser.add_option("--viper", dest="viper", default=False,
			action="store_true", help="Rotate icosahedral densities from Eman orientation to Viper orientation")
		self.parser.add_option("--norm", dest="norm", default=False,
			action="store_true", help="Normalize the final density such that mean=0, sigma=1")
		self.parser.add_option("--sym", "--symm", "--symmetry", dest="sym", type="int",
			help="Symmetry id in the database", metavar="INT")
		self.parser.add_option("--reconid", dest="reconid",
			help="RefinementData Id for this iteration (not the recon id)", metavar="INT")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.5,
			help="Zoom factor for snapshot rendering (1.5 by default)", metavar="FLOAT")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=1.5,
			help="Sigma level at which snapshot of density will be contoured (1.5 by default)", metavar="FLOAT")
		
		return 

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a sessionID")
		if self.params['apix'] is None:
			apDisplay.printError("enter a pixel size")
		if self.params['sym'] is None:
			apDisplay.printError("enter a symmetry ID")
		if self.params['res'] is None:
			apDisplay.printError("enter a resolution")
		if self.params['file'] is None:
			apDisplay.printError("enter a file name for processing")
		self.params['filepath'] = os.path.dirname(os.path.abspath(self.params['file']))
		self.params['filename'] = os.path.basename(self.params['file'])
		if self.params['ampfile'] is not None:
			### ampfile was requested
			if self.params['maxfilt'] is None:
				apDisplay.printError("if performing amplitude correction, enter a filter limit")
			self.params['ampfile'] = self.locateAmpFile()
		return

	#=====================
	def setRunDir(self):
		self.params['rundir'] = os.path.join(self.params['filepath'], "postproc",self.params['runname'])
		return

	#=====================
	def locateAmpFile(self):
		### may be ready to use as is
		ampabspath = os.path.abspath(self.params['ampfile'])
		if os.path.isfile(ampabspath):
			return ampabspath
		### try to find it in the appion directory
		appiondir = apParam.getAppionDirectory()
		ampabspath = os.path.join(appiondir, "lib", os.path.basename(self.params['ampfile']))
		if os.path.isfile(ampabspath):
			return ampabspath
		### can't find it
		apDisplay.printError("Could not locate amplitude file: %s" % (self.params['ampfile'],))

	#=====================
	def start(self):
		### start the outfile name
		fileroot = os.path.splitext(self.params['filename'])[0]
		fileroot += "-"+self.timestamp

		if self.params['ampfile'] is not None:
			### run amplitude correction
			self.params['box'] = apVolume.getModelDimensions(self.params['file'])
			spifile = apVolume.MRCtoSPI(self.params['file'], self.params['rundir'])
			tmpfile = apVolume.createAmpcorBatchFile(spifile, self.params)
			apVolume.runAmpcor()

			### check if spider was successful
			fileroot += ".amp"
			if not os.path.isfile(tmpfile) :
				apDisplay.printError("amplitude correction failed")
				
			### convert amplitude corrected file back to mrc
			fileroot += ".amp"
			emancmd = "proc3d "+tmpfile+" "
		else :
			### just run proc3d
			emancmd = "proc3d "+self.params['file']+" "

		emancmd+="apix=%s " %self.params['apix']
		if self.params['lp'] is not None:
			fileroot += (".lp%d" % ( int(self.params['lp']), ))
			emancmd += "lp=%d " %self.params['lp']

		if self.params['yflip'] is True:
			fileroot += ".yflip"
			emancmd +="yflip "

		if self.params['invert'] is True:
			fileroot += ".inv"
			emancmd +="mult=-1 "

		if self.params['viper'] is True:
			fileroot += ".vip"
			emancmd +="icos5fTo2f "
			
		if self.params['mask'] is not None:
			# convert ang to pixels
			maskpix=int(self.params['mask']/self.params['apix'])
			fileroot += (".m%d" % ( int(self.params['mask']), ))
			emancmd += "mask=%d " %maskpix
			self.params['mask'] = maskpix

		if self.params['imask'] is not None:
			# convert ang to pixels
			maskpix=int(self.params['imask']/self.params['apix'])
			fileroot += (".im%d" % ( int(self.params['imask']), ))
			emancmd += "imask=%d " %maskpix
			self.params['imask'] = maskpix
			
		if self.params['norm'] is True:
			fileroot += ".norm"
			emancmd += "norm=0,1 "
			
		### add output filename to emancmd string
		fileroot += ".mrc"
		self.params['name'] = fileroot
		
		outfile = os.path.join(self.params['rundir'], fileroot)
		emancmd = re.sub(" apix=",(" %s apix=" % outfile), emancmd)

		apEMAN.executeEmanCmd(emancmd)

		if self.params['description'] is None:
			self.params['description'] = "Volume from recon with amplitude adjustment"
			
		### clean up files created during amp correction
		if self.params['ampfile'] is not None:
			apFile.removeFile(spifile)
			apFile.removeFile(tmpfile)

		## see if density is in the database
		md5 = apFile.md5sumfile(outfile)
		if apDatabase.isModelInDB(md5):
			### they are the same and its in the database already
			apDisplay.printError("3d density with md5sum '"+md5+"' already exists in the DB!")

		if self.params['commit'] is True:
			insert3dDensity(self.params)
			### render chimera images of model
			symdata  = apUpload.getSymmetryData(self.params['sym'])
			symmetry = symdata['eman_name']

			apChimera.filterAndChimera(outfile, res=self.params['res'], apix=self.params['apix'], box=self.params['box'], 
				chimtype='snapshot', contour=self.params['contour'], zoom=self.params['zoom'], sym=symmetry)

#=====================
#=====================
if __name__ == '__main__':
	postProc = PostProcScript()
	postProc.start()
	postProc.close()

	
