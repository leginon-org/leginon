import os
import shutil

import imageprocessor
import leginon.gui.wx.RaptorProcessor
import leginondata
import runRaptor
from pyami import mrc

class RaptorProcessor(imageprocessor.ImageProcessor):
	panelclass = leginon.gui.wx.RaptorProcessor.Panel
	settingsclass = leginondata.RaptorProcessorSettingsData
	defaultsettings = dict(imageprocessor.ImageProcessor.defaultsettings)
	defaultsettings.update({
		'time': 15,
		'binning': 2,
		'path': '/tmp',
	})

	def processImageList(self, imagelist):
		if not imagelist:
			self.logger.warning('No images in image list.')
			return

		mrc_files = []
		imagepath = self.session['image path']
		tiltseries = imagelist[0]['tilt series']
		for imagedata in imagelist:
			mrc_name = imagedata['filename'] + '.mrc'
			fullname = os.path.join(imagepath, mrc_name)
			mrc_files.append(fullname)
		self.writeParamsFile(tiltseries, mrc_files)
		self.logger.info('making stack for tilt series %d' % (tiltseries['number'],))
		self.makeStack(tiltseries, mrc_files)
		self.runRaptor(tiltseries)

	def getFilename(self, tiltseries):
		# determine param filename
		session_name = self.session['name']
		seriesnumber = tiltseries['number']
		numberstr = '%03d' % (seriesnumber,)
		path = self.settings['path']
		filename = session_name + '_' + numberstr
		filename = os.path.join(path, filename)
		return filename

	def writeParamsFile(self, tiltseries, mrc_files):
		# determine param filename
		paramsfilename = self.getFilename(tiltseries) + '.rap'

		# params to put into param file
		time = self.settings['time']
		binning = self.settings['binning']

		# write params to file
		f = open(paramsfilename, 'w')
		f.write('%d\n' % (time,))
		f.write('%d\n' % (binning,))
		for mrc_file in mrc_files:
			f.write(mrc_file+'\n')

	def runRaptor(self, tiltseries):
		filename = self.getFilename(tiltseries)
		paramsfilename = filename + '.rap'
		outfilename = filename + '.out'
		errfilename = filename + '.err'
		self.logger.info('running raptor on tilt series %d' % (tiltseries['number'],))
		runRaptor.run(paramsfilename, outfilename, errfilename)
		self.logger.info('raptor done with tilt series %d' % (tiltseries['number'],))

	def makeStack(self, tiltseries, mrc_files):
		stackname = self.getFilename(tiltseries) + '_stack.mrc'
		stackname = os.path.join(self.settings['path'], stackname)
		shutil.copy(mrc_files[0], stackname)

		for mrcfile in mrc_files:
			im = mrc.read(mrcfile)
			mrc.append(im, stackname)
