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
		targetdata['delta column'] = dcol
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
		lastnumber = self.lastTargetNumber(image=image, list=list, session=self.session)
		number = lastnumber + 1
		targetdata = self.newTarget(image=image, scope=image['scope'], camera=image['camera'], preset=image['preset'], drow=drow, dcol=dcol, number=number, session=self.session, **kwargs)
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
		targetdata = self.newTarget(grid=grid, drow=drow, dcol=dcol, number=number, session=self.session, **kwargs)
		return targetdata

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


