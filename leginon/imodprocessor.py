import imageprocessor
import os
import gui.wx.RaptorProcessor
import leginondata
#import runImod
from pyami import mrc, imagefun, correlator, peakfinder
import shutil
from tomography import tiltcorrelator
try:
	import apImod
	noappion = False
except:
	noappion = True

class ImodProcessor(imageprocessor.ImageProcessor):
	panelclass = gui.wx.RaptorProcessor.Panel
	settingsclass = leginondata.RaptorProcessorSettingsData
	defaultsettings = dict(imageprocessor.ImageProcessor.defaultsettings)
	defaultsettings.update({
		'time': 15,
		'binning': 2,
		'path': '/tmp',
	})

	def processImageList(self, imagelist):
		self.processpath = self.settings['path']
		if not os.path.isdir(self.processpath):
			os.makedirs(self.processpath)
		if not imagelist:
			self.logger.warning('No images in image list.')
			return
		self.nopeaks = True
		self.correlator = tiltcorrelator.Correlator(self, 0, 4,lpf=1.5)
		mrc_files = []
		self.peaks = [{'x':0.0,'y':0.0}]
		imagepath = self.session['image path']
		tiltseries = imagelist[0]['tilt series']
		tiltangledict = {}
		correlationpeak = {}
		self.second_group = False 
		for imagedata in imagelist:
			tilt = imagedata['scope']['stage position']['a']*180/3.14159
			if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
				if self.second_group:
					direction=-tiltseries['tilt step']
				else:
					direction= tiltseries['tilt step']
					# switch group in getCorrelationPeak not here
					self.second_group = False
				tilt = tilt+0.001*direction
			tiltangledict[tilt] = imagedata
			try:
				correlationpeak[tilt] = self.getCorrelationPeak(tiltseries, tilt, imagedata)
			except:
				self.nopeaks = True
		tiltkeys = tiltangledict.keys()
		tiltkeys.sort()
		for key in tiltkeys:
			imagedata = tiltangledict[key]
			mrc_name = imagedata['filename'] + '.mrc'
			fullname = os.path.join(imagepath, mrc_name)
			mrc_files.append(fullname)
		#self.writeParamsFile(tiltseries, mrc_files)
		self.logger.info('making stack for tilt series %d' % (tiltseries['number'],))
		self.makeStack(tiltseries, mrc_files)
		self.writeRawtltFile(tiltseries,tiltkeys)
		if not self.nopeaks:
			self.writePrexfFile(tiltseries,correlationpeak)
		if not noappion:
			self.runImod(tiltseries)
		else:
			self.logger.error('Need APPION and IMOD to process')

	def getCorrelationPeak(self, tiltseries, tilt, imagedata):
		bin = self.settings['binning']
		q = leginondata.TomographyPredictionData(image=imagedata)
		results = q.query()
		if len(results) > 0:
			peak = results[0]['correlation']
		else:
			raise ValueError
		start = tiltseries['tilt start']
		if tilt < start:
			peak['x']=-peak['x']
			peak['y']=-peak['y']
		if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
			self.correlator.correlate(imagedata, tiltcorrection=True, channel=None)
			if self.second_group:
				self.peaks = [{'x':0.0,'y':0.0}]
				peak = self.correlator.getShift(False)
				if tiltseries['tilt step'] > 0:
					return (-peak['x']/bin,peak['y']/bin)
				else:
					return (peak['x']/bin,-peak['y']/bin)
			else:
				self.second_group = True
				return
		self.peaks.append(peak)
		return ((peak['x']-self.peaks[-2]['x'])/bin,-(peak['y']-self.peaks[-2]['y'])/bin)

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

	def runImod(self, tiltseries):
		self.logger.info('running quick imod on tilt series %d' % (tiltseries['number'],))
		filename = self.getFilename(tiltseries)
		self.logger.info('alignement of %d' % (tiltseries['number'],))
		if self.nopeaks:
			apImod.coarseAlignment(self.settings['path'],filename)
		apImod.convertToGlobalAlignment(self.settings['path'],filename)
		self.logger.info('creating aligned stack of %d' % (tiltseries['number'],))
		apImod.createAlignedStack(self.settings['path'],filename)
		self.logger.info('creating a highly binned tomogram of %d' % (tiltseries['number'],))
		apImod.recon3D(self.settings['path'],filename)
		self.logger.info('imod done with tilt series %d' % (tiltseries['number'],))

	def makeStack(self, tiltseries, mrc_files):
		stackname = self.getFilename(tiltseries) + '.st'
		stackname = os.path.join(self.settings['path'], stackname)
		im = mrc.read(mrc_files[0])
		image = imagefun.bin(im, int(self.settings['binning']))
		mrc.write(image,stackname)
		#shutil.copy(mrc_files[0], stackname)
		del mrc_files[0]
		for mrcfile in mrc_files:
			im = mrc.read(mrcfile)
			image = imagefun.bin(im, int(self.settings['binning']))
			mrc.append(image, stackname)

	def writeRawtltFile(self,tiltseries,tilts):
		rawtltname = self.getFilename(tiltseries) + '.rawtlt'
		rawtltname = os.path.join(self.settings['path'], rawtltname)
		f = open(rawtltname, 'w')
		for tilt in tilts:
			f.write('%6.2f\n' % (tilt,))
		f.close()

	def writePrexfFile(self,tiltseries,xpeaks):
		rawtltname = self.getFilename(tiltseries) + '.prexf'
		rawtltname = os.path.join(self.settings['path'], rawtltname)
		f = open(rawtltname, 'w')
		tilts = xpeaks.keys()
		tilts.sort()
		f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (1.0,0.0,0.0,1.0,0.0,0.0))
		for tilt in tilts:
			if xpeaks[tilt] is not None:
				f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (1.0,0.0,0.0,1.0,xpeaks[tilt][0],xpeaks[tilt][1]))
		f.close()
