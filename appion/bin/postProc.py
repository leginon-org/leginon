#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

import os
import apDB
import sys
import re
import appionScript

import apParam
import apDisplay
import apEMAN
import apVolume
import apFile


#=====================
#=====================
class PostProcScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
			+"[options]")
		self.parser.add_option("-f", "--file", dest="file",
			help="Filename of the density", metavar="FILE")
		self.parser.add_option("--amp", dest="ampfile",
			help="Filename of the amplitude file", metavar="FILE")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Density pixel size in Angstroms per pixel", metavar="FLOAT")
		self.parser.add_option("--lp", dest="lp", type="float",
			help="Low pass filter value (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--mask", dest="mask", type="float",
			help="Radius of outer mask (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--imask", dest="imask", type="float",
			help="Radius of inner mask (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--maxfilt", dest="maxfilt", type="float",
			help="filter limit to which data will adjusted (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to which output file will be saved", metavar="PATH")
		self.parser.add_option("-y", "--yflip", dest="yflip", default=False,
			action="store_true", help="Flip the handedness of the density")
		self.parser.add_option("-i", "--invert", dest="invert", default=False,
			action="store_true", help="Invert the density values")
		self.parser.add_option("--viper", dest="viper", default=False,
			action="store_true", help="Rotate icosahedral densities from Eman orientation to Viper orientation")
		self.parser.add_option("--norm", dest="norm", default=False,
			action="store_true", help="Normalize the final density such that mean=0, sigma=1")
		# no commit self.params yet
		#self.parser.add_option("--commit", dest="commit", default=True,
		#	action="store_true", help="Commit template to database")
		#self.parser.add_option("--no-commit", dest="commit", default=True,
		#	action="store_false", help="Do not commit template to database")
		return 

	#=====================
	def checkConflicts(self):
		if self.params['apix'] is None:
			apDisplay.printError("enter a pixel size")
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
	def setOutDir(self):
		self.params['outdir'] = os.path.join(self.params['filepath'], "postproc")
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
		outfile = os.path.join(self.params['outdir'], fileroot)

		if self.params['ampfile'] is not None:
			### run amplitude correction
			self.params['box'] = apVolume.getModelDimensions(self.params['file'])
			spifile = apVolume.MRCtoSPI(self.params['file'], self.params['outdir'])
			tmpfile = apVolume.createAmpcorBatchFile(spifile, self.params)
			apVolume.runAmpcor()

			### convert amplitude corrected file back to mrc
			outfile += ".amp"
			emancmd = "proc3d "+tmpfile+" "
		else :
			### just run proc3d
			emancmd = "proc3d "+self.params['file']+" "

		emancmd+="apix=%s " %self.params['apix']
		if self.params['lp'] is not None:
			outfile += (".lp%d" % ( int(self.params['lp']), ))
			emancmd += "lp=%d " %self.params['lp']

		if self.params['yflip'] is True:
			outfile += ".yflip"
			emancmd +="yflip "

		if self.params['invert'] is True:
			outfile += ".inv"
			emancmd +="invert "

		if self.params['viper'] is True:
			outfile += ".vip"
			emancmd +="icos5fTo2f "
			
		if self.params['mask'] is not None:
			# convert ang to pixels
			maskpix=int(self.params['mask']/self.params['apix'])
			outfile += (".m%d" % ( int(self.params['mask']), ))
			emancmd += "mask=%d " %maskpix

		if self.params['imask'] is not None:
			# convert ang to pixels
			maskpix=int(self.params['imask']/self.params['apix'])
			outfile += (".im%d" % ( int(self.params['imask']), ))
			emancmd += "imask=%d " %maskpix
			
		if self.params['norm'] is True:
			outfile += ".norm"
			emancmd += "norm=0,1 "
			
		### add output filename to emancmd string
		outfile += ".mrc"
		emancmd = re.sub(" apix=",(" %s apix=" % outfile), emancmd)

		apEMAN.executeEmanCmd(emancmd)

		### clean up files created during amp correction
		if self.params['ampfile'] is not None:
			apFile.removeFile(spifile)
			apFile.removeFile(tmpfile)

#=====================
#=====================
if __name__ == '__main__':
	postProc = PostProcScript()
	postProc.start()
	postProc.close()

	
