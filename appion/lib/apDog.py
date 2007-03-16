#Part of the new pyappion

import sys
import libcv2
#import Mrc
import selexonFunctions  as sf1
#import selexonFunctions2 as sf2

def modifyDefaultParams(params):
	#params={}
	params["outdir"]="/tmp"
	params["apix"]=1
	params["diam"]=0
	params["bin"]=4
	params["sizerange"]=0
	params["numslices"]=1
	params["minthresh"]=3
	params["maxthresh"]=7
	params["id"]='picka_'
	params['doneDictName'] = ".dogdonedict"
	return params

def dogHelp():
	print "dogpicker.py dbimages=<session>,<preset> diam=<particle_pixels> bin=<binning>"+\
		" range=<number_of_sizes> mint=<minimum_threshold_sigma> maxt=<maximum_threshold_sigma>"+\
		" id=<runid> [commit]"
	sys.exit(1)
	return

def parseDogInput(args,params):
	for arg in args[1:]:
		elements=arg.split('=')


def runDogDetection(imagename, params):
	#imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
	#image = Mrc.mrc_to_numeric(imgpath)
	image = sf1.getImageData(imagename)['image']
	scale          = params['apix']
	binpixrad      = params['binpixdiam']/2
	search_range   = params['sizerange']
	sampling       = params['numslices']
	mintreshold    = params['minthresh']
	maxtreshold    = params['maxthresh']
	bin            = params['bin']

	sys.stderr.write(" ... running dog picker")
	peaks = libcv2.dogDetector(image,bin,binpixrad,search_range,sampling,mintreshold,maxtreshold)
	print " ... done"

	return peaks
