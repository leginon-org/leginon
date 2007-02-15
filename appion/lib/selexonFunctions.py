#!/usr/bin/python -O
# Python functions for selexon.py

import os, re, sys
import tempfile
import cPickle
import data
import dbdatakeeper
import convolver
import Mrc
import imagefun
import peakfinder
import correlator
import math
import particleData
import project
import string
import time
import numarray
import numarray.convolve as convolve
import numarray.nd_image as nd_image

db=dbdatakeeper.DBDataKeeper()
partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
projdb=dbdatakeeper.DBDataKeeper(db='project')

def createDefaults():
	# create default values for parameters
	params={}
	params["mrcfileroot"]=''
	params["template"]=''
	params["templatelist"]=[]
	params["apix"]=None
	params["diam"]=0
	params["bin"]=4
	params["startang"]=0
	params["endang"]=10
	params["incrang"]=20
	params["thresh"]=0.5
	params["autopik"]=0
	params["lp"]=30
	params["hp"]=600
	params["box"]=0
	params["crud"]=False
	params["cdiam"]=0
	params["cblur"]=3.5
	params["clo"]=0.6
	params["chi"]=0.95
	params["cstd"]=1
	params["crudonly"]=False
	params["continue"]=False
	params["multiple_range"]=False
	params["dbimages"]=False
	params["alldbimages"]=False
	params["session"]=None
	params["preset"]=None
	params["runid"]='run1'
	params["commit"]=False
	params["defocpair"]=False
	params["abspath"]=os.path.abspath('.')+'/'
	params["shiftonly"]=False
	params["templateIds"]=''
	params["ogTmpltInfo"]=[]
	params["scaledapix"]={}
	params["outdir"]=None
	params['description']=None
	params['scale']=1
	params['projectId']=None
	params['prtltype']=None
	params['method']="updated"
	params['overlapmult']=1.5
	params['maxpeaks']=1500
	params["cschi"]=1
	params["csclo"]=0
	params["convolve"]=0
	params["no_hull"]=False
	params["no_length_prune"]=False
	params["stdev"]=0
	params["test"]=False

	return params

def printUploadHelp():
	print "\nUsage:\nuploadTemplate.py template=<name> apix=<pixel> session=<session> [commit]\n"
	print "selexon template=groEL apix=1.63 session=06nov10a commit\n"
	print "template=<name>      : name should not have the extension, or number."
	print "                       groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>         : angstroms per pixel (unbinned)"
	print "diam=<n>             : approximate diameter of particle (in Angstroms, unbinned)"
	print "session=<sessionId>  : session name associated with template (i.e. 06mar12a)"
	print "description=\"text\"   : description of the template - must be in quotes"
	print "\n"

	sys.exit(1)

def printPrtlUploadHelp():
	print "\nUsage:\nuploadParticles.py <boxfiles> scale=<n>\n"
	print "selexon *.box scale=2\n"
	print "<boxfiles>            : EMAN box file(s) containing picked particle coordinates"
	print "runid=<runid>         : name associated with these picked particles (default is 'manual1')"
	print "scale=<n>             : If particles were picked on binned images, enter the binning factor"
	print "\n"

	sys.exit(1)

def printSelexonHelp():
	print "\nUsage:\nselexon.py <file> template=<name> apix=<pixel> diam=<n> bin=<n> [templateIds=<n,n,n,n,...>] [range=<start,stop,incr>] [thresh=<threshold> or autopik=<n>] [lp=<n>] [hp=<n>] [crud or cruddiam=<n>] [crudonly] [crudblur=<n>] [crudlow=<n>] [crudhi=<n>] [box=<n>] [continue] [dbimages=<session>,<preset>] [alldbimages=<session>] [commit] [defocpair] [shiftonly] [outdir=<path>] [method=<method>] [overlapmult=<n>]"
	print "Examples:\nselexon 05jun23a_00001en.mrc template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud"
	print "selexon template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud dbimages=05jun23a,en continue\n"
	print "template=<name>    : name should not have the extension, or number."
	print "                     groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
	print "apix=<pixel>       : angstroms per pixel (unbinned)"
	print "diam=<n>           : approximate diameter of particle (in Angstroms, unbinned)"
	print "bin=<n>            : images will be binned by this amount (default is 4)"
	print "range=<st,end,i>   : each template will be rotated from the starting angle to the"
	print "                     stop angle at the given increment"
	print "                     User can also specify ranges for each template (i.e. range1=0,60,20)"
	print "                     NOTE: if you don't want to rotate the image, leave this parameter out"
	print "thresh=<thr>       : manual cutoff for correlation peaks (0-1), don't use if want autopik (default is 0.5)"
	print "autopik=<thr>      : automatically calculate threshold, n = average number of particles per image"
	print "                     NOTE: autopik does NOT work for *updated* method"
	print "lp=<n>, hp=<n>     : low-pass and high-pass filter (in Angstroms) - (defaults are 30 & 600)"
	print "                     NOTE: high-pass filtering is currently disabled"
	print "crud               : run the crud finder after the particle selection"
	print "                     (will use particle diameter by default)"
	print "cruddiam=<n>       : set the diameter to use for the crud finder"
	print "                     (don't need to use the \"crud\" option if using this)"
	print "crudblur=<n>       : amount to blur the image for edge detection (default is 3.5)"
	print "crudlo=<n>         : lower limit for edge detection (0-1, default=0.6)"
	print "crudhi=<n>         : upper threshold for edge detection (0-1, default=0.95)"
	print "crudstd=<n>        : lower limit for scaling the edge detection limits (i.e. stdev of the image) (default=1= never scale)"
	print "crudonly           : only run the crud finder to check and view the settings"
	print "box=<n>            : output will be saved as EMAN box file with given box size"
	print "continue           : if this option is turned on, selexon will skip previously processed"
	print "                     micrographs"
	print "commit             : if commit is specified, particles will be stored to the database (not implemented yet)"
	print "dbimages=<sess,pr> : if this option is turned on, selexon will continuously get images from the database"
	print "alldbimages=<sess> : if this option is turned on selexon will query the database for all images"
	print "                     associated with the session"
	print "runid=<runid>      : subdirectory for output (default=run1)"
	print "                     do not use this option if you are specifying particular images"
	print "defocpair          : calculate shift between defocus pairs"
	print "shiftonly          : skip particle picking and only calculate shifts"
	print "templateIds        : list the database id's of the templates to use"
	print "outdir=<path>      : output directory in which results will be written"
	print "method=<method>    : choices: classic, updated (default), and experimental"
	print "                       classic - calls findem and viewit"
	print "                       updated - uses findem and internally find peaks (default)"
	print "                       experimental - internally generates cc maps and find peaks"
	print "overlapmult=<n>    : distance multiple for two particles to overlap (default is 1.5 X)"
	print "maxpeaks=<n>       : maximum number of particles allowed per image"
	print "crudschi=<n>               : image standard deviation hi limit for scaling the edge detection limits (default=1: use crudhi&crudlo)"
	print "crudsclo=<n>               : image standard deviation lower limit for scaling the edge detection limits (default=0: use crudhi&crudlo)"
	print "convolve=<n>               : if not zero, convolve the thresholded edge blobs with a disk at the particle diameter to unify blobs"
	print "                             and then threshold it at <n> fraction of peak self covolution of the disk (0-1, default=0"
	print "no_hull                    : if ON, convex hull is not calculated"
	print "no_length_prune            : if ON, pruning by crud perimeters is not done before convex hull"
	print "stdev=<n>                  : if not zero, only regions with stdev larger than n*image_stdev is passed (default=0)"
	print "test                       : if ON, images at each step are saved"
	print "\n"

	sys.exit(1)

def parseUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printUploadHelp()

	# save the input parameters into the "params" dictionary
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		elif (elements[0]=='session'):
			params['session']=elements[1]
		elif (elements[0]=='description'):
			params['description']=elements[1]
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
        
def parsePrtlUploadInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printPrtlUploadHelp()

	lastarg=1
	
	# first get all box files
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		else:
			boxfile=arg
			if (os.path.exists(boxfile)):
				# in case of multiple extenstions, such as pik files
				splitfname=(os.path.basename(boxfile).split('.'))
				mrcfileroot.append(splitfname[0])
				params['extension']=string.join(splitfname[1:],'.')
				params['prtltype']=splitfname[-1]
			else:
				print ("\nERROR: file \'%s\' does not exist \n" % boxfile)
				sys.exit()
		lastarg+=1
	params["imgs"]=mrcfileroot

	# save the input parameters into the "params" dictionary
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='scale'):
			params['scale']=int(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
        
def parseSelexonInput(args,params):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help' or args[1]=='--help' \
		or args[1]=='-h' or args[1]=='-help') :
		printSelexonHelp()

	lastarg=1

	# save the input parameters into the "params" dictionary

	# first get all images
	mrcfileroot=[]
	for arg in args[lastarg:]:
		# gather all input files into mrcfileroot list
		if '=' in  arg:
			break
		elif (arg=='crudonly' or arg=='crud'):
			break
		else:
			mrcfile=arg
			mrcfileroot.append(os.path.splitext(mrcfile)[0])
		lastarg+=1
	params['mrcfileroot']=mrcfileroot

	# next get all selection parameters
	for arg in args[lastarg:]:
		elements=arg.split('=')
		if (elements[0]=='template'):
			params['template']=elements[1]
		elif (elements[0]=='apix'):
			params['apix']=float(elements[1])
		elif (elements[0]=='diam'):
			params['diam']=int(elements[1])
		elif (elements[0]=='bin'):
			params['bin']=int(elements[1])
		elif (elements[0]=='range'):
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang']=int(angs[0])
				params['endang']=int(angs[1])
				params['incrang']=int(angs[2])
			else:
				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
				sys.exit(1)
		elif (re.match('range\d+',elements[0])):
			num=elements[0][-1]
			angs=elements[1].split(',')
			if (len(angs)==3):
				params['startang'+num]=int(angs[0])
				params['endang'+num]=int(angs[1])
				params['incrang'+num]=int(angs[2])
				params['multiple_range']=True
			else:
 				print "\nERROR: \'range\' must include 3 angle parameters: start, stop, & increment\n"
				sys.exit(1)
		elif (elements[0]=='thresh'):
			params["thresh"]=float(elements[1])
		elif (elements[0]=='autopik'):
			params["autopik"]=float(elements[1])
		elif (elements[0]=='lp'):
			params["lp"]=float(elements[1])
		elif (elements[0]=='hp'):
			params["hp"]=float(elements[1])
		elif (elements[0]=='box'):
			params["box"]=int(elements[1])
		elif (arg=='crud'):
			params["crud"]=True
		elif (elements[0]=='cruddiam'):
			params["crud"]=True
			params["cdiam"]=int(elements[1])
		elif (elements[0]=='crudblur'):
			params["cblur"]=float(elements[1])
		elif (elements[0]=='crudlo'):
			params["clo"]=float(elements[1])
		elif (elements[0]=='crudhi'):
			params["chi"]=float(elements[1])
		elif (elements[0]=='crudstd'):
			params["cstd"]=float(elements[1])
		elif (elements[0]=='runid'):
			params["runid"]=elements[1]
		elif (arg=='crudonly'):
			params["crudonly"]=True
		elif (arg=='continue'):
			params["continue"]=True
		elif (elements[0]=='templateIds'):
			templatestring=elements[1].split(',')
			params['templateIds']=templatestring
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo) == 2:
				params['sessionname']=dbinfo[0]
				params['preset']=dbinfo[1]
				params["dbimages"]=True
				params["continue"]=True # continue should be on for dbimages option
			else:
				print "\nERROR: dbimages must include both \'session\' and \'preset\'"+\
					"parameters (ex: \'07feb13a,en\')\n"
				sys.exit(1)
		elif (elements[0]=='alldbimages'):
			params['sessionname']=elements[1]
			params['alldbimages']=True
		elif arg=='commit':
			params['commit']=True
		elif arg=='defocpair':
			params['defocpair']=True
		elif arg=='shiftonly':
			params['shiftonly']=True
		elif (elements[0]=='method'):
			params['method']=str(elements[1])
		elif (elements[0]=='overlapmult'):
			params['overlapmult']=float(elements[1])
		elif (elements[0]=='maxpeaks'):
			params['maxpeaks']=int(elements[1])
		elif (elements[0]=='crudschi'):
			params["cschi"]=float(elements[1])
		elif (elements[0]=='crudsclo'):
			params["csclo"]=float(elements[1])
		elif (elements[0]=='convolve'):
			params["convolve"]=float(elements[1])
		elif (elements[0]=='stdev'):
			params["stdev"]=float(elements[1])
		elif (arg=='no_hull'):
			params["no_hull"]=True
		elif (arg=='no_length_prune'):
			params["no_length_prune"]=True
		elif (arg=='test'):
			params["test"]=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
        
