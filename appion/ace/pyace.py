#!/usr/bin/env python

import os, sys
import cPickle
import pymat
import glob
import data
import dbdatakeeper
import time

db=dbdatakeeper.DBDataKeeper()
acedonename='.acedone.py'

def printHelp():
	print "\nUsage:\npyace.py edgethcarbon=<n> edgethice=<n> pfcarbon=<n> pfice=<n> overlap=<n> fieldsize=<n> resamplefr=<n> drange=<n>"
	sys.exit()
		 
def createDefaults():
	# create default values for parameters
	params={}
	params['edgethcarbon']=0.8
	params['edgethice']=0.6
	params['pfcarbon']=0.9
	params['pfice']=0.3
	params['overlap']=2
	params['fieldsize']=512
	params['resamplefr']=1
	params['drange']=0
	params['dbimages']='FALSE'
	params['session']=None
	params['preset']=None
	params['tempdir']='./temp/'
	params['medium']='carbon'
	params['cs']=2.0
	params['outdir']=None
	params['runid']='run1'
	params['display']=1
	params['stig']=0
	params['continue']='FALSE'

	return(params)

def parseInput(args):
	# check that there are enough input parameters
	if (len(args)<2 or args[1]=='help') :
		printHelp()

	# create params dictionary & set defaults
	params=createDefaults()
	for arg in args[1:]:
		elements=arg.split('=')
		if (elements[0]=='edgethcarbon'):
			params["edgethcarbon"]=elements[1]
		elif (elements[0]=='edgethice'):
			params["edgethice"]=float(elements[1])
		elif (elements[0]=='pfcarbon'):
			params["pfcarbon"]=float(elements[1])
		elif (elements[0]=='pfice'):
			params["pfice"]=float(elements[1])
		elif (elements[0]=='overlap'):
			params["overlap"]=int(elements[1])
		elif (elements[0]=='fieldsize'):
			params["fieldsize"]=int(elements[1])
		elif (elements[0]=='resamplefr'):
			params["resamplefr"]=int(elements[1])
		elif (elements[0]=='drange'):
			drange=int(elements[1])
			if drange == 1 or drange== 0:
				params["drange"]=drange
			else:
				print "Error: drange should only be 0 or 1"
				sys.exit()
		elif (elements[0]=='dbimages'):
			dbinfo=elements[1].split(',')
			if len(dbinfo)==2:
				params['session']=dbinfo[0]
				params['preset']=dbinfo[1]
				params['dbimages']='TRUE'
			else:
				print "dbimages must include both session and preset parameters"
				sys.exit()
		elif (elements[0]=='tempdir'):
			params['tempdir']=elements[1]
		elif (elements[0]=='medium'):
			medium=elements[1]
			if medium=='carbon' or medium=='ice':
				params['medium']=medium
			else:
				print "medium can only be 'carbon' or 'ice'"
				sys.exit()
		elif (elements[0]=='cs'):
			params['cs']=float(elements[1])
		elif (elements[0]=='outdir'):
			params['outdir']=elements[1]
		elif (elements[0]=='runid'):
			params['runid']=elements[1]
		elif (elements[0]=='display'):
			display=int(elements[1])
			if display==0 or display==1:
				params['display']=display
			else:
				print "display must be 0 or 1"
				sys.exit()		
		elif (elements[0]=='stig'):
			stig=int(elements[1])
			if stig==0 or stig==1:
				params['stig']=stig
			else:
				print "stig must be 0 or 1"
				sys.exit()
		elif arg=='continue':
			params['continue']='TRUE'		
		else:
			print "undefined parameter", arg
			sys.exit()
		
	return(params)	

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
	return (imagelist)

def getPixelSize(imagedata):
	pixelsizeq=data.PixelSizeCalibrationData()
	pixelsizeq['magnification']=imagedata['scope']['magnification']
	pixelsizeq['tem']=imagedata['scope']['tem']
	pixelsizeq['ccdcamera'] = imagedata['camera']['ccdcamera']
	pixelsizedata=db.query(pixelsizeq, results=1)
	binning=imagedata['camera']['binning']['x']
	pixelsize=pixelsizedata[0]['pixelsize'] * binning
	return(pixelsize*1e10)

def getDoneDict(params):
	#write done dict to rundir
	params['acedonepath']=os.path.join(params['rundir'],acedonename)
	if os.path.exists(params['acedonepath']):
		# unpickle previously modified dictionary
		f=open(params['acedonepath'],'r')
		donedict=cPickle.load(f)
		f.close()
	else:
		#set up dictionary
		donedict={}
	return (params,donedict)

def writeDoneDict(donedict,params):
	f=open(params['acedonepath'],'w')
	cPickle.dump(donedict,f)
	f.close()
	return
	
def doneCheck(donedict,im):
	# check to see if image has been processed yet and
	# append dictionary if it hasn't
	# this may not be the best way to do this
	if donedict.has_key(im):
		pass
	else:
		donedict[im]=None
	return

def mkTempDir(temppath):
	if os.path.exists(temppath):
		print "\nWarning: temporary directory,", temppath, "already exists\n"
	else:
		os.mkdir(temppath)
	return

def setScopeParams(matlab,params):
	if os.path.exists(params['tempdir']):
		acecommand=("setscopeparams(%d,%f,%f,'%s');" % (params['kv'],params['cs'],params['apix'],params['tempdir']))
