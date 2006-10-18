# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/navigator.py,v $
# $Revision: 1.114 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-18 22:04:04 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import node
import event
import data
import time
import calibrationclient
import correlator
import peakfinder
import math
import gui.wx.Navigator
import newdict
import instrument
import presets
import imagefun
import types

class NavigatorClient(object):
	eventoutputs = [event.MoveToTargetEvent]

	def __init__(self, node):
		self.node = node

	def moveToTarget(self, target, movetype, precision=0.0):
		ev = event.MoveToTargetEvent(target=target, movetype=movetype)
		ev['move precision'] = precision
		self.node.outputEvent(ev, wait=True)

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
		'max error': 200,
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
		self.logger.info('handling %s request from %s' % (movetype, nodename,))
		imagedata = targetdata['image']
		self.newImage(imagedata)
		rows = targetdata['delta row']
		cols = targetdata['delta column']

		if precision:
			check=True
		else:
			check=False
		self.move(rows, cols, movetype, precision, check)
		self.confirmEvent(ev)

	def newImage(self, imagedata):
		self.oldimagedata = self.newimagedata
		self.newimagedata = imagedata
		self.setImage(imagedata['image'], 'Image')
		self.correlator.insertImage(imagedata['image'])

	## called by GUI when image is clicked
	def navigate(self, xy):
		movetype = self.settings['move type']
		precision = self.settings['precision']
		clickrow = xy[1]
		clickcol = xy[0]
		clickshape = self.newimagedata['image'].shape

		# calculate delta from image center
		centerr = clickshape[0] / 2.0 - 0.5
		centerc = clickshape[1] / 2.0 - 0.5
		deltarow = clickrow - centerr
		deltacol = clickcol - centerc

		check = self.settings['check calibration']
		self.move(deltarow, deltacol, movetype, precision, check)

		# wait for a while
		time.sleep(self.settings['pause time'])

		## acquire image if check not done
		if not check:
			self.reacquireImage()

		self.panel.navigateDone()

	def _moveback(self):
		self.logger.info('moving back to previous state')
		emdat = data.ScopeEMData(initializer=self.oldstate)
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
		emdat = data.ScopeEMData(initializer=newstate)
		try:
			self.instrument.setData(emdat)
		except:
			self.logger.exception(errstr % 'unable to set instrument')
			return True

		return False

	def move(self, row, col, movetype, precision=0.0, check=False):
		self.setStatus('processing')
		self.origimagedata = self.newimagedata
		self.origmove = row,col
		err = self._move(row, col, movetype)
		if err:
			self.setStatus('idle')
			return

		if check:
			self.reacquireImage()
			r,c,dist = self.checkMoveError()
			self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))

			if precision:
				self.logger.info('checking that move error is less than %.3e' % (precision,))
				while dist > precision:
					self._move(r, c, movetype)
					self.reacquireImage()
					lastdist = dist
					r,c,dist = self.checkMoveError()
					self.logger.info('move error: pixels: %s, %s, %.3em,' % (r,c,dist,))
					if dist > lastdist:
						self.logger.info('error got worse')
						self._moveback()
						break
				self.logger.info('correction done')

		self.setStatus('idle')

	def checkMoveError(self):
		maxerror = self.settings['max error']
		limit = (int(maxerror*2), int(maxerror*2))

		oldshape = self.oldimagedata['image'].shape
		location = oldshape[0]/2.0-0.5+self.origmove[0], oldshape[1]/2.0-0.5+self.origmove[1]
		im1 = imagefun.crop_at(self.origimagedata['image'], location, limit)
		im2 = imagefun.crop_at(self.newimagedata['image'], 'center', limit)
		pc = correlator.phase_correlate(im2,im1,zero=False)
		subpixelpeak = self.peakfinder.subpixelPeak(newimage=pc, guess=(0,0), limit=limit)
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
		if self.newimagedata is None:
			raise RuntimeError('no image to reacquire')
		# configure camera just like current image
		cameradata = self.newimagedata['camera']
		ccdcamera = cameradata['ccdcamera']
		## except correction channel should be opposite
		if self.newimagedata['correction channel']:
			corchannel = 0
		else:
			corchannel = 1
		self.instrument.setCorrectionChannel(corchannel)
		#camerasettings = data.CameraSettingsData(initializer=camera)
		self.instrument.setCCDCamera(ccdcamera['name'])
		self.instrument.setData(cameradata)
		return self._acquireImage()

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
		return self._acquireImage()

	def _acquireImage(self):
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
