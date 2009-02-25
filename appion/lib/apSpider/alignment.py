
## python
import time
import os
import subprocess
import cPickle
import sys
import math
from string import lowercase
import random
## PIL
## spider
import spyder
## appion
import apEMAN
import apParam
import apDisplay
import apFile

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
image stack file: 
	*****stack.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def refFreeAlignParticles(stackfile, template, numpart, pixrad,
		firstring=2, lastring=100, dataext=".spi", rundir = "alignment"):
	"""
	inputs:
		stack
		template
		search params
	outputs:
		aligned stack
		rotation/shift params
	"""
	### setup
	if dataext in template:
		template = template[:-4]
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	t0 = time.time()
	apParam.createDirectory(rundir)

	### remove previous iterations
	numiter = 0
	while os.path.isfile(rundir+"/avgimg%02d%s" % (numiter+1, dataext)):
		apFile.removeFile(rundir+"/avgimg%02d%s" % (numiter+1, dataext))
		pngfile = rundir+"/avgimg%02d%s" % (numiter+1, ".png")
		apFile.removeFile(pngfile)
		numiter += 1

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	apDisplay.printMsg("Performing particle alignment")
	# copy template to memory
	mySpider.toSpiderQuiet("CP", (template+"@1"), "_9") 
	mySpider.toSpider("AP SR", 
		spyder.fileFilter(stackfile)+"@******", "1-"+str(numpart), 
		str(int(pixrad)), str(int(firstring))+","+str(int(lastring)), 
		"_9", rundir+"/avgimg**", rundir+"/paramdoc**")
	mySpider.close()

	### find number of iterations
	numiter = 0
	while os.path.isfile(rundir+"/avgimg%02d%s" % (numiter+1, dataext)):
		emancmd = ("proc2d "
			+" "+rundir+"/avgimg"+("%02d%s" % (numiter+1, dataext))
			+" "+rundir+"/avgimg"+("%02d%s" % (numiter+1, ".png"))
		)
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		numiter += 1
	if numiter == 0:
		apDisplay.printError("alignment failed, no iterations were found")
	emancmd = ("proc2d "
		+" "+rundir+"/avgimg"+("%02d%s" % (numiter, dataext))
		+" "+rundir+"/average.mrc"
	)
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)	
	apDisplay.printMsg(str(numiter)+" alignment iterations were run by spider")

	### convert spider rotation, shift data to python
	docfile = rundir+("/paramdoc%02d" % (numiter))+dataext
	picklefile = rundir+("/paramdoc%02d" % (numiter))+".pickle"
	partlist = readRefFreeDocFile(docfile, picklefile)

	### write aligned stack -- with python loop
	alignedstack = "alignedstack"
	alignStack(stackfile, alignedstack, partlist, dataext)

	td1 = time.time()-t0
	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return ("alignedstack.spi", partlist)

def runCoranClass(params,cls):
	print "processing class",cls

	#set up cls dir
	clsdir=cls.split('.')[0]+'.dir'
	
	clscmd='clstoaligned.py ' + cls
	## if multiprocessor, don't run clstoaligned yet
	if params['proc'] == 1:
		#make aligned stack
		os.system(clscmd)
#	       	if os.path.exists('aligned.spi'):
#			os.rename('aligned.spi',os.path.join(clsdir,'aligned.spi'))

	corancmd=clscmd+'\n'

	coranbatch='coranfor'+cls.split('.')[0]+'.bat'

	#make spider batch
	params['nptcls']=apEMAN.getNPtcls(cls)
	# if no particles, create an empty class average
	if params['nptcls'] == 0:
		os.mkdir(clsdir)
		apEMAN.writeBlankImage(os.path.join(clsdir,'classes_avg.spi'),params['boxsize'],0,'spider')
		print "WARNING!! no particles in class"
			
	# if only 3 particles or less, turn particles into the class averages
	elif params['nptcls'] < 4:
