
## python
import time
import os
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
	if dataext in template:
		template = template[:-4]
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	t0 = time.time()
	rundir = "alignment"
	apParam.createDirectory(rundir)

	### remove previous iterations

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
		rundir+"/paramdoc**",                       # output angles document file
	)
	mySpider.close()

	### find number of iterations

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

	### generate eigen images
	for fact in range(1,numfactors+1):
		mySpider.toSpiderQuiet(
			"CA SRE", rundir+"/corandata", str(fact), 
			rundir+"/eigenimg@"+("%02d" % (fact)), )
	mySpider.close()

	### remove worthless temporary files
	### save _PIX, _MAS for Differential images
	for tail in ["_SEQ", "_SET", "_MAS", "_PIX", ]:
		if os.path.isfile(rundir+"/corandata"+tail+dataext):
			print "x"
			#os.remove(rundir+"/corandata"+tail+dataext)

	eigf = open(rundir+"/corandata_EIG"+dataext, "r")
	count = 0
	for line in eigf:
		bits = line.strip().split()
		contrib = float(bits[1])
		cumm = float(bits[2])
		eigval = float(bits[0])
		if len(bits) == 3:
			count += 1
			print count, contrib, cumm, eigval

	### make nice pngs for webpage
	for fact in range(1,numfactors+1):
		pngfile = rundir+"/eigenimg"+("%02d" % (fact))+".png"
		if os.path.isfile(pngfile):
			os.remove(pngfile)
		emancmd = ("proc2d "+rundir+"/eigenimg.spi "
			+pngfile+" "
			+" first="+str(fact-1)+" last="+str(fact-1))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	### convert SPIDER image to IMAGIC for webpage
	eigenimg = rundir+"/eigenimg.hed"
	if os.path.isfile(eigenimg):
		os.remove(eigenimg)
		os.remove(eigenimg[:-4]+".img")
	emancmd = "proc2d "+rundir+"/eigenimg.spi "+eigenimg
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	td1 = time.time()-t0
	apDisplay.printMsg("completed correspondence analysis of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	### generate factor maps
	for f1 in range(1,numfactors):
		for f2 in range(f1+1, numfactors+1):
			### factor plot
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
				"\n\n\n\n","\n\n\n\n","\n", #9 extra steps, use default
			)
			mySpider.close()
			#hack to get postscript converted to png
			cmd = "convert -trim -size=640x640 "+factorfile+".ps "+factorfile+".png"
			print cmd
			os.popen2(cmd)

			### factor map???
			mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
			coordnums = []
			numpix = 2
			totpix = numpix*2 + 1
			for c1 in range(-1*numpix,numpix+1):
				for c2 in range(-1*numpix,numpix+1):
					prefix = rundir+"/typical"
					coordnum = ("%02d%02d" % (c1+numpix+1, c2+numpix+1))
					mySpider.toSpiderQuiet(
						"CA SRA", 
						rundir+"/corandata", #coran prefix
						str(f1)+","+str(f2), #factors to plot
						str(c1)+","+str(c2), #coordinates to plot
						prefix+coordnum,
					)
					coordnums.append(coordnum)
			numstr = ""
			for i in coordnums:
				numstr += i+","
			numstr = numstr[:-1]
			mySpider.toSpider(
				"MN S", #montage	
				prefix+"****", numstr,
				str(totpix)+",1", "2", 
				rundir+"/montage"+("%02d-%02d" % (f1,f2)),
			)
			mySpider.close()
			for i in coordnums:
				file = prefix+i+dataext
				if os.path.isfile(file):
					os.remove(prefix+i+dataext)

			### visualization
			mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
			mySpider.toSpider(
				"SD C", #create coordinate file
				rundir+"/corandata", #coran prefix	
				str(f1)+","+str(f2), #factors to plot
				rundir+"/sdcdoc"+("%02d%02d" % (f1,f2)),
			)
			mySpider.toSpider(
				"CA VIS", #visualization	
				"(700,700)",
				rundir+"/sdcdoc"+("%02d%02d" % (f1,f2)), #input doc from 'sd c'
				rundir+"/visdoc"+("%02d%02d" % (f1,f2)), #output doc
				rundir+"/corandata_MAS", # image in series ???
				"(10,10)", #num of rows, cols
				"5",       #stdev range
				"(1.5,2.5)",   #upper, lower thresh
				rundir+"/visimg"+("%02d%02d" % (f1,f2)), #output image
				"1-"+str(numpart),
				"2,3",
			)
			mySpider.close()
	return









