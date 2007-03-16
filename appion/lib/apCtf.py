#Part of the new pyappion

import pymat
import os,re,sys

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
		insertAceParams(params,expid)

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
			insertCtfParams(img,params,imgname,matfile,expid,ctfparams,opimfile1,opimfile2)
	return

def _printResults(params,nominal,ctfparams):
	
	if (params['stig']==0):
		print " +---------+---------+-------+-------+---------+ "
		print " | Nominal | Defocus | Conf1 | Conf2 | TotConf | "
		print(" | %1.3f   |  %1.3f  | %1.3f | %1.3f |  %1.3f  | " % \
			( float(-nominal*1e6), float(ctfparams[0]*1e6), float(ctfparams[16]),\
			float(ctfparams[17]), float(ctfparams[16])*abs(float(ctfparams[17])) ))
		print " +---------+---------+-------+-------+---------+ "
	else:
		print " +---------+----------+----------+-------+-------+---------+ "
		print " | Nominal | Defocus1 | Defocus2 | Conf1 | Conf2 | TotConf | "
		print(" |  %1.3f  |   %1.3f  |  %1.3f   | %1.3f | %1.3f |  %1.3f  | " % \
			( float(-nominal*1e6), float(ctfparams[0]*1e6), float(ctfparams[1]*1e6),\
			float(ctfparams[16]), float(ctfparams[17]), float(ctfparams[16])*abs(float(ctfparams[17])) ))
		print " +---------+----------+----------+-------+-------+---------+ "
	return