#this is an ugly hack, just average the particles together, no ref-free
		os.mkdir(clsdir)
		avgcmd=("proc2d %s %s average" % (os.path.join(clsdir,'aligned.spi'),os.path.join(clsdir,'classes_avg.spi')))
		if params['proc']==1:
			os.system(avgcmd)
		corancmd+=avgcmd+'\n'
		dummyclsdir=os.path.join(clsdir,'classes')
		os.mkdir(dummyclsdir)
		dummyfilename='clhc_cls0001.spi'
		dummyfile=open(os.path.join(dummyclsdir,dummyfilename),'w')
		dummyfile.write(';bat/spi\n')
		for ptcl in range(0,params['nptcls']):
			dummyfile.write('%d 1 %d\n' % (ptcl,ptcl+1))
		dummyfile.close()
		print "WARNING!! not enough particles in class for subclassification"

	# otherwise, run coran
	else:
		makeSpiderCoranBatch(params,coranbatch,clsdir)
		spidercmd = ("spider bat/spi @%s\n" % coranbatch.split('.')[0])
		## if multiprocessor, don't run spider yet
		if params['proc'] == 1:
			os.system(spidercmd)
		corancmd+=spidercmd
		return corancmd
	
#===============================
def readRefFreeDocFile(docfile, picklefile):
	apDisplay.printMsg("processing alignment doc file")
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 4:
			continue
		partdict = {
			'num': int(data[0]),
			'rot': float(data[2]),
			'xshift': float(data[3]),
			'yshift': float(data[4]),
		}
		partlist.append(partdict)
	docf.close()
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def refBasedAlignParticles(stackfile, templatestack, 
		origstackfile, 
		xysearch, xystep, 
		numpart, numtemplate,
		firstring=2, lastring=100, 
		dataext=".spi", 
		iternum=1, oldpartlist=None):
	"""
	inputs:
		stack
		template
		search params
	outputs:
		aligned stack
		rotation/shift params
	"""
	### setup
	if dataext in templatestack:
		templatestack = templatestack[:-4]
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	if dataext in origstackfile:
		origstackfile = origstackfile[:-4]
	t0 = time.time()
	rundir = "alignments"
	apParam.createDirectory(rundir)
	nproc = apParam.getNumProcessors()

	### remove previous iterations
	apFile.removeFile(rundir+"/paramdoc%02d%s" % (iternum, dataext))

	### perform alignment, should I use 'AP SH' instead?
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc)
	mySpider.toSpider("AP MQ", 
		spyder.fileFilter(templatestack)+"@**",     # reference image series
		"1-"+str(numtemplate),                      # enter number of templates of doc file
		str(int(xysearch))+","+str(int(xystep)),    # translation search range, step size
		str(int(firstring))+","+str(int(lastring)), # first and last ring for rotational correlation
		spyder.fileFilter(stackfile)+"@******",     # unaligned image series
		"1-"+str(numpart),                          # enter number of particles of doc file
		rundir+("/paramdoc%02d" % (iternum)),       # output angles document file
	)
	mySpider.close()

	### convert spider rotation, shift data to python
	docfile = rundir+("/paramdoc%02d" % (iternum))+dataext
	picklefile = rundir+("/paramdoc%02d" % (iternum))+".pickle"
	if oldpartlist is not None and iternum > 1:
		apDisplay.printMsg("updating particle doc info")
		partlist = updateRefBasedDocFile(oldpartlist, docfile, picklefile)
	elif iternum == 1:	
		apDisplay.printMsg("reading initial particle doc info")
		partlist = readRefBasedDocFile(docfile, picklefile)
	else:
		apDisplay.printError("reading (not updating) particle doc info on iteration "+str(iternum))

	### write aligned stack -- with python loop
	alignedstack = rundir+("/alignedstack%02d" % (iternum))
	alignStack(origstackfile, alignedstack, partlist, dataext)

	### average stack
	emancmd = ( "proc2d "+alignedstack+dataext+" "
		+rundir+("/avgimg%02d" % (iternum))+".mrc "
		+" average")
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	td1 = time.time()-t0
	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return alignedstack+dataext, partlist