def runFindEM(params,file):
	# run FindEM
	tmplt=params["template"]
	numcls=len(params['templatelist'])
	pixdwn=str(params["apix"]*params["bin"])
	d=str(params["diam"])
	if (params["multiple_range"]==False):
		strt=str(params["startang"])
		end=str(params["endang"])
		incr=str(params["incrang"])
	bw=str(int((1.5 * params["diam"]/params["apix"]/params["bin"])/2))

	classavg=1
	while classavg<=len(params['templatelist']):
		# first remove the existing cccmaxmap** file
		cccfile="cccmaxmap%i00.mrc" %classavg
		if (os.path.exists(cccfile)):
			os.remove(cccfile)

		if (params["multiple_range"]==True):
			strt=str(params["startang"+str(classavg)])
			end=str(params["endang"+str(classavg)])
			incr=str(params["incrang"+str(classavg)])
		fin='';
		#fin=os.popen('${FINDEM_PATH}/FindEM_SB','w')
		fin=os.popen('${FINDEM_EXE}','w')
		#fin=os.popen('/home/vossman/appion2/findem/bin/findem.exe','w')
		fin.write(file+".dwn.mrc\n")
		if (len(params['templatelist'])==1 and not params['templateIds']):
			fin.write(tmplt+".dwn.mrc\n")
		else:
			fin.write(tmplt+str(classavg)+".dwn.mrc\n")
		fin.write("-200.0\n")
		fin.write(pixdwn+"\n")
		fin.write(d+"\n")
		fin.write(str(classavg)+"00\n")
		fin.write(strt+','+end+','+incr+"\n")
		fin.write(bw+"\n")
		print "running findem.exe"
		fin.flush
		fin.close()
		classavg+=1
	return
        
def getProjectId(params):
	projectdata=project.ProjectData()
	projects=projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name']==params['session']:
			params['projectId']=i['projectId']
	if not params['projectId']:
		print "\nERROR: no project associated with this session\n"
		sys.exit()
	return
	
def getOutDirs(params):
	sessionq=data.SessionData(name=params['session']['name'])
	sessiondata=db.query(sessionq)
	impath=sessiondata[0]['image path']
	params['imgdir']=impath+'/'

	if params['outdir']:
		pass
	else:
		outdir=os.path.split(impath)[0]
		outdir=os.path.join(outdir,'extract/')
		params['outdir']=outdir

	params['rundir']=os.path.join(params['outdir'],params['runid'])
	
	if os.path.exists(params['rundir']):
		print " !!! WARNING: run directory for \'"+str(params['runid'])+"\' already exists.\n",\
			" ... make sure continue option is on if you don't want to overwrite previous run."
		time.sleep(2)
	else:
		os.makedirs(params['rundir'])

	return(params)

def findPeaks(params,file):
	# create tcl script to process the cccmaxmap***.mrc images & find peaks
	tmpfile=tempfile.NamedTemporaryFile()
	imgsize=int(getImgSize(file))
	wsize=str(int(1.5 * params["diam"]/params["apix"]/params["bin"]))
	clsnum=str(len(params['templatelist']))
	cutoff=str(params["thresh"])
	scale=str(params["bin"])
	sz=str(imgsize/params["bin"])
	min_thresh="0.2"

	# remove existing *.pik files
	i=1
	while i<=int(clsnum):
		fname="pikfiles/%s.%i.pik" % (file,i)
		if (os.path.exists(fname)):
			os.remove(fname)
			print "removed existing file:",fname
		i+=1
	if (os.path.exists("pikfiles/"+file+".a.pik")):
		os.remove("pikfiles/"+file+".a.pik")
        
	cmdlist=[]
	cmdlist.append("#!/usr/bin/env viewit\n")
	cmdlist.append("source $env(SELEXON_PATH)/graphics.tcl\n")
	cmdlist.append("source $env(SELEXON_PATH)/io_subs.tcl\n")
	cmdlist.append("-iformat MRC\nif { "+clsnum+" > 1} {\n")
	cmdlist.append("  for {set x 1 } { $x <= "+clsnum+" } {incr x } {\n")
	cmdlist.append("    -i cccmaxmap${x}00.mrc -collapse\n")
	# run auto threshold if no threshold is set
	if (params["thresh"]==0):
		autop=str(params["autopik"])
		# set number of bins for histogram
		nbins=str(int(params["autopik"]/20))
		cmdlist.append("    set peaks [-zhimg_peak BYNUMBER "+autop+" "+wsize+" ]\n")
		cmdlist.append("    set peak_hist [-zhptls_hist "+nbins+"]\n")
		cmdlist.append("    set threshold [-zhhist_thresh  BYZHU 0.02]\n")
		cmdlist.append("    if { $threshold < "+min_thresh+" } {\n")
		cmdlist.append("      set threshold "+min_thresh+"}\n")
		cmdlist.append("    set final_peaks [list]\n")
		cmdlist.append("    for {set y 0} {$y < [llength $peaks] } {incr y } {\n")
		cmdlist.append("      set apick [lindex $peaks $y]\n")
		cmdlist.append("      if { [lindex $apick 3] > $threshold } {")
		cmdlist.append("        lappend final_peaks $apick} }\n")
		cmdlist.append("    write_picks "+file+".mrc $final_peaks "+scale+" pikfiles/"+file+".$x.pik\n}\n}\n")
	else:
		cmdlist.append("    set peaks [-zhimg_peak BYVALUE "+cutoff+" "+wsize+" ]\n")
		cmdlist.append("    write_picks "+file+".mrc $peaks "+scale+" pikfiles/"+file+".$x.pik\n}\n}\n")

	cmdlist.append("-dim 2 "+sz+" "+sz+" -unif -1.0\n")
	cmdlist.append("-store cccmaxmap_max\n")
	cmdlist.append("for {set x 1 } { $x <= "+clsnum+" } {incr x } {\n")
	cmdlist.append("  -i cccmaxmap${x}00.mrc -collapse\n")
	cmdlist.append("  -store cccmaxmap\n")
	cmdlist.append("  -load ss1 cccmaxmap_max\n")
	cmdlist.append("  -load ss2 cccmaxmap\n")
	cmdlist.append("  -zhreg_max\n")
	cmdlist.append("  -store cccmaxmap_max ss1\n}\n")
	cmdlist.append("-load ss1 cccmaxmap_max\n")
	if (params["thresh"]==0):
		cmdlist.append("set peaks [-zhimg_peak BYNUMBER "+autop+" "+wsize+"]\n")
		cmdlist.append("set peak_hist [-zhptls_hist "+nbins+"]\n")
		cmdlist.append("set threshold [-zhhist_thresh  BYZHU 0.02]\n")
		cmdlist.append("if { $threshold < "+min_thresh+"} {\n")
		cmdlist.append("  set threshold "+min_thresh+"}\n")
		cmdlist.append("for {set x 0} {$x < [llength $peaks] } {incr x } {\n")
		cmdlist.append("  set apick [lindex $peaks $x]\n")
		cmdlist.append("  if { [lindex $apick 3] > $threshold } {")
		cmdlist.append("    lappend final_peaks $apick} }\n")
		cmdlist.append("write_picks "+file+".mrc $final_peaks "+scale+" pikfiles/"+file+".a.pik\n")
	else:
		cmdlist.append("set peaks [-zhimg_peak BYVALUE "+cutoff+" "+wsize+"]\n")
		cmdlist.append("puts \"$peaks\"\n")
		cmdlist.append("write_picks "+file+".mrc $peaks "+scale+" pikfiles/"+file+".a.pik\nexit\n")

	tclfile=open(tmpfile.name,'w')
	tclfile.writelines(cmdlist)
	tclfile.close()
	f=os.popen('viewit '+tmpfile.name)
	result=f.readlines()
	if (params["thresh"]!=0):
		line=result[-2].split()
		peaks=line[0]
		print peaks,"peaks were extracted"
	f.close()

