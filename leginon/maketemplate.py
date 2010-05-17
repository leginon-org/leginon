#!/usr/bin/env python

import leginon.leginondata
import subprocess
import sys
import os
import pyami.ccd
import pyami.imagefun

def run_image_viewer(filename):
	cmd = ['ImageViewer.py', filename]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	targets = proc.stdout.read()
	targets = targets.strip()
	if not targets:
		return []
	targets = targets.split('\n')
	targets = [map(int,target.split()) for target in targets]
	targets = [(target[1],target[0]) for target in targets]
	return targets

def run():
	name = sys.argv[1]
	boxsize = int(sys.argv[2])
	filenames = sys.argv[3:]

	'''
	session_name = sys.argv[3]
	preset_name = sys.argv[3]
	squery = leginon.leginondata.SessionData(name=session_name)
	session = squery.query()[0]
	pquery = leginon.leginondata.PresetData(name=preset_name, session=session)
	iquery = leginon.leginondata.AcquisitionImageData(session=session, preset=pquery, version=0)
	images = iquery.query(readimages=False)
	image_path = session['image path']
	filenames = []
	for image in images:
		filename = image['filename'] + '.mrc'
		fullname = os.path.join(image_path, filename)
		filenames.append(fullname)
	'''

	accumulator = pyami.ccd.Accumulator()
	for filename in filenames:
		points = run_image_viewer(filename)
		image = pyami.mrc.read(filename)
		for point in points:
			crop = pyami.imagefun.crop_at(image, point, (boxsize,boxsize), mode='nearest')
			accumulator.insert(crop)
	mean = accumulator.mean()
	pyami.mrc.write(mean, name)

if __name__ == '__main__':
	run()
