#!/usr/bin/env python
import data
import event

class TargetHandler(object):
	'''
	nodes should inherit this if they want to work with targets
	'''
	############# DATABASE INTERACTION #################

	eventinputs = []
	eventoutputs = [event.ImageTargetListPublishEvent]

	def compareTargetNumber(self, first, second):
		### if come from different images, compare image dbid
		if 'image' in first and 'image' in second:
			if None not in (first['image'], second['image']):
				if first['image'] is not second['image']:
					return cmp(first['image'].dbid, second['image'].dbid)
		return cmp(first['number'], second['number'])

	def researchTargets(self, **kwargs):
		'''
		Get a list of all targets that match the specified keywords.
		Only get most recent versions of each
		'''
		targetquery = data.AcquisitionImageTargetData(**kwargs)
		targets = self.research(datainstance=targetquery)

		## now filter out only the latest versions
		# map target id to latest version
		# assuming query result is ordered by timestamp, this works
		have = {}
		for target in targets:
			targetnum = target['number']
			if 'image' in target and target['image'] is not None:
				imageid = target['image'].dbid
			else:
				imageid = None
			key = (imageid, targetnum)
			if key not in have:
				have[key] = target
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

	def newTargetList(self, label='', mosaic=False, image=None):
		'''
		label will be included in filenames
		mosaic is boolean to indicate list of targets will
		generate a mosaic
		'''
		listdata = data.ImageTargetListData(session=self.session, label=label, mosaic=mosaic, image=image)
		return listdata

	def newTarget(self, drow, dcol, **kwargs):
		'''
		create new AcquistionImageTargetData and fill in all fields
		'''
		targetdata = data.AcquisitionImageTargetData(initializer=kwargs)
		targetdata['delta row'] = drow
		targetdata['delta column'] = dcol
		if 'session' not in kwargs:
			targetdata['session'] = self.session
		if 'version' not in kwargs:
			targetdata['version'] = 0
		if 'status' not in kwargs:
			targetdata['status'] = 'new'
		return targetdata

	def newTargetForImage(self, imagedata, drow, dcol, **kwargs):
		'''
		returns a new target data object with data filled in from the image data
		'''
		if 'grid' in imagedata and imagedata['grid'] is not None:
			grid = imagedata['grid']
		else:
			grid = None

		## get next number if not already specified
		if 'number' not in kwargs or kwargs['number'] is None:
			lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
			kwargs['number'] = lastnumber + 1

		targetdata = self.newTarget(image=imagedata, scope=imagedata['scope'], camera=imagedata['camera'], preset=imagedata['preset'], drow=drow, dcol=dcol, session=self.session, **kwargs)
		return targetdata

	def newTargetForGrid(self, grid, drow, dcol, **kwargs):
		'''
		generate a new target associated with a grid, but not an image
		'''
		## do we need nullimage if using list or grid???
		nullimage = data.NULL(data.AcquisitionImageData)
		if 'list' in kwargs:
			list = kwargs['list']
		else:
			list = None
		lastnumber = self.lastTargetNumber(grid=grid, list=list, image=nullimage, session=self.session)
		number = lastnumber + 1
		targetdata = self.newTarget(grid=grid, drow=drow, dcol=dcol, number=number, session=self.session, image=nullimage, **kwargs)
		return targetdata

	def newSimulatedTarget(self):
		lastnumber = self.lastTargetNumber(session=self.session, type='simulated')
		nextnumber = lastnumber + 1
		newtarget = self.newTarget(drow=None, dcol=None, number=nextnumber, type='simulated')
		return newtarget

	###########################################################


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