def createJPG(params,img):
	# create a jpg image to visualize the final list of targetted particles
	tmpfile=tempfile.NamedTemporaryFile()

	# create "jpgs" directory if doesn't exist
	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")
    
	scale=str(params["bin"])
	file=img
	size=str(int(params["diam"]/30)) #size of cross to draw

	cmdlist=[]
	cmdlist.append("#!/usr/bin/env viewit\n")
	cmdlist.append("source $env(SELEXON_PATH)/graphics.tcl\n")
	cmdlist.append("source $env(SELEXON_PATH)/io_subs.tcl\n")
	cmdlist.append("set pick [read_list pikfiles/"+file+".a.pik]\n")
	cmdlist.append("set num_picks [llength $pick]\n")
	cmdlist.append("for {set x 0} {$x < $num_picks} {incr x} {\n")
	cmdlist.append("  set apick [lindex $pick $x]\n")
	cmdlist.append("  set filename [lindex $apick 0]\n")
	cmdlist.append("  set xcord    [expr round ([lindex $apick 1]/"+scale+")]\n")
	cmdlist.append("  set ycord    [expr round ([lindex $apick 2]/"+scale+")]\n")
	cmdlist.append("  lappend particles($filename) [list $filename $xcord $ycord]\n}\n")
	cmdlist.append("set thickness 2\n")
	cmdlist.append("set pixel_value 255\n")
	cmdlist.append("set searchid [array startsearch particles ]\n")
	cmdlist.append("set filename [array nextelement particles $searchid]\n")
	cmdlist.append('while { $filename != ""} {\n');
	cmdlist.append("  set particles_list $particles($filename)\n")
	cmdlist.append("  if { [llength pikfiles/"+file+".a.pik] > 0 } {\n")
	cmdlist.append("    -iformat MRC -i [file join . $filename] -collapse\n")
	cmdlist.append("    set x "+scale+"\n")
	cmdlist.append("    while { $x > 1} {\n-scale 0.5 0.5\nset x [expr $x / 2]\n}\n")
	cmdlist.append("    -linscl 0 255\n")
	cmdlist.append("    draw_points $particles_list 0 "+size+" $thickness $pixel_value\n")
	cmdlist.append("    -oformat JPEG -o \"jpgs/$filename.prtl.jpg\"\n}\n")
	cmdlist.append("  set filename [array nextelement particles $searchid]\n}\n")
	cmdlist.append("array donesearch particles $searchid\nexit\n")
    
	tclfile=open(tmpfile.name,'w')
	tclfile.writelines(cmdlist)
	tclfile.close()
	f=os.popen('viewit '+tmpfile.name)
	result=f.readlines()
	f.close()
    
