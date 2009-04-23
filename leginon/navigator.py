# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/navigator.py,v $
# $Revision: 1.130 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-14 22:08:15 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import node
import event
import leginondata
import time
import calibrationclient
from pyami import correlator, peakfinder, imagefun, ordereddict
import math
import gui.wx.Navigator
import instrument
import presets
import types
import numpy
import leginondata
import threading

class NavigatorClient(object):
	eventoutputs = [event.MoveToTargetEvent]
	eventinputs = [event.MoveToTargetDoneEvent]

	def __init__(self, node):
		self.node = node
		self.node.addEventInput(event.MoveToTargetDoneEvent, self.handleMoveDone)
		self.movedone = threading.Event()

	def handleMoveDone(self, evt):
		self.movedonestatus = evt['status']
		self.movedone.set()

	def moveToTarget(self, target, movetype, precision=0.0, accept_precision=1e-3, final_imageshift=False):
		self.node.startTimer('moveToTarget')
		ev = event.MoveToTargetEvent(target=target, movetype=movetype)
		ev['move precision'] = precision
		ev['accept precision'] = accept_precision
		ev['final image shift'] = final_imageshift
		self.movedone.clear()
		self.node.outputEvent(ev, wait=False)
		## wait for event
		self.movedone.wait()
		self.node.stopTimer('moveToTarget')
		return self.movedonestatus

