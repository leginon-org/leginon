#!/usr/bin/env python

#pythonlib
import os
import sys
import math
import shutil
import subprocess
#pyami
from pyami import fileutil
#leginon
from leginon import ddinfo
#appion
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata
import deProcessFrames
import glob
from pyami import mrc


class MakeAlignedSumLoop(appionLoop2.AppionLoop):
	#=====================
	def setupParserOptions(self):
		configuration_options = deProcessFrames.ConfigurationOptions( )
		options_list = configuration_options.get_options_list( )
		sections = options_list.keys( )
		for section in sections :
			for option in options_list[ section ] :
				if section == 'gainreference' or section == 'darkreference':
					if option['name'] in ['filename', 'framecount']:
						continue
				if section == 'boxes':
					if option['name'] in ['fromlist','fromonefile','fromfiles','boxsize','minimum']:
						continue
				if section == 'input' and option['name']=='framecount':
					continue
				if section == 'radiationdamage':
#					if option['name'] in ['apix', 'voltage']:
					if option['name'] in ['voltage']:
						continue
#				if section == 'alignment' and option['name']=='correct':
#					continue
				if option[ 'type' ] == str :
					metavar = "STR"
				elif option[ 'type' ] == int :
					metavar = "INT"
				elif option[ 'type' ] == float :
					metavar = "FLOAT"
				self.parser.add_option( "--%s_%s" % ( section, option[ 'name' ] ), type = option[ 'type' ], metavar = metavar, help = option[ 'help' ], default=option['default'] )

		self.parser.add_option("--alignlabel", dest="alignlabel", default='a',
			help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")
		self.parser.add_option('--dryrun', dest='dryrun', action='store_true', default=False, help="Just show the command, but do not execute")
		self.parser.add_option("--border", dest='border', type='int', default=0, help='Clip border specified border pixels and pad back out with mean value')
		self.parser.add_option("--hackcopy", dest='hackcopy', action='store_true', default=False, help='Copy corrected image to session directory and overwrite the original image, saving the orignal with a new extension ".orig.mrc"')

	#=======================
	def checkConflicts(self):
	
		pass

		
	def getFrameType(self):
		# set how frames are saved depending on what is found in the basepath
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if sessiondata['frame path']:
			# 3.0+
			return ddinfo.getRawFrameType(sessiondata['frame path'])
		else:
			# pre-3.0
			return ddinfo.getRawFrameType(sessiondata['image path'])

	#=======================
	def preLoopFunctions(self):
		self.dd = apDDprocess.initializeDDFrameprocess(self.params['sessionname'],self.params['wait'])
		self.dd.setRunDir(self.params['rundir'])
		self.dd.setRawFrameType(self.getFrameType())
		self.dd.setDoseFDriftCorrOptions(self.params)
		
		self.imageids = []
		# Optimize AppionLoop wait time for this since the processing now takes longer than
		# image acquisition
		self.setWaitSleepMin(0.4)
		self.setProcessBatchCount(1)
		self.params['output_fileformat'] = 'mrc'

	#=======================
	def processImage(self, imgdata):
		# need to avoid non-frame saved image for proper caching
		if imgdata is None or imgdata['camera']['save frames'] != True:
			apDisplay.printWarning('%s skipped for no-frame-saved\n ' % imgdata['filename'])
			return

		### set processing image
		try:
			self.dd.setImageData(imgdata)
		except Exception, e:
			apDisplay.printWarning(e.args[0])
			return


		# Align
		# Doing the alignment

		#flatfield references
		brightrefpath=imgdata['bright']['session']['image path']
		brightrefname=imgdata['bright']['filename']
		brightnframes=imgdata['bright']['camera']['nframes']
		darkrefpath=imgdata['dark']['session']['image path']
		darkrefname=imgdata['dark']['filename']
		darknframes=imgdata['dark']['camera']['nframes']
		brightref=os.path.join(brightrefpath,brightrefname+'.mrc')
		darkref=os.path.join(darkrefpath,darkrefname+'.mrc')
		print brightref
		print darkref			

		kev=imgdata['scope']['high tension']/1000
		apix=apDatabase.getPixelSize(imgdata)
		nframes=imgdata['camera']['nframes']

		#set appion specific options
		self.params['gainreference_filename']=brightref
		self.params['gainreference_framecount']=brightnframes
		self.params['darkreference_filename']=darkref
		self.params['darkreference_framecount']=darknframes
		self.params['input_framecount']=nframes
		#self.params['run_verbosity']=3
		self.params['output_invert']=0
		self.params['radiationdamage_apix']=apix
		self.params['radiationdamage_voltage']=kev
		#self.params['boxes_boxsize']=boxsize

		outpath=os.path.join(self.params['rundir'],imgdata['filename'])
		if os.path.exists(outpath):
			shutil.rmtree(outpath)
		os.mkdir(outpath)

		command=['deProcessFrames.py']
		keys=self.params.keys()
		keys.sort()
		for key in keys:
			param=self.params[key]
			#print key, param, type(param)
			if param == None or param=='':
				pass
			else:
				option='--%s=%s' % (key,param)
				command.append(option)
		command.append(outpath)
		framespath=imgdata['session']['frame path']
		framespathname=os.path.join(framespath,imgdata['filename']+'.frames')
		command.append(framespathname)
		print command
		if self.params['dryrun'] is False:
			subprocess.call(command)
			
			#cleanup and reformat image
			innamepath=glob.glob(os.path.join(outpath,'*.mrc'))[0]
			print innamepath
			outname=imgdata['filename']+'-'+self.params['alignlabel']+'.mrc'
			outnamepath=os.path.join(outpath,outname)
			if self.params['border'] != 0:
				command=['proc2d',innamepath, outnamepath]
				header=mrc.readHeaderFromFile(innamepath)
				origx=header['nx']
				origy=header['ny']
				newx=origx-self.params['border']
				newy=origy-self.params['border']
				command.append('clip=%d,%d' % (newx,newy))
				print command
				subprocess.call(command)
				
				
				command=['proc2d',outnamepath,outnamepath]
				command.append('clip=%d,%d' % (origx,origy))
				command.append('edgenorm')
				print command
				subprocess.call(command)
		
			if self.params['hackcopy'] is True:
				origpath=imgdata['session']['image path']
				shutil.move(os.path.join(origpath,imgdata['filename']+'.mrc'), os.path.join(origpath,imgdata['filename']+'.orig.mrc'))
				shutil.move(outnamepath, os.path.join(origpath,imgdata['filename']+'.mrc'))

#		sys.exit()
#		if os.path.isfile(self.dd.aligned_sumpath):
#			self.aligned_imagedata = self.dd.makeAlignedImageData(alignlabel=self.params['alignlabel'])
#			if os.path.isfile(self.dd.aligned_stackpath):
#				# aligned_stackpath exists either because keepstack is true
#				apDisplay.printMsg(' Replacing unaligned stack with the aligned one....')
#				apFile.removeFile(self.dd.framestackpath)
#				apDisplay.printMsg('Moving %s to %s' % (self.dd.aligned_stackpath,self.dd.framestackpath))
#				shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)
#		# Clean up tempdir in case of failed alignment
#		if self.dd.framestackpath != self.dd.tempframestackpath:
#			apFile.removeFile(self.dd.tempframestackpath)

	def insertFunctionRun(self):
		pass
		
#		if self.params['stackid']:
#			stackdata = apStack.getOnlyStackData(self.params['stackid'])
#		else:
#			stackdata = None
#		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=self.params['align'],bin=self.params['bin'],stack=stackdata)
#		qpath = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
#		sessiondata = self.getSessionData()
#		q = appiondata.ApDDStackRunData(runname=self.params['runname'],params=qparams,session=sessiondata,path=qpath)
#		results = q.query()
#		if results:
#			return results[0]
#		else:
#			if self.params['commit'] is True:
#				q.insert()
#				return q

	def commitToDatabase(self,imgdata):
		pass
#		if self.aligned_imagedata != None:
#			apDisplay.printMsg('Uploading aligned image as %s' % self.aligned_imagedata['filename'])
#			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=self.aligned_imagedata,ddstackrun=self.rundata)
#			q.insert()

if __name__ == '__main__':
	makeSum = MakeAlignedSumLoop()
	makeSum.run()