def findCrud(params,file):
	# run the crud finder
	tmpfile=tempfile.NamedTemporaryFile()

	# create "jpgs" directory if doesn't exist
	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")
    
	# remove crud pik file if it exists
	if (os.path.exists("pikfiles/"+file+".a.pik.nocrud")):
		os.remove("pikfiles/"+file+".a.pik.nocrud")

	# remove crud info file if it exists
	if (os.path.exists("crudfiles/"+file+".crud")):
		os.remove("crudfiles/"+file+".crud")

	diam=str(params["diam"]/4)
	cdiam=str(params["cdiam"]/4)
	if (params["cdiam"]==0):
		cdiam=diam
	scale=str(params["bin"])
	size=str(int(params["diam"]/30)) #size of cross to draw    
	sigma=str(params["cblur"]) # blur amount for edge detection
	low_tn=float(params["clo"]) # low threshold for edge detection
	high_tn=float(params["chi"]) # upper threshold for edge detection
	standard=float(params["cstd"]) # lower threshold for full scale edge detection
	pm="2.0"
	am="3.0" 

	# scale the edge detection limit if the image standard deviation is lower than the standard
	# This creates an edge detection less sensitive to noises in mostly empty images
	image=Mrc.mrc_to_numeric(file+".mrc")
	imean=imagefun.mean(image)
	istdev=imagefun.stdev(image,known_mean=imean)
	print imean,istdev
	low_tns=low_tn/(istdev/standard)
	high_tns=high_tn/(istdev/standard)
	if (low_tns > 1.0):
		low_tns=1.0
	if (low_tns < low_tn):
		low_tns=low_tn
	if (high_tns > 1.0):
		high_tns=1.0
	if (high_tns < high_tn):
		high_tns=high_tn
	high_t=str(high_tns)
	low_t=str(low_tns)
	print high_tns,low_tns



	cmdlist=[]
	cmdlist.append("#!/usr/bin/env viewit\n")
	cmdlist.append("source $env(SELEXON_PATH)/io_subs.tcl\n")
	cmdlist.append("source $env(SELEXON_PATH)/image_subs.tcl\n")
	if (params["crudonly"]==False):
		cmdlist.append("set x 0\n")
		cmdlist.append("set currentfile \"not_a_valid_file\"\n")
		cmdlist.append("set fp [open pikfiles/"+file+".a.pik r]\n")
		cmdlist.append("while {[gets $fp apick ] >= 0} {\n")
		cmdlist.append("  set xcenter    [expr [lindex $apick 1] / "+scale+"]\n")
		cmdlist.append("  set ycenter    [expr [lindex $apick 2] / "+scale+"]\n")
		cmdlist.append("  if { [string compare $currentfile "+file+".mrc] != 0 } {\n")
		cmdlist.append("    if { [string compare $currentfile \"not_a_valid_file\"] != 0 } {\n")
		cmdlist.append("      -load ss1 outlined_img\n")
		cmdlist.append("      -oformat JPEG -o \"jpgs/"+file+".a.pik.nocrud.jpg\"}\n")
	cmdlist.append("    -iformat MRC -i [file join . "+file+".mrc] -collapse\n")
	cmdlist.append("    set x "+scale+"\n")
	if (params["bin"]>1):
		cmdlist.append("    -store orig_img ss1\n")
		cmdlist.append("    while { $x > 1} {\n")
		cmdlist.append("      -scale 0.5 0.5\n")
		cmdlist.append("      set x [expr $x / 2]\n")
		cmdlist.append("    }\n")    
	cmdlist.append("    -store scaled_img ss1\n")
	cmdlist.append("    set imgheight [get_rows]\n")
	cmdlist.append("    set imgwidth  [get_cols]\n")
	cmdlist.append("    puts \"image size is now scaled to $imgheight X $imgwidth\"\n")
	cmdlist.append("    set list_t [expr round ("+pm+" * 3.1415926 * "+cdiam+" / "+scale+")]\n")
	cmdlist.append("    set radius [expr "+cdiam+" / 2.0 / "+scale+"]\n")
	cmdlist.append("    set area_t  [expr round("+am+" * 3.1415926 * $radius * $radius)]\n")
	cmdlist.append("    puts \"binned radius is $radius, binned list_t = $list_t, binned area_t = $area_t\"\n")
	cmdlist.append("    set iter 3\n")
	cmdlist.append("    -zhcanny_edge "+sigma+" "+low_t+" "+high_t+" tmp.mrc\n")
	cmdlist.append("    -zhimg_dila $iter\n")
	cmdlist.append("    -zhimg_eros $iter\n")
	cmdlist.append("    -zhimg_label\n")
	cmdlist.append("    -zhprun_lpl LENGTH $list_t\n")
	cmdlist.append("    -zhmerge_plgn INSIDE\n")
	cmdlist.append("    -zhptls_chull\n")
	cmdlist.append("    -zhprun_plgn BYSIZE $area_t\n")
	cmdlist.append("    -zhmerge_plgn CONVEXHULL\n")
	cmdlist.append("    set zmet [-zhlpl_attr]\n")
	cmdlist.append("    set currentfile "+file+".mrc\n")
	cmdlist.append("    set fic [open crudfiles/"+file+".crud w+]\n")
	cmdlist.append("    puts $fic $zmet\n")
	cmdlist.append("    close $fic\n")
	cmdlist.append("    -store convex_hulls ss1\n")
	cmdlist.append("    set line_width 2\n")
	cmdlist.append("    set line_intensity 0\n")
	cmdlist.append("    -xchg\n")
	cmdlist.append("    -load ss1 scaled_img\n")
	cmdlist.append("    -linscl 0 255\n")
	cmdlist.append("    -xchg\n")
	cmdlist.append("    -zhsuper_plgn $line_width $line_intensity 1\n")
	cmdlist.append("    -xchg\n")
	cmdlist.append("    -store outlined_img ss1\n")
	cmdlist.append("    -load ss1 convex_hulls\n")
	if (params["crudonly"]==False):
		cmdlist.append("    set currentfile "+file+".mrc\n")
		cmdlist.append("  } else {\n")
		cmdlist.append("    -load ss1 convex_hulls}\n")
		cmdlist.append("  set st [-zhinsd_plgn $xcenter $ycenter]\n")
		cmdlist.append("  if {[string equal $st \"o\" ]} {\n")
		cmdlist.append("    set fid [open pikfiles/"+file+".a.pik.nocrud a+]\n")
		cmdlist.append("    puts $fid $apick\n")
		cmdlist.append("    close $fid\n")
		cmdlist.append("  } else {\n")
		cmdlist.append("    puts \"reject $apick because st = $st\"\n")
		cmdlist.append("    incr x}\n")
	cmdlist.append("  set thickness 2\n")
	cmdlist.append("  set pixel_value 255\n")
	cmdlist.append("  -load ss1 outlined_img\n")
	if (params["crudonly"]==False):
		cmdlist.append("  -zhsuper_prtl 0 $xcenter $ycenter "+size+" $thickness $pixel_value\n")
	cmdlist.append("  -store outlined_img ss1\n")
	if (params["crudonly"]==False):
		cmdlist.append("}\n")
		cmdlist.append("close $fp\n")
	cmdlist.append("-load ss1 outlined_img\n")
	cmdlist.append("-oformat JPEG -o \"jpgs/"+file+".a.pik.nocrud.jpg\"\n")
	if (params["crudonly"]==False):
		cmdlist.append("puts \"$x particles rejected due to being inside a crud.\"\n")
	cmdlist.append("exit\n")

	tclfile=open(tmpfile.name,'w')
	tclfile.writelines(cmdlist)
	tclfile.close()
	f=os.popen('viewit '+tmpfile.name)
	result=f.readlines()
	line=result[-2].split()
	reject=line[1]
	print "crudfinder rejected",reject,"particles"
	f.close()
        return

def getImgSize(fname):
	# get image size (in pixels) of the given mrc file
	imageq=data.AcquisitionImageData(filename=fname)
	imagedata=db.query(imageq, results=1, readimages=False)
	if imagedata:
		size=int(imagedata[0]['camera']['dimension']['y'])
		return(size)
	else:
		print "\nERROR: Image",fname,"not found in database\n"
		sys.exit(1)
	return(size)

def checkTemplates(params,upload=None):
	# determine number of template files
	# if using 'preptemplate' option, will count number of '.mrc' files
	# otherwise, will count the number of '.dwn.mrc' files

	name=params["template"]
	stop=0 
    
	# count number of template images.
	# if a template image exists with no number after it
	# counter will assume that there is only one template
	n=0
	while (stop==0):
		if (os.path.exists(name+'.mrc') and os.path.exists(name+str(n+1)+'.mrc')):
			# templates not following naming scheme
			print "ERROR: Both",name+".mrc and",name+str(n+1)+".mrc exist\n"
			sys.exit(1)
		if (os.path.exists(name+'.mrc')):
			params['templatelist'].append(name+'.mrc')
			n+=1
			stop=1
		elif (os.path.exists(name+str(n+1)+'.mrc')):
			params['templatelist'].append(name+str(n+1)+'.mrc')
			n+=1
		else:
			stop=1

	if not params['templatelist']:
		print "\nERROR: There are no template images found with basename \'"+name+"\'\n"
		sys.exit(1)

	return(params)

def dwnsizeImg(params,img):
	#downsize and filter leginon image     
	imagedata=getImageData(img)    
	bin=params['bin']
	#print " ... downsizing", img
	im=binImg(imagedata['image'],bin)
	#print " ... filtering", img
	apix=params['apix']*bin
	im=filterImg(im,apix,params['lp'])
	Mrc.numeric_to_mrc(im,(img+'.dwn.mrc'))
	return

def dwnsizeTemplate(params,filename):
	#downsize and filter arbitary MRC template image
	bin=params['bin']
	im=Mrc.mrc_to_numeric(filename)
	boxsize=im.shape
	if ((boxsize[0]/bin)%2!=0):
		print "\nERROR: binned image must be divisible by 2\n"
		sys.exit(1)
	if (boxsize[0]%bin!=0):
		print "\nERROR: box size not divisible by binning factor\n"
		sys.exit(1)
	#print " ... downsizing", filename
	im=binImg(im,bin)
	#print " ... filtering",filename
	apix=params['apix']*bin
	im=filterImg(im,apix,params['lp'])

	#replace extension with .dwn.mrc
	ext=re.compile('\.mrc$')
	filename=ext.sub('.dwn.mrc',filename)
	Mrc.numeric_to_mrc(im,(filename))
	return

