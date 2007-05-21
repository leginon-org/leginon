#!/usr/bin/python -O

import sys
import os
import apCtf
import apDatabase
import apDB

ctfdb= apDB.apdb


def printHelp():
	print "\nUsage: getBestDefocus.py dbimages=<session>,<preset> outfile=<filename>"
	sys.exit()
	return

def createDefaults():
	params={}
	params['dbimages']=False
	params['session']=None
	params['preset']=None
	params['outfile']=None
	return(params)

def parseInput(args):
	#check that there are enough parameters
	if len(args) < 2 or args[1]=='help':
		printHelp()
	
	# create params dictionary & set defaults
	params=createDefaults()
	for arg in args[1:]:
		elements=arg.split('=')
		if elements[0] == 'dbimages':
			dbinfo=elements[1].split(',')
			if len(dbinfo)==2:
				params['session']=dbinfo[0]
				params['preset']=dbinfo[1]
				params['dbimages']=True
			else:
				print "dbimages must include both session and preset parameters"
				sys.exit()
		elif elements[0] == 'outfile':
			params['outfile']=elements[1]
		else:
			print "undefined parameter", arg
			sys.exit()
	return (params)

if __name__ == '__main__':
	
	params=parseInput(sys.argv)
	#check for missing parameters
	if not params['dbimages']:
		print "\nERROR: Please specify dbimages=<session>,<preset>\n"
		sys.exit()
	if not params['outfile']:
		print "\nERROR: Please specify outfile=<filename>\n"
		sys.exit()
	
	images=apDatabase.getImagesFromDB(params['session'],params['preset'])
	f=open(params['outfile'],'w')
	for img in images:
		ctfparams=apCtf.getCTFParamsForImage(img)
		bestconf=ctfparams[0]['confidence']
		bestconfd=ctfparams[0]['confidence_d']
		bestctf=ctfparams[0]
		for ctf in ctfparams:
			conf=ctf['confidence']
			confd=ctf['confidence_d']
			if conf > bestconf or confd > bestconfd:
				bestconf=conf
				bestconf_d=confd
				bestctf=ctf
		
		acerunref=bestctf.special_getitem('aceId',dereference=False)
		aceruninfo=ctfdb.direct_query(ctfData.ace_params,acerunref.dbid)
		if aceruninfo['stig']==0:
			print img['filename']+'.mrc',bestctf['defocus1'], bestctf['confidence'],bestctf['confidence_d']
			f.write('%s\t%f\t%f\t%f\n' % (img['filename'],-bestctf['defocus1']*1e6,bestctf['confidence'],bestctf['confidence_d']))
		else:
			print img['filename']+'.mrc',bestctf['defocus1'], bestctf['defocus2'],bestctf['confidence'],bestctf['confidence_d']
			f.write('%s\t%f\t%f\t%f\t%f\n' % (img['filename'],-bestctf['defocus1']*1e6,-bestctf['defocus2']*1e6,bestctf['confidence'],bestctf['confidence_d']))

	f.close()	 	
	print "Done!"
