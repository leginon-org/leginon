#!/usr/bin/env python

import glob,os,sys
import EMAN
import shutil
import math
import string
import re

clslist=glob.glob('cls*.lst')

def makeSpiderBatch(params,filename,clsdir):
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

def getNPtcls(filename):
	f=open(filename)
	lines=f.readlines()
	f.close()
	nlines=len(lines)
	return(nlines-2)

def cc(img1,img2):
	npix=img1.xSize()*img1.ySize()
	avg1=img1.Mean()
	avg2=img2.Mean()
	
	var1=img1.Sigma()
	var1=var1*var1
	var2=img2.Sigma()
	var2=var2*var2
	
	cc=img1.dot(img2)
	cc=cc/npix
	cc=cc-(avg1*avg2)
	cc=cc/math.sqrt(var1*var2)
	return(cc)

def parseInput(args,params):
	for arg in args:
		elements=arg.split('=')
		if elements[0]=='iter':
			params['iter']=int(elements[1])
		elif elements[0]=='mask':
			params['mask']=int(elements[1])
		elif elements[0]=='haccut':
			params['haccut']=float(elements[1])
		elif elements[0]=='proc':
			params['proc']=int(elements[1])
		elif elements[0]=='sym':
			params['sym']=elements[1]
		elif elements[0]=='hard':
			params['hard']=int(elements[1])
		elif arg=='eotest':
			params['eotest']=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
def createDefaults():
	params={}
	params['corandir']='coran'
	params['mask']=None
	params['iter']=None
	params['haccut']=0.15
	params['proc']=1
	params['sym']='c1'
	params['hard']=None
	params['eotest']=False
	return(params)
	
def getNPtclsSpider(filepath):
	f=open(filepath,'r')
	lines=f.readlines()
	f.close()
	return(len(lines)-1)
	
def convertSpiderToEMAN(spifile, origlst):
	fileroot = os.path.splitext(spifile)[0]
	outfile = fileroot+".lst"
	inlines = open(spifile, "r")
	out = open(outfile, "w")
	out.write('#LST\n')

	# save ptls in an array from cls####.lst file
	origptls=[]
	f=open(origlst,'r')
	for line in f:
		n=line.split('\t')
		if re.match("^[0-9]+",n[0]) and n[1].strip()!="proj.img":
			origptls.append(line)

	# create new lst file
	for line in inlines:
		if line.strip()[0]!=';':
			words = line.split()
			ptcl = int(float(words[2]))
			# get this particle in the cls####.lst array
			spiptcl = origptls[ptcl-1]
			out.write(spiptcl)
	out.close()
	inlines.close()
	return outfile

def makeClassAverages(lst, outputstack,e,mask):
        #align images in class
	print "creating class average from",lst,"to",outputstack
        images=EMAN.readImages(lst,-1,-1,0)
        for image in images:
                image.rotateAndTranslate()
                if image.isFlipped():
                        image.hFlip()

        #make class average
        avg=EMAN.EMData()
        avg.makeMedian(images)

        #write class average
        avg.setRAlign(e)
        avg.setNImg(len(images))
        avg.applyMask(params['mask'],0)
        avg.writeImage(outputstack,-1)

