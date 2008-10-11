#!/usr/bin/env python

import glob,os,sys
import EMAN
import shutil
import math
import string
import re
import apEMAN
from apSpider import alignment

clslist=glob.glob('cls*.lst')

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

if __name__== '__main__':
	#Parse inputs
	args=sys.argv[1:]
	params=createDefaults()
	parseInput(args,params)
	
	#Determine box size
	tmpimg=EMAN.readImages('start.hed',1,1)
	params['boxsize']=tmpimg[0].xSize()

	#Set up for coran
	params['corandir']=params['corandir']+str(params['iter'])
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
		print "processing class",cls
		#make aligned stack
		command='clstoaligned.py ' + cls
		print command
		os.system(command)
		
		#set up cls dir
		clsdir=cls.split('.')[0]+'.dir'
		os.mkdir(clsdir)
	
		if os.path.exists('aligned.spi'):
			os.rename('aligned.spi',os.path.join(clsdir,'aligned.spi'))
		
		coranbatch='coranfor'+cls.split('.')[0]+'.bat'

		#make spider batch
		params['nptcls']=apEMAN.getNPtcls(cls)
		# if no particles, create an empty class average
		if params['nptcls'] == 0:
			apEMAN.writeBlankImage('classes_avg.spi',params['boxsize'],0,EMAN.EMData.SINGLE_SPIDER)
			print "WARNING!! no particles in class"
			
		# if only 3 particles or less, turn particles into the class averages
		elif params['nptcls'] < 4:
			#this is an ugly hack, just average the particles together, no ref-free
			os.system("proc2d %s %s average" % (os.path.join(clsdir,'aligned.spi'),os.path.join(clsdir,'classes_avg.spi')))
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
			alignment.makeSpiderCoranBatch(params,coranbatch,clsdir)
			os.system("spider bat/spi @%s\n" % coranbatch.split('.')[0])
		
	f.close()
	print "Running spider"
	#os.system('runpar proc=%d file=%s' % (params['proc'],'commands.txt'))

	#Determine best averages
	#Create list of cc values	
	for cls in range(0,len(clslist)):
		# if no particles in class, create empty class averages
		if not os.path.exists(os.path.join(clslist[cls].split('.')[0]+'.dir','aligned.spi')):
			# blank projection image
			writeBlankImage('goodavgs.hed',params['boxsize'],-1)
			# blank class average
			writeBlankImage('goodavgs.hed',params['boxsize'],-1)
			# blank "good" average
			writeBlankImage('allavgs.hed',params['boxsize'],-1)
			if params['eotest'] is True:
				writeBlankImage('goodavgs.even.hed',params['boxsize'],-1)
				writeBlankImage('goodavgs.odd.hed',params['boxsize'],-1)
				continue
			
		avgname=os.path.join(clslist[cls].split('.')[0]+'.dir','classes_avg.spi')
		averages=EMAN.readImages(avgname,-1,-1,0)
		e=projections[cls].getEuler()
		cclist=[]
		projections[cls].setNImg(-1)
		projections[cls].writeImage('goodavgs.hed',-1)
		print "CC Values:"
		for avg in averages:
			ccval=apEMAN.getCC(projections[cls],avg)
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
		
		nptcls=apEMAN.getNPtclsSpider(classname,spider=True)
		averages[bestclass].setNImg(nptcls)
		averages[bestclass].setRAlign(e)
		averages[bestclass].writeImage('goodavgs.hed',-1)
		# convert spider lst to EMAN lst
		convertlst = apEMAN.convertSpiderToEMAN(classname,clslist[cls])

		#create new flaged class list from good particle list
		apEMAN.flagGoodParticleInClassLst(clslist[cls],convertlst)
    
		if params['eotest'] is True:
			f = open(convertlst,'r')
			f.readline()
			lines=f.readlines()
			f.close()
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
				apEMAN.makeClassAverages(evenlst,evenstack,e,params['mask'])
			if nodd>0:
		       		apEMAN.makeClassAverages(oddlst,oddstack,e,params['mask'])
			

	pad=int(params['boxsize']*1.25)
	if pad%2:
		pad=pad+1

	# save previous model
	mvcommand='mv ../threed.%d.mrc ../threed.%d.old.mrc' % (params['iter'],params['iter'])
	os.system(mvcommand)
	mvcommand='mv ../threed.%da.mrc ../threed.%da.old.mrc' % (params['iter'],params['iter'])
	os.system(mvcommand)
	
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
	
	mvcommand='mv goodavgs.hed ../classes_coran.%d.hed' % params['iter']
	os.system(mvcommand)
	mvcommand='mv goodavgs.img ../classes_coran.%d.img' % params['iter']
	os.system(mvcommand)
	rmcommand='rm -f ../classes.%d.hed ../classes.%d.img' % (params['iter'], params['iter'])
	os.system(rmcommand)
	lncommand='ln -s classes_coran.%d.hed ../classes.%d.hed' % (params['iter'], params['iter'])
	os.system(lncommand)
	lncommand='ln -s classes_coran.%d.img ../classes.%d.img' % (params['iter'], params['iter'])
	os.system(lncommand)

	print "updating %s" % classfile
	os.system('tar -cvf %s cls*.lst' % classfile)
	mvcommand='mv %s ../%s' % (classfile,classfile)
	os.system(mvcommand)
	
	
	print "Done!"