def binImg(img,binning):
	#bin image using leginon imagefun library
	#img must be a numarray image

	#imagefun.bin results in memory loss
	#return imagefun.bin(img,binning)
	return nd_image.zoom(img,1.0/float(binning),order=1)
    
def filterImg(img,apix,res):
	# low pass filter image to res resolution
	if res==0:
		print " ... skipping low pass filter"
		return(img)
	else:
		print " ... performing low pass filter"
		c=convolver.Convolver()
		sigma=(res/apix)/3.0
		kernel=convolver.gaussian_kernel(sigma)
		#Mrc.numeric_to_mrc(kernel,'kernel.mrc')
	return(c.convolve(image=img,kernel=kernel))
    
def pik2Box(params,file):
	box=params["box"]

	if (params["crud"]==True):
		fname="pikfiles/"+file+".a.pik.nocrud"
	else:
		fname="pikfiles/"+file+".a.pik"
        
	# read through the pik file
	pfile=open(fname,"r")
	piklist=[]
	for line in pfile:
		elements=line.split(' ')
		xcenter=int(elements[1])
		ycenter=int(elements[2])
		xcoord=xcenter - (box/2)
		ycoord=ycenter - (box/2)
		if (xcoord>0 and ycoord>0):
			piklist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
	pfile.close()

	# write to the box file
	bfile=open(file+".box","w")
	bfile.writelines(piklist)
	bfile.close()

	print "results written to \'"+file+".box\'"
	return

def writeSelexLog(commandline, file=".selexonlog"):
	f=open(file,'a')
	out=""
	for n in commandline:
		out=out+n+" "
	f.write(out)
	f.write("\n")
	f.close()

def getDoneDict(selexondonename):
	if os.path.exists(selexondonename):
		# unpickle previously modified dictionary
		f=open(selexondonename,'r')
		donedict=cPickle.load(f)
		f.close()
	else:
		#set up dictionary
		donedict={}
	return (donedict)

def writeDoneDict(donedict,selexondonename):
	f=open(selexondonename,'w')
	cPickle.dump(donedict,f)
	f.close()

def doneCheck(donedict,im):
	# check to see if image has been processed yet and
	# append dictionary if it hasn't
	# this may not be the best way to do this
	if donedict.has_key(im):
		pass
	else:
		donedict[im]=None
	return

def getImageData(imagename):
	# get image data object from database
	imagedataq = data.AcquisitionImageData(filename=imagename)
	imagedata = db.query(imagedataq, results=1, readimages=False)
	imagedata[0].holdimages=False
	if imagedata:
		return imagedata[0]
	else:
		print "\nERROR: Image", imagename,"not found in database\n"
		sys.exit(1)

