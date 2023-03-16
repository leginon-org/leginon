#!/usr/bin/env python
from leginon import leginondata
from leginon import ptolemyhandler as ph
import time
import sys

tem_hostname = 'leginon-docker'
mosaic_name = None
commit = False
test_tnumber = 1000

def getCurrentSession(hostname):
	q_inst = leginondata.InstrumentData(hostname=hostname)
	results = leginondata.ScopeEMData(tem=q_inst).query(results=1)
	if results:
		return results[0]['session']
	else:
		raise ValueError('no session using this tem host')

def getMosaicLabel(session,mosaic_name=None):
	if mosaic_name is None:
		# set to use the most recent label
		r = leginondata.ImageTargetListData(session=session, mosaic=True).query(results=1)
		if not r:
			return
		mosaic_name = r[0]['label']
	return mosaic_name

def updateSquareTargetOrder(session, is_first=False, mosaic_name=None):
	if not is_first:
		# update score from gaussian probability
		blob_dicts = ph.select_next_square()
	else:
		# just order by current score first
		blob_dicts=ph.current_lm_state()
	mosaic_label = getMosaicLabel(session,mosaic_name)
	scores = []
	target_numbers = []
	# specify which mosaic label is used.
	desired_imagelists = leginondata.ImageListData(targets=leginondata.ImageTargetListData(mosaic=True,label=mosaic_label,session=session)).query()
	desired_imagelists = list(map((lambda x:x.dbid), desired_imagelists))
	print('imagelist dbids of label "%s": %s' % (mosaic_label,desired_imagelists))
	blob_dicts = filter((lambda x: x['grid_id'] in desired_imagelists),blob_dicts)
	for n, b in enumerate(blob_dicts):
		#ptolemy write its coordinates in (x,y) modify them first. we want
		# them in (row, col)
		b['tile_image'] = leginondata.AcquisitionImageData().direct_query(b['image_id'])
		try:
			ptolemy_square = leginondata.PtolemySquareData(grid_id=b['grid_id'],tile_id=b['tile_id'], square_id=b['square_id']).query(results=1)[0]
		except:
			print('Error: Blob from ptolemy current_lm_state not saved previously')
			continue
		statslinks = leginondata.PtolemySquareStatsLinkData(ptolemy=ptolemy_square).query()
		if not statslinks:
			print('bad ptolemy grid,tile,square ids=(%d,%d,%d) at dbid=%d' % (b['grid_id'],b['tile_id'],b['square_id'],ptolemy_square.dbid))
			continue
		targets = leginondata.AcquisitionImageTargetData(square=statslinks[0]['stats'],status='new').query()
		if not targets:
			continue
		t = targets[0]
		# This should be the same for all targets from blob_dicts
		square_targeting_targetlist=t['list']
		# TODO: Is this still needed ?
		if t['session'].dbid == session.dbid:
			if t['number'] in target_numbers:
				# replace with higher score
				exist_index = target_numbers.index(t['number'])
				exist_score = scores[exist_index]
				if b['score'] > exist_score:
					scores[exist_index] = b['score']
					target_numbers[exist_index] = t['number']
			else:
				scores.append(b['score'])
				target_numbers.append(t['number'])
			if t['number']==test_tnumber:
				print('test target number %d: ptolemy_square_id %d, score %.5f' % (t['number'], b['square_id'],b['score']))
			# next set number
			results=leginondata.PtolemyScoreHistoryData(session=session,square=ptolemy_square).query(results=1)
			if results:
				old_number = results[0]['set_number']
				if old_number == None:
					old_number = 0
				set_number= old_number+1
			else:
				set_number= 1
			# save score history on all blobs
			q=leginondata.PtolemyScoreHistoryData(session=session,square=ptolemy_square, score=b['score'], set_number=set_number)
			if commit:
				q.insert(force=True)
		else:
			print('Error: target %d is in grid atlas %d and session %s, not current one' % (t.dbid,b['grid_id'], t['session']['name']))

	indices = [index for value, index in sorted(((v, i) for i,v in enumerate(scores)), reverse=True)]
	target_order = list(map((lambda x: target_numbers[x]), indices))
	try:
		index_47=target_numbers.index(test_tnumber)
		score_47_orig = scores[index_47]
		order_47=target_order.index(test_tnumber)
		print('test target number %d is ordered at %d' % (test_tnumber, order_47))
	except:
		pass
	print(target_order)
	q = leginondata.TargetOrderData(session=session, list=square_targeting_targetlist,order=target_order)
	if commit:
		q.insert(force=True)

sessiondata = getCurrentSession(tem_hostname)
updateSquareTargetOrder(sessiondata, True, mosaic_name)
wait_minutes = 5
wait_time = wait_minutes*60
print('Waiting for %d minutes to start' % wait_minutes)
time.sleep(wait_time)
while True:
	updateSquareTargetOrder(sessiondata, False, mosaic_name)
	print('Waiting for %d minutes until next update' % wait_minutes)
	time.sleep(wait_time)
