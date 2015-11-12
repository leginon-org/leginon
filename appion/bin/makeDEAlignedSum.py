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
from appionlib import appionPBS
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apFile
from appionlib import apStack
from appionlib import appiondata
import deProcessFrames
import glob
from pyami import mrc
from appionlib import apDBImage

class MakeAlignedSumLoop(appionPBS.AppionPBS):
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
		self.parser.add_option("--border", dest='border', type='int', default=0, help='Clip border specified border pixels and pad back out with mean value')
		self.parser.add_option("--hackcopy", dest='hackcopy', action='store_true', default=False, help='Copy corrected image to session directory and overwrite the original image, saving the orignal with a new extension ".orig.mrc"')
		
	#=======================
	def checkConflicts(self):
		#if override-dark or bright selected, should check for override-darkframes
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

		self.exposurerate_is_default = self.params['radiationdamage_exposurerate'] == 1.0
		
		self.imageids = []
		# Optimize AppionLoop wait time for this since the processing now takes longer than
		# image acquisition
		self.setWaitSleepMin(0.4)
		self.setProcessBatchCount(1)
		self.params['output_fileformat'] = 'mrc'

	def getTargets(self, imgdata, scratchdir='', handlefiles='direct'):
		targetdict={}
		#copy flatfields
		
		brightrefpath=imgdata['bright']['session']['image path']
		brightrefname=imgdata['bright']['filename']+'.mrc'
		brightref=os.path.join(brightrefpath,brightrefname)
		
		darkrefpath=imgdata['dark']['session']['image path']
		darkrefname=imgdata['dark']['filename']+'.mrc'
		darkref=os.path.join(darkrefpath,darkrefname)
		
		#################################### do away with override flatfield option
		framesdirname=imgdata['filename']+'.frames'
		apDisplay.printMsg('Copying frames %s' % (framesdirname))
		framespath=imgdata['session']['frame path']
		framespathname=os.path.join(framespath,framesdirname)
	
		if handlefiles == 'direct':
			targetdict['brightref']=brightref
			targetdict['darkref']=darkref
			targetdict['framespathname']=framespathname
			targetdict['outpath']=self.params['rundir']
		elif handlefiles == 'copy':
			shutil.copy(brightref,scratchdir)
			shutil.copy(darkref,scratchdir)
			targetdict['brightref']=os.path.join(scratchdir,brightrefname)
			targetdict['darkref']=os.path.join(scratchdir,darkrefname)
			try:
				shutil.copytree(framespathname,os.path.join(scratchdir, framesdirname))
			except:
				apDisplay.printWarning('there was a problem copying the frames for %s' % (imgdata['filename']))
			targetdict['framespathname']=os.path.join(scratchdir,framesdirname)
			targetdict['outpath']=os.path.join(scratchdir,imgdata['filename'])
			
		elif handlefiles == 'link':
			os.symlink(brightref,os.path.join(scratchdir,brightrefname))
			os.symlink(darkref,os.path.join(scratchdir,darkrefname))
			os.symlink(framespathname,os.path.join(scratchdir, framesdirname))
			
			targetdict['brightref']=os.path.join(scratchdir,brightrefname)
			targetdict['darkref']=os.path.join(scratchdir,darkrefname)
			targetdict['framespathname']=os.path.join(scratchdir,framesdirname)
			targetdict['outpath']=os.path.join(scratchdir,imgdata['filename'])
		return targetdict

	def calculateListDifference(self,list1,list2):
		from sets import Set
		set1 = Set(list1)
		set2 = Set(list2)
		list_diff = list(set1.difference(set2))
		list_diff.sort()
		return list_diff

	def getCameraDefects(self, imgdata):
		"""
		Set defects for camera in self.params if not entered already.
		"""
		corrector_plan = imgdata['corrector plan']
		cam_size = imgdata['camera']['dimension']
		border = self.params['border']
		# map name to de params name and leginon corrector plan name
		namemap = {'x':('columns','cols'),'y':('rows','rows')}

		if not corrector_plan:
			return
		for axis in namemap.keys():
			de_name = 'defects_%s' % namemap[axis][0]
			leg_name = 'bad_%s' % namemap[axis][1]
			exclude_list = []
			# figure out the defects if not specified already
			if not self.params[de_name] and corrector_plan[leg_name]:
				# Do not include a location in defects for DE 
				# process if in the border because large number
				# of defect correction is slow.
				if border:
					exclude_list = range(0,border)
					exclude_list.extend(range(cam_size[axis]-border,cam_size[axis]))
				bad = self.calculateListDifference(corrector_plan[leg_name],exclude_list)
				self.params[de_name] = ','.join(map((lambda x: '%d' % x),bad))
		# TODO: need to handle bad pixels, too

	def generateCommand(self, imgdata, targetdict):
		
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

		kev=imgdata['scope']['high tension']/1000
		apix=apDatabase.getPixelSize(imgdata)
		nframes=imgdata['camera']['nframes']
		try:
			dose=apDatabase.getDoseFromImageData(imgdata)
		except:
			dose=None
		# overwrite radiationdamage_exposurerate if it is at default
		if dose and self.exposurerate_is_default:
			self.params['radiationdamage_exposurerate']=dose/nframes

		#set appion specific options
		#flatfield references
		self.params['gainreference_filename']=targetdict['brightref']		
		brightnframes=imgdata['bright']['camera']['nframes']
		self.params['gainreference_framecount']=brightnframes

		self.params['darkreference_filename']=targetdict['darkref']		
		darknframes=imgdata['dark']['camera']['nframes']
		self.params['darkreference_framecount']=darknframes
		self.getCameraDefects(imgdata)

		self.params['input_framecount']=nframes
		#self.params['run_verbosity']=3
		self.params['output_invert']=0
		self.params['radiationdamage_apix']=apix
		self.params['radiationdamage_voltage']=kev
		#self.params['boxes_boxsize']=boxsize

		if os.path.exists(targetdict['outpath']):
			shutil.rmtree(targetdict['outpath'])
		os.mkdir(targetdict['outpath'])

		command=['runDEProcessFrames.py']
		keys=self.params.keys()
		keys.sort()
		for key in keys:
			param=self.params[key]
			#print key, param, type(param)
			if param == None or param=='' or key=='description':
				pass
			else:
				option='--%s=%s' % (key,param)
				command.append(option)
		command.append(targetdict['outpath'])
		#framespath=imgdata['session']['frame path']
		#framespathname=os.path.join(framespath,imgdata['filename']+'.frames')
		framespathname=targetdict['framespathname']
		
		#check to see if there are frames in the path
		framesinpath=len(glob.glob(os.path.join(framespathname,'*')))
		if framesinpath == 0:
			apDisplay.printWarning('%s skipped because %d frames were found' % (imgdata['filename'],framesinpath))
			return
		
		command.append(framespathname)
		return command
		
	# def getDoneFile(self,targetdict):
	# 	return os.path.join(targetdict['outpath'],'*sum_???-???.mrc')

	def collectResults(self, imgdata,targetdict):
		"""
		Overwrite collectResults to do final processing of the
		queue job result and commit
		"""
		#cleanup and reformat image
		try:
			innamepath=glob.glob(os.path.join(targetdict['outpath'],'*.mrc'))[0]
			print innamepath
		except IndexError:
			apDisplay.printWarning('queued job for %s failed' % (imgdata['filename']))
			return
		outname=imgdata['filename']+'-'+self.params['alignlabel']+'.mrc'
		outnamepath=os.path.join(targetdict['outpath'],outname)
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
		
		newimg_array = mrc.read(outnamepath)
		self.commitAlignedImageToDatabase(imgdata,newimg_array,self.params['alignlabel'])
		# return None since everything is committed within this function.
	
		if self.params['hackcopy'] is True:
			origpath=imgdata['session']['image path']
			archivecopy=os.path.join(origpath,imgdata['filename']+'.orig.mrc')
			if os.path.exists(archivecopy) is True:
				apDisplay.printMsg('archive copy for %s already exists, so skipping archive' % (archivecopy))
			else:
				shutil.move(os.path.join(origpath,imgdata['filename']+'.mrc'), archivecopy)
			shutil.copyfile(outnamepath, os.path.join(origpath,imgdata['filename']+'.mrc'))

		return None

	'''
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

		kev=imgdata['scope']['high tension']/1000
		apix=apDatabase.getPixelSize(imgdata)
		nframes=imgdata['camera']['nframes']
		dose=imgdata['preset']['dose']/10**20

		#set appion specific options
		#flatfield references
		if self.params['override-bright'] is None:
			brightrefpath=imgdata['bright']['session']['image path']
			brightrefname=imgdata['bright']['filename']
			brightref=os.path.join(brightrefpath,brightrefname+'.mrc')
			self.params['gainreference_filename']=brightref
		else:
			self.params['gainreference_filename']=self.params['override-bright']
		
		if self.params['override-brightnframes'] is None:
			brightnframes=imgdata['bright']['camera']['nframes']
			self.params['gainreference_framecount']=brightnframes
		else:
			self.params['gainreference_framecount']=self.params['override-brightnframes']


		if self.params['override-dark'] is None:
			darkrefpath=imgdata['dark']['session']['image path']
			darkrefname=imgdata['dark']['filename']
			darkref=os.path.join(darkrefpath,darkrefname+'.mrc')
			self.params['darkreference_filename']=darkref
		else:
			self.params['darkreference_filename']=self.params['override-dark']
		
		if self.params['override-darknframes'] is None:
			darknframes=imgdata['dark']['camera']['nframes']
			self.params['darkreference_framecount']=darknframes
		else:
			self.params['darkreference_framecount']=self.params['override-darknframes']

		self.params['input_framecount']=nframes
		#self.params['run_verbosity']=3
		self.params['output_invert']=0
		self.params['radiationdamage_apix']=apix
		self.params['radiationdamage_voltage']=kev
		self.params['radiationdamage_exposurerate']=dose/nframes
		#self.params['boxes_boxsize']=boxsize

		outpath=os.path.join(self.params['rundir'],imgdata['filename'])
		if os.path.exists(outpath):
			shutil.rmtree(outpath)
		os.mkdir(outpath)

		command=['runDEProcessFrames.py']
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
		
		#check to see if there are frames in the path
		framesinpath=len(glob.glob(os.path.join(framespathname,'*')))
		if framesinpath == 0:
			apDisplay.printWarning('%s skipped because %d frames were found' % (imgdata['filename'],framesinpath))
			return
		
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
	'''
	def insertFunctionRun(self):
		
		stackdata = None
		qparams = appiondata.ApDDStackParamsData(preset=self.params['preset'],align=None,bin=None,stack=None, method='de_aligner', )
		qpath = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		sessiondata = self.getSessionData()
		qdeparams=appiondata.ApDEAlignerParamsData()
		print qdeparams
		qdeparams['alignment_correct']=self.params['alignment_correct']
		qdeparams['alignment_quanta']=self.params['alignment_quanta']
		qdeparams['radiationdamage_compensate']=self.params['radiationdamage_compensate']
		qdeparams['radiationdamage_multiplier']=self.params['radiationdamage_multiplier']
		qdeparams['output_sumranges']=self.params['output_sumranges']
		qparams['de_aligner']=qdeparams
		
		q = appiondata.ApDDStackRunData(runname=self.params['runname'],params=qparams,session=sessiondata,path=qpath)
		results = q.query()
		
		if results:
			return results[0]
		else:
			if self.params['commit'] is True:
				q.insert()
				return q

	def commitAlignedImageToDatabase(self,imgdata,newimage,alignlabel='a'):
		if self.params['commit'] is False:
			return
		camdata=imgdata['camera']
		newimagedata=apDBImage.makeAlignedImageData(imgdata,camdata,newimage,alignlabel)
		newimageresults=newimagedata.query()
		
		if newimageresults:
			return
		else:
			apDisplay.printMsg('Uploading aligned image as %s' % newimagedata['filename'])
			newimagedata.insert()
			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=newimagedata,ddstackrun=self.rundata)
			q.insert()

	def commitToDatabase(self,imgdata):
		"""
		This commitToDatabase does nothing. The actual commit is handled in commitAlignedImageToDatabase where the input also include the new image array.
		"""
		return

if __name__ == '__main__':
	makeSum = MakeAlignedSumLoop()
	makeSum.run()