def getPixelSize(img):
	# use image data object to get pixel size
	# multiplies by binning and also by 1e10 to return image pixel size in angstroms
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=img['scope']['magnification']
	pixelsizeq['tem']=img['scope']['tem']
	pixelsizeq['ccdcamera'] = img['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	
	binning=img['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	
	return(pixelsize*1e10)

def getImagesFromDB(session,preset):
	# returns list of image names from DB
	print "Querying database for images"
	sessionq = data.SessionData(name=session)
	presetq=data.PresetData(name=preset)
	imageq=data.AcquisitionImageData()
	imageq['preset'] = presetq
	imageq['session'] = sessionq
	# readimages=False to keep db from returning actual image
	# readimages=True could be used for doing processing w/i this script
	imagelist=db.query(imageq, readimages=False)
	#loop through images and make data.holdimages false 	 
	#this makes it so that data.py doesn't hold images in memory 	 
	#solves a bug where selexon quits after a dozen or so images 	 
	for img in imagelist: 	 
		img.holdimages=False
	return (imagelist)

def getAllImagesFromDB(session):
	# returns list of image data based on session name
	print "Querying database for images"
	sessionq= data.SessionData(name=session)
	imageq=data.AcquisitionImageData()
	imageq['session']=sessionq
	imagelist=db.query(imageq, readimages=False)
	return (imagelist)
	
def createImageLinks(imagelist):
	# make a link to all images in list if they are not already in curr dir
	for n in imagelist:
		imagename=n['filename']
		imgpath=n['session']['image path'] + '/' + imagename + '.mrc'
		if not os.path.exists((imagename + '.mrc')):
			command=('ln -s %s .' %  imgpath)
			print command
			os.system(command)
	return

def getDBTemplates(params):
	tmptmplt=params['template']
	i=1
	for tid in params['templateIds']:
		# find templateImage row
		tmpltinfo=partdb.direct_query(data.templateImage, tid)
		if not (tmpltinfo):
			print "\nERROR: TemplateId",tid,"not found in database.  Use 'uploadTemplate.py'\n"
			sys.exit(1)
		fname=tmpltinfo['templatepath']
		apix=tmpltinfo['apix']
		# store row data in params dictionary
		params['ogTmpltInfo'].append(tmpltinfo)
		# copy file to current directory
		print "getting image:",fname
		os.system("cp "+fname+" "+tmptmplt+str(i)+".mrc")
		params['scaledapix'][i]=0
		i+=1
	return

def rescaleTemplates(img,params):
	i=1
	for tmplt in params['ogTmpltInfo']:
		ogtmpltname="originalTemporaryTemplate"+str(i)+".mrc"
		newtmpltname="scaledTemporaryTemplate"+str(i)+".mrc"
		
		if params['apix']!=params['scaledapix'][i]:
			print "rescaling template",str(i),":",tmplt['apix'],"->",params['apix']
			scalefactor=tmplt['apix']/params['apix']
			scaleandclip(ogtmpltname,(scalefactor,scalefactor),newtmpltname)
			params['scaledapix'][i]=params['apix']
			dwnsizeTemplate(params,newtmpltname)
		i+=1
	return
	
def scaleandclip(fname,scalefactor,newfname):
	image=Mrc.mrc_to_numeric(fname)
	if(image.shape[0] != image.shape[1]):
		print "WARNING: template is NOT square, this may cause errors"
	boxsz=image.shape
	scaledimg=imagefun.scale(image,scalefactor)

	scboxsz=scaledimg.shape[1]
	#make sure the box size is divisible by 16
	if (scboxsz%16!=0):
		padsize=int(math.ceil(float(scboxsz)/16)*16)
		padshape = numarray.array([padsize,padsize])
		print " ... changing box size from",scboxsz,"to",padsize
		#GET AVERAGE VALUE OF EDGES
		leftedgeavg = nd_image.mean(scaledimg[0:scboxsz, 0:0])
		rightedgeavg = nd_image.mean(scaledimg[0:scboxsz, scboxsz:scboxsz])
		topedgeavg = nd_image.mean(scaledimg[0:0, 0:scboxsz])
		bottomedgeavg = nd_image.mean(scaledimg[scboxsz:scboxsz, 0:scboxsz])
		edgeavg = (leftedgeavg + rightedgeavg + topedgeavg + bottomedgeavg)/4.0
		#PAD IMAGE
		scaledimg = convolve.iraf_frame.frame(scaledimg, padshape, mode="constant", cval=edgeavg)
        	#WHY ARE WE USING EMAN???
		#os.system("proc2d "+newfname+" "+newfname+" clip="+str(padsize)+\
			#","+str(padsize)+" edgenorm")
	Mrc.numeric_to_mrc(scaledimg,newfname)

def getDefocusPair(imagedata):
	target=imagedata['target']
	qtarget=data.AcquisitionImageTargetData()
	qtarget['image'] = target['image']
	qtarget['number'] = target['number']
	qsibling=data.AcquisitionImageData(target=qtarget)
	origid=imagedata.dbid
	allsiblings = db.query(qsibling, readimages=False)	
	if len(allsiblings) > 1:
		#could be multiple siblings but we are taking only the most recent
		#this may be bad way of doing things
		for sib in allsiblings:
			if sib.dbid == origid:
				pass
			else:
				defocpair=sib
				defocpair.holdimages=False
				break
	else:
		defocpair=None
	return(defocpair)

def getShift(imagedata1,imagedata2):
	#assumes images are square.
	print "Finding shift between", imagedata1['filename'], 'and', imagedata2['filename']
	dimension1=imagedata1['camera']['dimension']['x']
	binning1=imagedata1['camera']['binning']['x']
	dimension2=imagedata2['camera']['dimension']['x']
	binning2=imagedata2['camera']['binning']['x']
	finalsize=512
	#test to make sure images are at same mag
	if imagedata1['scope']['magnification']!=imagedata2['scope']['magnification']:
		print "Warning: Defocus pairs are at different magnifications, so shift can't be calculated."
		peak=None
	#test to see if images capture the same area
	elif (dimension1 * binning1) != (dimension2 * binning2):
		print "Warning: Defocus pairs do not capture the same imaging area, so shift can't be calculated."
		peak=None
	#images must not be less than finalsize (currently 512) pixels. This is arbitrary but for good reason
	elif dimension1 < finalsize or dimension2 < finalsize:
		print "Warning: Images must be greater than", finalsize, "to calculate shift."
		peak=None
	else:
		shrinkfactor1=dimension1/finalsize
		shrinkfactor2=dimension2/finalsize
		binned1=binImg(imagedata1['image'],shrinkfactor1)
		binned2=binImg(imagedata2['image'],shrinkfactor2)
		pc=correlator.phase_correlate(binned1,binned2,zero=True)
		#Mrc.numeric_to_mrc(pc,'pc.mrc')
		peak=findSubpixelPeak(pc, lpf=1.5) # this is a temp fix. When jim fixes peakfinder, this should be peakfinder.findSubpixelPeak
		subpixpeak=peak['subpixel peak']
		#find shift relative to origin
		shift=correlator.wrap_coord(subpixpeak,pc.shape)
		peak['scalefactor']=dimension2/float(dimension1)
		peak['shift']=(shift[0]*shrinkfactor1,shift[1]*shrinkfactor1)
	return(peak)

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	#this is a temporary fix while Jim fixes peakfinder
	pf=peakfinder.PeakFinder(lpf=lpf)
	pf.subpixelPeak(newimage=image, npix=npix, guess=guess, limit=limit)
	return pf.getResults()

def recordShift(params,img,sibling,peak):
	filename=params['session']['name']+'.shift.txt'
	f=open(filename,'a')
	f.write('%s\t%s\t%f\t%f\t%f\t%f\n' % (img['filename'],sibling['filename'],peak['shift'][1],peak['shift'][0],peak['scalefactor'],peak['subpixel peak value']))
	f.close()
	return()

def insertShift(img,sibling,peak):
	shiftq=particleData.shift()
	shiftq['dbemdata|AcquisitionImageData|image1']=img.dbid
	shiftdata=partdb.query(shiftq)
	if shiftdata:
		print "Warning: Shift values already in database"
	else:
		shiftq['dbemdata|AcquisitionImageData|image2']=sibling.dbid
		shiftq['shiftx']=peak['shift'][1]
		shiftq['shifty']=peak['shift'][0]
		shiftq['scale']=peak['scalefactor']
		shiftq['correlation']=peak['subpixel peak value']
		print 'Inserting shift beteween', img['filename'], 'and', sibling['filename'], 'into database'
		partdb.insert(shiftq)
	return()

def insertManualParams(params,expid):
	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		print "inserting manual runId into database"
 		manparams=particleData.selectionParams()
 		manparams['runId']=runq
 		manparams['diam']=params['diam']
 		partdb.insert(runq)
 	       	partdb.insert(manparams)
	
def insertSelexonParams(params,expid):

	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=partdb.query(runq, results=1)

 	# if no run entry exists, insert new run entry into run.dbparticledata
 	# then create a new selexonParam entry
 	if not(runids):
		if len(params['templatelist'])==1:
			if params['templateIds']:
				imgname=params['templateIds'][0]
			else:
				imgname=params['abspath']+params['template']+'.mrc'
			insertTemplateRun(params,runq,imgname,params['startang'],params['endang'],params['incrang'])
		else:
			for i in range(1,len(params['templatelist'])+1):
				if params['templateIds']:
					imgname=params['templateIds'][i-1]
				else:
					imgname=params['abspath']+params['template']+str(i)+'.mrc'
				if (params["multiple_range"]==True):
					strt=params["startang"+str(i)]
					end=params["endang"+str(i)]
					incr=params["incrang"+str(i)]
					insertTemplateRun(params,runq,imgname,strt,end,incr)
				else:
					insertTemplateRun(params,runq,imgname,params['startang'],params['endang'],params['incrang'])
 		selexonparams=particleData.selectionParams()
 		selexonparams['runId']=runq
 		selexonparams['diam']=params['diam']
 		selexonparams['bin']=params['bin']
 		selexonparams['manual_thresh']=params['thresh']
 		selexonparams['auto_thresh']=params['autopik']
 		selexonparams['lp_filt']=params['lp']
 		selexonparams['hp_filt']=params['hp']
 		selexonparams['crud_diameter']=params['cdiam']
 		selexonparams['crud_blur']=params['cblur']
 		selexonparams['crud_low']=params['clo']
 		selexonparams['crud_high']=params['chi']
 		selexonparams['crud_std']=params['cstd']
 		partdb.insert(runq)
 	       	partdb.insert(selexonparams)
		
 	# if continuing a previous run, make sure that all the current
 	# parameters are the same as the previous
 	else:
		# get existing selexon parameters from previous run
 		partq=particleData.selectionParams(runId=runq)
		tmpltq=particleData.templateRun(runId=runq)

 		partresults=partdb.query(partq, results=1)
		tmpltresults=partdb.query(tmpltq)
		selexonparams=partresults[0]
		# make sure that using same number of templates
		if len(params['templatelist'])!=len(tmpltresults):
			print "\nERROR: All parameters for a selexon run must be identical!"
			print "You do not have the same number of templates as your last run"
			sys.exit(1)
		# param check if using multiple ranges for templates
		if (params['multiple_range']==True):
			# check that all ranges have same values as previous run
			for i in range(0,len(params['templatelist'])):
				if params['templateIds']:
					tmpltimgq=partdb.direct_query(data.templateImage,params['templateIds'][i])
				else:
					tmpltimgq=particleData.templateImage()
					tmpltimgq['templatepath']=params['abspath']+params['template']+str(i+1)+'.mrc'

				tmpltrunq=particleData.templateRun()

				tmpltrunq['runId']=runq
				tmpltrunq['templateId']=tmpltimgq

				tmpltNameResult=partdb.query(tmpltrunq,results=1)
				strt=params["startang"+str(i+1)]
				end=params["endang"+str(i+1)]
				incr=params["incrang"+str(i+1)]
				if (tmpltNameResult[0]['range_start']!=strt or
				    tmpltNameResult[0]['range_end']!=end or
				    tmpltNameResult[0]['range_incr']!=incr):
					print "\nERROR: All parameters for a selexon run must be identical!"
					print "Template search ranges are not the same as your last run"
					sys.exit(1)
		# param check for single range
		else:
			if (tmpltresults[0]['range_start']!=params["startang"] or
			    tmpltresults[0]['range_end']!=params["endang"] or
			    tmpltresults[0]['range_incr']!=params["incrang"]):
				print "\nERROR: All parameters for a selexon run must be identical!"
				print "Template search ranges are not the same as your last run"
				sys.exit(1)
 		if (selexonparams['diam']!=params['diam'] or
		    selexonparams['bin']!=params['bin'] or
		    selexonparams['manual_thresh']!=params['thresh'] or
		    selexonparams['auto_thresh']!=params['autopik'] or
		    selexonparams['lp_filt']!=params['lp'] or
		    selexonparams['hp_filt']!=params['hp'] or
		    selexonparams['crud_diameter']!=params['cdiam'] or
		    selexonparams['crud_blur']!=params['cblur'] or
		    selexonparams['crud_low']!=params['clo'] or
		    selexonparams['crud_high']!=params['chi'] or
		    selexonparams['crud_std']!=params['cstd']):
			print "\nERROR: All parameters for a selexon run must be identical!"
			print "please check your parameter settings."
 			sys.exit(1)
	return

def insertTemplateRun(params,runq,imgname,strt,end,incr):
	templateq=particleData.templateRun()
	templateq['runId']=runq

	if params['templateIds']:
		templateId=partdb.direct_query(data.templateImage,imgname)
	else:
		templateImgq=particleData.templateImage(templatepath=imgname)
		templateId=partdb.query(templateImgq,results=1)[0]

	# if no templates in the database, exit
	if not (templateId):
		print "\nERROR: Template",imgname,"not found in database. Use preptemplate"
		sys.exit(1)
	templateq['templateId']=templateId
	templateq['runId']=runq
	templateq['range_start']=float(strt)
	templateq['range_end']=float(end)
	templateq['range_incr']=float(incr)
	partdb.insert(templateq)

def insertTemplateImage(params):
	for name in params['templatelist']:
		templateq=particleData.templateImage()
		templateq['templatepath']=params['abspath']+name
		templateId=partdb.query(templateq, results=1)
	        #insert template to database if doesn't exist
		if not (templateId):
			print "Inserting",name,"into the template database"
			templateq['apix']=params['apix']
			templateq['diam']=params['diam']
			templateq['description']=params['description']
			templateq['project|projects|projectId']=params['projectId']
			partdb.insert(templateq)
	return

def insertParticlePicks(params,img,expid,manual=False):
	runq=particleData.run()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	runids=partdb.query(runq, results=1)

	# get corresponding selectionParams entry
	selexonq=particleData.selectionParams(runId=runq)
	selexonresult=partdb.query(selexonq, results=1)

        legimgid=int(img.dbid)
        legpresetid=None
	if img['preset']:
		legpresetid =int(img['preset'].dbid)

	imgname=img['filename']
        imgq = particleData.image()
        imgq['dbemdata|SessionData|session']=expid
        imgq['dbemdata|AcquisitionImageData|image']=legimgid
        imgq['dbemdata|PresetData|preset']=legpresetid
	imgids=partdb.query(imgq, results=1)

        # if no image entry, make one
        if not (imgids):
		print "Inserting image entry for",imgname
                partdb.insert(imgq)
		imgq=None
		imgq = particleData.image()
		imgq['dbemdata|SessionData|session']=expid
		imgq['dbemdata|AcquisitionImageData|image']=legimgid
		imgq['dbemdata|PresetData|preset']=legpresetid
		imgids=partdb.query(imgq, results=1)

	# WRITE PARTICLES TO DATABASE
	print "Inserting",imgname,"particles into Database..."

	
      	# first open pik file, or create a temporary one if uploading a box file
	if (manual==True and params['prtltype']=='box'):
		fname="temporaryPikFileForUpload.pik"

		# read through the pik file
		boxfile=open(imgname+".box","r")
		piklist=[]
		for line in boxfile:
			elements=line.split('\t')
			xcoord=int(elements[0])
			ycoord=int(elements[1])
			xbox=int(elements[2])
			ybox=int(elements[3])
			xcenter=(xcoord + (xbox/2))*params['scale']
			ycenter=(ycoord + (ybox/2))*params['scale']
			if (xcenter < 4096 and ycenter < 4096):
				piklist.append(imgname+" "+str(xcenter)+" "+str(ycenter)+" 1.0\n")			
		boxfile.close()

		# write to the pik file
		pfile=open(fname,"w")
		pfile.writelines(piklist)
		pfile.close()
		
	elif (manual==True and params['prtltype']=='pik'):
		fname=imgname+"."+params['extension']
	else:
		if (params["crud"]==True):
			fname="pikfiles/"+imgname+".a.pik.nocrud"
		else:
			fname="pikfiles/"+imgname+".a.pik"
        
	# read through the pik file
	pfile=open(fname,"r")
	piklist=[]
	for line in pfile:
		if(line[0] != "#"):
			elements=line.split(' ')
			xcenter=int(elements[1])
			ycenter=int(elements[2])
			corr=float(elements[3])

			particlesq=particleData.particle()
			particlesq['runId']=runq
			particlesq['imageId']=imgids[0]
			particlesq['selectionId']=selexonresult[0]
			particlesq['xcoord']=xcenter
			particlesq['ycoord']=ycenter
			particlesq['correlation']=corr

			presult=partdb.query(particlesq)
			if not (presult):
				partdb.insert(particlesq)
	pfile.close()
	
	return
