#!/usr/bin/env python

import math


def parseTilt(tiltfile):
	f=open(tiltfile)
	lines=f.readlines()
	f.close()
	
	#first loop through file to find image names
	#using two loops for complete parsing for ease of coding
	imagedict={}
	parameterdict={}
	for n in lines:
		words=n.split()
		if 'FILE' in words:
			imagenum=int(words[1])
			imagedict[imagenum]={'filename':words[3]}
		elif 'PSI' in words:
			parameterdict['psi']=float(words[1])
		elif 'THETA' in words:
			parameterdict['theta']=float(words[1])
		elif 'PHI' in words:
			parameterdict['phi']=float(words[1])
		elif 'TILT' in words and 'AZIMUTH' in words:
			parameterdict['azimuth'] = float(words[2])
		elif 'TILT' in words and 'SERIES' in words:
			seriesname=words[2]
			
	for n in lines:
		words=n.split()
		if 'ORIGIN' in words:
			imagenum=int(words[1])
			xcoord=float(words[4])
			ycoord=float(words[5])
			imagedict[imagenum]['x']=xcoord
			imagedict[imagenum]['y']=ycoord
		elif 'TILT' in words and 'ANGLE' in words:
			imagenum=int(words[1])
			tilt=float(words[4])
			rotation=float(words[6])
			imagedict[imagenum]['tilt']=tilt
			imagedict[imagenum]['rotation']=rotation			
	return imagedict, parameterdict, seriesname

def writeTiltFile(outfilename, seriesname, imagedict, parameterdict=False):
	f=open(outfilename,'w')
	f.write('\n')
	f.write( ' TILT SERIES %s\n' % seriesname)
	if parameterdict:
		f.write('\n\n   PARAMETER\n')
		f.write('     PSI   %8.3f\n' % parameterdict['psi'])
		f.write('     THETA %8.3f\n' % parameterdict['theta'])
		f.write('     PHI   %8.3f\n' % parameterdict['phi'])
		f.write('\n\n   PARAMETER\n')
		f.write('     TILT AZIMUTH %8.3f\n' % parameterdict['azimuth'])
	f.write('\n\n')
	keys=imagedict.keys()
	keys.sort()
	for n in keys:
		f.write('   IMAGE %-5d FILE %s\n' % (n, imagedict[n]['filename']))
	f.write('\n')
	for n in keys:
		f.write('   IMAGE %-5d ORIGIN  [ %8.3f %8.3f ]\n' % (n, imagedict[n]['x'], imagedict[n]['y']))
	f.write('\n')
	for n in keys:
		f.write('   IMAGE %-5d TILT ANGLE %8.3f   ROTATION %8.3f\n' % (n, imagedict[n]['tilt'], imagedict[n]['rotation']))
	f.write('\n\n\n END\n\n')
	f.close()
