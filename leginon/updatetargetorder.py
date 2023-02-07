#!/usr/bin/env python
from leginon import leginondata
from leginon import ptolemyhandler as ph
import time

ctf= 3.0
tem_hostname='leginon-docker'

def getCurrentSession(hostname):
	q_inst = leginondata.InstrumentData(hostname=hostname)
	results = leginondata.ScopeEMData(tem=q_inst).query(results=1)
	if results:
		return results[0]['session']
	else:
		raise ValueError('no session using this tem host')

def updateSquareTargetOrder(session):
	print session
	blob_dicts = ph.current_lm_state()
	scores = []
	target_numbers = []
	if blob_dicts:
		current_grid_id = blob_dicts[-1]['grid_id']
		atlas_targetlist = leginondata.ImageListData().direct_query(current_grid_id)['targets']
		print current_grid_id, atlas_targetlist.dbid
		if atlas_targetlist['session'].dbid != session.dbid:
			raise ValueError('current grid in process is not in current session')
	for n, b in enumerate(blob_dicts):
		#ptolemy write its coordinates in (x,y) modify them first. we want
		# them in (row, col)
		b['tile_image'] = leginondata.AcquisitionImageData().direct_query(b['image_id'])
		try:
			ptolemy_square = leginondata.PtolemySquareData(grid_id=b['grid_id'],tile_id=b['tile_id'], square_id=b['square_id']).query(results=1)[0]
		except:
			print b
			continue
		statslinks = leginondata.PtolemySquareStatsLinkData(ptolemy=ptolemy_square).query()
		if not statslinks:
			print('bad ptolemy square id=%d' % ptolemy_square.dbid)
			continue
		targets = leginondata.AcquisitionImageTargetData(square=statslinks[0]['stats'],status='new').query()
		if not targets:
			print n, 'not selected as target before'
			continue
		t = targets[0]
		# This should be the same for all targets from blob_dicts
		square_targeting_targetlist=t['list']
		if t['session'].dbid == session.dbid and b['grid_id']==current_grid_id:
			print('saving score on target %d' % t.dbid)
			scores.append(b['score'])
			target_numbers.append(t['number'])
			q=leginondata.PtolemyScoreHistoryData(session=session,square=ptolemy_square, score=b['score'])
			q.insert(force=True)
		else:
			print 'target %d is in grid atlas %d and session %s, not current one' % (t.dbid,b['grid_id'], t['session']['name'])
	indices = [index for value, index in sorted(((v, i) for i,v in enumerate(scores)), reverse=True)]
	target_order = list(map((lambda x: target_numbers[x]), indices))
	print target_order
	q = leginondata.TargetOrderData(session=session, list=square_targeting_targetlist,order=target_order)
	q.insert(force=True)

sessiondata = getCurrentSession(tem_hostname)
time_limit = '-0 00:5:00'
wait_minutes = 5
wait_time = wait_minutes*60
while True:
	updateSquareTargetOrder(sessiondata)
	print('Waiting for %d minutes until next update' % wait_minutes)
	time.sleep(wait_time)
