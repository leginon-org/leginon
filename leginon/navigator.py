#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import node
import event
import data
import time
import camerafuncs
import calibrationclient
import copy
import uidata
import correlator
import peakfinder
import math
import EM

class Navigator(node.Node):

	eventinputs = node.Node.eventinputs + [event.ImageClickEvent,
																					event.ImageAcquireEvent] \
									+ EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.CameraImagePublishEvent] \
									+ EM.EMClient.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.pcal = calibrationclient.PixelSizeCalibrationClient(self)
		self.currentselection = None
		self.stagelocations = []
		self.getLocationsFromDB()

		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()
		self.newshape = None
		self.oldshape = None

		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.ImageAcquireEvent, self.handleImageAcquire)

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

	def handleImageClick(self, clickevent):
		self.logger.info('Handling image click...')
		## get relavent info from click event
		clickrow = clickevent['array row']
		clickcol = clickevent['array column']
		clickshape = clickevent['array shape']
		clickscope = clickevent['scope']
		clickcamera = clickevent['camera']

		## calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		## to shift clicked point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		pixelshift = {'row':deltarow, 'col':deltacol}
		mag = clickscope['magnification']

		## figure out shift
		movetype = self.movetype.getSelectedValue()
		calclient = self.calclients[movetype]
		try:
			newstate = calclient.transform(pixelshift, clickscope, clickcamera)
		except:
			message = ('Error in transform. Likely missing calibration for %s at %s'
									+ ' and current high tension') % (movetype, mag)
			self.messagelog.error(message)
			self.logger.error(message)
			node.beep()
			return
		if not self.completestate.get():
			if movetype == 'modeled stage position':
				newmovetype = 'stage position'
			else:
				newmovetype = movetype
			newstate = {newmovetype: newstate[newmovetype]}
		emdat = data.ScopeEMData(initializer=newstate)
		self.emclient.setScope(emdat)

		# wait for a while
		time.sleep(self.delaydata.get())

		## acquire image
		self.acquireImage()

		## calibration error checking
		if self.calerror.get():
			newshift = self.newShift()
			if newshift is None:
				self.logger.info('Error not calculated')
			else:
				self.logger.info('Request %s, new shift %s' % (pixelshift, newshift))
				r_error = pixelshift['row'] - newshift[0]
				c_error = pixelshift['col'] - newshift[1]
				error = r_error, c_error
				errordist = math.hypot(error[0], error[1])

				pixsize = self.pcal.retrievePixelSize(mag)
				binning = clickcamera['binning']['x']
				dist = errordist * pixsize * binning
				umdist = dist * 1000000.0
				self.logger('Error %s pixels, distance %s pixels (%s microns)'
										% (error, errordist, umdist))
				if (abs(pixelshift['row']) > clickshape[0]/4) or (abs(pixelshift['col']) > clickshape[1]/4):
					self.logger.info('Correlation untrusted due to large requested shift')
				else:
					## insert into DB?
					pass


		##just in case this is a fake click event
		## (which it is now when it comes from navigator's own image
		if isinstance(clickevent, event.ImageClickEvent):
			self.confirmEvent(clickevent)

		node.beep()

	def handleImageAcquire(self, acqevent):
		self.acquireImage()
		self.confirmEvent(acqevent)

	# I wouldn't expect this to actually work
	def handleImageClick2(self, xy):
		click = {'array row': xy[1],
							'array column': xy[0],
							'array shape': self.shape,
							'scope': self.scope,
							'camera': self.camera}
		self.handleImageClick(click)

	def acquireImage(self):
		self.cam.uiApplyAsNeeded()
		try:
			imagedata = self.cam.acquireCameraImageData()
		except camerafuncs.NoCorrectorError:
			self.messagelog.error('No Corrector node, acquisition failed')
			return

		if imagedata is None:
			self.messagelog.error('acquisition failed')
			return

		self.scope = imagedata['scope']
		self.camera = imagedata['camera']
		newimage = imagedata['image']
		self.shape = newimage.shape
		self.newImage(newimage)
		self.image.setImage(newimage)

	def fromScope(self, name, comment=''):
		'''
		create a new location with name
		if a location by this name already exists in my 
		list of managed locations, it will be replaced by the new one
		also returns the new location object
		'''
		allstagedata = self.emclient.getScope()['stage position']
		stagedata = {}
		stagedata['x'] = allstagedata['x']
		stagedata['y'] = allstagedata['y']
		xyonly = self.xyonly.get()
		if not xyonly:
			stagedata['z'] = allstagedata['z']
			stagedata['a'] = allstagedata['a']

		newloc = data.StageLocationData()
		newloc.update(stagedata)
		newloc['xy only'] = xyonly
		newloc['session'] = self.session
		newloc['name'] = name

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
		self.logger.info('Location names %s' % (locnames,))
		self.uiselectlocation.set(locnames, len(locnames)-1)
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
			locremove['removed'] = 1
			self.locationToDB(locremove)
		locnames = self.locationNames()
		self.uiselectlocation.set(locnames, 0)

	def uiSelectedToScope(self):
		new = self.uiselectlocation.getSelectedValue()
		self.toScope(new)

	def locationNames(self):
		names = [loc['name'] for loc in self.stagelocations]
		return names

	def uiSelectedFromScope(self):
		sel = self.uiselectlocation.getSelectedValue()
		newlocation = self.fromScope(sel)

	def uiSelectedRemove(self):
		sel = self.uiselectlocation.getSelectedValue()
		self.removeLocation(sel)

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		newcomment = self.enteredcomment.get()
		if newname:
			newloc = self.fromScope(newname, newcomment)

	def uiSelectCallback(self, index):
		try:
			self.currentselection = self.stagelocations[index]
		except IndexError:
			self.currentselection = None
		self.locationToParams(self.currentselection)
		return index

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
		locdata = None
		if type(loc) is int:
			locdata = self.stagelocations[p]
		elif type(loc) is str:
			for location in self.stagelocations:
				if loc == location['name']:
					locdata = location
					break
		elif isinstance(loc, data.StageLocationData):
			locdata = loc
		else:
			self.logger.error('Bad argument for toScope')
			return

		if locdata is None:
			self.logger.error('No such location')
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
			self.logger.exception('Maybe EM is not running')
		else:
			self.currentlocation = locdata
			self.logger.info('Moved to location %s' % (name,))

	def locationToDict(self, locationdata):
		d = {}
		if locationdata is None:
			self.locationparams.set(d, callback=False)
			return d

		for key in ('comment', 'x', 'y'):
			if locationdata[key] is not None:
				d[key] = locationdata[key]
		if not locationdata['xy only']:
			for key in ('z','a'):
				if locationdata[key] is not None:
					d[key] = locationdata[key]
		return d

	def locationToParams(self, locationdata):
		d = self.locationToDict(locationdata)
		self.locationparams.set(d, callback=False)

	def uiParamsCallback(self, value):
		if (self.currentselection is None) or (not value):
			return {}
		else:
			self.currentselection.update(value)
			self.locationToDB(self.currentselection)
			d = self.locationToDict(self.currentselection)
		return d

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Message Log')

		self.calerror = uidata.Boolean('Calibration Error Checking', False, 'rw', persist=True)

		movetypes = self.calclients.keys()
		self.movetype = uidata.SingleSelectFromList('TEM Parameter', movetypes, 0)
		self.delaydata = uidata.Float('Delay (sec)', 2.5, 'rw')
		self.completestate = uidata.Boolean('Complete State', False, 'rw', persist=True)

		#self.usecamconfig = uidata.Boolean('Use This Configuration', True, 'rw', persist=True)
		cameraconfigure = self.cam.uiSetupContainer()

		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.movetype, self.completestate, self.delaydata, cameraconfigure))

		acqmeth = uidata.Method('Acquire', self.acquireImage)
		self.image = uidata.ClickImage('Navigation', self.handleImageClick2, None)
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((self.calerror, acqmeth, self.image))


		## Location Presets
		locationcontainer = uidata.Container('Stage Locations')
		self.xyonly = uidata.Boolean('From Scope gets X and Y Only', True, 'rw')
		self.enteredname = uidata.String('New Name', '', 'rw')
		self.enteredcomment = uidata.String('New Comment', '', 'rw')
		newfromscopemethod = uidata.Method('New Location From Scope', self.uiNewFromScope)
		self.locationparams = uidata.Struct('Location Parameters', {}, 'rw', self.uiParamsCallback)
		self.uiselectlocation = uidata.SingleSelectFromList('Location Selector', [], 0, callback=self.uiSelectCallback)
		toscopemethod = uidata.Method('To Scope', self.uiSelectedToScope)
		fromscopemethod = uidata.Method('From Scope', self.uiSelectedFromScope)
		removemethod = uidata.Method('Remove', self.uiSelectedRemove)
		obs = (
			self.xyonly,
			self.enteredname,
			self.enteredcomment,
			newfromscopemethod,
			self.uiselectlocation,
			toscopemethod,
			fromscopemethod,
			removemethod,
			self.locationparams,
		)
		locationcontainer.addObjects(obs)

		locnames = self.locationNames()
		self.uiselectlocation.set(locnames, 0)

		## main Navigator container
		container = uidata.LargeContainer('Navigator')
		container.addObjects((self.messagelog, controlcontainer, settingscontainer, locationcontainer))
		self.uicontainer.addObject(container)

class SimpleNavigator(Navigator):
	def __init__(self, id, session, managerlocation, **kwargs):
		Navigator.__init__(self, id, session, managerlocation, **kwargs)
		self.defineUserInterface()
		self.start()


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