#===============================
def updateRefBasedDocFile(oldpartlist, docfile, picklefile):
	apDisplay.printMsg("updating data from alignment doc file "+docfile)
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 6:
			continue
		templatenum = float(data[2])
		newpartdict = {
			'num': int(data[0]),
			'template': int(abs(templatenum)),
			'mirror': checkMirror(templatenum),
			'score': float(data[3]),
			'rot': wrap360(float(data[4])),
			'xshift': float(data[5]),
			'yshift': float(data[6]),
		}
		oldpartdict = oldpartlist[newpartdict['num']-1]
		### this is wrong because the shifts are not additive without a back rotation
		if newpartdict['num'] == oldpartdict['num']:
			adjxshift = ( oldpartdict['xshift']*math.cos(math.radians(newpartdict['rot'])) 
				- oldpartdict['yshift']*math.sin(math.radians(newpartdict['rot'])) )
			adjyshift = ( oldpartdict['xshift']*math.sin(math.radians(newpartdict['rot'])) 
				+ oldpartdict['yshift']*math.cos(math.radians(newpartdict['rot'])) )
			partdict = {
				'num': newpartdict['num'],
				'template': newpartdict['template'],
				'score': newpartdict['score'],
				'mirror': bool(oldpartdict['mirror']-newpartdict['mirror']),
				'rot': wrap360(oldpartdict['rot']+newpartdict['rot']),
				'xshift': adjxshift + newpartdict['xshift'],
				'yshift': adjyshift + newpartdict['yshift'],
			}
		else:
			print oldpartdict
			print newpartdict
			apDisplay.printError("wrong particle in update")
		#if partdict['num'] in [3,6,7]:
		#	print "old", oldpartdict['num'], oldpartdict['template'], oldpartdict['mirror'], round(oldpartdict['rot'],3)
		#	print "new", newpartdict['num'], newpartdict['template'], newpartdict['mirror'], round(newpartdict['rot'],3)
		#	print "update", partdict['num'], partdict['template'], partdict['mirror'], round(partdict['rot'],3)
		partlist.append(partdict)
	docf.close()
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def wrap360(theta):
	f = theta % 360
	if f > 180:
		f = f - 360
	return f

#===============================
def readRefBasedDocFile(docfile, picklefile):
	apDisplay.printMsg("processing alignment doc file "+docfile)
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 6:
			continue
		templatenum = float(data[2])
		partdict = {
			'num': int(data[0]),
			'template': int(abs(templatenum)),
			'mirror': checkMirror(templatenum),
			'score': float(data[3]),
			'rot': wrap360(float(data[4])),
			'xshift': float(data[5]),
			'yshift': float(data[6]),
		}
		partlist.append(partdict)
	docf.close()
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def checkMirror(templatenum):
	if templatenum < 0:
		return True
	return False

#===============================
def alignStack(oldstack, alignedstack, partlist, dataext=".spi"):
	"""
	write aligned stack -- with python loop

	inputs:
		oldstack
		newstack (empty)
		list of particle dictionaries for operations
	modifies:
		newstack
	output:
		none

	I tried this loop in both spider and python; 
	python was faster?!? -neil
	"""
	if not os.path.isfile(oldstack+dataext):
		apDisplay.printError("Could not find original stack: "+oldstack+dataext)
	boxsize = apFile.getBoxSize(oldstack+dataext)

	apDisplay.printMsg("applying alignment parameters to stack")
	apFile.removeFile(alignedstack+dataext)
	count = 0
	t0 = time.time()
	nproc = apParam.getNumProcessors()

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc)
	#create stack in core
	numpart = len(partlist)
	mySpider.toSpiderQuiet(
		"MS I", #command
		"_2@", #name
		"%d,%d,1"%(boxsize), #boxsize
		str(numpart+1), #num part to create in memory
		str(numpart+1), #max particle number
	)
	for partdict in partlist:
		partnum = partdict['num']
		#if partdict['num'] in [3,6,7]:
		#	print partdict['num'], partdict['template'], partdict['mirror'], round(partdict['rot'],3)

		### Rotate and Shift operations
		count += 1
		#rotate/shift
		mySpider.toSpiderQuiet(
			"RT SQ",
			spyder.fileFilter(oldstack)+"@"+("%06d" % (partnum)),
			"_1",
			str(partdict['rot']), str(partdict['xshift'])+","+str(partdict['yshift']),
		)
		#mirror, if necessary
		if 'mirror' in partdict and partdict['mirror'] is True:
			mySpider.toSpiderQuiet(
				"MR", "_1",
				"_2@"+("%06d" % (partnum)),	"Y", 
			)
		else:
			mySpider.toSpiderQuiet(
				"CP", "_1",
				"_2@"+("%06d" % (partnum)),
			)

	### finish up
	#save stack to file
	mySpider.toSpiderQuiet(
		"CP", "_2@",
		spyder.fileFilter(alignedstack)+"@",	
	)
	#delete stack
	mySpider.toSpiderQuiet(
		"DE", "_2",
	)
	mySpider.close()

	apDisplay.printMsg("Completed transforming %d particles in %s"%(count, apDisplay.timeString(time.time()-t0)))

	if not os.path.isfile(alignedstack+dataext):
		apDisplay.printError("Failed to create stack "+alignedstack+dataext)

	return


