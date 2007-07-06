#!/usr/bin/env python

import os
import sys
import appionLoop
import apImage
import subprocess
import apFindEM
import apDB
import appionData
import apParticle
import apDatabase
apdb=apDB.apdb

def runManualPicker(imgname,params):
	#use ImageViewer to pick particles
	#this is a total hack but an idea that can be expanded on
	imgpath=os.path.join(params['rundir'],imgname)
	commandlst=['ImageViewer.py',imgpath]
	manpicker=subprocess.Popen(commandlst,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	outstring=manpicker.stdout.read()
	words=outstring.split()
	particlelst=[]
	#print outstring
	#print words
	for xy in range(0,len(words)/2):
		particle={}
		print xy, words[2*xy], words[2*xy+1]
		particle['xcoord']=int(words[2*xy])*params['bin']
		particle['ycoord']=int(words[2*xy+1])*params['bin']
		particle['correlation']=None
		particle['peakmoment']=None
		particle['peakstddev']=None
		particle['peakarea']=1
		particle['tmplnum']=None
		particle['template']=None
		particlelst.append(particle)
	#print particlelst
	return particlelst

def insertManualParams(params,expid):
	manparamsq=appionData.ApManualParamsData()
	manparamsq['diam']=params['diam']
	manparamsq['lp_filt']=params['lp']
	manparamsq['hp_filt']=params['hp']
	manparamsq['bin']=params['bin']
	manparamsdata=apdb.query(manparamsq,results=1)
	
	runq=appionData.ApSelectionRunData()
	runq['name']=params['runid']
	runq['dbemdata|SessionData|session']=expid
	
	runids=apdb.query(runq,results=1)
	
	if not runids:
		runq['manparams']=manparamsq
		apdb.insert(runq)
	else:
		#make sure all params are the same as previous session
		pkeys=manparamsq.keys()
		for pkey in pkeys:
			if manparamsq[pkey] != manparamsdata[0][pkey]:
				print "All parameters for a particular manualpicker run must be identical"
				print pkey,manparamsq[pkey],"not equal to",manparamsdata[0][pkey]
				sys.exit()
	return		

def deleteOldPicks(imgdata,params):
	particles=apParticle.getParticlesForImageFromRunName(imgdata,params['runid'])
	count=0
	if particles:
		print "Deleting old picks"
		for particle in particles:
			#print particle
			count+=1
			#print count,
			apdb.remove(particle)
	return

def processAndSaveAllImages(params):
	print "Preprocessing images before picking"
	imgtree=apDatabase.getImagesFromDB(params['sessionname'], params['preset'])
	for imgdata in imgtree:
		imgpath=os.path.join(params['rundir'],imgdata['filename']+'.dwn.mrc')
		if os.path.exists(imgpath):
			print "Skipping",imgdata['filename']
		else:
			apFindEM.processAndSaveImage(imgdata,params=params)
			
class manualPicker(appionLoop.AppionLoop):
	def setProcessingDirName(self):
		self.processdirname = "extract"

	def preLoopFunctions(self):
		if self.params['dbimages']:
			processAndSaveAllImages(self.params)
	
	def processImage(self, imgdata):
		#apFindEM.processAndSaveImage(imgdata, params=self.params)
		self.peaktree  = runManualPicker(imgdata['filename']+'.dwn.mrc',self.params)

	def commitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		insertManualParams(self.params,expid)
		#deleteOldPicks(imgdata,self.params)
		apParticle.insertParticlePeaks(self.peaktree, imgdata, expid, self.params)
		return

	def specialDefaultParams(self):
		self.params['lp']=0.0
		self.params['hp']=0.0
		self.params['bin']=1.0

	def specialCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"pikfiles"),warning=False)

	def specialParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			#print elements
			if (elements[0]=='help' or elements[0]=='--help' \
				or elements[0]=='-h' or elements[0]=='-help'):
				sys.exit(1)
			elif (elements[0]=='thresh'):
				self.params['thresh']= float(elements[1])
			elif (elements[0]=='lp'):
				self.params['lp']= float(elements[1])
			elif (elements[0]=='hp'):
				self.params['hp']= float(elements[1])
			else:
				print elements[0], "is not recognized as a valid parameter"
				sys.exit()

	def specialParamConflicts(self):
		pass

if __name__ == '__main__':
	imgLoop = manualPicker()
	imgLoop.run()
