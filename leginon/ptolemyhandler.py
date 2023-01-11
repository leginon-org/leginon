import requests
import json
from pyami import mrc
from leginon import leginondata
import time
import io
import csv

BASEURL = 'http://127.0.0.1:8000'

def initialize():
	payload={'historical_state_paths':[]}
	payload = json.dumps(payload)
	requests.post(BASEURL + '/initialize_new_session', data=payload)

def push_lm(imagedata):
	imagelist_id = imagedata['list'].dbid
	image_id = imagedata.dbid
	a = imagedata['image']
	# Use imagedata.dbid as tile_id for ptolemy
	payload={'image': a.tolist(), 'grid_id':imagelist_id, 'tile_id':image_id}
	payload = json.dumps(payload)
	requests.post(BASEURL + '/push_lm', payload)

def _read_csv(csv_dicts):
	int_keys = ['square_id','tile_id','grid_id']
	float_keys = ['prior_score',]
	bool_keys = ['visited',]
	center_keys = ['center_x','center_y']
	vertice_keys = [['vert_1_x','vert_1_y'],['vert_2_x','vert_2_y'],['vert_3_x','vert_3_y'],['vert_4_x','vert_4_y']]
	#
	all_data = []
	for r in csv_dicts:
		data = {}
		for k in int_keys:
			data[k] = int(r[k])
		for k in float_keys:
			data[k] = float(r[k])
		for k in bool_keys:
			data[k] = r[k].lower()=='true'
		data['vertices'] = []
		#center
		c=center_keys
		cname = 'center'
		data[cname] = [float(r[c[0]]),float(r[c[1]])] # same order as center_keys (x,y)
		#vertices
		for v in vertice_keys:
			vname = v[0][:-2]
			value = []
			for i in range(2):
				coord = list(map((lambda x: float(x)),r[v[0]][1:-1].split(',')))
				value.append(coord[0]) # Taking the first number, Paull will fix this
			data['vertices'].append(value)
		# GP_probs only exists after it learned enough.
		k = 'GP_probs'
		if k in r.keys():
			data[k] = float(r[k])
			data['score'] = data[k]
		else:
			data[k] = None
			data['score'] = data['prior_score']
		data['image_id'] = data['tile_id']
		data['area'] = 4000.0
		data['brightness'] = 40.0
		all_data.append(data)
	return all_data

def current_lm_state():
	r=requests.get(BASEURL + '/current_lm_state')
	data=csv.DictReader(io.StringIO(r.json()))
	return _read_csv(data)


if __name__=='__main__':
	initialize()
	for tile_id in (1945,):
		t0=time.time()
		tiledata = leginondata.MosaicTileData.direct_query(tile_id)
		print('running %d' % tile_id)
		push_lm(tiledata['image'])
		print('%d time= %.2f----' % (tile_id, time.time()-t0))
	r=current_lm_state()
	print(list(r))
	for row in r:
		print(row)