#		print acecommand
		pymat.eval(matlab,acecommand)
		pymat.eval(matlab,("scopeparams = [%d, %f, %f];" % (params['kv'],params['cs'],params['apix'])))
	else:
		print "Temp directory not present."
		sys.exit()
	return

def setAceConfig(matlab,params):
	tempdir=params['tempdir']
	if os.path.exists(tempdir):
		aceconfig=tempdir+'aceconfig.mat'
		pymat.eval(matlab, ("edgethcarbon=%f;" % params['edgethcarbon']))
		pymat.eval(matlab, ("edgethice=%f;" % params['edgethice']))
		pymat.eval(matlab, ("pfcarbon=%f;" % params['pfcarbon']))
		pymat.eval(matlab, ("pfice=%f;" % params['pfice']))
		pymat.eval(matlab, ("overlap=%d;" % params['overlap']))
		pymat.eval(matlab, ("fieldsize=%d;" % params['fieldsize']))
		pymat.eval(matlab, ("resamplefr=%d;" % params['resamplefr']))
		pymat.eval(matlab, ("drange=%d;" % params['drange']))
		acecommand=("save('%s','edgethcarbon','edgethice','pfcarbon','pfice','overlap','fieldsize','resamplefr','drange');" % aceconfig )
#		print acecommand
		pymat.eval(matlab,acecommand)
	else:
		print "Temp directory not present."
		sys.exit()
	return

def writePyAceLog(commandline):
	f=open('.pyacelog', 'a')
	out=""
	for n in commandline:
		out=out+n+" "
	f.write(out)
	f.write("\n")
	f.close()

def runAce(matlab,img,params):
	imgpath=img['session']['image path']
	imgname=img['filename']
	imgpath=imgpath + '/' + imgname + '.mrc'
	
	nominal=img['scope']['defocus']
	pymat.eval(matlab,("dforig = %f;" % nominal))
	acecommand=("ctfparams = ace('%s','%s',%d,%d,'%s',%f,'%s');" % (imgpath, params['outtextfile'], params['display'], params['stig'], params['medium'], -nominal, params['tempdir']))
	print "Processing", imgname
	pymat.eval(matlab,acecommand)

	matname=imgname+'.mrc.mat'
	matfile=os.path.join(params['matdir'],matname)
	savematcommand=("save('%s','ctfparams','scopeparams','dforig');" % (matfile))
#	print savematcommand
	pymat.eval(matlab,savematcommand)
	if params['display']:
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
	return

def getOutDirs(params):
	if params['outdir']:
		pass
	else:
		sessionq=data.SessionData(name=params['session'])
		sessiondata=db.query(sessionq)
		impath=sessiondata[0]['image path']
		outdir=os.path.split(impath)[0]
		outdir=os.path.join(outdir,'ctf_ace/')
		params['outdir']=outdir

	params['rundir']=os.path.join(params['outdir'],params['runid'])
	params['matdir']=os.path.join(params['rundir'],'matfiles')
	params['opimagedir']=os.path.join(params['rundir'],'opimages')
#	print params['rundir']
	
	if os.path.exists(params['outdir']):
		if os.path.exists(params['rundir']):
			print "\nWarning: run directory for", params['runid'],"already exists. Make sure continue option is on if you don't want to overwrite previous run.\n"
		else:
			os.makedirs(params['matdir'])
			os.makedirs(params['opimagedir'])
	else:
		os.makedirs(params['matdir'])
		os.makedirs(params['opimagedir'])
	
	return(params)

def getOutTextFile(params):
	session=params['session']
	rundir=params['rundir']
	outtextfile=os.path.join(rundir,(session+'.txt'))
	params['outtextfile']=outtextfile
	return(params)
			
if __name__ == '__main__':

	writePyAceLog(sys.argv)
	#parse input and set up output dirs and params dictionary
	params=parseInput(sys.argv)
	params=getOutDirs(params)
	params=getOutTextFile(params)
	mkTempDir(params['tempdir'])

	#start connection to matlab	
	print "Connecting to matlab"
	matlab=pymat.open()
	
	#write ace config file to temp directory
	setAceConfig(matlab,params)
	
	#get dictionary of completed images
	(params, donedict)=getDoneDict(params)
	
	#get image data objects from Leg. database
	images=getImagesFromDB(params['session'],params['preset'])
	
	notdone=True
	while notdone:
		for img in images:
	
			#if continue option is true, check to see if image has already been processed
			doneCheck(donedict,img['filename'])
			if params['continue']=='TRUE':
				if donedict[img['filename']]:
					print img['filename'], 'already processed. To process again, remove "continue" option.'
					continue
			
			#set up and write scopeparams.mat file to temp directory
			#do this for every image because pixel size can be different
			scopeparams={}
			scopeparams['kv']=img['scope']['high tension']/1000
			scopeparams['apix']=getPixelSize(img)
			scopeparams['cs']=params['cs']
			scopeparams['tempdir']=params['tempdir']
			setScopeParams(matlab,scopeparams)
			
			#run ace
			runAce(matlab,img,params)
			
			#write results to donedict
			donedict[img['filename']]=True
			writeDoneDict(donedict,params)
			
		if params['dbimages']=='TRUE':
			notdone=True
			print "Waiting one minute for new images"
			time.sleep(60)
			images=getImagesFromDB(params['session'],params['preset'])
		else:
			notdone=False
				
			
	pymat.close(matlab)
	print "Done!"
