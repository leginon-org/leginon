#!/usr/bin/env python
# Upload pik or box files to the database

import os
import sys
import time
import apUpload
import apParam
import apDisplay
import apDatabase
import apParticle
import appionScript

class UploadParticles(appionScript.AppionScript):
	def setupParserOptions(self):
		# create params dictionary & set defaults
		params = apUpload.createDefaults()
		params['runname'] = "manual1"

		# parse command line input
		apUpload.parsePrtlUploadInput(sys.argv,params)


	def checkConflicts(self):
		# check to make sure that incompatible parameters are not set
		if params['diam'] is None or params['diam']==0:
			apDisplay.printError("please input the diameter of your particle (for display purposes only)")
		
		# get list of input images, since wildcards are supported
		if params['imgs'] is None:
			apDisplay.printError("please enter the image names with picked particle files")
		imglist = params["imgs"]

	def start(self):
		print "getting image data from database:"
		totimgs = len(imglist)
		imgtree = []
		for i in range(len(imglist)):
			imgname = imglist[i]
			print "image",i+1,"of",totimgs,":",apDisplay.short(imgname)
			imgdata = apDatabase.getImageData(imgname)
			imgtree.append(imgdata)
		params['session'] = imgdata['session']['name']

		# upload Particles
		for imgdata in imgtree:
			# insert selexon params into dbappiondata.selectionParams table
			expid = int(imgdata['session'].dbid)
			apUpload.insertManualParams(params,expid)
			apParticle.insertParticlePicks(params, imgdata, manual=True)

if __name__ == '__main__':
	uploadpart = UploadParticles()
	uploadpart.start()
	uploadpart.close()