class Navigator(node.Node):
	panelclass = gui.wx.Navigator.Panel
	settingsclass = leginondata.NavigatorSettingsData
	defaultsettings = {
		'instruments': {'tem':None, 'ccdcamera':None},
		'pause time': 2.5,
		'move type': 'image shift',
		'check calibration': True,
		'precision': 0.0,
		'accept precision': 1e-3,
		'complete state': True,
		'override preset': False,
		'max error': 256,
		'cycle after': False,
		'cycle each': False,
		'final image shift': False,
		'camera settings':
			leginondata.CameraSettingsData(
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
	eventoutputs = node.Node.eventoutputs + presets.PresetsClient.eventoutputs + [event.CameraImagePublishEvent, event.MoveToTargetDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.calclients = ordereddict.OrderedDict()
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
		self.oldimagedata = None
		self.newimagedata = None
		self.oldstate = None
		self.newstate = None

		self.addEventInput(event.MoveToTargetEvent, self.handleMoveEvent)

		self.start()

	def handleMoveEvent(self, ev):
		nodename = ev['node']
		movetype = ev['movetype']
		targetdata = ev['target']
		precision = ev['move precision']
		accept_precision = ev['accept precision']
		final_imageshift = ev['final image shift']
		self.logger.info('handling %s request from %s' % (movetype, nodename,))
		imagedata = targetdata['image']
		self.newImage(imagedata)
		preset = imagedata['preset']
		rows = targetdata['delta row']
		cols = targetdata['delta column']

		if precision:
			check=True
		else:
			check=False
		self.startTimer('move')
		status = self.move(rows, cols, movetype, precision, accept_precision, check, preset=preset, final_imageshift=final_imageshift)
		self.stopTimer('move')

		evt = event.MoveToTargetDoneEvent(status=status, target=targetdata)
		evt['destination'] = nodename
		self.outputEvent(evt)

	def newImage(self, imagedata):
		self.oldimagedata = self.newimagedata
		self.newimagedata = imagedata
		self.setImage(imagedata['image'], 'Image')
		self.correlator.insertImage(imagedata['image'])

	## called by GUI when image is clicked
	def navigate(self, xy):
		movetype = self.settings['move type']
		precision = self.settings['precision']
		accept_precision = self.settings['accept precision']
		final_imageshift = self.settings['final image shift']
		clickrow = xy[1]
		clickcol = xy[0]
		clickshape = self.newimagedata['image'].shape

		# calculate delta from image center
		centerr = clickshape[0] / 2.0 - 0.5
		centerc = clickshape[1] / 2.0 - 0.5
		deltarow = clickrow - centerr
		deltacol = clickcol - centerc

		check = self.settings['check calibration']
		status = self.move(deltarow, deltacol, movetype, precision, accept_precision, check, final_imageshift=final_imageshift)

		# wait for a while
		time.sleep(self.settings['pause time'])

		## acquire image if check not done
		if not check:
			self.reacquireImage()
		elif status != 'error' and movetype != 'image shift' and final_imageshift:
			self.reacquireImage()

		self.panel.navigateDone()

	def _moveback(self):
		self.logger.info('moving back to previous state')
		emdat = leginondata.NavigatorScopeEMData()
		emdat.friendly_update(self.oldstate)
		try:
			self.instrument.setData(emdat)
		except:
			self.logger.exception('unable to set instrument')
			return

	def _move(self, row, col, movetype):
		errstr = 'Move failed: %s'
		# get relavent info from click event

		self.logger.info('Moving...')

		pixelshift = {'row':-row, 'col':-col}
		scope = self.newimagedata['scope']
		camera = self.newimagedata['camera']

		# figure out shift
		calclient = self.calclients[movetype]
		try:
			newstate = calclient.transform(pixelshift, scope, camera)
		except calibrationclient.NoMatrixCalibrationError, e:
			errsubstr = 'unable to find calibration for %s' % e
			self.logger.error(errstr % errsubstr)
			self.beep()
			self.panel.navigateDone()
			return True
		except Exception, e:
			self.logger.exception(errstr % e)
			self.beep()
			self.panel.navigateDone()
			return True

		self.oldstate = self.newstate
		self.newstate = newstate
		emdat = leginondata.NavigatorScopeEMData()
		emdat.friendly_update(newstate)
		try:
			self.instrument.setData(emdat)
		except:
			self.logger.exception(errstr % 'unable to set instrument')
			return True

		return False

	def move_away_move_back(self, label, moves, distance, angle=None):
		# initial move
		origstage = self.instrument.tem.StagePosition
		origx = origstage['x']
		origy = origstage['y']
		if angle is None:
			rangle = 2 * numpy.pi * numpy.random.rand()
		else:
			rangle = angle
		deltax = distance * numpy.cos(rangle)
		deltay = distance * numpy.sin(rangle)
		tmpx = origx + deltax
		tmpy = origy + deltay
		self.instrument.tem.StagePosition = {'x': tmpx, 'y': tmpy}
		time.sleep(2)
		self.instrument.tem.StagePosition = {'x': origx, 'y': origy}
		time.sleep(2)
		self.acquireImage()

		self.origmove = 0,0
		self.origimagedata = self.newimagedata
		origscope = self.origimagedata['scope']
		origcamera = self.origimagedata['camera']
		origstage = origscope['stage position']
		origx = origstage['x']
		origy = origstage['y']
		for i in range(moves):
			if angle is None:
				rangle = 2 * numpy.pi * numpy.random.rand()
			else:
				rangle = angle
			deltax = distance * numpy.cos(rangle)
			deltay = distance * numpy.sin(rangle)
			tmpx = origx + deltax
			tmpy = origy + deltay
			self.instrument.tem.StagePosition = {'x': tmpx, 'y': tmpy}
			time.sleep(2)
			self.instrument.tem.StagePosition = {'x': origx, 'y': origy}
			time.sleep(2)
			self.reacquireImage()
			r,c,dist = self.checkMoveError()
			self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))
			repdata = leginondata.StageReproducibilityData()
			repdata['session'] = self.session
			repdata['label'] = label
			repdata['move x'] = deltax
			repdata['move y'] = deltay
			repdata['error pixels r'] = r
			repdata['error pixels c'] = c
			repdata['error meters'] = dist
			repdata.insert(force=True)

	def cycleToPreset(self, preset=None, keep_shift=False):
		if preset is None:
			return
		self.logger.info('preset cycle')
		self.presetsclient.toScope(preset['name'], keep_shift=keep_shift)

	def move(self, row, col, movetype, precision=0.0, accept_precision=1e-3, check=False, preset=None, final_imageshift=False):
		self.setStatus('processing')
		self.origimagedata = self.newimagedata
		self.origmove = row,col
		err = self._move(row, col, movetype)
		if err:
			self.setStatus('idle')
			return 'error'

		shape = self.origimagedata['image'].shape
		target = shape[0]/2.0-0.5+self.origmove[0], shape[1]/2.0-0.5+self.origmove[1]
		status = 'ok'
		if check:
			if self.outofbounds(target, shape):
				self.logger.info('target out of bounds, so cannot check error')
				self.setStatus('idle')
				self.reacquireImage()
				return 'error'
			if self.settings['cycle each']:
				self.cycleToPreset(preset)
			self.reacquireImage()
			r,c,dist = self.checkMoveError()
			self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))

			if precision:
				self.logger.info('checking that move error is less than %.3e' % (precision,))
				while dist > precision:
					time.sleep(0.2)
					self._move(r, c, movetype)
					time.sleep(2.0)
					if self.settings['cycle each']:
						self.cycleToPreset(preset)
					self.reacquireImage()
					lastdist = dist
					r,c,dist = self.checkMoveError()
					self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))
					if dist > lastdist:
						self.logger.info('error got worse')
						if dist > accept_precision:
							status = 'error'
						else:
							self._moveback()
						break

				# final image shift
				if status != 'error' and movetype != 'image shift' and final_imageshift:
					self.logger.info('making final correction with image shift')
					self._move(r, c, 'image shift')
					
				self.logger.info('move correction done, status: %s' % (status,))
				if self.settings['cycle after']:
					self.cycleToPreset(preset, keep_shift=True)

		self.setStatus('idle')
		return status

	def outofbounds(self, coord, shape):
		if coord[0] < 0 or coord[0] > shape[0]-1:
			return True
		if coord[1] < 0 or coord[1] > shape[1]-1:
			return True
		return False

	def checkMoveError(self):
		#maxerror = self.settings['max error']
		#limit = (int(maxerror*2), int(maxerror*2))

		oldshape = self.oldimagedata['image'].shape
		limit = oldshape
		location = oldshape[0]/2.0-0.5+self.origmove[0], oldshape[1]/2.0-0.5+self.origmove[1]
		
		im1 = imagefun.crop_at(self.origimagedata['image'], location, limit, mode='constant', cval=0.0)
		im2 = imagefun.crop_at(self.newimagedata['image'], 'center', limit)

		pc = correlator.phase_correlate(im2, im1, zero=False)
		subpixelpeak = self.peakfinder.subpixelPeak(newimage=pc, guess=(0.5,0.5), limit=limit)
		res = self.peakfinder.getResults()
		pixelpeak = res['pixel peak']
		unsignedpixelpeak = res['unsigned pixel peak']
		peaktargets = [(unsignedpixelpeak[1], unsignedpixelpeak[0])]
		r_error = subpixelpeak[0]
		c_error = subpixelpeak[1]

		self.setImage(pc, 'Correlation')
		peaktargets = [(unsignedpixelpeak[1], unsignedpixelpeak[0])]
		self.setTargets(peaktargets, 'Peak')

		## calculate error distance
		scope = self.newimagedata['scope']
		camera = self.newimagedata['camera']
		mag = scope['magnification']
		tem = scope['tem']
		ccdcamera = camera['ccdcamera']
		pixelsize = self.pcal.retrievePixelSize(tem, ccdcamera, mag)
		cbin = camera['binning']['x']
		rbin = camera['binning']['y']
		rpix = r_error * rbin
		cpix = c_error * cbin
		pixdist = math.hypot(rpix,cpix)
		distance = pixdist * pixelsize

		return r_error, c_error, distance

	def uiAcquireImage(self):
		self.acquireImage()
		self.panel.acquisitionDone()

	def reacquireImage(self):
		if self.origimagedata is None:
			raise RuntimeError('no image to reacquire')
		# configure camera just like current image
		cameradata = self.origimagedata['camera']
		ccdcamera = cameradata['ccdcamera']
		## except correction channel should be opposite
		if self.origimagedata['correction channel']:
			corchannel = 0
		else:
			corchannel = 1
		#camerasettings = leginondata.CameraSettingsData(initializer=camera)
		self.instrument.setCCDCamera(ccdcamera['name'])
		self.instrument.setData(cameradata)
		self._acquireImage(corchannel)

	def acquireImage(self):
		if self.settings['override preset']:
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
				errstr = 'Acquire image failed: %s'
				self.logger.error(errstr % e)
				return
		else:
			# default to current camera config set by preset
			if self.presetsclient.getCurrentPreset() is None:
				self.logger.error('Preset is unknown and preset override is off')
				return
		self._acquireImage()

	def _acquireImage(self, channel=0):
		try:
			imagedata = self.acquireCorrectedCameraImageData(channel=channel)
		except:
			self.logger.error('unable to get corrected image')
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
			newloc = leginondata.StageLocationData()
			newloc['name'] = name
			newloc['xy only'] = xyonly
		else:
			newloc = leginondata.StageLocationData(initializer=loc.toDict())

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
		elif type(loc) in types.StringTypes:
			loccopy = list(self.stagelocations)
			for location in loccopy:
				if location['name'] == loc:
					locremove = location
					self.stagelocations.remove(location)
		else:
			locremove = loc 
			self.stagelocations.remove(loc)

		if locremove is not None:
			removeloc = leginondata.StageLocationData(initializer=locremove.toDict())
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
		locdata = leginondata.StageLocationData(session=self.session)
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
		elif isinstance(loc, leginondata.StageLocationData):
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