if __name__== '__main__':
	#Parse inputs
	args=sys.argv[1:]
	params=createDefaults()
	parseInput(args,params)
	
	#Determine box size
	tmpimg=EMAN.readImages('start.hed',1,1)
	params['boxsize']=tmpimg[0].xSize()
	#Set up for coran
	if os.path.exists(params['corandir']):
		print "Warning %s exists and is being overwritten" % params['corandir']
		shutil.rmtree(params['corandir'])
		os.mkdir(params['corandir'])
	else:
		os.mkdir(params['corandir'])
	classfile='cls.'+str(params['iter'])+'.tar'
	shutil.copy(classfile,os.path.join(params['corandir'],classfile))
	shutil.copy('proj.hed',os.path.join(params['corandir'],'proj.hed'))
	shutil.copy('proj.img',os.path.join(params['corandir'],'proj.img'))
	os.chdir(params['corandir'])
	os.system('tar xf %s' % classfile)
	os.system('ln -s ../start.hed .')
	os.system('ln -s ../start.img .')
	
	#Loop through classes and prepare for spider
	clslist=glob.glob('cls*.lst')
	# sort the list numerically
	clslist.sort()

	projections=EMAN.readImages('proj.hed',-1,-1,0)
	if len(projections)!=len(clslist):
		print "Error: Number of projections (%d) not equal to number of classes (%d)" % (len(projections),len(clslist))
		sys.exit()

	f=open('commands.txt','w')
	for cls in clslist:
		#make aligned stack
		command='clstoaligned.py ' + cls
		print command
		os.system(command)
		
		#set up cls dir
		clsdir=cls.split('.')[0]+'.dir'
		os.mkdir(clsdir)
	
		os.rename('aligned.spi',os.path.join(clsdir,'aligned.spi'))
		
		coranbatch='coranfor'+cls.split('.')[0]+'.bat'
		print coranbatch

		#make spider batch
		params['nptcls']=getNPtcls(cls)
		# if only 3 particles or less, turn particles into the class averages
		if params['nptcls'] < 4:
			#this is an ugly hack because spider sux
			os.system("proc2d %s %s average" % (os.path.join(clsdir,'aligned.spi'),os.path.join(clsdir,'classes_avg.spi')))
			dummyclsdir=os.path.join(clsdir,'classes')
			os.mkdir(dummyclsdir)
			dummyfilename='clhc_cls0001.spi'
			dummyfile=open(os.path.join(dummyclsdir,dummyfilename),'w')
			dummyfile.write(';bat/spi\n')
			for ptcl in range(0,params['nptcls']):
				dummyfile.write('%d 1 spidersux\n' % ptcl)
			dummyfile.close()
		# otherwise, run coran
		else:
			makeSpiderBatch(params,coranbatch,clsdir)
			os.system("spider bat/spi @%s\n" % coranbatch.split('.')[0])
		
	f.close()
	print "Running spider"
	#os.system('runpar proc=%d file=%s' % (params['proc'],'commands.txt'))

	#Determine best averages
	#Create list of cc values	
	for cls in range(0,len(clslist)):
		avgname=os.path.join(clslist[cls].split('.')[0]+'.dir','classes_avg.spi')
		averages=EMAN.readImages(avgname,-1,-1,0)
		e=projections[cls].getEuler()
		cclist=[]
		projections[cls].setNImg(-1)
		projections[cls].writeImage('goodavgs.hed',-1)
		print "CC Values:"
		for avg in averages:
			ccval=cc(projections[cls],avg)
			cclist.append(ccval)
			avg.setNImg(10)
			avg.setRAlign(e)
			avg.writeImage('allavgs.hed',-1)
			print ccval
		bestclass=cclist.index(max(cclist))
		print "Using average %d for class %d" % (bestclass, cls)

		#get N imgs
		classnamepath = clslist[cls].split('.')[0]+'.dir/classes'
		clhcbasename = 'clhc_cls'+string.zfill(bestclass+1,4)
		classname=os.path.join(classnamepath, clhcbasename+'.spi')
		
		nptcls=getNPtclsSpider(classname)
		averages[bestclass].setNImg(nptcls)
		averages[bestclass].setRAlign(e)
		averages[bestclass].writeImage('goodavgs.hed',-1)

		# convert spider lst to EMAN lst
		convertlst = convertSpiderToEMAN(classname,clslist[cls])
		f = open(convertlst,'r')
		f.readline()
		lines=f.readlines()
		f.close()

		if params['eotest'] is True:
			# set up even & odd lst files
			evenlst = os.path.join(classnamepath, clhcbasename+'.even.lst')
			oddlst = os.path.join(classnamepath, clhcbasename+'.odd.lst')
			even = open(evenlst,'w')
			odd = open(oddlst,'w')
			even.write("#LST\n")
			odd.write("#LST\n")
			neven=0
			nodd=0
			for line in range(0,len(lines)):
				newline = re.sub('start','../../start',lines[line])
				if line%2:
					nodd+=1
					odd.write(newline)
				else:
					neven+=1
					even.write(newline)
			even.close()
			odd.close()

			# create even and odd class stacks
			evenstack = 'goodavgs.even.hed'
			oddstack = 'goodavgs.odd.hed'

			if neven>0:
				makeClassAverages(evenlst,evenstack,e,params['mask'])
			if nodd>0:
		       		makeClassAverages(oddlst,oddstack,e,params['mask'])
			

	pad=params['boxsize']*1.25
	if pad%2:
		pad=pad+1
	# create 3d model:
	make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], params['sym'], pad, params['hard'])
	print make3dcommand
	os.system(make3dcommand)
	proc3dcommand='proc3d threed.%d.mrc ../threed.%da.mrc mask=%d norm' % (params['iter'],params['iter'],params['mask'])
	print proc3dcommand
	os.system(proc3dcommand)

	if params['eotest'] is True:
		# create even 3d model:
		make3dcommand='make3d goodavgs.even.hed out=threed.te.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['mask'], params['sym'], pad, params['hard'])
		print make3dcommand
		os.system(make3dcommand)

		# create odd 3d model:
		make3dcommand='make3d goodavgs.odd.hed out=threed.to.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['mask'], params['sym'], pad, params['hard'])
		print make3dcommand
		os.system(make3dcommand)
	
		# calculate fsc for even/odd models:
		fsccommand='proc3d threed.te.mrc threed.to.mrc fsc=../fsc.eotest.%d' % params['iter']
		print fsccommand
		os.system(fsccommand)
	
	mvcommand='mv ../classes.%d.hed ../classes.%d.old.hed' % (params['iter'],params['iter'])
	os.system(mvcommand)
	mvcommand='mv ../classes.%d.img ../classes.%d.old.img' % (params['iter'],params['iter'])
	os.system(mvcommand)
	mvcommand='mv goodavgs.hed ../classes.%d.hed' % params['iter']
	os.system(mvcommand)
	mvcommand='mv goodavgs.img ../classes.%d.img' % params['iter']
	os.system(mvcommand)
	
	
	print "Done!"
