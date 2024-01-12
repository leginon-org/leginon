#!/usr/bin/env python
from leginon import leginondata
from leginon import ptolemyhandler as ph
from pyami import simplelogger
import time
import sys

# values for testing
tem_hostname = 'leginon-docker'
test_tnumber = 1000

def getCurrentSession(hostname):
	q_inst = leginondata.InstrumentData(hostname=hostname)
	results = leginondata.ScopeEMData(tem=q_inst).query(results=1)
	if results:
		return results[0]['session']
	else:
		raise ValueError('no session using this tem host')

def getMosaicLabel(session,mosaic_name=None):
	'''
	return mosaic label. Maybe an empty label, or named label.
	it returns False if no match found.
	'''
	if mosaic_name is None:
		# set to use the most recent label
		r = leginondata.ImageTargetListData(session=session, mosaic=True).query(results=1)
		if not r:
			# handle image target list not found from bad workflow.
			return False
		mosaic_name = r[0]['label']
	return mosaic_name

class SquareTargetOrderUpdater(object):
	def __init__(self, sessiondata, logger, commit=True, test_tnumber=1000):
		self.session = sessiondata
		self.commit = commit
		self.test_tnumber = test_tnumber
		self.logger = logger
		self.mosaic_targetlist = None

	def saveScoreHistory(self, ptolemy_square, score):
		# next set number
		results=leginondata.PtolemyScoreHistoryData(session=self.session,square=ptolemy_square,list=self.mosaic_targetlist).query(results=1)
		if results:
			old_number = results[0]['set_number']
			if old_number == None:
				old_number = 0
			set_number= old_number+1
		else:
			set_number= 1
		# save score history on all blobs
		q=leginondata.PtolemyScoreHistoryData(session=self.session,square=ptolemy_square, list=self.mosaic_targetlist,score=score, set_number=set_number)
		if self.commit:
			q.insert(force=True)

	def updateOrder(self, is_first=False, mosaic_name=None):
		if not is_first:
			try:
				# update score from gaussian probability
				blob_dicts = ph.select_next_square()
			except:
				self.logger.error('failed to obtain active learned order to update')
				return
		else:
			# just order by current score first
			blob_dicts=ph.current_lm_state()
		mosaic_label = getMosaicLabel(self.session,mosaic_name)
		if mosaic_label == False:
			self.logger.error('no atlas target list with label "%s"' % mosaic_label)
			return
		ordering_scores = []
		target_numbers = []
		# specify which mosaic label is used.
		results=leginondata.ImageTargetListData(mosaic=True,label=mosaic_label,session=self.session).query()
		if not results:
			self.logger.error('no atlas target list with label "%s"' % mosaic_label)
			return
		self.mosaic_targetlist = results[0]
		desired_imagelists = leginondata.ImageListData(targets=self.mosaic_targetlist).query()
		desired_imagelists = list(map((lambda x:x.dbid), desired_imagelists))
		self.logger.debug('imagelist dbids of label "%s": %s' % (mosaic_label,desired_imagelists))
		blob_dicts = filter((lambda x: x['grid_id'] in desired_imagelists),blob_dicts)
		if len(blob_dicts) == 0:
				self.logger.error('Error mapping blobs to any atlas target list')
				return
		for n, b in enumerate(blob_dicts):
			#ptolemy write its coordinates in (x,y) modify them first. we want
			# them in (row, col)
			b['tile_image'] = leginondata.AcquisitionImageData().direct_query(b['image_id'])
			try:
				ptolemy_square = leginondata.PtolemySquareData(grid_id=b['grid_id'],tile_id=b['tile_id'], square_id=b['square_id']).query(results=1)[0]
			except:
				self.logger.error('Blob from ptolemy current_lm_state not saved previously')
				continue
			statslinks = leginondata.PtolemySquareStatsLinkData(ptolemy=ptolemy_square).query()
			if not statslinks:
				self.logger.error('bad ptolemy grid,tile,square ids=(%d,%d,%d) at dbid=%d' % (b['grid_id'],b['tile_id'],b['square_id'],ptolemy_square.dbid))
				continue
			targets = leginondata.AcquisitionImageTargetData(square=statslinks[0]['stats'],status='new').query()
			if not targets:
				continue
			t = targets[0]
			# This should be the same for all targets from blob_dicts
			square_targeting_targetlist=t['list']
			if square_targeting_targetlist['session'].dbid != self.session.dbid:
				raise ValueError('Error mapping blob to targets to the same session')
			# save score on all blobs
			self.saveScoreHistory(ptolemy_square, b['score'])
			# ordering targets with best score in target
			# ordering score on the target is from the ptolemy square with higher score.
			if t['number'] in target_numbers:
				# replace with higher score
				exist_index = target_numbers.index(t['number'])
				exist_score = ordering_scores[exist_index]
				if b['score'] > exist_score:
					ordering_scores[exist_index] = b['score']
					target_numbers[exist_index] = t['number']
			else:
				ordering_scores.append(b['score'])
				target_numbers.append(t['number'])
			if t['number']==self.test_tnumber:
				self.logger.warning('test target number %d: ptolemy_square_id %d, score %.5f' % (t['number'], b['square_id'],b['score']))

		indices = [index for value, index in sorted(((v, i) for i,v in enumerate(ordering_scores)), reverse=True)]
		target_order = list(map((lambda x: target_numbers[x]), indices))
		try:
			index_47=target_numbers.index(self.test_tnumber)
			score_47_orig = ordering_scores[index_47]
			order_47=target_order.index(self.test_tnumber)
			self.logger.warning('test target number %d is ordered at %d' % (self.test_tnumber, order_47))
		except ValueError:
			# self.test_tnumber not in range
			pass
		self.logger.debug(target_order)
		q = leginondata.TargetOrderData(session=self.session, list=square_targeting_targetlist,order=target_order)
		if self.commit:
			q.insert(force=True)
		self.logger.info('new target order saved')

if __name__=='__main__':
	sessiondata = getCurrentSession(tem_hostname)
	app = SquareTargetOrderUpdater(sessiondata, simplelogger.Logger(is_debug=True),False)
	app.updateOrder(True, None)
	wait_minutes = 5
	wait_time = wait_minutes*60
	print('Waiting for %d minutes to start' % wait_minutes)
	time.sleep(wait_time)
	while True:
		app.updateOrder(False, None)
		print('Waiting for %d minutes until next update' % wait_minutes)
		time.sleep(wait_time)
