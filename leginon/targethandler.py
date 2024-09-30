#!/usr/bin/env python
from leginon import leginondata
from leginon import event
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
		if hasattr(self.transformedtarget,'dbid'):
			dbidtext = '%d' % self.transformedtarget.dbid
		else:
			dbidtext = 'None'
		self.logger.info('got back a transformed target with id= %s' % dbidtext)
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

	def isPreviewOnly(self, targetlistdata):
		if not targetlistdata:
			return False
		all_new = leginondata.AcquisitionImageTargetData(status='new',list=targetlistdata).query()
		preview_new = leginondata.AcquisitionImageTargetData(type='preview',status='new',list=targetlistdata).query()
		# if there are new targets, and not all of them  are not preview targets
		return len(all_new) > 0 and len(all_new) == len(preview_new)

	def reportTargetListDone(self, targetlistdata, status):
		listid = targetlistdata.dbid
		self.logger.info('%s done with target list ID: %s, status: %s' % (self.name, listid, status))
		# send event so waiting stops.
		e = event.TargetListDoneEvent(targetlistid=listid, status=status, targetlist=targetlistdata)
		self.outputEvent(e)
		if self.isPreviewOnly(targetlistdata):
			# targetlist containing only preview needs to avoid being marked as done.
			return
		# DoneTargetList should not be inserted on targetlist originated from mosaic finders.
		# This is so that more targets can be submitted
		if targetlistdata['node']:
			if not targetlistdata['node']['class string'].startswith('Mosaic'):
				# TODO: using class string text to test is not a good idea. Need better solutions.
				self.insertDoneTargetList(targetlistdata)
			else:
				# but need to notify autodone for auto session.
				self.notifyAutoDone('full')

	def insertDoneTargetList(self, targetlistdata):
		if targetlistdata:
			if not (type(self.targetfinder_from)==type({}) and self.targetfinder_from['is_direct_bound']):
				return
		# only insert if the node is directly bound to the targetlistdata['node']
		# otherwise the Focus or Preview may call targetlist done before Exposure.
		# See Issue #10094
		# TODO: what if we do have a TargetFilter between Finder and Acquisition ?
		if targetlistdata and targetlistdata['node'] and self.targetfinder_from['node']['alias'] == targetlistdata['node']['alias']:
			q = leginondata.DoneImageTargetListData(session=self.session,list=targetlistdata)
			q.insert()
			self.logger.debug('targetlist %d is inserted as done' % (targetlistdata.dbid))
		else:
			self.logger.debug('targetlist %d is not insert as done' % (targetlistdata.dbid))
		return

	def researchTargets(self, **kwargs):
		'''
		This gives back all targets matching kwargs. They are sorted
		by list, number, version, status.
		'''
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
		tls = list(organized.keys())
		tls.sort()
		for targetlist in tls:
			numbers = list(organized[targetlist].keys())
			numbers.sort()
			for n in numbers:
				statuses = list(organized[targetlist][n]['targets'].keys())
				## take only most recent status in this order:
				for status in ('done', 'aborted', 'processing', 'new'):
					if status in organized[targetlist][n]['targets']:
						final.append(organized[targetlist][n]['targets'][status])
						break
		return final

	def startQueueProcessor(self):
		self.total_queue_left_in_loop = 0
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
			active = ordereddict.OrderedDict(list(zip(keys,targetlists)))
			keys = [dequeuedlist.special_getitem('list', dereference=False).dbid for dequeuedlist in dequeuedlists]
			done = ordereddict.OrderedDict(list(zip(keys,keys)))
			for id in done:
				try:
					del active[id]
				except:
					self.logger.warning('done %s list not in target list' % (id,))
			return list(active.values())
	
	def inDequeued(self,targetlist):
		dequeuedquery = leginondata.DequeuedImageTargetListData(list=targetlist)
		dequeuedlists = self.research(datainstance=dequeuedquery)
		if len(dequeuedlists) > 0:
			return True
		else:
			return False

	def inDoneTargetList(self,targetlist):
		listid = targetlist.dbid
		dequeuedquery = leginondata.DoneImageTargetListData(list=targetlist)
		dequeuedlists = self.research(datainstance=dequeuedquery)
		if len(dequeuedlists) > 0:
			self.logger.info('targetlist id %d in DoneTargetList' % listid)
			return True
		else:
			self.logger.info('targetlist id %d not in DoneTargetList' % listid)
			return False

	def queueIdleFinish(self):
		self.logger.warning('this idle timer is not used any more')

	def toggleQueueTimeout(self):
		self.logger.warning('this idle timer is not used any more')

	def postQueueCount(self, count):
		# implemented in TargetWatcher
		raise NotImplementedError()

	def queueProcessor(self):
		'''
		this is run in a thread to watch for and handle queue updates
		'''
		trials = 0
		while 1:
			# wait for a queue update
			self.setStatus('idle')
			
			## hard coded idletime before giving up
			if self.queueidleactive:
				idletime = 20
			else:
				idletime = None
			state = self.player.state()
			if state != 'stopqueue':
				# wait here for TargetFinder.publishQueue() to start processing
				self.queueupdate.wait(idletime)
				if not self.queueupdate.isSet():
					self.queueIdleFinish()
					# close valves, stop doing everything or quit
		
				self.setStatus('processing')
				self.queueupdate.clear()
				self.logger.info('received queue update')

			# abort if image number limit reached
			if self.settings['limit image']:
				if self.isAboveImageNumberLimit():
					self.logger.info('Image number limit reached. set active queue to 0')
					active = []
				else:
					active = self.getListsInQueue(self.getQueue())
			else:
				active = self.getListsInQueue(self.getQueue())
			self.logger.info('%d targetlists in queue' % len(active))
			self.postQueueCount(len(active))
			self.total_queue_left_in_loop = len(active)
			# process all target lists in the queue
			for targetlist in active:
				# abort if image number limit reached
				if self.settings['limit image']:
					if self.isAboveImageNumberLimit():
						self.logger.info('Image number limit reached. stop processing active')
						break
				state = self.clearBeamPath()
				if state == 'stopqueue' or self.inDequeued(targetlist) or self.inDoneTargetList(targetlist):
					self.logger.info('Queue aborted, skipping target list')
				else:
					# FIX ME: empty targetlist does not need to revert Z.
					try:
						self.revertTargetListZ(targetlist)
					except Exception as e:
						self.logger.error('Failed to revert targetlist z: %s' % (e,))
						break
					try:
						self.processTargetList(targetlist)
					except Exception as e:
						self.logger.error('Failed to process targetlist from queue: %s' % (e,))
						self.logger.error('Fix and repeat submitting queue for processing')
						break
					state = self.player.wait()
					if state != 'stopqueue':
						self.player.play()
				self.total_queue_left_in_loop -= 1
				self.postQueueCount(self.total_queue_left_in_loop)
				donetargetlist = leginondata.DequeuedImageTargetListData(session=self.session, list=targetlist, queue=self.targetlistqueue)
				self.publish(donetargetlist, database=True)
				if targetlist['image']:
					self.logger.info('dequeued targetlist from %s' % targetlist['image']['filename'])
				else:
					self.logger.info('dequeued targetlist id=%d without parent' % targetlist,dbid)
			if state == 'stopqueue':
				if len(active) == 0 or trials > 3:
					self.logger.info ('all targets in this active queue done. Releasing queue abort')
					self.player.play()
					trials = 0
				elif trials > 3:
					self.logger.warning('Keep finding more in queue. Releasing queue abort to avoid infinite loop')
					self.player.play()
					trials = 0
				else:
					trials += 1
					self.logger.info('check for queue one more time. since last # of active = %d' % len(active))
					continue
			else:
				self.player.play()
			end_state = self.player.state()
			if end_state != 'stopqueue' and len(active) == 0 and self.settings['reset tilt']:
				# FIX ME: reset tilt and xy at the end of queue.  This is different
				# from non-queue case. The current code resets each time active queue
				# runs out.
				self.resetTiltStage()

	def resetTiltStage(self):
		try:
			zerostage = {'a':0.0}
			self.instrument.tem.setStagePosition(zerostage)
			zerostage = {'x':0.0,'y':0.0}
			self.instrument.tem.setStagePosition(zerostage)
			stageposition = self.instrument.tem.getStagePosition()
			self.logger.info('return x,y, and alpha tilt to %.1f um,%.1f um,%.1f deg' % (stageposition['x']*1e6,stageposition['y'],stageposition['a']))
		except Exception as e:
			self.logger.error(e)
			self.logger.error('Failed reset to x,y,a of the stage: %s' %(e,))

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
		if self.this_node is None and image is not None:
			self.logger.error('Not in an application and therefore can not find node spec for targetlist from %s' % (image['filename']))
		listdata = leginondata.ImageTargetListData(session=self.session, label=label, mosaic=mosaic, image=image, queue=queuedata, sublist=sublist, node=self.this_node)
		return listdata

	def getQueue(self, label=None):
		'''
		This returns the QueueData for this session and label.
		self.targetlistqueue is set during this call
		'''
		if hasattr(self,'targetlistqueue'):
			# This is set to the Targeting node QueueData if the queue has been published there.
			return self.targetlistqueue
		if label is None:
			# This is wrong. Acquisition node name is not the label we want.
			# However, it has not caused problem, it seems.
			label = self.name
		queuequery = leginondata.QueueData(session=self.session, label=label)
		queues = self.research(datainstance=queuequery)
		if queues:
			self.targetlistqueue = queues[0]
		else:
			newqueue = leginondata.QueueData(session=self.session, label=label)
			self.publish(newqueue, database=True)
			self.logger.info('Made new queue with label %s' % label)
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
		except Exception as e:
			self.logger.error('getting scopedata failed: %s' % (e))
			raise
		self.targetlist_reset_tilt = scopedata['stage position']['a']
		self.targetlist_z = scopedata['stage position']['z']
		scopedata.friendly_update(preset)
		lastnumber = self.lastTargetNumber(session=self.session, type='simulated')
		nextnumber = lastnumber + 1
		# fix for #14305
		# all simulated targets from the same node will share the same targetlist
		simu_list = self.newTargetList()
		newtarget = self.newTarget(drow=0, dcol=0, number=nextnumber, type='simulated', scope=scopedata, preset=preset, grid=grid, list=simu_list)
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

	def getQueueTargetListToDo(self):
		'''
		Get unprocessed targetlist. This is used in Stop Queue MessageDialog.
		'''
		if not hasattr(self,'targetlistqueue') or self.targetlistqueue['label'] == self.name:
			# no queue is published to here yet after the node is created.
			return 0
		if not self.queueupdate.isSet() and self.total_queue_left_in_loop:
			# in the loop of processing active targetlists
			return self.total_queue_left_in_loop
		# not in the loop
		# include ones not sent to process but submitted.
		active = self.getListsInQueue(self.targetlistqueue)
		return len(active)

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
		except AttributeError as KeyError:
			pass
		if tlistid is None:
			eventdict = self.targetlistevents
		else:
			eventdict = {tlistid:self.targetlistevents[tlistid]}
		status = None
		for tid, teventinfo in list(eventdict.items()):
			self.logger.info('Waiting for target list ID %s...' % (tid,))
			teventinfo['received'].wait()
			status = teventinfo['status']
			self.logger.info('Target ID %s has been processed.  Status: %s' % (tid,status))
			del self.targetlistevents[tid]
		self.logger.info('%s done waiting' % (self.name,))
		## if waiting for more than one, only returns status of final one
		return status


if __name__ == '__main__':
	from leginon import node
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
	print('s', s)

	im = db.direct_query(leginondata.AcquisitionImageData, 49780)
	print('DONE DIRECT', im.dbid)
	tar = t.researchTargets(session=s, image=im)
	print('LEN', len(tar))
	print('DBID', tar[0].dbid)
	#print('TAR0', tar[0])
	print('IM REF', tar[0].special_getitem('image', dereference=False))

