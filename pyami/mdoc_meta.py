#!/usr/bin/env python
import re
import math
import os
import ntpath

xy_vector_meta_map = [
		('BeamTilt','beam tilt', 0.001),
		('XTilt', 'phase plate plane shift', 0.001),
		('ImageShift', 'image shift', 1e-6),
		('StagePosition',  'stage position', 1e-6),
	]
scaler_meta_map = [
		('Voltage','high tension', 1000),
		('Magnification', 'magnification', 1),
		('Intensity', 'intensity', 1), # unknown scale
		('SpotSize', 'spot size', 1),
		('ImageDistanceOffset', 'parallel illumication offset', 1e-4),
		('ExposureTime', 'exposure time', 1),
		('ExposureDose', 'dose', 1e20),
		('TargetDefocus', 'intended defocus', 1e-6),
		('Defocus', 'defocus', 1e-6),
		('NumSubFrames', 'nframes', 1),
		('PixelSpacing', 'apix', 1),
	]

dict_key_meta_map = [
		('StageZ',  'stage position','z', 1e-6),
		('StageZ',  'stage position','z', 1e-6),
		('TiltAngle',  'stage position','a', math.pi/180.0),
	]

dict_key_xy_meta_map = [
		('ObjectiveStig',  'stigmator','objective', 1e-3),
]

def parse_value(raw):
	"""Convert a raw value string into int/float, list of floats, or leave as string."""
	raw = raw.strip()
	tokens = raw.split()

	def try_num(tok):
		try:
			if '.' in tok or 'e' in tok.lower():
				return float(tok)
			return int(tok)
		except ValueError:
			return None

	if len(tokens) == 0:
		return raw  # empty value, keep as-is (rare)

	nums = [try_num(t) for t in tokens]

	if all(n is not None for n in nums):
		return nums[0] if len(nums) == 1 else nums

	# Not fully numeric -> keep as original string (e.g. the "T =" line)
	return raw

def read_mdoc(mdoc_path):
	data = {}
	frame_sets = []
	current_section = None
	section_re = re.compile(r'^\[(.+?)\]$')
	with open(mdoc_path,'r') as f:
		lines = f.readlines()
	for line in lines:
		line = line.rstrip('\n')
		stripped = line.strip()
		if not stripped:
			continue
		m = section_re.match(stripped) #matching section pattern
		if m:
			# e.g. "FrameSet = 0"
			header = m.group(1)
			if '=' in header:
				name, idx = header.split('=', 1)
				name = name.strip()
				idx = idx.strip()
			else:
				name, idx = header.strip(), None
			current_section = {'_type': name, '_index': parse_value(idx)}
			frame_sets.append(current_section)
			continue
		if '=' in stripped:
			key, val = stripped.split('=', 1)
			key = key.strip()
			val = parse_value(val)

		if current_section is not None:
			current_section[key] = val
		else:
			data[key] = val
		if frame_sets:
			data['FrameSets'] = frame_sets
	return data

def rotation_flip_number_2leginon(v):
	flip = bool(v // 4)
	rotate = v % 4
	return {'frame flip': flip,'frame rotate':rotate}

def _mdoc2leginon(k,v, imginfo):
		for item in scaler_meta_map:
			if k == item[0]:
				imginfo.update({item[1]:v*item[-1]})
		for item in dict_key_meta_map:
			if k == item[0]:
				if item[1] not in imginfo.keys():
					imginfo.update({item[1]:{}})
				new_dict = imginfo[item[1]]
				new_dict.update({item[2]: v * item[-1]})
				imginfo[item[1]].update(new_dict)
				return
		for item in xy_vector_meta_map:
			if k == item[0]:
				if item[1] not in imginfo.keys():
					imginfo.update({item[1]:{}})
				new_dict = imginfo[item[1]]
				new_dict.update({'x': v[0] * item[-1]})
				new_dict.update({'y': v[1] * item[-1]})
				return
		for item in dict_key_xy_meta_map:
			if k == item[0]:
				if item[1] not in imginfo.keys():
					imginfo.update({item[1]:{item[2]:{}}})
				new_dict = imginfo[item[1]][item[2]]
				new_dict.update({'x': v[0] * item[-1]})
				new_dict.update({'y': v[1] * item[-1]})
				imginfo[item[1]][item[2]] = new_dict
				return

def mdoc2leginon(mdoc_data, mount_dir):
	imginfo = {}
	for k in mdoc_data:
		v = mdoc_data[k]
		_mdoc2leginon(k, v, imginfo)
		if k in ('FrameSets',):
			for fk in mdoc_data[k][0]:
				v = mdoc_data[k][0][fk]
				_mdoc2leginon(fk, v, imginfo)
				if fk == 'SubFramePath':
					filename = ntpath.basename(v)
					root, ext = os.path.splitext(filename)
					imginfo['filename'] = root
					imginfo['original filepath'] = os.path.join(mount_dir,filename)
				if fk == 'RotationAndFlip':
					imginfo.update(rotation_flip_number_2leginon(v))
				if fk == 'PixelSpacing':
					apix = v
					mpix = apix * 1e-10 #meters per pixel
					if 'Binning' in mdoc_data[k][0].keys():
						mdoc_binning = mdoc_data[k][0]['Binning']
						if mdoc_binning < 1:
							imginfo['binning'] = {'x':1,'y':1}
							imginfo['unbinned pixelsize'] = mpix
						else:
							imginfo['binning'] = {'x':mdoc_binning, 'y':mdoc_binning}
							imginfo['unbinned pixelsize'] = mpix / mdoc_binning
					else:
						imginfo['binning'] = {'x':1,'y':1}
						imginfo['unbinned pixelsize'] = mpix
	return imginfo

if __name__ == '__main__':
	#mdoc_name = '/Users/anchi.cheng/tests/sem_upload/data/lafis_in_vac01_000.tif.mdoc'
	mdoc_name = '/Users/anchi.cheng/tests/sem_upload/data2/p26jul24a_ronchi_56-7_0003_-0.0.tif.mdoc'
	mount_dir = ntpath.dirname(mdoc_name)
	data = read_mdoc(mdoc_name)
	print(mdoc2leginon(data, mount_dir))