#===============================
def correspondenceAnalysis(alignedstack, boxsize, maskpixrad, numpart, numfactors=8, dataext=".spi"):
	"""
	inputs:
		aligned stack
		search params
	outputs:
		eigen images
		eigen vectors
		coran parameters
	"""
	### setup
	if dataext in alignedstack:
		alignedstack = alignedstack[:-4]
	t0 = time.time()
	rundir = "coran"
	apParam.createDirectory(rundir)

	### make template in memory
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpiderQuiet("MO", "_9", "%d,%d" % (boxsize, boxsize), "C", str(maskpixrad*2.0))

	### performing correspondence analysis
	apDisplay.printMsg("Performing correspondence analysis (long wait)")
	mySpider.toSpider(
		"CA S",
		spyder.fileFilter(alignedstack)+"@******", "1-"+str(numpart),
		"_9", str(numfactors), "C", "10",
		rundir+"/corandata")
	mySpider.close()

	contriblist = analyzeEigenFactors(alignedstack, rundir, numpart, numfactors, dataext)

	td1 = time.time()-t0
	apDisplay.printMsg("completed correspondence analysis of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return contriblist


#===============================
def analyzeEigenFactors(alignedstack, rundir, numpart, numfactors=8, dataext=".spi"):
	"""
	inputs:
		coran run data
	outputs:
		1. generate eigen images
		2. collect eigenimage contribution percentage
		3. 2D factor plot
		Broken 4. 2D factor plot visualization
	"""
	### 1. generate eigen images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	for fact in range(1,numfactors+1):
		mySpider.toSpiderQuiet(
			#"CA SRE", rundir+"/corandata", str(fact), 
			#rundir+"/eigenstack@"+("%02d" % (fact)), )
			"CA SRD", rundir+"/corandata", str(fact), str(fact), 
			rundir+"/eigenstack@***", )
	mySpider.close()

	### convert to nice individual eigen image pngs for webpage
	for fact in range(1,numfactors+1):
		pngfile = rundir+"/eigenimg"+("%02d" % (fact))+".png"
		apFile.removeFile(pngfile)
		emancmd = ("proc2d "+rundir+"/eigenstack.spi "
			+pngfile+" "
			+" first="+str(fact-1)+" last="+str(fact-1))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	### convert eigen SPIDER stack to IMAGIC for stack viewer
	eigenstack = rundir+"/eigenstack.hed"
	apFile.removeStack(eigenstack)
	emancmd = "proc2d "+rundir+"/eigenstack.spi "+eigenstack
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	### 2. collect eigenimage contribution percentage
	eigf = open(rundir+"/corandata_EIG"+dataext, "r")
	count = 0
	contriblist = []
	for line in eigf:
		bits = line.strip().split()
		if len(contriblist) == numfactors:
			break
		if len(bits) < 3:
			continue
		contrib = float(bits[1])
		cumm = float(bits[2])
		eigval = float(bits[0])
		if len(bits) == 3:
			count += 1
			contriblist.append(contrib)
			print "Factor", count, contrib, "%\t", cumm, "%\t", eigval
	### need to plot & insert this data

	### hack to get 'CA VIS' to work: break up stack into individual particles
	"""
	### this is broken in SPIDER 13.0
	apParam.createDirectory("unstacked")
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet(
		"DO LB1 i=1,"+str(numpart),
		" CP",
		" "+alignedstack+"@{******x0}",
		" unstacked/img{******x0}",
		"LB1",
	)
	mySpider.close()
	"""

	### generate factor maps
	apDisplay.printMsg("creating factor maps")
	for f1 in range(1,min(numfactors,2)):
		for f2 in range(f1+1, numfactors+1):
			sys.stderr.write(".")
			try:
				createFactorMap(f1, f2, rundir, dataext)
			except:
				sys.stderr.write("#")
				pass
	sys.stderr.write("\n")

	return contriblist

#===============================
def createFactorMap(f1, f2, rundir, dataext):
	### 3. factor plot
	apParam.createDirectory(rundir+"/factors", warning=False)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	factorfile = rundir+"/factors/factorps"+("%02d-%02d" % (f1,f2))
	mySpider.toSpiderQuiet(
		"CA SM", "I",
		rundir+"/corandata", #coran prefix
		"0",
		str(f1)+","+str(f2), #factors to plot
		"S", "+", "Y", 
		"5", "0",
		factorfile, 
		"\n\n\n\n","\n\n\n\n","\n", #9 extra steps, use defaults
	)
	time.sleep(2)
	mySpider.close()
	# hack to get postscript converted to png, require ImageMagick
	convertPostscriptToPng(factorfile+".ps", factorfile+".png", size=200)
	apFile.removeFile(factorfile+".ps")

	### 4. factor plot visualization
	"""
	### this is broken in SPIDER 13.0
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"SD C", #create coordinate file
		rundir+"/corandata", #coran prefix	
		str(f1)+","+str(f2), #factors to plot
		rundir+"/sdcdoc"+("%02d%02d" % (f1,f2)),
	)
	visimg = rundir+"/visimg"+("%02d%02d" % (f1,f2))
	mySpider.toSpider(
		"CA VIS", #visualization	
		"(1024,1024)",
		rundir+"/sdcdoc"+("%02d%02d" % (f1,f2)), #input doc from 'sd c'
		rundir+"/visdoc"+("%02d%02d" % (f1,f2)), #output doc
		"alignedstack@00001", # image in series ???
		"(12,12)", #num of rows, cols
		"5.0",       #stdev range
		"(5.0,5.0)",   #upper, lower thresh
		visimg, #output image
		"1,"+str(numpart),
		"1,2",
	)
	mySpider.close()
	emancmd = ("proc2d "+visimg+dataext+" "+visimg+".png ")
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
	"""
	return

#===============================
def makeDendrogram(alignedstack, numfactors=1, corandata="coran/corandata", dataext=".spi"):

	rundir = "cluster"
	apParam.createDirectory(rundir)
	### make list of factors 	 
	factorstr = "" 	 
	for fact in range(1,numfactors+1): 	 
		factorstr += str(fact)+","
	factorstr = factorstr[:-1]

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"CL HC",
		corandata+"_IMC", # path to coran data
		factorstr, # factor string
	)

	## weight for each factor
	for fact in range(numfactors):
		mySpider.toSpiderQuiet("1.0")	 
	mySpider.toSpider(
		"5",         #use Ward's method
		"T", "5.1", rundir+"/dendrogram.ps",  #dendrogram image file
		"Y", rundir+"/dendrogramdoc", #dendrogram doc file
	)
	mySpider.close()

	convertPostscriptToPng("cluster/dendrogram.ps", "dendrogram.png")

