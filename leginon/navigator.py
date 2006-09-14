#!/usr/bin/env python

#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#

import node
import event
import data
import time
import calibrationclient
import copy
import correlator
import peakfinder
import math
import gui.wx.Navigator
import newdict
import instrument
import presets

class NavigatorClient(object):
	eventoutputs = [event.MoveToTargetEvent]

	def __init__(self, node):
		self.node = node

	def moveToTarget(self, target, movetype, precision=0.0):
		ev = event.MoveToTargetEvent(target=target, movetype=movetype)
		ev['move precision'] = precision
		print 'nav client waiting'
		self.node.outputEvent(ev, wait=True)
		print 'nav client done waiting'


class Navigator(node.Node):
	panelclass = gui.wx.Navigator.Panel
	settingsclass = data.NavigatorSettingsData
	defaultsettings = {
		'instruments': {'tem':None, 'ccdcamera':None},
		'pause time': 2.5,
		'move type': 'image shift',
		'check calibration': True,
		'precision': 0.0,
		'complete state': True,
		'override preset': False,
		'camera settings':
			data.CameraSettingsData(
				initializer={
					'dimension': {
						'x': 1024,
						'y': 1024,
					},
					'offset': {
						'x': 0,
						'y': 0,
					},
					'binning': {
						'x': 1,
						'y': 1,
					},
					'exposure time': 1000.0,
				}
			),
	}
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs + [event.MoveToTargetEvent]
	eventoutputs = node.Node.eventoutputs + [event.CameraImagePublishEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.calclients = newdict.OrderedDict()
		self.calclients['image shift'] = calibrationclient.ImageShiftCalibrationClient(self)
		self.calclients['stage position'] = calibrationclient.StageCalibrationClient(self)
		self.calclients['modeled stage position'] = calibrationclient.ModeledStageCalibrationClient(self)
		self.calclients['beam shift'] = calibrationclient.BeamShiftCalibrationClient(self)
		self.calclients['image beam shift'] = calibrationclient.ImageBeamShiftCalibrationClient(self)

		self.pcal = calibrationclient.PixelSizeCalibrationClient(self)
		self.presetsclient = presets.PresetsClient(self)
		self.stagelocations = []
		self.getLocationsFromDB()

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.imagedata = None
		self.oldimagedata = None
		self.oldstate = None
		self.newstate = None

		self.addEventInput(event.MoveToTargetEvent, self.handleMoveEvent)

		self.start()

	def handleMoveEvent(self, ev):
		nodename = ev['node']
		movetype = ev['movetype']
		targetdata = ev['target']
		precision = ev['move precision']
		self.logger.info('handling %s request from %s' % (movetype, nodename,))
		imagedata = targetdata['image']
		self.newImage(imagedata)
		rows = targetdata['delta row']
		cols = targetdata['delta column']
		
		self.move(imagedata, rows, cols, movetype, precision)
		self.confirmEvent(ev)

	def newImage(self, imagedata):
		self.oldimagedata = self.imagedata
		self.imagedata = imagedata
		self.correlator.insertImage(imagedata['image'])
		self.setImage(imagedata['image'])

	def newShift(self):
		if self.oldshape is None or self.newshape is None:
			return None
		if self.oldshape != self.newshape:
			return None
		pc = self.correlator.phaseCorrelate()
		self.peakfinder.setImage(pc)
		peak = self.peakfinder.subpixelPeak()
		delta = correlator.wrap_coord(peak, pc.shape)
		return delta

	## called by GUI when image is clicked
	def navigate(self, xy):
		movetype = self.settings['move type']
		precision = self.settings['precision']
		clickrow = xy[1]
		clickcol = xy[0]
		clickshape = self.imagedata['image'].shape

		# calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		self.move(self.imagedata, deltarow, deltacol, movetype, precision)

		# wait for a while
		time.sleep(self.settings['pause time'])

		## acquire image
		self._acquireImage()

		#if self.settings['check calibration']:
		#	self.errorCheck()

		self.panel.navigateDone()

	def _moveback(self):
		self.logger.info('moving back to previous state')
		emdat = data.ScopeEMData(initializer=self.oldstate)
		try:
			self.instrument.setData(emdat)
		except:
			self.logger.exception(errstr % 'unable to set instrument')
			return

	def _move(self, image, row, col, movetype):
		errstr = 'Move failed: %s'
		# get relavent info from click event

		self.logger.info('Moving...')

		pixelshift = {'row':-row, 'col':-col}
		scope = image['scope']
		camera = image['camera']

		# figure out shift
		calclient = self.calclients[movetype]
		try:
			newstate = calclient.transform(pixelshift, scope, camera)
		except calibrationclient.NoMatrixCalibrationError, e:
			errsubstr = 'unable to find calibration for %s' % e
			self.logger.error(errstr % errsubstr)
			self.beep()
			self.panel.navigateDone()
			return
		except Exception, e:
			self.logger.exception(errstr % e)
			self.beep()
			self.panel.navigateDone()
			return

		self.oldstate = self.newstate
		self.newstate = newstate
		emdat = data.ScopeEMData(initializer=newstate)
		try:
			self.instrument.setData(emdat)
		except:
			self.logger.exception(errstr % 'unable to set instrument')
			return

	def move(self, image, row, col, movetype, precision=0.0):
		self.setStatus('processing')
		self._move(image, row, col, movetype)

		if precision:
			self.logger.info('checking that move error is less than %.3e' % (precision,))
			image2 = self._acquireImage(previousimage=image)
			r,c,dist = self.checkMoveError(image, image2, row, col)
			self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))
			while dist > precision:
				self._move(image2, r, c, movetype)
				image2 = self._acquireImage(previousimage=image2)
				lastdist = dist
				r,c,dist = self.checkMoveError(image, image2, r, c)
				self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))
				if dist > lastdist:
					self.logger.info('error got worse')
					self._moveback()
					break

			self.logger.info('correction done')

		self.setStatus('idle')

	def checkMoveError(self, image1, image2, rmove, cmove):
			pc = self.correlator.phaseCorrelate()
			self.peakfinder.setImage(pc)
			peak = self.peakfinder.subpixelPeak()
			rcmoved = correlator.wrap_coord(peak, pc.shape)
			print 'MOVE', rmove, cmove
			r_error = rmove + rcmoved[0]
			c_error = cmove + rcmoved[1]
			print 'ERROR', r_error, c_error

			## calculate error distance
			mag = image1['scope']['magnification']
			tem = image1['scope']['tem']
			ccdcamera = image1['camera']['ccdcamera']
			pixelsize = self.pcal.retrievePixelSize(tem, ccdcamera, mag)
			cbin = image1['camera']['binning']['x']
			rbin = image1['camera']['binning']['y']
			rpix = r_error * rbin
			cpix = c_error * cbin
			pixdist = math.hypot(rpix,cpix)
			distance = pixdist * pixelsize

			return r_error, c_error, distance

	def acquireImage(self):
		self._acquireImage()
		self.panel.acquisitionDone()

	def _acquireImage(self, previousimage=None):
		errstr = 'Acquire image failed: %s'

		# configure camera
		if previousimage is not None:
			## acquire just like previous image
			cameradata = previousimage['camera']
			ccdcamera = cameradata['ccdcamera']
			#camerasettings = data.CameraSettingsData(initializer=camera)
			self.instrument.setCCDCamera(ccdcamera['name'])
			self.instrument.setData(cameradata)
		elif self.settings['override preset']:
			## use override
			instruments = self.settings['instruments']
			try:
				self.instrument.setTEM(instruments['tem'])
				self.instrument.setCCDCamera(instruments['ccdcamera'])
			except ValueError, e:
				self.logger.error('Cannot set instruments: %s' % (e,))
				return
			try:
				self.instrument.ccdcamera.Settings = self.settings['camera settings']
			except Exception, e:
				self.logger.error(errstr % e)
				return
		else:
			# default to current camera config set by preset
			if self.presetsclient.getCurrentPreset() is None:
				self.logger.error('Preset is unknown and preset override is off')
				return

		# acquire image
		try:
			imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		except:
			self.logger.error(errstr % 'unable to get corrected image')
			return

		if imagedata is None:
			self.logger.error('Acquire image failed')
			return

		self.newImage(imagedata)
		return imagedata

	def fromScope(self, name, comment='', xyonly=True):
		'''
		create a new location with name
		if a location by this name already exists in my 
		list of managed locations, it will be replaced by the new one
		also returns the new location object
		'''
		errstr = 'Location from instrument failed: %s'
		try:
			allstagedata = self.instrument.tem.StagePosition
		except:
			self.logger.error(errstr % 'unable to get stage position')
			return
		stagedata = {}
		stagedata['x'] = allstagedata['x']
		stagedata['y'] = allstagedata['y']
		if not xyonly:
			stagedata['z'] = allstagedata['z']
			stagedata['a'] = allstagedata['a']

		loc = self.getLocation(name)
		if loc is None:
			newloc = data.StageLocationData()
			newloc['name'] = name
			newloc['xy only'] = xyonly
		else:
			newloc = data.StageLocationData(initializer=loc.toDict())

		newloc['session'] = self.session
		newloc.update(stagedata)

		## save comment, remove the old location
		for loc in self.stagelocations:
			if loc['name'] == name:
				comment = loc['comment']
				self.stagelocations.remove(loc)
				break
		newloc['comment'] = comment
		newloc['removed'] = False

		self.stagelocations.append(newloc)

		self.locationToDB(newloc)
		locnames = self.locationNames()
		self.panel.locationsEvent(locnames)
		#self.logger.info('Location names %s' % (locnames,))
		return newloc

	def removeLocation(self, loc):
		'''
		remove a location by index or reference
		loc is either a location, or index of the location
		'''
		locremove = None
		if type(loc) is int:
			locremove = self.stagelocations[loc]
			del self.stagelocations[loc]
		elif type(loc) is str:
			loccopy = list(self.stagelocations)
			for location in loccopy:
				if location['name'] == loc:
					locremove = location
					self.stagelocations.remove(location)
		else:
			locremove = loc 
			self.stagelocations.remove(loc)

		if locremove is not None:
			removeloc = data.StageLocationData(initializer=locremove.toDict())
			removeloc['removed'] = True
			self.locationToDB(removeloc)
		locnames = self.locationNames()
		self.panel.locationsEvent(locnames)

	def locationNames(self):
		names = [loc['name'] for loc in self.stagelocations]
		return names

	def getLocation(self, name):
		for i in self.stagelocations:
			if i['name'] == name:
				return i
		return None

	def getLocationNames(self):
		return map(lambda l: l['name'], self.stagelocations)

	def getLocationsFromDB(self):
		'''
		get list of locations for this session from DB
		and use them to create self.stagelocations list
		'''
		### get location from database
		locdata = data.StageLocationData(session=self.session)
		locations = self.research(datainstance=locdata)

		### only want most recent of each name
		### since they are ordered by timestamp, just take the
		### first one of each name
		mostrecent = []
		names = []
		for loc in locations:
			if loc['name'] not in names:
				names.append(loc['name'])
				if not loc['removed']:
					mostrecent.append(loc)
		self.stagelocations[:] = mostrecent

	def locationToDB(self, stagelocdata):
		'''
		stores a location in the DB under the current session name
		if no location is specified, store all self.stagelocations
		'''
		self.publish(stagelocdata, database=True, dbforce=True)

	def toScope(self, loc):
		'''
		loc is either index, location, or name
		'''
		errstr = 'Set instrument failed: %s'
		locdata = None
		if type(loc) is int:
			locdata = self.stagelocations[p]
		elif type(loc) in (str, unicode):
			for location in self.stagelocations:
				if loc == location['name']:
					locdata = location
					break
		elif isinstance(loc, data.StageLocationData):
			locdata = loc
		else:
			self.logger.error(errstr % 'bad argument')
			return

		if locdata is None:
			self.logger.error(errstr % 'no such location')
			return

		name = locdata['name']
		self.logger.info('Moving to location %s' % (name,))

		## should switch to using AllEMData
		stagedict = {}
		stagedict['x'] = locdata['x']
		stagedict['y'] = locdata['y']
		if not locdata['xy only']:
			stagedict['z'] = locdata['z']
			stagedict['a'] = locdata['a']
		try:
			self.instrument.tem.StagePosition = stagedict
		except:
			self.logger.exception(errstr % 'unable to set instrument')
		else:
			self.currentlocation = locdata
			self.logger.info('Moved to location %s' % (name,))

if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
