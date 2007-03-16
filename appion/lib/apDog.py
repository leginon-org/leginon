#Part of the new pyappion

import sys
import libcv2
#import Mrc
import selexonFunctions  as sf1
#import selexonFunctions2 as sf2

def modifyDefaultParams(params):
	#params={}
	params["ourdir"]="/tmp"
	params["apix"]=1
	params["diam"]=0
	params["bin"]=4
	params["range"]=0
	params["sample"]=1
	params["mint"]=3
	params["maxt"]=7
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
		if (elements[0]=='bin'):
			params['bin']=float(elements[1])
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=float(elements[1])
		elif (elements[0]=='range'):
			params['range']=float(elements[1])
		elif (elements[0]=='sample'):
			params['sample']=float(elements[1])
		elif (elements[0]=='mint'):
			params["mint"]=float(elements[1])
		elif (elements[0]=='maxt'):
			params["maxt"]=float(elements[1])
		elif (elements[0]=='id'):
			params["id"]=elements[1]
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
			else:
				print "dbimages must include both session and preset parameters"
				sys.exit()
		elif (elements[0]=='commit'):
			params['commit']=True
		else:
			print "undefined parameter '"+arg+"'\n"
			sys.exit(1)

def runDogDetection(imagename, params):
	#imgpath = img['session']['image path'] + '/' + imagename + '.mrc'
	#image = Mrc.mrc_to_numeric(imgpath)
	image = sf1.getImageData(imagename)['image']

	scale          = params['apix']
	estimated_size = params['diam']/2
	search_range   = params['range']
	sampling       = params['sample']
	mintreshold    = params['mint']
	maxtreshold    = params['maxt']
	bin            = params['bin']

	sys.stderr.write(" ... running dog picker")
	peaks = libcv2.dogDetector(image,bin,estimated_size,search_range,sampling,mintreshold,maxtreshold)
	print " ... done"

	return peaks