#===============================
def convertPostscriptToPng(psfile, pngfile, size=1024):

	### better pstopnm pre-step
	pstopnmcmd = "pstopnm -xsize=2000 -ysize=2000 -xborder=0 -yborder=0 -portrait "+psfile
	apEMAN.executeEmanCmd(pstopnmcmd, verbose=False, showcmd=False)

	### direct conversion
	ppmfile = os.path.splitext(psfile)[0]+"001.ppm"
	if os.path.isfile(ppmfile):
		imagemagickcmd = ("convert -colorspace Gray -trim -resize "
			+str(size)+"x"+str(size)+" "+ppmfile+" "+pngfile)
	else:
		ppmfile = psfile+"001.ppm"
		if os.path.isfile(ppmfile):
			imagemagickcmd = ("convert -colorspace Gray -trim -resize "
				+str(size)+"x"+str(size)+" "+ppmfile+" "+pngfile)
		else:
			imagemagickcmd = ("convert -colorspace Gray -trim -resize "
				+str(size)+"x"+str(size)+" "+psfile+" "+pngfile)
	apEMAN.executeEmanCmd(imagemagickcmd, verbose=False, showcmd=False)

	if os.path.isfile(ppmfile):
		apFile.removeFile(ppmfile)

	if not os.path.isfile(pngfile):
		apDisplay.printWarning("Postscript image conversion failed")	


#===============================
def hierarchCluster(alignedstack, numpart=None, numclasses=40, timestamp=None,
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):

	rundir = "cluster"
	apParam.createDirectory(rundir)
	### step 1: use coran data to create hierarchy
	dendrogramfile = hierarchClusterProcess(numpart, factorlist, corandata, rundir, dataext)
	### step 2: asssign particles to groups based on hierarchy
	classavg,classvar = hierarchClusterClassify(alignedstack, dendrogramfile, numclasses, timestamp, rundir, dataext)
	return classavg,classvar

