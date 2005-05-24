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
																						event.ImageTargetListPublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + targethandler.TargetHandler.eventoutputs + [event.TargetListDoneEvent]

	def __init__(self, id, session, managerlocation, target_types=('acquisition',),
								**kwargs):
		watchfor = [event.ImageTargetListPublishEvent, event.QueuePublishEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor,
															**kwargs)

		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)

		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
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
			self.setStatus('idle')
			self.queueupdate.wait()
			self.setStatus('processing')
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
				state = self.player.wait()
				if state == 'stopqueue':
					self.logger.info('Queue aborted, skipping target list')
				else:
					self.revertTargetListZ(targetlist)
					self.processTargetList(targetlist)
					state = self.player.wait()
					if state == 'stopqueue':
						continue
					else:
						self.player.play()
				donetargetlist = data.DequeuedImageTargetListData(list=targetlist, queue=self.targetlistqueue)
				self.publish(donetargetlist, database=True)
			self.player.play()

	def processData(self, newdata):
		if isinstance(newdata, data.ImageTargetListData):
			self.setStatus('processing')
			self.processTargetList(newdata)
			self.player.play()
			self.setStatus('idle')
		if isinstance(newdata, data.QueueData):
			self.processTargetListQueue(newdata)

	def processTargetListQueue(self, newdata):
		self.targetlistqueue = newdata
		self.queueupdate.set()

	def revertTargetListZ(self, targetlistdata):
		'''use the z position of the target list parent image'''
		imageref = targetlistdata.special_getitem('image', dereference=False)
		imageid = imageref.dbid
		imagedata = self.researchDBID(data.AcquisitionImageData, imageid, readimages=False)
		scope = imagedata['scope']
		z = scope['stage position']['z']
		tem = scope['tem']
		filename = imagedata['filename']
		self.logger.info('returning %s to z=%.4e of parent image %s' % (tem['name'], z, filename,))
		self.instrument.setTEM(tem['name'])
		self.instrument.tem.StagePosition = {'z': z}
		self.logger.info('z change done')

	def processTargetList(self, newdata):
		self.setStatus('processing')

		### get targets that belong to this target list
		targetlist = self.researchTargets(list=newdata)
		listid = newdata.dbid
		self.logger.debug('TargetWatcher will process %s targets in list %s' % (len(targetlist), listid))

		# separate the good targets from the rejects
		goodtargets = []
		rejects = []
		ignored = []

		for target in targetlist:
			im = target['image']
			if im is not None:
				imageid = target['image'].dbid
			else:
				imageid = None
			self.logger.debug('IMAGEID ' + str(imageid))
			if target['type'] in self.target_types:
				goodtargets.append(target)
			elif not rejects:
				## this only allows one reject
				rejects.append(target)
			else:
				ignored.append(target)

		self.logger.debug('%d process, %d pass, %d ignored, %d total' % (len(goodtargets), len(rejects), len(ignored), len(targetlist)))

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
			if state in ('stop', 'stopqueue'):
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
				if state in ('stop', 'stopqueue'):
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
		if targets:
			parentimage = targets[0]['image']
		else:
			parentimage = None
		rejectlist = self.newTargetList(image=parentimage)
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

