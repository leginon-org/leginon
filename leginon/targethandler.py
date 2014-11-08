#!/usr/bin/env python
from leginon import leginondata
import event
import threading
from pyami import ordereddict
import sys

target_types = ('acquisition', 'focus', 'preview', 'meter')

class TargetHandler(object):
	'''
	nodes should inherit this if they want to work with targets
	'''
	############# DATABASE INTERACTION #################

	eventinputs = [event.QueuePublishEvent, event.TransformTargetDoneEvent]
	eventoutputs = [event.ImageTargetListPublishEvent, event.QueuePublishEvent, event.TransformTargetEvent]

	def __init__(self):
		self.queueupdate = threading.Event()
		self.addEventInput(event.TransformTargetDoneEvent, self.handleTransformTargetDoneEvent)
		self.transformtargetevent = threading.Event()
		self.queueidleactive = False

	def handleTransformTargetDoneEvent(self, evt):
		self.transformedtarget = evt['target']
		self.logger.info('got back a transformed target')
		self.transformtargetevent.set()

	def requestTransformTarget(self, targetdata):
		evt = event.TransformTargetEvent()
		evt['target'] = targetdata
		evt['level'] = self.settings['adjust for transform']
		evt['use parent mover'] = self.settings['use parent mover']
		self.transformtargetevent.clear()
		self.logger.info('requesting transformed target')
		self.outputEvent(evt)
		self.transformtargetevent.wait()
		return self.transformedtarget

	def transpose_points(self, points):
		newpoints = []
		for point in points:
			newpoints.append((point[1],point[0]))
		return newpoints

	def compareTargetNumber(self, first, second):
		return cmp(first['number'], second['number'])

	def reportTargetListDone(self, targetlistdata, status):
		listid = targetlistdata.dbid
		self.logger.info('%s done with target list ID: %s, status: %s' % (self.name, listid, status))
		e = event.TargetListDoneEvent(targetlistid=listid, status=status, targetlist=targetlistdata)
		self.outputEvent(e)

	def researchTargets(self, **kwargs):
		targetquery = leginondata.AcquisitionImageTargetData(**kwargs)
		targets = targetquery.query()
		# organize by list, number, version, status
		organized = {}
		for target in targets:
			if target['list'] is None:
				targetlist = None
			else:
				targetlist = target['list'].dbid
			if targetlist not in organized:
				organized[targetlist] = {}

			number = target['number']
			version = target['version']
			status = target['status']

			if number not in organized[targetlist]:
				organized[targetlist][number] = {'version': 0, 'targets': {}}

			recentversion = organized[targetlist][number]['version']

			if version > recentversion:
				organized[targetlist][number]['version'] = version
				organized[targetlist][number]['targets'] = {status: target}
			elif version == recentversion:
				organized[targetlist][number]['targets'][status] = target

		final = []
		tls = organized.keys()
		tls.sort()
		for targetlist in tls:
			numbers = organized[targetlist].keys()
			numbers.sort()
			for number in numbers:
				statuses = organized[targetlist][number]['targets'].keys()
				## take only most recent status in this order:
				for status in ('done', 'aborted', 'processing', 'new'):
					if status in organized[targetlist][number]['targets']:
						final.append(organized[targetlist][number]['targets'][status])
						break
		return final

	def startQueueProcessor(self):
		t = threading.Thread(target=self.queueProcessor)
		t.setDaemon(True)
		t.start()

	def getListsInQueue(self, queuedata):
			'''
			get a list of all active (not done) target lists in the queue
			'''
			if queuedata is None:
				return []
			# get targetlists relating to this queue
			tarlistquery = leginondata.ImageTargetListData(queue=queuedata)
			targetlists = self.research(datainstance=tarlistquery)
			# need FIFO queue (query returns LIFO)
			targetlists.reverse()
			dequeuedquery = leginondata.DequeuedImageTargetListData(queue=queuedata)
			dequeuedlists = self.research(datainstance=dequeuedquery)
			keys = [targetlist.dbid for targetlist in targetlists]
			active = ordereddict.OrderedDict(zip(keys,targetlists))
			keys = [dequeuedlist.special_getitem('list', dereference=False).dbid for dequeuedlist in dequeuedlists]
			done = ordereddict.OrderedDict(zip(keys,keys))
			for id in done:
				try:
					del active[id]
				except:
					self.logger.warning('done %s list not in target list' % (id,))
			return active.values()
	
	def inDequeued(self,targetlist):
		dequeuedquery = leginondata.DequeuedImageTargetListData(list=targetlist)
		dequeuedlists = self.research(datainstance=dequeuedquery)
		if len(dequeuedlists) > 0:
			return True
		else:
			return False

	def queueIdleFinish(self):
		if not self.queueidleactive:
			return
		self.instrument.tem.ColumnValvePosition = 'closed'
		print 'column valves closed and exiting leginon'
		self.logger.warning('column valves closed')
		if self.settings['emission off']:
			self.instrument.tem.Emission = False
			self.logger.warning('emission switched off')
		self.queueidleactive = False

	def toggleQueueTimeout(self):
		if self.queueidleactive:
			self.queueidleactive = False
			self.logger.info('Queue timeout deactivated')
		else:
			self.queueidleactive = True
			self.queueupdate.set()
			self.logger.info('Queue timeout activated')

	def queueProcessor(self):
		'''
		this is run in a thread to watch for and handle queue updates
		'''
		while 1:
			# wait for a queue update
			self.setStatus('idle')
			
			## hard coded idletime before giving up
			if self.queueidleactive:
				idletime = 20
			else:
				idletime = None
			self.queueupdate.wait(idletime)
			if not self.queueupdate.isSet():
				self.queueIdleFinish()
				# close valves, stop doing everything or quit
		
			self.setStatus('processing')
			self.queueupdate.clear()
			self.logger.info('received queue update')

			active = self.getListsInQueue(self.getQueue())

			# process all target lists in the queue
			for targetlist in active:
				state = self.clearBeamPath()
				if state == 'stopqueue' or self.inDequeued(targetlist):
					self.logger.info('Queue aborted, skipping target list')
				else:
					self.revertTargetListZ(targetlist)
					self.processTargetList(targetlist)
					state = self.player.wait()
					if state != 'stopqueue':
						self.player.play()
				donetargetlist = leginondata.DequeuedImageTargetListData(session=self.session, list=targetlist, queue=self.targetlistqueue)
				self.publish(donetargetlist, database=True)
			self.player.play()
			if self.settings['reset tilt']:
				self.resetTiltStage()

	def resetTiltStage(self):
		zerostage = {'a':0.0}
		self.instrument.tem.setStagePosition(zerostage)
		zerostage = {'x':0.0,'y':0.0}
		self.instrument.tem.setStagePosition(zerostage)
		stageposition = self.instrument.tem.getStagePosition()
		self.logger.info('return x,y, and alpha tilt to %.1f um,%.1f um,%.1f deg' % (stageposition['x']*1e6,stageposition['y'],stageposition['a']))

	def queueStatus(self, queuedata):
		active = self.getListsInQueue(queuedata)
		# get info on each target list

	def researchTargetLists(self, **kwargs):
		targetlist = leginondata.ImageTargetListData(session=self.session, **kwargs)
		targetlists = self.research(datainstance=targetlist)
		return targetlists

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

	def newTargetList(self, label='', mosaic=False, image=None, queue=False, sublist=False):
		'''
		label will be included in filenames
		mosaic is boolean to indicate list of targets will
		generate a mosaic
		'''
		if queue:
			queuedata = self.getQueue()
		else:
			queuedata = None
		listdata = leginondata.ImageTargetListData(session=self.session, label=label, mosaic=mosaic, image=image, queue=queuedata, sublist=sublist)
		return listdata

	def getQueue(self, label=None):
		if hasattr(self,'targetlistqueue'):
			return self.targetlistqueue
		if label is None:
			label = self.name
		queuequery = leginondata.QueueData(session=self.session, label=label)
		queues = self.research(datainstance=queuequery)
		if queues:
			self.targetlistqueue = queues[0]
		else:
			newqueue = leginondata.QueueData(session=self.session, label=label)
			self.publish(newqueue, database=True)
			self.targetlistqueue = newqueue
		return self.targetlistqueue

	def newReferenceTarget(self, image_data, drow, dcol):
		target_data = leginondata.ReferenceTargetData()
		target_data['image'] = image_data
		target_data['scope'] = image_data['scope']
		target_data['camera'] = image_data['camera']
		target_data['preset'] = image_data['preset']
		target_data['grid'] = image_data['grid']
		target_data['delta row'] = drow
		target_data['delta column'] = dcol
		target_data['session'] = self.session
		return target_data

	def newTarget(self, drow, dcol, **kwargs):
		'''
		create new AcquistionImageTargetData and fill in all fields
		'''
		targetdata = leginondata.AcquisitionImageTargetData(initializer=kwargs)
		targetdata['delta row'] = drow
		targetdata['delta column'] = dcol
		if 'session' not in kwargs:
			targetdata['session'] = self.session
		if 'version' not in kwargs:
			targetdata['version'] = 0
		if 'status' not in kwargs:
			targetdata['status'] = 'new'
		return targetdata

	def newTargetForTile(self, imagedata, drow, dcol, **kwargs):
		return self.newTargetForImage(imagedata, drow, dcol, fortile=True, **kwargs)

	def newTargetForImage(self, imagedata, drow, dcol, fortile=False, **kwargs):
		'''
		returns a new target data object with data filled in from the image data
		'''
		if 'grid' in imagedata and imagedata['grid'] is not None:
			grid = imagedata['grid']
		else:
			grid = None

		## get next number if not already specified
		if 'number' not in kwargs or kwargs['number'] is None:
			## If image is a mosaic tile, then target number should be global for
			## the entire mosaic to be sure they are in the same order chosen
			if fortile:
				lastnumber = self.lastTargetNumberOnMosaic(imagedata['list'])
			else:
				lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
			kwargs['number'] = lastnumber + 1

		targetdata = self.newTarget(image=imagedata, scope=imagedata['scope'], camera=imagedata['camera'], preset=imagedata['preset'], drow=drow, dcol=dcol, session=self.session, grid=grid, **kwargs)
		return targetdata

	def lastTargetNumberOnMosaic(self, imagelist):
		qimagedata = leginondata.AcquisitionImageData()
		qimagedata['list'] = imagelist
		targetquery = leginondata.AcquisitionImageTargetData(image=qimagedata, status='new')
		targets = self.research(datainstance=targetquery, results=1)
		if targets:
			for target in targets:
				if target['number'] is not None:
					return target['number']
		return 0

	def newTargetForGrid(self, grid, drow, dcol, **kwargs):
		'''
		generate a new target associated with a grid, but not an image
		'''
		if 'list' in kwargs:
			list = kwargs['list']
		else:
			list = None
		lastnumber = self.lastTargetNumber(grid=grid, list=list, image=None, session=self.session)
		number = lastnumber + 1
		targetdata = self.newTarget(grid=grid, drow=drow, dcol=dcol, number=number, session=self.session, image=None, **kwargs)
		return targetdata

	def newSimulatedTarget(self, preset=None,grid=None):
		## current state of TEM, but use preset
		try:
			scopedata = self.instrument.getData(leginondata.ScopeEMData)
		except Exception, e:
			self.logger.error('getting scopedata failed: %s' % (e))
			raise
		scopedata.friendly_update(preset)
		lastnumber = self.lastTargetNumber(session=self.session, type='simulated')
		nextnumber = lastnumber + 1
		newtarget = self.newTarget(drow=0, dcol=0, number=nextnumber, type='simulated', scope=scopedata, preset=preset, grid=grid)
		return newtarget

	def getReferenceTarget(self):
		target_data = leginondata.ReferenceTargetData()
		target_data['session'] = self.session
		try:
			return self.research(target_data, results=1)[-1]
		except IndexError:
			return None

	def reportTargetStatus(self, target, status):
		# look up most recent version of this target
		tquery = leginondata.AcquisitionImageTargetData()
		tquery['session'] = target['session']
		tquery['list'] = target['list']
		tquery['number'] = target['number']
		tquery['type'] = target['type']
		mostrecent = tquery.query(results=1)
		if mostrecent:
			mostrecent = mostrecent[0]
		else:
			mostrecent = target

		newtarget = leginondata.AcquisitionImageTargetData(initializer=mostrecent, status=status)
		newtarget.insert(force=True)
		self.logger.debug('target stored in DB: %s, %s' % (newtarget.dbid, status))
		return newtarget

	def markTargetsDone(self, targets):
		for target in targets:
			self.reportTargetStatus(target, 'done')

	def clearBeamPath(self):
		'''
		Check column valve and any other obstacles for the beam
		to reach the camera.Simply pass player state here.
		'''
		return self.player.state()