#===============================
def hierarchClusterProcess(numpart=None, factorlist=range(1,5), 
		corandata="coran/corandata", rundir=".", dataext=".spi"):
	"""
	inputs:
		coran data
		number of particles
		factor list
		output directory
	output:
		dendrogram doc file
		factorkey
	"""
	#apFile.removeFile(rundir+"/dendrogramdoc"+dataext)

	### make list of factors 	 
	factorstr = ""
	factorkey = ""	 
	for fact in factorlist: 	 
		factorstr += str(fact)+","
		factorkey += "_"+str(fact)
	factorstr = factorstr[:-1]

	dendrogramfile = rundir+"/dendrogramdoc"+factorkey+dataext
	if os.path.isfile(dendrogramfile):
		apDisplay.printMsg("Dendrogram file already exists, skipping processing "+dendrogramfile)
		return dendrogramfile

	apDisplay.printMsg("Creating dendrogram file: "+dendrogramfile)
	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"CL HC",
		spyder.fileFilter(corandata)+"_IMC", # path to coran data
		factorstr, # factor string
	)
	## weight for each factor
	for fact in factorlist:
		mySpider.toSpiderQuiet("1.0")	
	minclasssize = "%.4f" % (numpart*0.0001+2.0)
	mySpider.toSpider(
		"5",         #use Ward's method
		"T", minclasssize, rundir+"/dendrogram.ps", #dendrogram image file
		"Y", spyder.fileFilter(dendrogramfile), #dendrogram doc file
	)
	mySpider.close()

	if not os.path.isfile(dendrogramfile):
		apDisplay.printError("dendrogram creation (CL HC) failed")
	convertPostscriptToPng("cluster/dendrogram.ps", "dendrogram.png")

	return dendrogramfile

#===============================
def hierarchClusterClassify(alignedstack, dendrogramfile, numclasses=40, timestamp=None, rundir=".", dataext=".spi"):
	"""
	inputs:
		aligned particle stack
		number of classes
		timestamp
		output directory
	output:
		class averages
		class variances
		dendrogram.png
	"""
	if timestamp is None:
		timestamp = time.strftime("%y%b%d").lower()+lowercase[time.localtime()[4]%26]

	classavg = rundir+"/"+("classavgstack_%s_%03d" %  (timestamp, numclasses))
	classvar = rundir+"/"+("classvarstack_%s_%03d" %  (timestamp, numclasses))

	thresh, classes = findThreshold(numclasses, dendrogramfile, rundir, dataext)

	### create class doc files
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"CL HE",
		thresh,
		spyder.fileFilter(dendrogramfile), # dendrogram doc file 
		rundir+"/classdoc_"+timestamp+"_****", # class doc file
	)

	### delete existing files
	sys.stderr.write("delete existing files")
	for dext in (".hed", ".img", dataext):
		apFile.removeFile(classavg+dext)
		apFile.removeFile(classvar+dext)
	print ""

	### create class averages
	sys.stderr.write("create class averages")
	for i in range(classes):
		sys.stderr.write(".")
		classnum = i+1
		mySpider.toSpiderQuiet(
			"AS R",
			spyder.fileFilter(alignedstack)+"@******",
			rundir+("/classdoc_"+timestamp+"_%04d" % (classnum)),
			"A",
			(classavg+"@%04d" % (classnum)),
			(classvar+"@%04d" % (classnum)),
		)
	mySpider.close()
	print ""

	### convert to IMAGIC
	emancmd = "proc2d "+classavg+".spi "+classavg+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
	emancmd = "proc2d "+classvar+".spi "+classvar+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	return classavg,classvar


