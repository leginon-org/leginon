
## python
import time
import os
import subprocess
## PIL
#import Image
## spider
import spyder
## appion
import apImage
import apEMAN
import apParam
import apDisplay

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def refFreeAlignParticles(stackfile, template, numpart, pixrad,
		firstring=2, lastring=100, dataext=".spi"):
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
	rundir = "alignment"
	apParam.createDirectory(rundir)

	### remove previous iterations
	numiter = 0
	while os.path.isfile(rundir+"/avgimg%02d%s" % (numiter+1, dataext)):
		os.remove(rundir+"/avgimg%02d%s" % (numiter+1, dataext))
		pngfile = rundir+"/avgimg%02d%s" % (numiter+1, ".png")
		if os.path.isfile(pngfile):
			os.remove(pngfile)
		numiter += 1

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext)
	# copy template to memory
	mySpider.toSpiderQuiet("CP", (template+"@1"), "_9") 
	mySpider.toSpider("AP SR", 
		stackfile+"@*****", "1-"+str(numpart), 
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
		apDisplay.printError("alignment failed")
	apDisplay.printMsg(str(numiter)+" alignment iterations were run by spider")

	### convert spider rotation, shift data to python

	### write aligned stack -- with python loop
	### I tried this loop in both spider and python: python was faster?!? -neil
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	for p in range(1,numpart+1):
		mySpider.toSpiderQuiet(
			"UD IC,"+str(p)+",x21,x22,x23",
			(rundir+"/paramdoc%02d" % (numiter)),
			"RT SQ",
			stackfile+"@"+("%05d" % (p)),
			"alignedstack@"+("%05d" % (p)),
			"x21", "x22,x23")
	mySpider.close()
	td1 = time.time()-t0

	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return "alignedstack.spi"

#===============================
def refBasedAlignParticles(stackfile, templatestack, 
		xysearch, xystep, 
		numpart, numtemplate,
		firstring=2, lastring=100, 
		dataext=".spi"):
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
	t0 = time.time()
	rundir = "alignment"
	apParam.createDirectory(rundir)

	### remove previous iterations
	numiter = 1

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext)
	# copy template to memory
	mySpider.toSpider("AP MQ", 
		templatestack+"@**",                        # reference image series
		"1-"+str(numtemplate),                      # enter number of templates of doc file
		str(int(xysearch))+","+str(int(xystep)),    # translation search range, step size
		str(int(firstring))+","+str(int(lastring)), # first and last ring for rotational correlation
		stackfile+"@*****",                         # unaligned image series
		"1-"+str(numpart),                          # enter number of particles of doc file
		rundir+("/paramdoc%02d" % (numiter)),                       # output angles document file
	)
	mySpider.close()

	### find number of iterations

	### convert spider rotation, shift data to python

	### write aligned stack -- with python loop
	### I tried this loop in both spider and python: python was faster?!? -neil
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	for p in range(1,numpart+1):
		mySpider.toSpiderQuiet(
			"UD IC,"+str(p)+",x21,x22,x23,x24,x25,x26",
			(rundir+"/paramdoc%02d" % (numiter)),
			"IF (X21.GT.0) THEN",
			"RT SQ",
			stackfile+"@"+("%05d" % (p)),
			"alignedstack@"+("%05d" % (p)),
			"x23", "x24,x25",
			"ELSE",
			"RT SQ",
			stackfile+"@"+("%05d" % (p)),
			"_1",
			"x23", "x24,x25",
			"MR",
			"_1",
			"alignedstack@"+("%05d" % (p)),
			"Y", "ENDIF",)
	mySpider.close()
	td1 = time.time()-t0

	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return "alignedstack.spi"

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
	mySpider = spyder.SpiderSession(dataext=dataext)
	mySpider.toSpiderQuiet("MO", "_9", "%d,%d" % (boxsize, boxsize), "C", str(maskpixrad*2))

	### performing correspondence analysis
	apDisplay.printMsg("Performing correspondence analysis (long wait)")
	mySpider.toSpider(
		"CA S",
		alignedstack+"@*****", "1-"+str(numpart),
		"_9", str(numfactors), "C", "10",
		rundir+"/corandata")
	mySpider.close()

	analyzeEigenFactors(alignedstack, rundir, numpart, numfactors, dataext)

	td1 = time.time()-t0
	apDisplay.printMsg("completed correspondence analysis of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return


#===============================
def analyzeEigenFactors(alignedstack, rundir, numpart, numfactors=8, dataext=".spi"):
	"""
	inputs:
		coran run data
	outputs:
		1. generate eigen images
		2. collect eigenimage contribution percentage
		3. 2D factor plot
		4. 2D factor plot visualization
	"""
	### 1. generate eigen images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	for fact in range(1,numfactors+1):
		mySpider.toSpiderQuiet(
			"CA SRE", rundir+"/corandata", str(fact), 
			rundir+"/eigenimg@"+("%02d" % (fact)), )
	mySpider.close()


	### convert to nice individual eigen image pngs for webpage
	for fact in range(1,numfactors+1):
		pngfile = rundir+"/eigenimg"+("%02d" % (fact))+".png"
		if os.path.isfile(pngfile):
			os.remove(pngfile)
		emancmd = ("proc2d "+rundir+"/eigenimg.spi "
			+pngfile+" "
			+" first="+str(fact-1)+" last="+str(fact-1))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	### convert eigen SPIDER stack to IMAGIC for stack viewer
	eigenimg = rundir+"/eigenimg.hed"
	if os.path.isfile(eigenimg):
		os.remove(eigenimg)
		os.remove(eigenimg[:-4]+".img")
	emancmd = "proc2d "+rundir+"/eigenimg.spi "+eigenimg
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	### 2. collect eigenimage contribution percentage
	eigf = open(rundir+"/corandata_EIG"+dataext, "r")
	count = 0
	for line in eigf:
		bits = line.strip().split()
		contrib = float(bits[1])
		cumm = float(bits[2])
		eigval = float(bits[0])
		if len(bits) == 3:
			count += 1
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
		" "+alignedstack+"@{*****x0}",
		" unstacked/img{*****x0}",
		"LB1",
	)
	mySpider.close()
	"""

	### generate factor maps
	for f1 in range(1,numfactors):
		for f2 in range(f1+1, numfactors+1):
			createFactorMap(f1, f2, rundir, dataext)
	return

#===============================
def createFactorMap(f1, f2, rundir, dataext):
	### 3. factor plot
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	factorfile = rundir+"/factorps"+("%02d-%02d" % (f1,f2))
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
	mySpider.close()
	# hack to get postscript converted to png, require ImageMagick
	cmd = "convert -trim -colorspace Gray -density 150x150 "+factorfile+".ps "+factorfile+".png"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()
	if os.path.isfile(factorfile+".png"):
		os.remove(factorfile+".ps")

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
def hierarchCluster(alignedstack, numpart,
		numclasses=40, factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	inputs:

	outputs:

	"""
	rundir = "cluster"
	apParam.createDirectory(rundir)
	### make list of factors
	factorstr = ""
	for fact in factorlist:
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
	for fact in factorlist:
		mySpider.toSpiderQuiet("1.0")	
	mySpider.toSpider(
		"5",         #use Ward's method
		"Y", rundir+"/dendogram.ps", #dendogram image file
		"Y", rundir+"/dendogramdoc", #dendogram doc file
	)
	mySpider.close()

	### determining threshold cutoff for number of classes
	thresh = 0.5
	stepsize = 0.25
	classes = 0
	count = 0
	
	while(classes != numclasses and count < 100):
		count += 1
		classfile = rundir+"/classes"
		if os.path.isfile(classfile+dataext):
			os.remove(classfile+dataext)
		mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
		mySpider.toSpiderQuiet(
			"CL HD",
			thresh, #threshold
			rundir+"/dendogramdoc", # dendogram doc file 
			classfile
		)
		mySpider.close()
		claf = open(classfile+dataext, "r")
		classes = len(claf.readlines()) - 1
		claf.close()
		print thresh, classes
		if classes > numclasses:
			thresh += stepsize
		elif classes < numclasses:
			thresh -= stepsize
		stepsize /= 2.0

	### create class doc files
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"CL HE",
		thresh,
		rundir+"/dendogramdoc", # dendogram doc file 
		rundir+"/classdoc****", # class doc file
	)

	if os.path.isfile(rundir+"/classavgimg"+dataext):
		os.remove(rundir+"/classavgimg"+dataext)
	if os.path.isfile(rundir+"/classvarimg"+dataext):
		os.remove(rundir+"/classvarimg"+dataext)

	### create class averages
	for classnum in range(1, classes):
		mySpider.toSpiderQuiet(
			"AS R",
			alignedstack+"@*****",
			rundir+("/classdoc%04d" % (classnum)),
			"A",
			rundir+("/classavgimg@%04d" % (classnum)),
			rundir+("/classvarimg@%04d" % (classnum)),
		)
	mySpider.close()

	return



def findThreshold():
	return
