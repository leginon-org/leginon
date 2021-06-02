import math
import time
import numpy

from pyami import correlator, peakfinder

import leginon.calibrationclient
import leginon.leginondata
import leginon.gui.wx.tomography.Tomography

import leginon.tomography.collection2
import leginon.tomography.tilts
import leginon.tomography.exposure2
import leginon.tomography.prediction2
from leginon.tomography.tomography import Tomography

from leginon.targetwatcher import PauseRepeatException
from leginon.targetwatcher import PauseRestartException
from leginon.targetwatcher import BypassException
from leginon.node import PublishError

class CalibrationError(Exception):
	pass

class LimitError(Exception):
    pass

class Tomography2(Tomography):
	settingsclass = leginon.leginondata.Tomography2SettingsData
	defaultsettings = dict(Tomography.defaultsettings)
	defaultsettings.update({
		'track preset': '',
		'cosine dose': True,
		'full track': False,
		'tolerance': 0.05,
		'maxfitpoints': 10
	})
	panelclass = leginon.gui.wx.tomography.Tomography.Panel2

	def __init__(self, *args, **kwargs):
		super(Tomography2, self).__init__(*args, **kwargs)
		self.calclients['image rotation'] = \
			leginon.calibrationclient.ImageScaleRotationCalibrationClient(self)
		self.calclients['stage'] = leginon.calibrationclient.StageCalibrationClient(self)

	def updateExposures(self):
		'''
		Update exposure values for data collection from settings
		Should be done after updateTilts.
		'''
		tilts = self.tilts.getTilts()

		total_dose = numpy.inf 		#self.settings['dose']
		exposure_min = 0			#self.settings['min exposure']
		exposure_max = numpy.inf 	#self.settings['max exposure']

		dose = 0.0
		exposure_time = 0.0
		try:
			name = self.settings['preset order'][-1]
			preset = self.presetsclient.getPresetFromDB(name)
		except (IndexError, ValueError):
			pass
		else:
			if preset['dose'] is not None:
				dose = preset['dose']*1e-20
			exposure_time = preset['exposure time']/1000.0

		try:
			self.exposure.update(total_dose=total_dose,
								 tilts=tilts,
								 dose=dose,
								 exposure=exposure_time,
								 exposure_min=exposure_min,
								 exposure_max=exposure_max,
								 fixed_exposure= not self.settings['cosine dose'],)
		except leginon.tomography.exposure.LimitError, e:
			self.logger.warning('Exposure dose out of range: %s.' % e)
			self.logger.warning('Adjust total exposure dose Or')
			msg = self.exposure.getExposureTimeLimits()
			self.logger.warning(msg)
			raise LimitError('Exposure limit error')
		except leginon.tomography.exposure.Default, e:
			self.logger.warning('Using preset exposure time: %s.' % e)
		else:
			try:
				exposure_range = self.exposure.getExposureRange()
			except ValueError:
				pass
			else:
				s = 'Exposure time range: %g to %g seconds.' % exposure_range
				self.logger.info(s)

	def getExposureObject(self):
		return leginon.tomography.exposure2.Exposure2()
			
	def getPredictionObject(self):
		return leginon.tomography.prediction2.Prediction2()
	
	def getCollectionObject(self,target):
		collect = leginon.tomography.collection2.Collection2()
		offsetdata = self.researchTargetOffset(target['list'])
		if offsetdata:
			collect.offset = offsetdata
			collect.trackpreset = \
				self.presetsclient.getPresetByName(self.settings['track preset'])
			collect.fulltrack = self.settings['full track']
		return collect
	
	def loadPredictionInfo(self):	
		# dummy function since we don't need previous history	
		pass
	
	def initGoodPredictionInfo(self,presetdata=None, tiltgroup=0):
		# dummy function since we don't need previous history
		pass
	
	def researchTargetOffset(self, targetlist):
		# (1) Get targetlist and query
		# (2) Match 'target' dbid with target dbid. 
		targetquery = leginon.leginondata.TomoTargetOffsetData(list=targetlist)
		targetoffset = targetquery.query()		 	# targetoffset should not be modified so shouldn't have to look for most recent version.
		if len(targetoffset) == 1:
			return targetoffset[0]
		else:
			return None								# Should be able to find targetoffset
	
	def newFocusTargetForImageFromTarget(self, imagedata, target, offset):
		# (1) Get position of acquisition target.
		# (2) Apply offset.
		# (3) Make new 
		dcol = target['delta column'] + offset[1]
		drow = target['delta row'] + offset[0]
		targetdata = self.newTarget(image=imagedata, scope=imagedata['scope'], \
								camera=imagedata['camera'], preset=imagedata['preset'], \
								drow=drow, dcol=dcol, session=self.session, type='focus')
		return targetdata


	def makeNewFocusTarget(self, target, offset, targetlist):
		# (1) Get parent image.
		# (2) Get and publish new version of parent image. 
		# (3) Make new focus target attach to targetlist.
		parentimage = target.special_getitem('image',readimages=False,dereference=True)			# (1) 
		newimagedata = self.copyImage(parentimage)												# (2) 
		focus_td = self.newFocusTargetForImageFromTarget(newimagedata, target, offset)			# (3)		# (3)
		focus_td['list'] = targetlist															
		return focus_td

	def markTargetsFailed(self, targets):
		for target in targets:
			self.reportTargetStatus(target, 'failed')
				
	def copyImage(self, oldimage):
		# copied from targetrepeater
		imagedata = leginon.leginondata.AcquisitionImageData()
		imagedata.update(oldimage)
		version = self.recentImageVersion(oldimage)
		imagedata['version'] = version + 1
		imagedata['filename'] = None
		imagedata['image'] = oldimage['image']
		## set the 'filename' value
		if imagedata['label'] == 'RCT':
			rctacquisition.setImageFilename(imagedata)
		else:
			self.setImageFilename(imagedata)
		self.logger.info('Publishing new copied image...')
		self.publish(imagedata, database=True)
		return imagedata

	def imageRotationTransform(self,pixvect, preset1,preset2,ht):
		'''
		Pixel vector need to be rotated to account for the rotation of
		specimen image rotation on the camera and the rotation of
		image shift coil relative to the specimen
		'''
		imageshift_axis_rotation = self.calclients['image shift'].calculateCalibrationAngleDifference(preset1['tem'],preset1['ccdcamera'],preset2['tem'], preset2['ccdcamera'], ht,preset1['magnification'],preset2['magnification'])
		stage_axis_rotation = self.calclients['stage'].calculateCalibrationAngleDifference(preset1['tem'],preset1['ccdcamera'],preset2['tem'], preset2['ccdcamera'], ht,preset1['magnification'],preset2['magnification'])
		# This is the rotation needs to be applied to the pixvect of preset1
		a = stage_axis_rotation - imageshift_axis_rotation
		m = numpy.matrix([[numpy.cos(a),numpy.sin(a)],[-numpy.sin(a),numpy.cos(a)]])
		rotated_vect = numpy.dot(pixvect,numpy.asarray(m))
		self.logger.info('Adjust for coil rotation: rotate %s to %s' % (pixvect, rotated_vect))
		return rotated_vect
	
	def recentImageVersion(self, imagedata):
		# copied from targetrepeater
		# find most recent version of this image
		p = leginon.leginondata.PresetData(name=imagedata['preset']['name'])
		q = leginon.leginondata.AcquisitionImageData()
		q['session'] = imagedata['session']
		q['target'] = imagedata['target']
		q['list'] = imagedata['list']
		q['preset'] = p
		allimages = q.query()
		version = 0
		for im in allimages:
			if im['version'] > version:
				version = im['version']
		return version

	def processGoodTargets(self, good_targets):
		# (1) Get offsetdata for this targetlist
		# (2) Determine if we want to focus. 
		# (3) Get new targetlist, publish to DB. 
		# (2) Get new focus target.
		# (3) Reject focus target.
		# (4) If focus successful, proceed to acquisiton. If not, report target done, move on to next acquisition target. 
		
		for i, target in enumerate(good_targets):
			if self.player.state() == 'pause':
				self.logger.info('paused after resetTiltInList')
				self.setStatus('user input')
				# FIX ME: if player does not wait, why should it pause ?
			state = self.clearBeamPath()
			self.setStatus('processing')
			# abort
			if state in ('stop', 'stopqueue'):
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				self.reportTargetStatus(target, 'aborted')
				## continue so that remaining targets are marked as done also
				continue
			
			targetlist = good_targets[0]['list']					# Get targetlist for these targets
			offsetdata = self.researchTargetOffset(targetlist)									# (1)
			if not offsetdata:										# somehow couldn't find offsetdata
				self.logger.info('Could not find TomoTargetOffsetData for target: %i' % target.dbid)
				self.markTargetsFailed(good_targets, 'failed')
				# This will go back to ~ line 325 in processTargetList in targetwatcher.py
				# Targetlist status will be reported as success. A bit strange??
				return
			focusoffset = offsetdata['focusoffset']		
			dofocus = not None in focusoffset	
			if dofocus:			# We have a focus spot for each acquisition target. 
				waitrejects = self.settings['wait for rejects']
				if waitrejects:																
					self.logger.info('Making new targetlist for focus target')
					focustargetlist = self.newTargetList()										# (3)

					self.logger.info('Publishing new targetlist')
					self.publish(focustargetlist,database=True, dbforce=True)
					self.logger.info('Making new focus target for acquisition target: %i' \
									% target.dbid)
					focustarget = self.makeNewFocusTarget(target,focusoffset,focustargetlist)	# (2)		
					self.logger.info('Publishing new focus target')
					self.publish(focustarget,database=True)
					self.logger.info('Rejecting new targetlist')

					rejectstatus = self.rejectTargets(focustargetlist)							# (3)
					if rejectstatus != 'success':
						# Focusing didn't work out. Report status, and move to next target.  
						self.reportTargetStatus(target, 'aborted')
						continue
					self.logger.info('Passed target processed, processing current target')
				else:
					self.logger.info('Skipping focus target for acquisition target: %i' % target.dbid)
					
			# target adjustment may have changed the tilt.
			if self.getIsResetTiltInList() and self.is_firstimage:
				# ? Do we need to reset on every target ?
				self.logger.info('Tilting to %.2f degrees on first good target.' % (self.targetlist_reset_tilt*180.0/math.pi))
				self.instrument.tem.setDirectStagePosition({'a':self.targetlist_reset_tilt})
			self.goodnumber = i
			self.logger.debug('target %s status %s' % (i, target['status'],))
			# ...
			if self.player.state() == 'pause':
				self.logger.info('paused after resetTiltInList')
				self.setStatus('user input')
				# FIX ME: if player does not wait, why should it pause ?
			state = self.clearBeamPath()
			self.setStatus('processing')
			# abort
			if state in ('stop', 'stopqueue'):
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				self.reportTargetStatus(target, 'aborted')
				## continue so that remaining targets are marked as done also
				continue

			# if this target is done, skip it
			if target['status'] in ('done', 'aborted'):
				self.logger.info('Target has been done, processing next target')
				continue
				
			adjustedtarget = self.reportTargetStatus(target, 'processing')
			
			# this while loop allows target to repeat
			process_status = 'repeat'
			attempt = 0
			while process_status == 'repeat':
				attempt += 1

				# now have processTargetData work on it
				self.startTimer('processTargetData')
				try:
					self.logger.info('Processing target id %d' % adjustedtarget.dbid)
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except BypassException, e:
					self.logger.error(str(e) + '... Bypass this target and pretend it is done')
					process_status = 'bypass'
				except PauseRestartException, e:
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then resubmit targets from previous step to repeat')
					self.beep()
					process_status = 'repeat'
				except PauseRepeatException, e:
					#TODO: NoMoveCalibration is a subclass of this. It is not handled now.
					self.player.pause()
					self.logger.error(str(e) + '... Fix it, then press play to repeat target')
					self.beep()
					process_status = 'repeat'
				except PublishError, e:
					self.player.pause()
					self.logger.exception('Saving image failed: %s' % e)
					process_status = 'repeat'
				except Exception, e:
					self.logger.exception('Process target failed: %s' % e)
					process_status = 'exception'
				finally:
					self.resetComaCorrection()
	
				self.stopTimer('processTargetData')

				if process_status == 'repeat':
					# Do not report targetstatus so that it can repeat even if
					# restart Leginon
					pass
				elif process_status != 'exception':
					self.reportTargetStatus(adjustedtarget, 'done')
				else:
					# set targetlist status to abort if exception not user fixable
					targetliststatus = 'aborted'
					self.reportTargetStatus(adjustedtarget, 'aborted')

				# pause check after a good target processing
				state =  self.pauseCheck('paused after processTargetData')
				self.setStatus('processing')
				if state in ('stop', 'stopqueue'):
					self.logger.info('Aborted')
					break
				if state in ('stoptarget',):
					self.logger.info('Aborted this target. continue to next')
					self.reportTargetStatus(adjustedtarget, 'aborted')
					self.player.play()

				# end of target repeat loop
			# next target is not a first-image
			self.is_firstimage = False
	
if __name__ == '__main__':
	import cPickle as pickle
	tomoargs = pickle.load(open('tomoargs.p','rb'))
	tomonode = Tomography2('Tomography',tomoargs,None) 
	pdb.set_trace()

