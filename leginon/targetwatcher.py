#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import event, data
import watcher
import threading
import targethandler
import node
import player
import newdict

class TargetWatcher(watcher.Watcher, targethandler.TargetHandler):
	'''
	TargetWatcher will watch for TargetLists
	It is also initialized with a specific type of target that it can
	process.  All other targets are republished in another target list.
	'''

	eventinputs = watcher.Watcher.eventinputs + targethandler.TargetHandler.eventinputs + [event.TargetListDoneEvent,
																						event.ImageTargetListPublishEvent,
																						event.AcquisitionImageDriftPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + targethandler.TargetHandler.eventoutputs + [event.TargetListDoneEvent, event.NeedTargetShiftEvent]

	def __init__(self, id, session, managerlocation, target_types=('acquisition',),
								**kwargs):
		watchfor = [event.ImageTargetListPublishEvent, event.QueuePublishEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor,
															**kwargs)

		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.addEventInput(event.AcquisitionImageDriftPublishEvent,
												self.handleImageDrift)

		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		self.received_image_drift = threading.Event()
		self.requested_drift = None
		self.target_types = target_types
		self.targetlistevents = {}
		self.queueupdate = threading.Event()
		self.startQueueProcessor()

	def startQueueProcessor(self):
		t = threading.Thread(target=self.queueProcessor)
		t.setDaemon(True)
		t.start()

	def queueProcessor(self):
		'''
		this is run in a thread to watch for and handle queue updates
		'''
		while 1:
			# wait for a queue update
			self.queueupdate.wait()
			self.queueupdate.clear()
			self.logger.info('received queue update')

			# get targetlists relating to this queue
			tarlistquery = data.ImageTargetListData(queue=self.targetlistqueue)
			targetlists = self.research(datainstance=tarlistquery)
			# need FIFO queue (query returns LIFO)
			targetlists.reverse()
			self.logger.info('%s target lists' % (len(targetlists),))
			dequeuedquery = data.DequeuedImageTargetListData(queue=self.targetlistqueue)
			dequeuedlists = self.research(datainstance=dequeuedquery)
			self.logger.info('%s target lists done' % (len(dequeuedlists),))

			## these dicts make it easier to figure out which lists are done
			keys = [targetlist.dbid for targetlist in targetlists]
			active = newdict.OrderedDict(zip(keys,targetlists))
			keys = [dequeuedlist.special_getitem('list', dereference=False).dbid for dequeuedlist in dequeuedlists]
			done = newdict.OrderedDict(zip(keys,keys))

			# process all target lists in the queue
			for dbid, targetlist in active.items():
				if dbid in done:
					continue
				self.processTargetList(targetlist)
				donetargetlist = data.DequeuedImageTargetListData(list=targetlist, queue=self.targetlistqueue)
				self.publish(donetargetlist, database=True)

	def handleImageDrift(self, ev):
		self.logger.debug('HANDLING IMAGE DRIFT')
		driftdata = ev['data']
		imageid = driftdata.special_getitem('image', dereference=False).dbid
		## only continue if this was one that I requested
		if imageid == self.requested_drift:
			self.requested_drift = driftdata
			self.received_image_drift.set()

	def processData(self, newdata):
		if isinstance(newdata, data.ImageTargetListData):
			self.processTargetList(newdata)
		if isinstance(newdata, data.QueueData):
			self.processTargetListQueue(newdata)

	def processTargetListQueue(self, newdata):
		self.targetlistqueue = newdata
		self.queueupdate.set()

	def adjustTargetForDrift(self, originaltarget, adjustedtarget):
		if originaltarget['image'] is None:
			return adjustedtarget
		## check if drift has occurred since target's parent image was acquired
		# hack to be sure image data is not read, since it's not needed
		imageref = originaltarget.special_getitem('image', dereference=False)
		imageid = imageref.dbid
		imagedata = self.researchDBID(data.AcquisitionImageData, imageid, readimages=False)
		# image time
		imagetime = imagedata['scope']['system time']
		# last declared drift
		lastdeclared = self.research(data.DriftDeclaredData(), results=1)
		if not lastdrift:
			## no drift declared, no adjustment needed
			return adjustedtarget
		# last declared drift time
		lastdeclared = lastdeclared[0]
		lastdeclaredtime = lastdeclared['system time']
		# has drift occurred?
		if imagetime < lastdeclaredtime:
			# yes, now we need a recent image drift for this image
			query = data.AcquisitionImageDriftData()
			query['image'] = imagedata
			imagedrift = self.research(query, results=1)
			# was image drift already measured for this image?
			if not imagedrift:
				# no, request measurement now
				imagedrift = self.requestImageDrift(imagedata)
			else:
				# yes, but was it measured after declared drift?
				imagedrift = imagedrift[0]
				if imagedrift['system time'] < lasdeclaredtime:
					# too old, need to measure it again
					imagedrift = self.requestImageDrift(imagedata)

			## create new adjusted target from old adjusted target and original target
			adjustedtarget = data.AcquisitionImageTargetData(initializer=adjustedtarget)
			adjustedtarget['version'] += 1
			adjustedtarget['delta row'] = originaltarget['delta row'] + imagedrift['rows']
			adjustedtarget['delta column'] = originaltarget['delta column'] + imagedrift['columns']
			self.publish(adjustedtarget, database=True, dbforce=True)
		return adjustedtarget

	def requestImageDrift(self, imagedata):
		# need to have drift manager do it
		self.received_image_drift.clear()
		ev = event.NeedTargetShiftEvent(image=imagedata)
		imageid = imagedata.dbid
		## set requested_drift to the reply can be recognized
		self.requested_drift = imageid
		self.logger.debug('Sending NeedTargetShiftEvent and waiting, imageid = %s' % (imageid,))
		self.outputEvent(ev)
		self.setStatus('waiting')
		self.received_image_drift.wait()
		self.setStatus('processing')
		self.logger.debug('Done waiting for NeedTargetShiftEvent')
		return self.requested_drift

	def processTargetList(self, newdata):
		self.setStatus('processing')

		### get targets that belong to this target list
		targetlist = self.researchTargets(list=newdata)
		listid = newdata.dbid
		self.logger.debug('TargetWatcher will process %s targets in list %s' % (len(targetlist), listid))

		# separate the good targets from the rejects
		goodtargets = []
		rejects = []

		for target in targetlist:
			im = target['image']
			if im is not None:
				imageid = target['image'].dbid
			else:
				imageid = None
			self.logger.debug('IMAGEID ' + str(imageid))
			if target['type'] in self.target_types:
				goodtargets.append(target)
			else:
				rejects.append(target)

		self.logger.debug('%d process, %d pass, %d total' % (len(goodtargets), len(rejects), len(targetlist)))

		# republish the rejects and wait for them to complete
		waitrejects = rejects and self.settings['wait for rejects']
		if waitrejects:
			rejectstatus = self.rejectTargets(rejects)
			if rejectstatus != 'success':
				## report my status as reject status
				## may not be a good idea all the time
				## This means if rejects were aborted
				## then this whole target list was aborted
				self.logger.warning('Passed targets not processed, aborting current target list')
				self.reportTargetListDone(newdata.dmid, rejectstatus)
				self.setStatus('idle')
				return

			self.logger.info('Passed targets processed, processing current target list')

		# process the good ones
		targetliststatus = 'success'
		for i, target in enumerate(goodtargets):
			self.logger.debug('target %s status %s' % (i, target['status'],))
			# ...
			if self.player.state() == 'pause':
				self.setStatus('user input')
			state = self.player.wait()
			self.setStatus('processing')
			# abort
			if state == 'stop':
				self.logger.info('Aborting current target list')
				targetliststatus = 'aborted'
				donetarget = data.AcquisitionImageTargetData(initializer=target, status='aborted')
				self.publish(donetarget, database=True)
				## continue so that remaining targets are marked as done also
				continue

			# if this target is done, skip it
			if target['status'] in ('done', 'aborted'):
				self.logger.info('Target has been done, processing next target')
				continue

			### generate a focus target
			if self.settings['duplicate targets']:
				focustarget = data.AcquisitionImageTargetData(initializer=target)
				focustarget['type'] = self.settings['duplicate target type']
				self.publish(focustarget, database=True)
				tlist = [focustarget]
				self.rejectTargets(tlist)

			self.logger.debug('Creating processing target...')
			adjustedtarget = data.AcquisitionImageTargetData(initializer=target,
																												status='processing')
			self.logger.debug('Publishing processing target...')
			self.publish(adjustedtarget, database=True)
			self.logger.debug('Processing target published')

			# this while loop allows target to repeat
			process_status = 'repeat'
			attempt = 0
			while process_status == 'repeat':
				attempt += 1

				adjustedtarget = self.adjustTargetForDrift(target, adjustedtarget)

				# now have processTargetData work on it
				try:
					process_status = self.processTargetData(adjustedtarget, attempt=attempt)
				except node.PublishError, e:
					self.player.pause()
					self.logger.exception('Saving image failed: %s' % e)
					process_status = 'repeat'
				except Exception, e:
					self.logger.exception('Process target failed: %s' % e)
					process_status = 'exception'

				# pause
				# ...
				if self.player.state() == 'pause':
					self.setStatus('user input')
				state = self.player.wait()
				self.setStatus('processing')
				if state == 'stop':
					self.logger.info('Aborted')
					break

				# end of target repeat loop

			self.logger.debug('Creating done target...')
			donetarget = data.AcquisitionImageTargetData(initializer=adjustedtarget,
																										status='done')
			#self.publish(donetarget, database=True, dbforce=True)
			## Why force???
			self.logger.debug('Publishing done target...')
			self.publish(donetarget, database=True)
			self.logger.debug('Done target published')

		self.player.play()
		self.reportTargetListDone(newdata.dmid, targetliststatus)
		self.setStatus('idle')

	def reportTargetListDone(self, listid, status):
		self.logger.info('%s done with target list ID: %s, status: %s' % (self.name, listid, status))
		e = event.TargetListDoneEvent(targetlistid=listid, status=status)
		self.outputEvent(e)

	def waitForRejects(self):
		# wait for focus target list to complete
		for tid, teventinfo in self.targetlistevents.items():
			teventinfo['received'].wait()

		## check status of all target lists
		## all statuses must be success in order for complete success
		status = 'success'
		for tid, teventinfo in self.targetlistevents.items():
			if teventinfo['status'] in ('failed', 'aborted'):
				status = teventinfo['status']
				break
		self.targetlistevents.clear()
		
		return status

	def rejectTargets(self, targets):
		self.logger.info('Publishing reject targets')
		rejectlist = self.newTargetList()
		self.publish(rejectlist, database=True, dbforce=True)
		for target in targets:
			reject = data.AcquisitionImageTargetData(initializer=target)
			reject['list'] = rejectlist
			self.publish(reject, database=True)
		tlistid = rejectlist.dmid
		self.targetlistevents[tlistid] = {}
		self.targetlistevents[tlistid]['received'] = threading.Event()
		self.targetlistevents[tlistid]['status'] = 'waiting'
		self.publish(rejectlist, pubevent=True)
		self.logger.info('Waiting for reject targets to be processed...')
		self.setStatus('waiting')
		rejectstatus = self.waitForRejects()
		self.setStatus('processing')
		return rejectstatus

	def handleTargetListDone(self, targetlistdoneevent):
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def processTargetData(self, targetdata):
		raise NotImplementedError()

	def abortTargetListLoop(self):
		self.player.stop()

	def pauseTargetListLoop(self):
		self.player.pause()

	def continueTargetListLoop(self):
		self.player.play()

	def onPlayer(self, state):
		infostr = ''
		if state == 'play':
			infostr += 'Continuing...'
		elif state == 'pause':
			infostr += 'Pausing...'
		elif state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)
		self.panel.playerEvent(state)

