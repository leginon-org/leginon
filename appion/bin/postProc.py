#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

import os
import apDB
import sys
import re
from optparse import OptionParser
import apParam
import apDisplay
import apDatabase
import appionData
import apEMAN
import apVolume

appiondb = apDB.apdb

def parseCommandLine():
	usage = ( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
		+"[options]")
	parser = OptionParser(usage=usage)

	parser.add_option("-f", "--file", dest="file",
		help="Filename of the density", metavar="FILE")
	parser.add_option("--amp", dest="ampfile",
		help="Filename of the amplitude file", metavar="FILE")
	parser.add_option("--apix", dest="apix", type="float",
		help="Density pixel size in Angstroms per pixel", metavar="FLOAT")
	parser.add_option("--lp", dest="lp", type="float",
		help="Low pass filter value (in Angstroms)", metavar="FLOAT")
	parser.add_option("--mask", dest="mask", type="float",
		help="Radius of outer mask (in Angstroms)", metavar="FLOAT")
	parser.add_option("--imask", dest="imask", type="float",
		help="Radius of inner mask (in Angstroms)", metavar="FLOAT")
	parser.add_option("--maxfilt", dest="maxfilt", type="float",
		help="filter limit to which data will adjusted (in Angstroms)", metavar="FLOAT")
	parser.add_option("-o", "--outdir", dest="outdir",
		help="Location to which output file will be saved", metavar="PATH")
	parser.add_option("-y", "--yflip", dest="yflip", default=False,
		action="store_true", help="Flip the handedness of the density")
	parser.add_option("-i", "--invert", dest="invert", default=False,
		action="store_true", help="Invert the density values")
	parser.add_option("--viper", dest="viper", default=False,
		action="store_true", help="Rotate icosahedral densities from Eman orientation to Viper orientation")
	parser.add_option("--norm", dest="norm", default=False,
		action="store_true", help="Normalize the final density such that mean=0, sigma=1")
	# no commit params yet
#	parser.add_option("--commit", dest="commit", default=True,
#		action="store_true", help="Commit template to database")
#	parser.add_option("--no-commit", dest="commit", default=True,
#		action="store_false", help="Do not commit template to database")

	params = apParam.convertParserToParams(parser)
	return params

def locateAmpFile(ampfile):
	## may be ready to use as is
	ampabspath = os.path.abspath(ampfile)
	if os.path.exists(ampabspath):
		return ampabspath

	## try to find it in same directory as apVolume.py
	ampfilebase = os.path.basename(ampfile)
	apvolfile = os.path.abspath(apVolume.__file__)
	apvoldir = os.path.dirname(apvolfile)
	ampabspath = os.path.join(apvoldir, ampfilebase)
	if os.path.exists(ampabspath):
		return ampabspath

	## can't find it
	return None

def checkConflicts(params):
	# make sure the necessary parameters are set
	if params['apix'] is None:
		apDisplay.printError("enter a pixel size")
	if params['file'] is None:
		apDisplay.printError("enter a file name for processing")
	if params['ampfile'] is not None:
		newampfile = locateAmpFile(params['ampfile'])
		if newampfile is None:
			apDisplay.printError("Could not locate amplitude file: %s" % (params['ampfile'],))
		else:
			params['ampfile'] = newampfile
			
	if params['ampfile'] is not None and params['maxfilt'] is None:
		apDisplay.printError("if performing amplitude correction, enter a filter limit")

if __name__ == '__main__':
	# create params dictionary & set defaults
	params = parseCommandLine()
	params['appiondir'] = apParam.getAppionDirectory()
	os.chdir(params['outdir'])
	apParam.writeFunctionLog(sys.argv)

	checkConflicts(params)

	params['path'],params['filename']=os.path.split(params['file'])
	if params['path']=='':
		params['path'] = os.path.dirname(os.path.abspath(params['file']))
		
	if params['outdir'] is None:
		#auto set the output directory to be same as input
		params['outdir'] = params['path']
		      
	params['fileroot'] , params['ext'] = os.path.splitext(params['filename'])

	#create the output directory, if needed
	apDisplay.printMsg("Out directory: "+params['outdir'])
	apParam.createDirectory(params['outdir'])

	outfile = os.path.join(params['outdir'],params['fileroot'])

	#run amplitude correction
	if params['ampfile'] is not None:
		params['box'] = apVolume.getModelDimensions(params['file'])
		spifile = apVolume.MRCtoSPI(params['file'],params['outdir'])
		tmpfile = apVolume.createAmpcorBatchFile(spifile,params)
		apVolume.runAmpcor()

		# convert amplitude corrected file back to mrc
		outfile+=".amp"
		emancmd="proc3d %s " %tmpfile

	#run proc3d
	else :
		emancmd = "proc3d %s " %params['file']
	emancmd+="apix=%s " %params['apix']
	if params['lp'] is not None:
		outfile+=".lp"
		emancmd +="lp=%s " %params['lp']

	if params['yflip'] is True:
		outfile+=".yflip"
		emancmd +="yflip "

	if params['invert'] is True:
		outfile+=".inv"
		emancmd +="invert "

	if params['viper'] is True:
		outfile+=".vip"
		emancmd +="icos5fTo2f "
		
	if params['mask'] is not None:
		# convert ang to pixels
		maskpix=int(params['mask']/params['apix'])
		outfile+=".mask"
		emancmd +="mask=%s " %maskpix

	if params['imask'] is not None:
		# convert ang to pixels
		maskpix=int(params['imask']/params['apix'])
		outfile+=".imask"
		emancmd +="imask=%s " %maskpix
		
	if params['norm'] is True:
		outfile+=".norm"
		emancmd +="norm "
		
	#add output filename to emancmd string
	outfile+=".mrc"
	emancmd = re.sub(" apix="," %s apix=" %outfile, emancmd)

	apEMAN.executeEmanCmd(emancmd)

	# clean up files created during amp correction
	if params['ampfile'] is not None:
		os.remove(spifile)
		os.remove(tmpfile)
	
	
	
