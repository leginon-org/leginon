#!/usr/bin/env python
import data
import event

class TargetHandler(object):
	'''
	nodes should inherit this if they want to work with targets
	'''
	############# DATABASE INTERACTION #################

	def compareTargetNumber(self, first, second):
		return cmp(first['number'], second['number'])

	def researchTargets(self, **kwargs):
		'''
		Get a list of all targets that match the specified keywords.
		Only get most recent versions of each
		'''
		targetquery = data.AcquisitionImageTargetData(**kwargs)
		print 'RESEARCH', targetquery
		targets = self.research(datainstance=targetquery)
		print 'DONE RESEARCH'

		## now filter out only the latest versions
		# map target id to latest version
		# assuming query result is ordered by timestamp, this works
		have = {}
		for target in targets:
			targetnum = target['number']
			if targetnum not in have:
				have[targetnum] = target
		havelist = have.values()
		havelist.sort(self.compareTargetNumber)
		if havelist:
			self.logger.info('Found %s targets' % (len(havelist),))
		return havelist

	def lastTargetNumber(self, **kwargs):
		'''
		Returns the number of the last target given the constraints
		'''
		targets = self.researchTargets(**kwargs)
		maxnumber = 0
		for target in targets:
			if target['number'] > maxnumber:
				maxnumber = target['number']
		return maxnumber


	########## TARGET CREATION #############

	def newTargetList(self, label='', mosaic=False):
		'''
		label will be included in filenames
		mosaic is boolean to indicate list of targets will
		generate a mosaic
		'''
		listdata = data.ImageTargetListData(label=label, mosaic=mosaic)
		return listdata

	def newTarget(self, drow, dcol, **kwargs):
		'''
		create new AcquistionImageTargetData and fill in all fields
		'''
		targetdata = data.AcquisitionImageTargetData(initializer=kwargs)
		targetdata['session'] = self.session
		targetdata['delta row'] = drow
		targetdata['delta col'] = dcol
		targetdata['version'] = 0
		targetdata['status'] = 'new'
		return targetdata

	def newTargetForImage(self, imagedata, drow, dcol, **kwargs):
		'''
		returns a new target data object with data filled in from the image data
		'''
		if 'grid' in image and image['grid'] is not None:
			grid = image['grid']
		else:
			grid = None
		lastnumber = self.lastTargetNumber(image=image, list=list)
		number = lastnumber + 1
		targetdata = self.newTarget(image=image, scope=image['scope'], camera=image['camera'], preset=image['preset'], drow=drow, dcol=dcol, number=number, **kwargs)
		return targetdata

	def newTargetForGrid(self, grid, drow, dcol, **kwargs):
		'''
		generate a new target associated with a grid, but not an image
		'''
		## do we need nullimage if using list or grid???
		nullimage = data.NULL(data.AcquisitionImageData)
		lastnumber = self.lastTargetNumber(grid=grid, image=nullimage)
		number = lastnumber + 1
		targetdata = self.newTarget(grid=grid, drow=drow, dcol=dcol, number=number, **kwargs)
		return targetdata

	###########################################################

	## from MosaicTargetMaker
	def publishTargetList(self, ievent=None):
		# make targets using current instrument state and selected preset
		self.setStatusMessage('getting current EM state')
		try:
			scope = self.emclient.getScope()
			camera = self.emclient.getCamera()
		except node.ResearchError:
			self.setStatusMessage('Error publishing targets, cannot find EM')
			return
		
		pname = self.presetname.get()

		if pname is None:
			self.setStatusMessage('Error publishing targets, no preset selected')
			return

		self.setStatusMessage('Finding preset "%s"' % pname)
		preset = self.presetsclient.getPresetByName(pname)

		if preset is None:
			message = 'Error publishing tagets, cannot find preset "%s"' % pname
			self.setStatusMessage(message)
			return

		self.setStatusMessage('Updating target settings')
		scope.friendly_update(preset)
		camera.friendly_update(preset)
		size = camera['dimension']['x']

		center = {'x': 0.0, 'y': 0.0}
		for key in center:
			# stage position
			scope['stage position'][key] = center[key]

		radius = self.radius.get()
		overlap = self.overlap.get()/100.0
		if overlap < 0.0 or overlap >= 100.0:
			self.setStatusMessage('Invalid overlap specified')
			return
		magnification = scope['magnification']
		try:
			pixelsize = self.pixelsizecalclient.retrievePixelSize(magnification)
		except calibrationclient.NoPixelSizeError:
			print 'No available pixel size'
			return
		binning = camera['binning']['x']
		imagesize = camera['dimension']['x']

		self.setStatusMessage('Creating target list')
		if ievent is None:
			### generated from user click
			targetlist = self.newTargetList(mosaic=True)
		else:
			### generated from external event
			grid = ievent['grid']
			gridid = grid['grid ID']
			label = ''
			targetlist = self.newTargetList(mosaic=True, label=label)

		for delta in self.makeCircle(radius, pixelsize, binning, imagesize, overlap):
			if ievent is not None:
				try:
					initializer['grid'] = ievent['grid']
				except (KeyError, AttributeError):
					pass
			targetdata = self.newTargetForGrid(list=targetlist, drow=delta[0], dcol=delta[1], scope=scope, camera=camera, preset=preset)
			self.publish(targetdata, database=True)
		self.setStatusMessage('Publishing target list')
		self.publish(targetlist, database=True, pubevent=True)
		self.setStatusMessage('Target list published')

	def makeCircle(self, radius, pixelsize, binning, imagesize, overlap=0.0):
		imagesize = int(round(imagesize*(1.0 - overlap)))
		if imagesize <= 0:
			raise ValueError('Invalid overlap value')
		pixelradius = radius/(pixelsize*binning)
		lines = [imagesize/2]
		while lines[-1] < pixelradius - imagesize:
			lines.append(lines[-1] + imagesize)
		pixels = [pixelradius*2]
		for i in lines:
			if i > pixelradius:
				pixels.append(0.0)
			else:
				pixels.append(pixelradius*math.cos(math.asin(i/pixelradius))*2)
		images = []
		for i in pixels:
			images.append(int(math.ceil(i/imagesize)))
		targets = []
		sign = 1
		for n, i in enumerate(images):
			xs = range(-sign*imagesize*(i - 1)/2, sign*imagesize*(i + 1)/2,
									sign*imagesize)
			y = n*imagesize
			for x in xs:
				targets.insert(0, (x, y))
				if y > 0:
					targets.append((x, -y))
			sign = -sign
		return targets

	## from TargetFinder
	def publishTargetList(self):
		'''
		Updates and publishes the target list self.targetlist. Waits for target
		to be "done" if specified.
		'''

		self.unNotifyUserSubmit()

		## map image id to max target number in DB
		## so we don't have to query DB every iteration of the loop
		targetnumbers = {}

		## add a 'number' to the target and then publish it
		for target in self.targetlist:
			# target may have number if it was previously published
			if target['number'] is None:
				parentimage = target['image']
				## should I use dmid or dbid?
				parentid = parentimage.dmid
				if parentid in targetnumbers:
					last_targetnumber = targetnumbers[parentid]
				else:
					last_targetnumber = self.lastTargetNumber(parentimage)
					targetnumbers[parentid] = last_targetnumber

				## increment target number
				targetnumbers[parentid] += 1
				target['number'] = targetnumbers[parentid]
			self.logger.info('Publishing (%s, %s) %s' %
					(target['delta row'], target['delta column'], target['image'].dmid))
			self.publish(target, database=True)
			#targetrefs.append(target.reference())

		## make a list of references to the targets
		refs = map(lambda x: x.reference(), self.targetlist)
		targetlistdata = data.ImageTargetListData(targets=refs)

		self.makeTargetListEvent(targetlistdata)

		self.publish(targetlistdata, pubevent=True)

		self.targetlist = []
		# wait for target list to be processed by other node
		if self.wait_for_done.get():
			self.waitForTargetListDone()


if __name__ == '__main__':
	import node
	import dbdatakeeper

	class TestNode(node.Node, TargetHandler):
		pass
		def __init__(self, id, session=None, managerlocation=None):
			node.Node.__init__(self, id, session, managerlocation)

	db = dbdatakeeper.DBDataKeeper()
	t = TestNode('testnode')

	s = data.SessionData(name='04may26a')
	s = db.query(s, results=1)
	s = s[0]
	print 's', s

	im = db.direct_query(data.AcquisitionImageData, 49780)
	print 'DONE DIRECT', im.dmid
	nullim = data.NULL(data.AcquisitionImageData)
	tar = t.researchTargets(session=s, image=im)
	print 'LEN', len(tar)
	print 'DBID', tar[0].dbid
	#print 'TAR0', tar[0]
	print 'IM REF', tar[0].special_getitem('image', dereference=False)






