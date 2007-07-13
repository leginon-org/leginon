#!/usr/bin/env python

import os
import sys
import particleLoop
import apImage
import subprocess
import apFindEM
import appionData
import apParticle
import apDatabase

class manualPicker(particleLoop.ParticleLoop):
	def preLoopFunctions(self):
		if self.params['dbimages']:
			self.processAndSaveAllImages()
	
	def particleProcessImage(self, imgdata):
		if not self.params['dbimages']:
			apFindEM.processAndSaveImage(imgdata, params=self.params)
		peaktree  = self.runManualPicker(imgdata['filename']+'.dwn.mrc')
		return peaktree

	def particleCommitToDatabase(self, imgdata):
		expid = int(imgdata['session'].dbid)
		self.insertManualParams(expid)
		#self.deleteOldPicks(imgdata,self.params)
		return

	def deleteOldPicks(self, imgdata):
		particles=apParticle.getParticlesForImageFromRunName(imgdata, self.params['runid'])
		count=0
		if particles:
			print "Deleting old picks"
			for particle in particles:
				#print particle
				count+=1
				#print count,
				self.appiondb.remove(particle)
		return

	def particleDefaultParams(self):
		self.params['mapdir']="manualmaps"

	def particleCreateOutputDirs(self):
		self._createDirectory(os.path.join(self.params['rundir'],"pikfiles"),warning=False)

	def particleParseParams(self, args):
		for arg in args:
			elements = arg.split('=')
			elements[0] = elements[0].lower()
			apDisplay.printError(str(elements[0])+" is not recognized as a valid parameter")

	def processAndSaveAllImages(self):
		print "Preprocessing images before picking"
		imgtree = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		for imgdata in imgtree:
			imgpath = os.path.join(self.params['rundir'], imgdata['filename']+'.dwn.mrc')
			if os.path.isfile(imgpath):
				print "Skipping",imgdata['filename']
			else:
				apFindEM.processAndSaveImage(imgdata, params=self.params)

	def insertManualParams(self, expid):
		manparamsq=appionData.ApManualParamsData()
		manparamsq['diam']    = self.params['diam']
		manparamsq['lp_filt'] = self.params['lp']
		manparamsq['hp_filt'] = self.params['hp']
		manparamsq['bin']     = self.params['bin']
		manparamsdata = self.appiondb.query(manparamsq, results=1)
		
		runq=appionData.ApSelectionRunData()
		runq['name'] = params['runid']
		runq['dbemdata|SessionData|session'] = expid
		runids = self.appiondb.query(runq, results=1)
		
		if not runids:
			runq['manparams']=manparamsq
			self.appiondb.insert(runq)
		else:
			#make sure all params are the same as previous session
			for pkey in manparamsq:
				if manparamsq[pkey] != manparamsdata[0][pkey]:
					print "All parameters for a particular manualpicker run must be identical"
					print pkey,manparamsq[pkey],"not equal to",manparamsdata[0][pkey]
					sys.exit()
			for i in manparamsq:
				if manparamsdata[0][i] != manparamsq[i]:
					apDisplay.printError("All parameters for a particular manualpicker run must be identical\n"+
						str(i)+":"+str(manparamsq[i])+" not equal to "+str(manparamsdata[0][i]))
		return

	def runManualPicker(self, imgname):
		#use ImageViewer to pick particles
		#this is a total hack but an idea that can be expanded on
		imgpath = os.path.join(self.params['rundir'],imgname)
		commandlst = ['ApImageViewer.py',imgpath]
		manpicker = subprocess.Popen(commandlst,stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		outstring = manpicker.stdout.read()
		words = outstring.split()
		peaktree=[]
		#print outstring
		#print words
		for xy in range(0,len(words)/2):
			particle={}
			print xy, words[2*xy], words[2*xy+1]
			particle['xcoord']=int(words[2*xy])*self.params['bin']
			particle['ycoord']=int(words[2*xy+1])*self.params['bin']
			particle['correlation']=None
			particle['peakmoment']=None
			particle['peakstddev']=None
			particle['peakarea']=1
			particle['tmplnum']=None
			particle['template']=None
			peaktree.append(particle)
		#print peaktree
		return peaktree

if __name__ == '__main__':
	imgLoop = manualPicker()
	imgLoop.run()
