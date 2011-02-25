#!/usr/bin/env python

import simplempi
import leginon.leginondata
import pyami.fileutil
import pyami.mrc
import pyami.numpil
import time
import os

class MRCJPG(simplempi.TaskHandler):
	def initTasks(self, session, outpath):
		## get all image filenames for this session
		qsession = leginon.leginondata.SessionData(name=session)
		session = qsession.query()
		session = session[0]
		inpath = session['image path']

		## query images
		qimages = leginon.leginondata.AcquisitionImageData(session=session)
		images = qimages.query()
		if not images:
			return []

		## create out dir
		pyami.fileutil.mkdirs(outpath)

		## create task list
		infilenames = [image['filename']+'.mrc' for image in images]
		full_infilenames = [os.path.join(inpath, infile) for infile in infilenames]

		outfilenames = [infile.replace('.mrc','.jpg') for infile in infilenames]
		full_outfilenames = [os.path.join(outpath, outfile) for outfile in outfilenames]

		tasks = zip(full_infilenames, full_outfilenames)
		return tasks

	def processTask(self, task):
		print self, task[0]
		mrcfile = task[0]
		jpgfile = task[1]
		im = pyami.mrc.read(mrcfile)
		pyami.numpil.write(im, jpgfile, format='JPEG')

import sys
session = sys.argv[1]
outpath = sys.argv[2]
m = MRCJPG(session=session, outpath=outpath)
m.run()
