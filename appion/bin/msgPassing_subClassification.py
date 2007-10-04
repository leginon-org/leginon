#!/usr/bin/env python

import glob,os,sys,time
import EMAN
import shutil
import math
import string
from Numeric import *
from subprocess import call

clslist=glob.glob('cls*.lst')

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
		elif elements[0]=='proc':
			params['proc']=int(elements[1])
		elif elements[0]=='sym':
			params['sym']=elements[1]
		elif elements[0]=='hard':
			params['hard']=int(elements[1])
		elif elements[0]=='corCutOff':			
			params['corCutOff']=float(elements[1])
		elif elements[0]=='minNumOfPtcls':			
			params['minNumOfPtcls']=int(elements[1])
		elif elements[0]=='findResolution':			
			params['findResolution']=elements[1]
			if params['findResolution']!='no':
				params['corandir']='resolution'
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
			
def createDefaults():
	params={}
	params['mask']=None
	params['iter']=None
	params['proc']=1
	params['sym']=None
	params['hard']=None
	params['corandir']='msgPassing'
	params['corCutOff']=0.8
	params['minNumOfPtcls']=500
	params['findResolution']='no'
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
	if os.path.exists(params['corandir']):
		print "Warning %s exists and is being overwritten" % params['corandir']
		#would like to use os functions for removal but doesn't work
		#os.rmdir(params['corandir'])
		try:
			os.system('rm -r %s' % params['corandir'])
		except:
			pass
			
		while os.path.exists(params['corandir']):
			print "Waiting and trying to delete again..\n"
			time.sleep(3)
			if os.path.exists(params['corandir']):
				try:
					os.system('rm -r %s' % params['corandir'])
				except:
					pass
				
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

	clslist=glob.glob('cls*.lst')
	projections=EMAN.readImages('proj.hed',-1,-1,0)
	if len(projections)!=len(clslist):
		print "Error: Number of projections not equal to number of classes"
		sys.exit()

	emanClsAvgs=EMAN.readImages('../classes.%d.hed' % params['iter'],-1,-1,0)

	#Loop through classes 
	clsNum=-1
	for cls in clslist:
		clsNum = clsNum+1
		fw=open(cls,'r')
		Ptcls = fw.readlines()
		fw.close()

		e=projections[clsNum].getEuler()
		projections[clsNum].setNImg(-1)
		projections[clsNum].writeImage('goodavgs.hed',-1)
		
		if len(Ptcls)-2 < params['minNumOfPtcls']:
			emanClsAvgs[(clsNum+1)*2 - 1].writeImage('goodavgs.hed',-1)
			continue;

		#make aligned stack
		if params['findResolution']=='no':
			command='clstoaligned.py ' + cls
		elif params['findResolution']=='odd':
			fw=open(cls,'r')
			Ptcls = fw.readlines()
			fw.close()
			fw = open('cls_odd.lst', 'w')					
			fw.writelines(Ptcls[0])
			fw.writelines(Ptcls[1])			
			for i1 in range(2,len(Ptcls)):
				if i1%2==0:
					fw.writelines(Ptcls[i1])
			fw.close()
			command='clstoaligned.py cls_odd.lst'
		elif params['findResolution']=='even':
			fw=open(cls,'r')
			Ptcls = fw.readlines()
			fw.close()
			fw = open('cls_even.lst', 'w')					
			fw.writelines(Ptcls[0])
			fw.writelines(Ptcls[1])
			for i1 in range(2,len(Ptcls)):
				if i1%2==1:
					fw.writelines(Ptcls[i1])
			fw.close()
			command='clstoaligned.py cls_even.lst'			

		print command
		os.system(command)
		
		#set up cls dir
		clsdir=cls.split('.')[0]+'.dir'
		os.mkdir(clsdir)

		os.rename('aligned.spi',os.path.join(clsdir,'aligned.spi'))

		alignedImgsName = os.path.join(clsdir,'aligned.spi')
		alignedImgs = EMAN.readImages(alignedImgsName,-1,-1,0)

		N = len(alignedImgs)
		
		D=ones((N,N))
		D=D*float(1)
		for i in range(0,N):
			for j in range(0,N):
				D[i,j] = cc(alignedImgs[i],alignedImgs[j])
				

		os.system('rm classes_avg.*')
		os.chdir(clsdir)
				

		print "\nStarted clustering process for ", clsdir
		Sarr = [];
		f1 = open('similarities.txt', 'w')
		for i in range(0,N):
			for j in range(0,N):
				if i!=j:
				   str1 = '%d %d %.10f\n' % (i+1,j+1,D[i,j])
				   f1.write(str1)
				   Sarr.append(D[i,j])
		f1.close()

		Sarr.sort()
		num = len(Sarr)
		if num%2:
			med = Sarr[num/2]
		else:
			med = (Sarr[num/2 - 1] + Sarr[num/2])/2
		
		f1 = open('preferences.txt', 'w')
		for i in range(0,N):
			f1.write('%.10f\n' % (med))
		f1.close()

		a=call(["apcluster.out","similarities.txt","preferences.txt","clusterOutput.txt"]) 		
		#if a:
		#	print "Error: Clustering code broke !!!"
		#	sys.exit()

		str1 = 'subClassAvgs'
		if os.path.exists(str1):
			os.system('rm -r %s' % str1)
		else:
			pass
		os.mkdir(str1)
		
		f1 = open('clusterOutput.txt')
		a = f1.read()
		f1.close()
		a = a.split()
		C = []
		E = [[] for i in range(0,N)]
		for i in range(0,N):
			C.append(int(a[i]))
			E[C[i]-1].append(i)
		
		os.system('rm subclasses_avg.*')
		os.system('rm tempClsAvg.*')		
		k=0
		for i in range(0,len(E)):
			if len(E[i])==0:
				continue;
			else:
				f1=open('%s/subcls%02d.lst' % (str1,k), 'w')
				for j in range(0,len(E[i])):
					f1.write('%d aligned.spi clusterCenterImgNum%d\n' % (E[i][j], i))
				f1.close()
				os.system('proc2d aligned.spi tempClsAvg.hed list=%s/subcls%02d.lst mask=%d average edgenorm' % (str1,k,params['mask']))
				k=k+1
				
		clsAvgs = EMAN.readImages('tempClsAvg.hed',-1,-1,0)
		j=0
		for i in range(0,len(E)):
			if len(E[i])==0:
				continue;
			else:
				clsAvgs[j].setNImg(len(E[i]))
				clsAvgs[j].writeImage('subclasses_avg.hed',-1)
				j=j+1
		os.chdir('../')	


		#Determine best averages

		os.system('rm tempClsAvg.*')		
		os.system('proc2d %s/aligned.spi tempClsAvg.hed mask=%d average edgenorm' % (clsdir, params['mask']))
		class_avg = EMAN.readImages('tempClsAvg.hed',-1,-1,0)

		avgname=os.path.join(clsdir,'subclasses_avg.hed')
		averages=EMAN.readImages(avgname,-1,-1,0)

		cclist=[]
		for avg in averages:
			cclist.append(cc(projections[clsNum],avg))
			print cclist[-1]
		
		f1 = open('%s/CCValues.txt'%(clsdir), 'w')
		for i in range(len(cclist)):
			f1.write(str(cclist[i])+'\n')
		f1.close()

		# Merge top best subclasses
	
		ccListSort = cclist
		ccListSort.sort()
		Ptcls = []
		for i in range(0,len(ccListSort)):
			cci = ccListSort[len(ccListSort)-i-1]
			if cci>=params['corCutOff']:
				bestclass_i=cclist.index(cci)
				classname_i=clslist[clsNum].split('.')[0]+'.dir/subClassAvgs/subcls'+string.zfill(bestclass_i,2)+'.lst'
				f1=open(classname_i,'r')
				Ptcls_i = f1.readlines()
				f1.close()
				Ptcls.extend(Ptcls_i)
			else:
				print "Not included - ", cci
				pass
		if len(Ptcls)>0:
		
			fw=open('mergeClasses.lst', 'w')				
			fw.writelines(Ptcls)
			fw.close()

			os.system('rm mergedClsAvg.spi')
			os.system('proc2d %s/aligned.spi mergedClsAvg.spi list=mergeClasses.lst mask=%d average' % (clsdir, params['mask']))
			mergedavg=EMAN.readImages('mergedClsAvg.spi',-1,-1,0)

			mergedavg[0].setNImg(len(Ptcls))
			mergedavg[0].setRAlign(e)
			mergedavg[0].writeImage('goodavgs.hed',-1)
		else:
			pass

	#Create list of cc values	
	for cls in range(0,len(clslist)):
		clsdir=clslist[cls].split('.')[0]+'.dir'
		print "\n Starting class number %d" %(cls)
		
		#break
	pad=params['boxsize']*1.25
	if pad%2:
		pad=pad+1
	if params['sym']==None:
		make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], pad, params['hard'])	
	else:
		make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], params['sym'], pad, params['hard'])
	print make3dcommand
	os.system(make3dcommand)
	proc3dcommand='proc3d threed.%d.mrc threed.%da.mrc mask=%d norm' % (params['iter'],params['iter'],params['mask'])
	print proc3dcommand
	os.system(proc3dcommand)
	if params['findResolution']=='no':
		os.system('cp threed.%da.mrc ../.'%(params['iter']))
		os.system('cp goodavgs.hed ../goodavgs.%d.hed' %(params['iter']))
		os.system('cp goodavgs.img ../goodavgs.%d.img' %(params['iter']))
	elif params['findResolution']=='odd':
		os.system('cp threed.%da.mrc ../threed.%da.o.mrc' %(params['iter'], params['iter']))
	elif params['findResolution']=='even':
		os.system('cp threed.%da.mrc ../threed.%da.e.mrc' %(params['iter'], params['iter']))
		os.system('proc3d threed.%da.mrc ../threed.%da.o.mrc fsc=../corEO%d.fsc.dat' %(params['iter'], params['iter'], params['iter']))

	print "Done!"
