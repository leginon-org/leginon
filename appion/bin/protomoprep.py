#!/usr/bin/env python

import leginon.leginondata
import sys
from appionlib import apProTomo
from appionlib import apTomo
from appionlib import apImod
import math
import os
from pyami import correlator, peakfinder
import numpy
from optparse import OptionParser
from appionlib import apParam

def getTiltSeriesFromId(tiltid):
	seriesdata=leginon.leginondata.TiltSeriesData.direct_query(tiltid)
	imgtree=apTomo.getImageList([seriesdata])
	return imgtree

def getPredictionDataForImage(imagedata):
	q=leginon.leginondata.TomographyPredictionData()
	q['image']=imagedata
	predictiondata=q.query()
	return predictiondata

def alignZeroShiftImages(imgtree,zerotilts):
	"""Align 0 degree images for tilt series where data is collect in two halves"""
	#index for imgtree images are one less than index in zerotilts b/c protomo images start at 1
	im1=imgtree[zerotilts[0]-1]['image']
	im2=imgtree[zerotilts[1]-1]['image']
	print "correlating images",zerotilts[0], "and", zerotilts[1]
	cc=correlator.cross_correlate(im1,im2)
	peak=peakfinder.findPixelPeak(cc)
	#print peak
	newy,newx=shiftPeak(cc,peak)
	print "new origin for image", zerotilts[0], "is", newx, newy
	shifty=cc.shape[0]/2 - newy
	shiftx=cc.shape[1]/2 - newx
	return {'shiftx':shiftx, 'shifty':shifty}

def shiftPeak(imgarray,peakarray):
	"""shifts peaks so that they are in the center of the image"""
	ycen=imgarray.shape[0]/2
	xcen=imgarray.shape[1]/2
	peaky=peakarray['pixel peak'][0]
	peakx=peakarray['pixel peak'][1]
	
	#use integer and modulo division for determining shift
	newy=ycen-(peaky//ycen*ycen)+peaky%ycen
	newx=xcen-(peakx//xcen*xcen)+peakx%xcen
	
	return (newy,newx)

def shiftHalfSeries(shiftdict,ptdict, lastimg):
	keys=ptdict.keys()
	keys.sort()
	for key in keys:
		if key <=lastimg:
			ptdict[key]['x']=ptdict[key]['x']-shiftdict['shiftx']
			ptdict[key]['y']=ptdict[key]['y']-shiftdict['shifty']
			print "shifting image", key
		else:
			break

def modifyShiftByImodprexg(ptdict,imgshape):
	ycen=imgshape[0]/2
	xcen=imgshape[1]/2
	keys=ptdict.keys()
	keys.sort()
	transforms = apImod.readTransforms('09feb18c_006.prexg')	
	for key in keys:
		ptdict[key]['x']=transforms[key-1][-2]+xcen
		ptdict[key]['y']=transforms[key-1][-1]+ycen

def parseOptions():
	parser=OptionParser()
	parser.add_option('--tiltid', dest='tiltid', help= 'Primary key for a tilt series from appion database')
	parser.add_option('--outtiltfile', dest='tiltfile', help='PROTOMO tilt file to output')
	parser.add_option('--seriesname', dest='seriesname', help='Prefix to use as the name of the tilt series for processing')
	parser.add_option('--tar', action="store_true", dest='tar', default=False, help="Create a tarball containing files and directories")
	params=apParam.convertParserToParams(parser)
	return params
				
if __name__=='__main__':
	
	inputparams=parseOptions()
	
	#set up directories
	print "Setting up directories"
	rootdir=os.getcwd()
	rawdir=os.path.join(rootdir, 'raw')
	aligndir=os.path.join(rootdir,'align')
	outdir=os.path.join(rootdir,'out')
	cleandir=os.path.join(rootdir,'clean')
	apParam.createDirectory(aligndir,warning=False)
	apParam.createDirectory(outdir,warning=False)
	apParam.createDirectory(cleandir,warning=False)
	apParam.createDirectory(rawdir,warning=False)
	
	imgtree= getTiltSeriesFromId(inputparams['tiltid'])
	tiltkeys,imgtree,mrcfiles,refindex = apTomo.orderImageList(imgtree)
	ptdict={}
	zerotilts=[]
	
	for n in range(len(imgtree)):
		print "determining parameters for", imgtree[n]['filename']
		imdict={}
		imdictkey=n+1
		
		#assign parameters to ptdict
		tilt=imgtree[n]['scope']['stage position']['a']*180/math.pi
		imdict['tilt']=tilt
		origx=imgtree[n]['camera']['dimension']['x']/2
		origy=imgtree[n]['camera']['dimension']['y']/2
		imdict['rotation']=0
		
		#determine shifts for each image from correlation during data collection
		predictdata=getPredictionDataForImage(imgtree[n])
		neworigx=origx-predictdata[0]['correlation']['x']
		neworigy=origy+predictdata[0]['correlation']['y']
		imdict['x']=neworigx
		imdict['y']=neworigy
		
		#set up names
		imgpath=imgtree[n]['session']['image path']
		presetname=imgtree[n]['preset']['name']
		imgprefix=presetname+imgtree[n]['filename'].split(presetname)[-1]
		imgname=imgprefix+'.img'
		imdict['filename']=imgprefix
		
		#create symlinks to files
		if not os.path.exists(os.path.join(rawdir,imgname)):
			os.symlink(os.path.join(imgpath,imgtree[n]['filename']+'.mrc'),os.path.join(rawdir,imgname))
		
		#determine zero tilt image
		if int(tilt*10)==0:
			zerotilts.append(imdictkey)
			#print "ref img and tilt is", imdictkey, tilt
		ptdict[imdictkey]=imdict
	
	refimg=zerotilts[-1]
	
	#shift first half of series with respect to second
	print
	shiftdict=alignZeroShiftImages(imgtree,zerotilts)
	shiftHalfSeries(shiftdict,ptdict,zerotilts[0])

	#modifyShiftByImodprexg(ptdict,imgtree[0]['image'].shape)	
	#write tilt file
	apProTomo.writeTiltFile(inputparams['tiltfile'],inputparams['seriesname'],ptdict)
	
	#write parameter file
	refineparamdict=apProTomo.createRefineDefaults(refimg,
		os.path.join(os.getcwd(),'raw'),os.path.join(os.getcwd(),'out'))
	apProTomo.writeRefineParamFile(refineparamdict,inputparams['seriesname']+'.param')
	
	#if tar is specified, create big tarball
	if inputparams['tar']:
		files='raw clean out align *.tlt *.param'
		command='tar cvfh %s %s' % ((inputparams['seriesname']+'.tar'), files)
		print command
		os.system(command)
		print '\n\n Please remember to remove tar file after transfering to processing computer'
	print "Done!"
	
	
