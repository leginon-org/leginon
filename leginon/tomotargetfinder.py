#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import threading
import numpy
import time
import scipy.ndimage as nd
from leginon import calibrationclient
from leginon import leginondata
from leginon import event
from leginon import targetfinder
from leginon import appclient
import leginon.gui.wx.TomoClickTargetFinder

class TomoClickTargetFinder(targetfinder.ClickTargetFinder):
	targetnames = ['preview', 'reference', 'focus', 'acquisition','track']
	panelclass = leginon.gui.wx.TomoClickTargetFinder.Panel
	eventoutputs = targetfinder.TargetFinder.eventoutputs + [event.ReferenceTargetPublishEvent]
	settingsclass = leginondata.TomoClickTargetFinderSettingsData
	defaultsettings = dict(targetfinder.ClickTargetFinder.defaultsettings)
	defaultsettings.update({'auto focus target': True,
									'focus target offset': 3e-6,
									'track target offset': 3e-6,
									'tomo beam diameter':  0e-6,
									'focus beam diameter': 0e-6,
									'track beam diameter': 0e-6,
									'stretch tomo beam': True,
									'stretch focus beam': True,
									'stretch track beam': True
									})
	def __init__(self, id, session, managerlocation, **kwargs):

		targetfinder.ClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.calclients['pixel size'] = \
				leginon.calibrationclient.PixelSizeCalibrationClient(self)
		self.trackimagevectors = {'x':(0,0),'y':(0,0)}
		self.trackbeamradius = 0	
		self.focus_node = None
		self.focusimagevectors = {'x':(0,0),'y':(0,0)}
		self.focusbeamradius = 0
		self.userpause = threading.Event()
		
		if self.__class__ == TomoClickTargetFinder:
			self.start()
			
	def getTrackImageVectors(self):
		return self.trackimagevectors

	def getTrackBeamRadius(self):
		#return 10
		return self.trackbeamradius

	def getFocusImageVectors(self):
		return self.focusimagevectors

	def getFocusBeamRadius(self):
		#return 20
		return self.focusbeamradius
	
	def getTiltRange(self):
		'''
		Get tilt range from tomography node settings.
		Called through gui to get tilt range for image processing.
		'''
		if not self.next_acq_node:
			return None
		settingsclassname = self.next_acq_node['node']['class string']+'SettingsData'
		results= self.researchDBSettings(getattr(leginondata,settingsclassname),self.next_acq_node['node']['alias'])
		acqsettings = results[0]
		try:
			return (acqsettings['tilt min'],acqsettings['tilt max'])
		except KeyError:
			# Not a tomography node.
			return (0.0,0.0)

	def handleApplicationEvent(self,evt):
		i = 0
		# Try a few times because tomo node may not load fast enough
		# and it really needs focus node.
		while not self.next_acq_node and i < 10:
			super(TomoClickTargetFinder,self).handleApplicationEvent(evt)
			i += 1
			time.sleep(1.0)
		if not self.next_acq_node:
			self.logger.error('next_acq_node unknown')
			return
		app = evt['application']
		# get focus node used for getting beam parameters
		self.focus_node = self.getFocusNodeThruBinding(app,self.next_acq_node['node']['alias'],'ImageTargetListPublishEvent','Focuser')
	
	def getFocusNodeThruBinding(self,appdata,from_node_alias,binding_name,next_node_baseclass_name):
		# Copied from appclient.
		# Slight modification since Tomograpy node is bound to to both 
		# Tomo Focus and Tomo Preview by ImageTargetListPublishEvent
		'''
		Use the binding in the application to get the next node of a defined base class.
		'''
		# Not to do  global import so that it does not import when the module is loaded
		from leginon import noderegistry
		next_class = noderegistry.getNodeClass(next_node_baseclass_name)
		# Try 10 iteration before giving up
		for iter in range(10):
			q = leginondata.BindingSpecData(application=appdata)
			q['event class string'] = binding_name
			q['from node alias'] = from_node_alias
			r = q.query()
			if not r:
				# no node bound by the binding
				return None
			for i in range(len(r)):
				next_alias = r[i]['to node alias']
				q = leginondata.NodeSpecData(application=appdata,alias=next_alias)
				next_bound_r = q.query()
				if next_bound_r:
					for nextnodedata in next_bound_r:
						if issubclass(noderegistry.getNodeClass(nextnodedata['class string']),next_class):
							return nextnodedata
					# next bound node is a filter.  Try again from there.
					from_node_alias = next_alias
					continue		

	def setOtherImageVectors(self, imagedata):
		try:
			cam_length_on_image,beam_diameter_on_image = self._getTrackTargetDimensions(self.current_image_pixelsize)
			self._setTrackImageVectors(cam_length_on_image,beam_diameter_on_image)
			cam_length_on_image,beam_diameter_on_image = self._getFocusTargetDimensions(self.current_image_pixelsize)
			self._setFocusImageVectors(cam_length_on_image,beam_diameter_on_image)
		except:
			pass
		
	def getBeamDiameter(self, presetdata):
		'''
		Get physical beam diameter in meters from preset if possible.
		'''
		beam_diameter = super(TomoClickTargetFinder, self).getBeamDiameter(presetdata)
		if beam_diameter is None or beam_diameter == 0:
			# handle no beam size calibration
			beam_diameter = self.settings['tomo beam diameter']
		return beam_diameter

	def getTrackTargetDimensions(self, imagedata):
		'''
		Get next track target image size and beam diameter displayed on imagedata
		'''
		if not self.next_acq_node:
			return 0,0
		image_pixelsize = self.calclients['image shift'].getImagePixelSize(imagedata)
		self.current_image_pixelsize = image_pixelsize
		return self._getTrackTargetDimensions(image_pixelsize)
	
	def getFocusTragetDimensions(self, imagedata):
		'''
		Get next focus target image size and beam diameter displayed on imagedata
		'''
		if not self.focus_node:
			return 0,0
		image_pixelsize = self.calclients['image shift'].getImagePixelSize(imagedata)
		self.current_image_pixelsize = image_pixelsize
		return self._getFocusTargetDimensions(image_pixelsize)
			
	def uiRefreshTargetImageVectors(self):
		'''
		refresh target image vector and beam size when ui exposure target panel tool
		is toggled on.
		'''
		super(TomoClickTargetFinder, self).uiRefreshTargetImageVectors()
		cam_length_on_image,beam_diameter_on_image = self._getTrackTargetDimensions(self.current_image_pixelsize)
		self._setTrackImageVectors(cam_length_on_image,beam_diameter_on_image)
		cam_length_on_image,beam_diameter_on_image = self._getFocusTargetDimensions(self.current_image_pixelsize)
		self._setFocusImageVectors(cam_length_on_image,beam_diameter_on_image)
	
	def _setTrackImageVectors(self,cam_length_on_image,beam_diameter_on_image):
		self.trackbeamradius = beam_diameter_on_image / 2
		self.trackimagevectors = {'x':(cam_length_on_image,0),'y':(0,cam_length_on_image)}

	def _getTrackTargetDimensions(self,image_pixelsize):
		try:
			# get settings for the next Acquisition node
			settingsclassname = self.next_acq_node['node']['class string']+'SettingsData'
			results= self.researchDBSettings(getattr(leginondata,settingsclassname),self.next_acq_node['node']['alias'])
			acqsettings = results[0]
			# use first preset in preset order for display
			presetname = acqsettings['track preset']
			# get image dimenzsion of the target preset
			acq_dim = self.presetsclient.getPresetImageDimension(presetname)
			dim_on_image = []
			for axis in ('x','y'):
				dim_on_image.append(int(acq_dim[axis]/image_pixelsize[axis]))
			# get Beam diameter on image
			acq_presetdata = self.presetsclient.getPresetFromDB(presetname)
			beam_diameter = self.calclients['beam size'].getBeamSize(acq_presetdata)
			if beam_diameter is None:
				# handle no beam size calibration
				#beam_diameter = 0
				beam_diameter = self.settings['track beam diameter']
			beam_diameter_on_image = int(beam_diameter/min(image_pixelsize.values()))
			return max(dim_on_image), beam_diameter_on_image
		except:
			# Set Length to 0 in case of any exception
			return 0,0
		
	def _setFocusImageVectors(self,cam_length_on_image,beam_diameter_on_image):
		self.focusbeamradius = beam_diameter_on_image / 2
		self.focusimagevectors = {'x':(cam_length_on_image,0),'y':(0,cam_length_on_image)}

	def _getFocusTargetDimensions(self,image_pixelsize):
		try:
			# get settings for the next Acquisition node
			settingsclassname = self.focus_node['class string']+'SettingsData'
			results= self.researchDBSettings(getattr(leginondata,settingsclassname),self.focus_node['alias'])
			acqsettings = results[0]
			# use first preset in preset order for display
			presetlist = acqsettings['preset order']
			presetname = presetlist[-1]		# Get the last one, usually last is beamshift
			# get image dimenzsion of the target preset
			acq_dim = self.presetsclient.getPresetImageDimension(presetname)
			dim_on_image = []
			for axis in ('x','y'):
				dim_on_image.append(int(acq_dim[axis]/image_pixelsize[axis]))
			# get Beam diameter on image
			acq_presetdata = self.presetsclient.getPresetFromDB(presetname)
			beam_diameter = self.calclients['beam size'].getBeamSize(acq_presetdata)
			if beam_diameter is None:
				# handle no beam size calibration
				#beam_diameter = 0
				beam_diameter = self.settings['focus beam diameter']
			beam_diameter_on_image = int(beam_diameter/min(image_pixelsize.values()))
			return max(dim_on_image), beam_diameter_on_image
		except:
			# Set Length to 0 in case of any exception
			return 0,0

	def publishTargets(self, imagedata, typename, targetlist):
		'''
		Publish specific type of targets on ImagePanel bound to an 
		AcquisitionImageData and TargetListData
		'''
		if typename == 'acquisition':
			self.publishTomoTargets(imagedata, typename, targetlist)
		elif typename == 'focus' or typename == 'track':
			pass
		else: 
			return super(TomoClickTargetFinder, self).publishTargets(imagedata, typename, targetlist)
	
	#def getTrackPreset(self):
	#	# TODO: hard coded. We want to get this as a user input in the future. 
	#	return 'track'
	
	def publishTomoTargets(self,imagedata, typename, targetlist):
		'''
		Publish Tomography targets and relationship between acquisition, focus, and track.
		'''
		# (1) Get all acquisition targets. 
		# (2) Publish them. 
		# (3) Get track offset and preset name. 
		# (4) If each acquisition target gets a focus target, input offset.
		# (5) Make and publish TomoTargetOffsetData for this target list
		# (6) If there is only one focus target for this targetlist, publish to database.

		assert(typename == 'acquisition')
		imagearray = imagedata['image']
		imageshape = imagearray.shape
		imagetargets = self.panel.getTargets('acquisition')											# (1)
		if not imagetargets:
			return
		# advance to next target number
		lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
		number = lastnumber + 1
		for imagetarget in imagetargets:															
			acquisition_td = self.getNewTargetForImage(imagedata,imageshape,imagetarget,targetlist,number)
			self.publish(acquisition_td, database=True)												# (2)
			number += 1

		trackoffset = self.getTrackOffset()															# (3)
		if self.panel.imagepanel.isAutoFocus():														# (4)	
			focusoffset = self.getFocusOffset()
		else:
			focusoffset = (None,None)				# single focus target for this targetlist 
		offset_td = leginondata.TomoTargetOffsetData(list=targetlist,focusoffset=focusoffset,		
											trackoffset=trackoffset) #,trackpreset=trackpreset)		# (5)
		self.publish(offset_td, database=True)
		
		if not self.panel.imagepanel.isAutoFocus():													# (6)
			focustarget = self.panel.getTargets('focus')
			if focustarget:
				focustarget = focustarget[0]
				focus_td = self.getNewTargetForImage(imagedata,imageshape,focustarget,targetlist,number)
				self.publish(focus_td, database=True)												
				number += 1
			else:
				pass

		
	def getNewTargetForImage(self,imagedata, imageshape, target_obj, targetlist, number):
		typename = target_obj.type.name
		column, row = target_obj.position
		drow = row - imageshape[0]/2
		dcol = column - imageshape[1]/2
		targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number,last_focused=self.last_focused)
		return targetdata

	def getTrackOffset(self, offset=None):
		imagedata = self.currentimagedata
		tem = imagedata['scope']['tem']
		ccd = imagedata['camera']['ccdcamera']
		mag = imagedata['scope']['magnification']
		ht = imagedata['scope']['high tension']
		# get image pixel size assume equal binning in both x and y
		args = (mag, tem, ccd)
		image_pixel_size = self.calclients['pixel size'].getPixelSize(*args) * imagedata['camera']['binning']['x']
		# get tilt angle in radians
		args = (tem, ccd, 'stage position', ht, mag, None)
		thetax, thetay = self.calclients['stage position'].getAngles(*args)
		if offset is None:				# Use node settings offset
			offset = self.settings['track target offset'] 
		image_pixel_offset = offset / image_pixel_size
		# This should be in row, col or y,x order
		pixeloffset = [image_pixel_offset * numpy.sin(thetax), image_pixel_offset * numpy.cos(thetax)]
		return pixeloffset

	def getFocusOffset(self, offset=None):
		imagedata = self.currentimagedata
		tem = imagedata['scope']['tem']
		ccd = imagedata['camera']['ccdcamera']
		mag = imagedata['scope']['magnification']
		ht = imagedata['scope']['high tension']
		# get image pixel size assume equal binning in both x and y
		args = (mag, tem, ccd)
		image_pixel_size = self.calclients['pixel size'].getPixelSize(*args) * imagedata['camera']['binning']['x']
		# get tilt angle in radians
		args = (tem, ccd, 'stage position', ht, mag, None)
		thetax, thetay = self.calclients['stage position'].getAngles(*args)
		if offset is None:				# Use node settings offset
			offset = self.settings['focus target offset'] 
		image_pixel_offset = offset / image_pixel_size
		# This should be in row, col or y,x order
		pixeloffset = [image_pixel_offset * numpy.sin(thetax), image_pixel_offset * numpy.cos(thetax)]
		return pixeloffset
	
	def getTiltAxis(self):
		# get tilt axis angle in radians
		imagedata = self.currentimagedata
		tem = imagedata['scope']['tem']
		ccd = imagedata['camera']['ccdcamera']
		mag = imagedata['scope']['magnification']
		ht = imagedata['scope']['high tension']
		args = (tem, ccd, 'stage position', ht, mag, None)
		thetax, thetay = self.calclients['stage position'].getAngles(*args)
		return thetax

