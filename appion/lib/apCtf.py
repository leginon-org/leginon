#Part of the new pyappion

import pymat
import os,re,sys
import aceFunctions as af
import ctfData
import math
#import apDatabase
import apLoop

def runAce(matlab,img,params):
	imgpath=img['session']['image path']
	imgname=img['filename']
	imgpath=imgpath + '/' + imgname + '.mrc'
	
	if params['nominal']:
		nominal=params['nominal']
	else:
		nominal=img['scope']['defocus']
	
	pymat.eval(matlab,("dforig = %e;" % nominal))

	expid=int(img['session'].dbid)
	if params['commit']==True:
		#insert ace params into dbctfdata.ace_params table in db
		af.insertAceParams(params,expid)

	acecommand=("ctfparams = ace('%s','%s',%d,%d,'%s',%e,'%s');" % \
		( imgpath, params['outtextfile'], params['display'], params['stig'],\
		params['medium'], -nominal, params['tempdir'] ))

	shortimgname = re.sub("_0*","_",imgname)
	shortimgname = re.sub("_v0[0-9]","",shortimgname)
	print " ... processing", shortimgname
	pymat.eval(matlab,acecommand)
	print "done"

	matname=imgname+'.mrc.mat'
	matfile=os.path.join(params['matdir'],matname)
	savematcommand=("save('%s','ctfparams','scopeparams','dforig');" % (matfile))
#	print savematcommand
	pymat.eval(matlab,savematcommand)
	ctfparams=pymat.get(matlab,'ctfparams')
	_printResults(params,nominal,ctfparams)
	#display must be on to be able to commit ctf results to db 	
	if (params['display']):
		imfile1=params['tempdir']+'im1.png'
		imfile2=params['tempdir']+'im2.png'
		opimname1=imgname+'.mrc1.png'
		opimname2=imgname+'.mrc2.png'
		opimfile1=os.path.join(params['opimagedir'],opimname1)
		opimfile2=os.path.join(params['opimagedir'],opimname2)
		
		pymat.eval(matlab,("im1 = imread('%s');" % (imfile1)))
		pymat.eval(matlab,("im2 = imread('%s');" % (imfile2))) 
		pymat.eval(matlab,("imwrite(im1,'%s');" % (opimfile1)))
		pymat.eval(matlab,("imwrite(im2,'%s');" % (opimfile2)))

		#insert ctf params into dbctfdata.ctf table in db
		if (params['commit']==True):
			af.insertCtfParams(img,params,imgname,matfile,expid,ctfparams,opimfile1,opimfile2)
	return

def _printResults(params,nominal,ctfparams):
	nom1 = float(-nominal*1e6)
	defoc1 = float(ctfparams[0]*1e6)
	if (params['stig']==0):
		defoc2 = float(ctfparams[0]*1e6)
	else:
		defoc2=None
	conf1 = float(ctfparams[16])
	conf2 = float(ctfparams[17])

	if(conf1 > 0 and conf2 > 0):
		totconf = math.sqrt(conf1*conf2)
	else:
		totconf = 0.0
	if (params['stig']==0):
		pererror = abs((nom1-defoc1)/defoc1)
		labellist = ["Nominal","Defocus","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,1,1,1,]
		_printWindow(labellist,numlist,typelist)
	else:
		avgdefoc = (defoc1+defoc2)/2.0
		pererror = abs((nom1-avgdefoc)/avgdefoc)
		labellist = ["Nominal","Defocus1","Defocus2","PerErr","Conf1","Conf2","TotConf",]
		numlist = [nom1,defoc1,defoc2,pererror,conf1,conf2,totconf,]
		typelist = [0,0,0,0,1,1,1,]
		_printWindow(labellist,numlist,typelist)
	return

def _printWindow(labellist,numlist,typelist):
	if len(labellist) != len(numlist) or len(typelist) != len(numlist):
		print "\nERROR: in _printWindow() list lengths are off"
		print len(labellist)," != ",len(numlist)," != ",len(typelist)
		sys.exit(1)
	print _headerStr(labellist)
	labelstr = " "
	for lab in labellist:
		labelstr += "| "+lab+" "
		if len(lab) < 5:
			for i in range(5-len(lab)):
				labelstr += " "
	print labelstr+"|"

	datastr = " "
	for i in range(len(labellist)):
		datastr += "| "
		if typelist[i] == 1:
			numstr = _colorNum(numlist[i])
		else:
			numstr = "%1.3f" % numlist[i]
		pad = len(labellist[i])-5
		if pad % 2 == 1:
			datastr += " "
			pad -= 1
		pad/=2
		if(pad > 0):
			for i in range(pad):
				datastr += " "
		datastr += numstr
		if(pad > 0):
			for i in range(pad):
				datastr += " "
		datastr += " "
	print datastr+"|"

	print _headerStr(labellist)

	
def _headerStr(labellist):
	headstr = " "
	for lab in labellist:
		headstr += "+"
		leng = len(lab)
		if leng < 5: leng = 5
		for i in range(leng+2):
			headstr += "-"
	headstr += "+"
	return headstr

def _colorNum(num,green=0.8,red=0.5):
	if(num == None):
		return None
	elif(num > green and num <= 1):
		numstr = "%1.3f" % num
		return apLoop.color(numstr,"green")
	elif(num < red and num >= 0):
		numstr = "%1.3f" % num
		return apLoop.color(numstr,"red")
	else:
		numstr = "%1.3f" % num
		return numstr




