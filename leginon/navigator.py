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
import camerafuncs
import calibrationclient
import copy
import correlator
import peakfinder
import math
import EM
import gui.wx.Navigator
import newdict

class Navigator(node.Node):
	panelclass = gui.wx.Navigator.Panel
	settingsclass = data.NavigatorSettingsData
	defaultsettings = {
		'pause time': 2.5,
		'move type': 'image shift',
		'check calibration': True,
		'complete state': True,
		'use camera settings': False,
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
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.CameraImagePublishEvent] \
									+ EM.EMClient.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.calclients = newdict.OrderedDict()
		self.calclients['image shift'] = calibrationclient.ImageShiftCalibrationClient(self)
		self.calclients['stage position'] = calibrationclient.StageCalibrationClient(self)
		self.calclients['modeled stage position'] = calibrationclient.ModeledStageCalibrationClient(self)
		self.calclients['beam shift'] = calibrationclient.BeamShiftCalibrationClient(self)
		self.calclients['image beam shift'] = calibrationclient.ImageBeamShiftCalibrationClient(self)

		self.pcal = calibrationclient.PixelSizeCalibrationClient(self)
		self.stagelocations = []
		self.getLocationsFromDB()

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.newshape = None
		self.oldshape = None

		self.scope = None
		self.camera = None
		self.shape = None
		self.start()

	def newImage(self, newimage):
		self.oldshape = self.newshape
		self.newshape = newimage.shape
		self.correlator.insertImage(newimage)

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

	def navigate(self, xy):
		errstr = 'Move failed: %s'
		# get relavent info from click event
		clickrow = xy[1]
		clickcol = xy[0]
		clickshape = self.shape
		clickscope = self.scope
		clickcamera = self.camera

		if None in (clickrow, clickcol, clickshape, clickscope, clickcamera):
			self.panel.navigateDone()
			return

		self.logger.info('Moving to clicked position...')

		# calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		# to shift clicked point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		pixelshift = {'row':deltarow, 'col':deltacol}
		mag = clickscope['magnification']

		# figure out shift
		movetype = self.settings['move type']
		calclient = self.calclients[movetype]
		try:
			newstate = calclient.transform(pixelshift, clickscope, clickcamera)
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
		if not self.settings['complete state']:
			if movetype == 'modeled stage position':
				newmovetype = 'stage position'
				newstate = {newmovetype: newstate[newmovetype]}
			elif movetype == 'image beam shift':
				newstate = {'image shift': newstate['image shift'], 'beam shift': newstate['beam shift']}
			else:
				newmovetype = movetype
				newstate = {newmovetype: newstate[newmovetype]}
		emdat = data.ScopeEMData(initializer=newstate)
		try:
			self.emclient.setScope(emdat)
		except node.PublishError:
			self.logger.exception(errstr % 'unable to set instrument')
			return
		except node.ConfirmationNoBinding:
			self.logger.exception(errstr % 'unable to set instrument (not bound)')
			return

		# wait for a while
		time.sleep(self.settings['pause time'])

		## acquire image
		self._acquireImage()

		## calibration error checking
		if self.settings['check calibration']:
			newshift = self.newShift()
			if newshift is None:
				res = 'Error calculation failed'
			else:
				r_error = pixelshift['row'] - newshift[0]
				c_error = pixelshift['col'] - newshift[1]
				error = r_error, c_error
				errordist = math.hypot(error[0], error[1])

				pixsize = self.pcal.retrievePixelSize(mag)
				binning = clickcamera['binning']['x']
				dist = errordist * pixsize * binning
				umdist = dist * 1000000.0

				res = 'Error: %.3f microns (%.3f pixels) [requested <%d, %d>, moved <%.2f, %.2f>]' % (umdist, errordist, pixelshift['col'], pixelshift['row'], newshift[1], newshift[0])

				if (abs(pixelshift['row']) > clickshape[0]/4) or (abs(pixelshift['col']) > clickshape[1]/4):
					self.logger.warning('Error calculation untrusted due to large requested move')
				else:
					## insert into DB?
					pass
			self.logger.info(res)

		self.beep()
		self.panel.navigateDone()

	def acquireImage(self):
		self._acquireImage()
		self.panel.acquisitionDone()

	def _acquireImage(self):
		errstr = 'Acquire image failed: %s'
		if self.settings['use camera settings']:
			try:
				self.cam.setCameraDict(self.settings['camera settings'])
			except camerafuncs.CameraError, e:
				self.logger.error(errstr % e)
				return
		try:
			imagedata = self.cam.acquireCameraImageData()
		except camerafuncs.NoCorrectorError:
			self.logger.error(errstr % 'unable to get corrected image')
			return

		if imagedata is None:
			self.logger.error('Acquire image failed')
			return

		self.scope = imagedata['scope']
		self.camera = imagedata['camera']
		newimage = imagedata['image']
		self.shape = newimage.shape
		self.newImage(newimage)
		self.setImage(newimage)

	def fromScope(self, name, comment='', xyonly=True):
		'''
		create a new location with name
		if a location by this name already exists in my 
		list of managed locations, it will be replaced by the new one
		also returns the new location object
		'''
		errstr = 'Location from instrument failed: %s'
		try:
			allstagedata = self.emclient.getScope()['stage position']
		except (EM.ScopeUnavailable, KeyError), e:
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
		scopedata = data.ScopeEMData()
		scopedata['stage position'] = stagedict
		try:
			self.emclient.setScope(scopedata)
		except node.PublishError:
			self.logger.exception(errstr % 'unable to set instrument')
		except node.ConfirmationNoBinding:
			self.logger.exception(errstr % 'unable to set instrument (not bound)')
		else:
			self.currentlocation = locdata
			self.logger.info('Moved to location %s' % (name,))

if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
