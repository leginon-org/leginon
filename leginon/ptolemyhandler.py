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

def _read_csv_row(r):
	int_keys = ['square_id','tile_id','grid_id','hole_id','mm_img_id']
	float_keys = ['prior_score', 'radius','ctf','ice_thickness','ctf_pred','ice_pred','ctf_var','ice_var']
	bool_keys = ['visited',]
	center_keys = ['center_x','center_y']
	#
	data = {}
	for k in int_keys:
		if k in r.keys():
			data[k] = int(r[k])
	for k in float_keys:
		if k in r.keys():
			if r[k] != '':
				data[k] = float(r[k])
			else:
				data[k] = None
	for k in bool_keys:
		if k in r.keys():
			data[k] = r[k].lower()=='true'
	#center
	c=center_keys
	cname = 'center'
	data[cname] = [float(r[c[0]]),float(r[c[1]])] # same order as center_keys (x,y)
	# GP_probs only exists after it learned enough.
	k = 'GP_probs'
	if k in r.keys():
		data[k] = float(r[k])
		data['score'] = data[k]
	else:
		data[k] = None
		data['score'] = data['prior_score']
	return data

def _read_lm_state_csv(csv_dicts):
	vertice_keys = [['vert_1_x','vert_1_y'],['vert_2_x','vert_2_y'],['vert_3_x','vert_3_y'],['vert_4_x','vert_4_y']]
	all_data = []
	for r in csv_dicts:
		data = _read_csv_row(r)
		#vertices
		data['vertices'] = []
		for v in vertice_keys:
			if v[0] in r.keys():
				vname = v[0][:-2]
				value = []
				for i in range(2):
					coord = list(map((lambda x: float(x)),r[v[0]][1:-1].split(',')))
					value.append(coord[0]) # Taking the first number, Paull will fix this
				data['vertices'].append(value)
		data['image_id'] = data['tile_id']
		data['area'] = 4000.0
		data['brightness'] = 40.0
		all_data.append(data)
	return all_data

def _read_mm_state_csv(csv_dicts):
	all_data = []
	for r in csv_dicts:
		data = _read_csv_row(r)
		data['image_id'] = data['mm_img_id']
		all_data.append(data)
	return all_data

def current_lm_state():
	r=requests.get(BASEURL + '/current_lm_state')
	data=csv.DictReader(io.StringIO(r.json()))
	return _read_lm_state_csv(data)

def set_noice_hole_intensity(value):
	payload={'value': float(value)}
	payload = json.dumps(payload)
	requests.post(BASEURL + '/set_noice_hole_intensity', payload)

def get_grid_tile_image(r):
	# input is imagedata at any point of the tree
	# output mosaic image targetlist
	if r['target']['list'] and r['target']['list']['mosaic']:
			return r
	if r['target']['image']:
		if r['target']['image']['target']:
			return get_grid_tile_image(r['target']['image'])
	else:
		# simulated
			return

def get_ptolemy_square(r):
	# input is imagedata at any point of the tree
	if r['target']['square']:
		results = leginondata.PtolemySquareStatsLinkData(stats=r['target']['square']).query(results=1)
		if not results:
			raise ValueError('Ptolemy active learning can not handle squares not found by ptolemy')
		return results[0]['ptolemy']
	else:
		if r['target']['image']:
			return get_ptolemy_square(r['target']['image'])
		else:
			raise ValueError('Ptolemy active learning can not handle simulated target')

def push_and_evaluate_mm(imagedata):
	grid_tile_image = get_grid_tile_image(imagedata)
	if not grid_tile_image:
		raise ValueError('Ptolemy active learning can not handle simulated target')
	mm_img_id = imagedata.dbid
	grid_id = grid_tile_image['target']['list'].dbid
	tile_id = grid_tile_image.dbid
	square_id = get_ptolemy_square(imagedata)['square_id']
	a = imagedata['image']
	#
	payload={'image': a.tolist(),
			'grid_id':grid_id,
			'tile_id':tile_id,
			'square_id':square_id,
			'mm_img_id':mm_img_id,
	}
	payload = json.dumps(payload)
	r = requests.post(BASEURL + '/push_and_evaluate_mm', payload)
	data=csv.DictReader(io.StringIO(r.json()))
	return _read_mm_state_csv(data)

def visit_holes(hole_ids, ctfs, ice_thicknesses):
	payload = {
			'hole_ids':hole_ids,
			'ctfs': ctfs,
			'ice_thicknesses': ice_thicknesses,
	}
	payload = json.dumps(payload)
	r = requests.post(BASEURL + '/visit_holes', payload)

if __name__=='__main__':
	initialize()
	#
	hl_id = 5897
	hlimage = leginondata.AcquisitionImageData.direct_query(hl_id)
	tile_image = get_grid_tile_image(hlimage)
	tile_image_id = tile_image.dbid
	t0=time.time()
	print('running %d' % tile_image_id)
	push_lm(tile_image)
	print('%d time= %.2f----' % (tile_image_id, time.time()-t0))
	r=current_lm_state()
	for row in r:
		print(row)
	i0 = 150
	set_noice_hole_intensity(i0)
	print(push_and_evaluate_mm(hlimage))
