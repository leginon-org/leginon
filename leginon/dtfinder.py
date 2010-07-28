#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import targetfinder
from pyami import correlator, imagefun, peakfinder

import threading
import gui.wx.DTFinder
import numpy
from pyami import quietscipy
import scipy.ndimage

class DTFinder(targetfinder.TargetFinder):
	panelclass = gui.wx.DTFinder.Panel
	settingsclass = leginondata.DTFinderSettingsData
	defaultsettings = dict(targetfinder.TargetFinder.defaultsettings)
	defaultsettings.update({
		'skip': False,
		'image filename': '',
		'correlation type': 'phase',
		'template size': 100,
		'correlation lpf': 1.3,
		'rotate': False,
		'angle increment': 5,
		'snr threshold': 6.0,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.images = {
			'original': None,
			'templateA': None,
			'templateB-unshifted': None,
			'templateB': None,
			'correlation': None,
		}

		self.cortypes = ['cross', 'phase']
		self.userpause = threading.Event()
		self.correlator = correlator.Correlator()

		self.start()

	def readImage(self, filename):
		targetfinder.TargetFinder.readImage(self, filename)
		self.images['original'] = self.currentimagedata['image']

	def makeTemplateA(self, current=None):
		newimagedata = self.currentimagedata

		if current is not None:
			tempinfo = {'image': self.currentimagedata, 'center_row': current[0], 'center_column': current[1]}
		else:
			# find most recent template info from this session
			qtempinfo = leginondata.DynamicTemplateData(session=self.session)
			try:
				tempinfo = qtempinfo.query(results=1)[0]
			except:
				self.images['templateA'] = None
				self.logger.info('No template found for this session.')
				return None
			self.oldpeakinfo = {}
			for key in ('minsum', 'snr'):
				self.oldpeakinfo[key] = tempinfo[key]

		oldimagedata = tempinfo['image']

		if oldimagedata['correction channel'] == newimagedata['correction channel']:
			self.logger.info('reversing template corrector channel')
			try:
				oldimagedata = self.reverseCorrectorChannel(oldimagedata)
			except:
				self.logger.warning('failed to reverse template corrector channel')

		oldimage = oldimagedata['image']
		newimage = newimagedata['image']

		# use template info to crop out region of interest from old image
		center_r = tempinfo['center_row']
		center_c = tempinfo['center_column']
		tempsize = self.settings['template size']
		if tempsize == 100:
			imcenter_r = oldimage.shape[0] / 2
			imcenter_c = oldimage.shape[1] / 2
			shift_r = imcenter_r - center_r
			shift_c = imcenter_c - center_c
			templateA = scipy.ndimage.shift(oldimage, (shift_r, shift_c), mode='wrap')
		else:
			tempsize = int(tempsize * oldimage.shape[0] / 100.0)
			tempshape = tempsize,tempsize
			templateA = imagefun.crop_at(oldimage, (center_r, center_c), tempshape, mode='wrap')
		self.images['templateA'] = templateA
		self.setImage(templateA, 'templateA')
		return templateA

	def makeTemplateB(self, angle=0):
		# rotate template
		if angle:
			template = scipy.ndimage.rotate(self.images['templateA'], angle, reshape=False)
		else:
			template = self.images['templateA']

		# pad with zeros to the size of the new image
		newimagedata = self.currentimagedata
		newimage = newimagedata['image']
		fulltemplate = numpy.zeros(newimage.shape, newimage.dtype)
		fulltemplate[:template.shape[0], :template.shape[1]] = template

		self.images['templateB-unshifted'] = fulltemplate
		self.setImage(fulltemplate, 'templateB')

		# shift center of template to 0,0
		shift = -template.shape[0]/2, -template.shape[1]/2
		fulltemplate = scipy.ndimage.shift(fulltemplate, shift, mode='wrap')

		self.images['templateB'] = fulltemplate

		return fulltemplate

	def makeAngles(self):
		angleinc = self.settings['angle increment']
		angles = [0]
		for angle in numpy.arange(angleinc, 180, angleinc):
			angles.extend([-angle, angle])
		angles.append(180)
		print 'ANGLES', angles
		return angles

	def autoCorrelate(self, point):
		self.makeTemplateA(current=point)
		self.makeTemplateB()
		self.newpeakinfo = self.correlateTemplate()

	def correlateRotatingTemplate(self):
		if not self.settings['rotate']:
			self.makeTemplateB()
			peakinfo = self.correlateTemplate()
			return

		angles = self.makeAngles()
		bestangle = None
		bestpeakinfo = {'snr': 0}
		goodcheck = False
		for angle in angles:
			print 'ANGLE', angle
			self.makeTemplateB(angle)
			peakinfo = self.correlateTemplate()
			peakinfo['template angle'] = angle
			snr = peakinfo['snr']
			if snr > bestpeakinfo['snr']:
				bestpeakinfo = peakinfo
				bestangle = angle
			#from pyami import mrc
			#mrc.write(self.images['correlation'], 'cor%d.mrc' % (angle,))
			if self.checkPeakInfo(peakinfo):
				goodcheck = True
				break
		if goodcheck:
			self.newpeakinfo = peakinfo
		else:
			self.newpeakinfo = bestpeakinfo
		self.logger.info('best angle: %s' % (self.newpeakinfo['template angle']))

		self.setImage(self.newpeakinfo['templateB-unshifted'], 'templateB')
		self.setImage(self.newpeakinfo['correlation'], 'correlation')
		corpeak = self.newpeakinfo['subpixel peak']
		ivtargets = [(corpeak[1], corpeak[0])]
		self.setTargets(ivtargets, 'peak', block=True)

	def checkPeakInfo(self, peakinfo):
		oldsnr = self.oldpeakinfo['snr']
		oldminsum = self.oldpeakinfo['minsum']
		newsnr = peakinfo['snr']
		newminsum = peakinfo['minsum']
		snrdiff = newsnr - oldsnr
		minsumdiff = newminsum - oldminsum
		percentsnr = 100 * snrdiff / oldsnr
		percentminsum = 100 * minsumdiff / oldminsum

		print '  NEW'
		print '    MINSUM', newminsum
		print '    SNR', newsnr
		print '  ERR'
		print '    MINSUM', minsumdiff, percentminsum
		print '    SNR', snrdiff, percentsnr

		if newsnr > self.settings['snr threshold']:
			return True
		else:
			return False

	def correlateTemplate(self):
		## correlate
		self.correlator.setImage(0, self.images['templateB'])
		if self.settings['correlation type'] == 'phase':
			cor = self.correlator.phaseCorrelate(zero=False)
		else:
			cor = self.correlator.crossCorrelate()
		self.images['correlation'] = cor

		# low pass filter
		if self.settings['correlation lpf']:
			cor = scipy.ndimage.gaussian_filter(cor, self.settings['correlation lpf'])

		# display correlation
		self.setImage(cor, 'correlation')

		# find peak
		peakinfo = peakfinder.findSubpixelPeak(cor)
		peakinfo['correlation'] = cor
		peakinfo['templateB-unshifted'] = self.images['templateB-unshifted']
		#self.printPeakInfo(peakinfo)
		corpeak = peakinfo['subpixel peak']
		ivtargets = [(corpeak[1], corpeak[0])]
		self.setTargets(ivtargets, 'peak', block=True)
		return peakinfo

	def printPeakInfo(self, peakinfo):
		print 'Peak Info:'
		for key in peakinfo:
			print '  %s:  %s' % (key, peakinfo[key])

	def makeFinalTargets(self):
		targets = self.panel.getTargetPositions('peak')
		self.setTargets(targets, 'acquisition', block=True)
		self.setTargets(targets, 'focus', block=True)

	def storeTemplateInfo(self, imagedata, row, column, peakinfo):
		temp = leginondata.DynamicTemplateData()
		temp['session'] = self.session
		temp['image'] = imagedata
		temp['center_row'] = row
		temp['center_column'] = column
		for key in ('minsum', 'snr'):
			temp[key] = peakinfo[key]
		temp.insert(force=True)

	def bypass(self):
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)

	def everything(self):
		templateA = self.makeTemplateA()
		if templateA is None:
			raise RuntimeError('could not make template')
		self.correlateRotatingTemplate()
		self.makeFinalTargets()

	def findTargets(self, imdata, targetlist):
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.images['original'] = imdata['image']
		self.currentimagedata = imdata
		self.correlator.setImage(1, self.images['original'])
		self.setImage(imdata['image'], 'Original')
		if not self.settings['skip']:
			autofailed = False
			try:
				self.everything()
			except Exception, e:
				self.logger.error('auto target finder failed: %s' % (e,))
				autofailed = True

		## user part
		if self.settings['user check'] or autofailed:
			self.setStatus('user input')
			self.logger.info('Waiting for user to check targets...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.panel.targetsSubmitted()
			self.setStatus('processing')
			targets = self.panel.getTargetPositions('acquisition')
			if targets:
				row = targets[0][1]
				col = targets[0][0]
				self.autoCorrelate((row,col))

		## store the acquisition target coords in template info
		targets = self.panel.getTargetPositions('acquisition')
		if len(targets) == 1:
			row = targets[0][1]
			col = targets[0][0]
			self.storeTemplateInfo(self.currentimagedata, row, col, self.newpeakinfo)
			self.logger.info('New template info stored')
		else:
			self.logger.info('No acquisition target, no new template info stored')

		self.logger.info('Publishing targets...')
		self.publishTargets(imdata, 'acquisition', targetlist)
		self.publishTargets(imdata, 'focus', targetlist)
		self.setStatus('idle')

	def autoEllipseCenter(self,params):
		centers = []
		disptarget = params['center'][0],params['center'][1]
		centers.append(disptarget)
		self.setTargets(centers, 'acquisition')	