#===============================
def kmeansCluster(alignedstack, numpart=None, numclasses=40, timestamp=None,
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	inputs:

	outputs:

	"""
	if timestamp is None:
		timestamp = time.strftime("%y%b%d").lower()+lowercase[time.localtime()[4]%26]

	if alignedstack[-4:] == dataext:
		alignedstack = alignedstack[:-4]

	rundir = "cluster"
	classavg = rundir+"/"+("classavgstack_%s_%03d" %  (timestamp, numclasses))
	classvar = rundir+"/"+("classvarstack_%s_%03d" %  (timestamp, numclasses))
	apParam.createDirectory(rundir)
	for i in range(numclasses):
		apFile.removeFile(rundir+("/classdoc%04d" % (i+1))+dataext)
	apFile.removeFile(rundir+("/allclassesdoc%04d" % (numclasses))+dataext)

	### make list of factors 	 
	factorstr = "" 	 
	for fact in factorlist: 	 
		factorstr += str(fact)+","
	factorstr = factorstr[:-1]

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider(
		"CL KM",
		corandata+"_IMC", # path to coran data
		str(numclasses), # num classes
		factorstr, # factor string
	)
	## weight for each factor
	for fact in factorlist:
		mySpider.toSpiderQuiet("1.0")	
	randnum = (int(random.random()*1000) + 1)
	mySpider.toSpider(
		str(randnum),
		rundir+"/classdoc_"+timestamp+"_****", # class doc file
		rundir+("/allclassesdoc%04d" % (numclasses)),	#clusterdoc file
	)
	mySpider.close()

	### delete existing files
	sys.stderr.write("delete existing files")
	for dext in (".hed", ".img", dataext):
		apFile.removeFile(classavg+dext)
		apFile.removeFile(classvar+dext)
	print ""

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	### create class averages
	apDisplay.printMsg("Averaging particles into classes")
	for i in range(numclasses):
		classnum = i+1
		mySpider.toSpiderQuiet(
			"AS R",
			spyder.fileFilter(alignedstack)+"@******",
			rundir+("/classdoc_"+timestamp+"_%04d" % (classnum)),
			"A",
			(classavg+"@%04d" % (classnum)),
			(classvar+"@%04d" % (classnum)),
		)
		if classnum % 10 == 0:
			sys.stderr.write(".")
		time.sleep(1)
	mySpider.close()

	### convert to IMAGIC
	emancmd = "proc2d "+classavg+".spi "+classavg+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
	emancmd = "proc2d "+classvar+".spi "+classvar+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	return classavg,classvar

#===============================
def ClCla(alignedstack, numpart=None, numclasses=40, 
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	this doesn't work
	"""
	if alignedstack[-4:] == dataext:
		alignedstack = alignedstack[:-4]

	rundir = "cluster"
	classavg = rundir+"/"+("classavgstack%03d" % numclasses)
	classvar = rundir+"/"+("classvarstack%03d" % numclasses)
	apParam.createDirectory(rundir)
	for i in range(numclasses):
		apFile.removeFile(rundir+("/classdoc%04d" % (i+1))+dataext)
	apFile.removeFile(rundir+"/clusterdoc"+dataext)

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider(
		"CL CLA",
		corandata, # path to coran data
		rundir+"/clusterdoc",	#clusterdoc file
		str(factorlist[-1]), #factor numbers
		"5,8", 
		"4", 
		"2", # minimum number of particles per class
		"Y", rundir+"/dendrogram.ps",
		"Y", rundir+"/dendrogramdoc",
	)
	mySpider.close()

#===============================
def findThreshold(numclasses, dendrogramdocfile, rundir, dataext):
	if not os.path.isfile(dendrogramdocfile):
		apDisplay.printError("dendrogram doc file does not exist")

	### determining threshold cutoff for number of classes
	minthresh = 0.0
	maxthresh = 1.0
	minclass = 0.0
	maxclass = 1.0
	classes = 0
	count = 0

	sys.stderr.write("finding threshold")
	while(classes != numclasses and count < 50):
		count += 1
		if count % 70 == 0:
			sys.stderr.write("\n["+str(minclass)+"->"+str(minclass)+"]")
		thresh = (maxthresh-minthresh)/3.0 + minthresh
		classfile = rundir+"/classes"
		apFile.removeFile(classfile+dataext)
		mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
		mySpider.toSpiderQuiet(
			"CL HD",
			thresh, #threshold
			spyder.fileFilter(dendrogramdocfile), # dendrogram doc file 
			classfile
		)
		mySpider.close()
		claf = open(classfile+dataext, "r")
		classes = len(claf.readlines()) - 1
		claf.close()
		if classes > numclasses:
			minthresh = thresh
			maxclass = classes
			sys.stderr.write(">")
		elif classes < numclasses:
			maxthresh = thresh
			minclass = classes
			sys.stderr.write("<")
		#print " ",count, classes, thresh, maxthresh, minthresh
	print count, "rounds for", classes, "classes"

	return thresh, classes

def makeSpiderCoranBatch(params,filename,clsdir):
	nfacts=20
	if params['nptcls'] < 21:
		nfacts=params['nptcls']-1
	f=open(filename,'w')
	f.write('MD ; verbose off in spider log file\n')
	f.write('VB OFF\n')
	f.write('\n')
	f.write('MD\n')
	f.write('SET MP\n')
	f.write('%d\n' % 4)
	f.write('\n')
	f.write('x99=%d  ; number of particles in stack\n' % params['nptcls']) 
	f.write('x98=%d   ; box size\n' % params['boxsize'])
	f.write('x94=%d    ; mask radius\n' % params['mask'])
	f.write('x93=%f  ; cutoff for hierarchical clustering\n' % params['haccut'])
	f.write('x92=20    ; additive constant for hierarchical clustering\n')
	f.write('\n')
	f.write('FR G ; aligned stack file\n')
	f.write('[aligned]%s/aligned\n' % clsdir)
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('FR G ; home dir\n')
	f.write('[home]%s/\n' % clsdir)
	f.write('\n')
	f.write('FR G ; where to write class lists\n')
	f.write('[clhc_cls]%s/classes/clhc_cls\n' % clsdir)
	f.write('\n')
	f.write('FR G ; where to write alignment data\n')
	f.write('[ali]%s/alignment/\n' % clsdir)
	f.write('\n')
	f.write('VM\n')
	f.write('mkdir %s/alignment\n' % clsdir) 
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write(';; create the sequential file and then use that file and do a hierarchical ;;\n')
	f.write(';; clustering. Run clhd and clhe to classify the particles into different  ;;\n')
	f.write(';; groups.                                                                 ;;\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo Performing multivariate statistical analysis\n')
	f.write('VM\n')
	f.write('echo "  making template file"\n')
	f.write('\n')
	f.write('MO      ; make mask template\n')
	f.write('_9      ; save template in memory\n')
	f.write('x98,x98 ; box size\n')
	f.write('c       ; circle\n')
	f.write('x94     ; radius of mask\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo "  doing correspondence analysis"\n')
	f.write('\n')
	f.write('CA S           ; do correspondence analysis\n')
	f.write('[aligned]@***** ; aligned stack\n')
	f.write('1-x99          ; particles to use\n')
	f.write('_9             ; mask file\n')
	f.write('%d             ; number of factors to be used\n' % nfacts)
	f.write('C              ; Coran analysis\n')
	f.write('x92            ; additive constant (since coran cannot have negative values)\n')
	f.write('[ali]coran     ; output file prefix\n')
	f.write('\n')
	f.write('\n')
	f.write('DO LB14 x11=1,%d\n' % nfacts)
	f.write('CA SRE\n')
	f.write('[ali]coran\n')
	f.write('x11\n')
	f.write('[ali]sre@{***x11}\n')
	f.write('LB14\n')
	f.write('\n')
	#f.write('VM\n')
	#f.write('eigendoc.py alignment/coran_EIG.spi alignment/eigendoc.out 30\n')
	#f.write('\n')
	f.write('VM\n')
	f.write('echo "  clustering..."\n')
	f.write('\n')
	f.write('CL HC          ; do hierarchical clustering\n')
	f.write('[ali]coran_IMC ; coran image factor coordinate file\n')
	f.write('1-3\n')
	f.write('1.00           ; factor numbers to be included in clustering algorithm\n')
	f.write('1.00           ; factor weights\n')
	f.write('1.00           ; for each factor number\n')
	f.write('5              ; use Wards method\n')
	f.write('Y              ; make a postscript of dendogram\n')
	f.write('[ali]clhc.ps   ; dendogram image file\n')
	f.write('Y              ; save dendogram doc file\n')
	f.write('[ali]clhc_doc  ; dendogram doc file\n')
	f.write('\n')
	f.write('\n')
	f.write(';;;determine number of classes for given threshold\n')
	f.write('CL HD\n')
	f.write('x93\n')
	f.write('[ali]clhc_doc\n')
	f.write('[home]clhc_classes\n')
	f.write('\n')
	f.write('UD N,x12\n')
	f.write('[home]clhc_classes\n')
	f.write('\n')
	f.write('VM\n')
	f.write('mkdir %s/classes\n' % clsdir)
	f.write('\n')
	f.write('VM\n')
	f.write('echo "Creating {%F5.1%x12} classes using a threshold of {%F7.5%x93}"\n')
	f.write('CL HE         ; generate doc files containing particle numbers for classes\n')
	f.write('x93         ; threshold (closer to 0=more classes)\n')
	f.write('[ali]clhc_doc      ; dendogram doc file\n')
	f.write('[clhc_cls]****  ; selection doc file that will contain # of objects for classes\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write(';; average aligned particles together ;;\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo Averaging particles into classes\n')
	f.write('\n')
	f.write('DO LB20 x81=1,x12\n')
	f.write('AS R\n')
	f.write('[aligned]@*****\n')
	f.write('[clhc_cls]{****x81}\n')
	f.write('A\n')
	f.write('[home]classes_avg@{****x81}\n')
	f.write('[home]classes_var@{****x81}\n')
	f.write('LB20\n')
	f.write('\n')
	f.write('EN D\n')