class TargetWaitHandler(TargetHandler):
	eventinputs = TargetHandler.eventinputs + [event.TargetListDoneEvent]
	def __init__(self):
		self.targetlistevents = {}
		TargetHandler.__init__(self)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)

	def handleTargetListDone(self, targetlistdoneevent):
		'''
		Receives a target list done event and sets the threading event.
		'''
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		self.logger.debug('Got target list done event, setting threading event %s'
											% (targetlistid,))
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def makeTargetListEvent(self, targetlistdata):
		'''
		Creates a threading event to be waited on for target list leginondata.
		'''
		tlistid = targetlistdata.dbid
		self.targetlistevents[tlistid] = {}
		self.targetlistevents[tlistid]['received'] = threading.Event()
		self.targetlistevents[tlistid]['status'] = 'waiting'
		return tlistid

	def waitForTargetListDone(self, tlistid=None):
		'''
		Waits until theading events of specified target list or all target lists are cleared.
		'''
		try:
			if 'queue' in self.settings and self.settings['queue']:
				return
		except AttributeError, KeyError:
			pass
		if tlistid is None:
			eventdict = self.targetlistevents
		else:
			eventdict = {tlistid:self.targetlistevents[tlistid]}
		status = None
		for tid, teventinfo in eventdict.items():
			self.logger.info('Waiting for target list ID %s...' % (tid,))
			teventinfo['received'].wait()
			status = teventinfo['status']
			self.logger.info('Target ID %s has been processed.  Status: %s' % (tid,status))
			del self.targetlistevents[tid]
		self.logger.info('%s done waiting' % (self.name,))
		## if waiting for more than one, only returns status of final one
		return status


if __name__ == '__main__':
	import node
	import sinedon

	class TestNode(node.Node, TargetHandler):
		pass
		def __init__(self, id, session=None, managerlocation=None):
			node.Node.__init__(self, id, session, managerlocation)

	db = sinedon.getConnection('leginondata')
	t = TestNode('testnode')

	s = leginondata.SessionData(name='04may26a')
	s = db.query(s, results=1)
	s = s[0]
	print 's', s

	im = db.direct_query(leginondata.AcquisitionImageData, 49780)
	print 'DONE DIRECT', im.dbid
	tar = t.researchTargets(session=s, image=im)
	print 'LEN', len(tar)
	print 'DBID', tar[0].dbid
	#print 'TAR0', tar[0]
	print 'IM REF', tar[0].special_getitem('image', dereference=False)

