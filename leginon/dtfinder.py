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
		'template size': 256,
	})
	def __init__(self, id, session, managerlocation, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.images = {
			'original': None,
			'template': None,
			'correlation': None,
		}

		self.corpeak = None

		self.cortypes = ['cross', 'phase']
		self.userpause = threading.Event()

		self.start()

	def readImage(self, filename):
		targetfinder.TargetFinder.readImage(self, filename)
		self.images['original'] = self.currentimagedata['image']

	def makeTemplate(self):
		# find most recent template info from this session
		qtempinfo = leginondata.DynamicTemplateData(session=self.session)
		try:
			tempinfo = qtempinfo.query(results=1)[0]
		except:
			self.images['template'] = None
			self.logger.info('No template found for this session.')
			return None

		oldimagedata = tempinfo['image']
		oldimage = oldimagedata['image']
		newimagedata = self.currentimagedata
		newimage = newimagedata['image']

		# use template info to crop out region of interest from old image
		center_r = tempinfo['center_row']
		center_c = tempinfo['center_column']
		tempsize = self.settings['template size']
		tempshape = tempsize,tempsize
		template = imagefun.crop_at(oldimage, (center_r, center_c), tempshape, mode='constant', cval=0)

		# pad with zeros to the size of the new image
		fulltemplate = numpy.zeros(newimage.shape, newimage.dtype)
		fulltemplate[:template.shape[0], :template.shape[1]] = template

		self.setImage(fulltemplate, 'template')

		# shift center of template to 0,0
		shift = -template.shape[0]/2, -template.shape[1]/2
		fulltemplate = scipy.ndimage.shift(fulltemplate, shift, mode='wrap')

		self.images['template'] = fulltemplate


		return fulltemplate

	def correlateTemplate(self):
		## correlate
		im1 = self.images['original']
		im2 = self.images['template']
		cor = correlator.phase_correlate(im1, im2, zero=False, pad=False)
		self.images['correlation'] = cor
		self.setImage(cor, 'correlation')
		
		# find peak
		peakinfo = peakfinder.findSubpixelPeak(cor)
		self.corpeak = peakinfo['subpixel peak']
		ivtargets = [(self.corpeak[1],self.corpeak[0])]
		self.setTargets(ivtargets, 'peak', block=True)

	def makeAcquisitionTargets(self):
		targets = self.panel.getTargetPositions('peak')
		self.setTargets(targets, 'acquisition')

	def storeTemplateInfo(self, imagedata, row, column):
		temp = leginondata.DynamicTemplateData()
		temp['session'] = self.session
		temp['image'] = imagedata
		temp['center_row'] = row
		temp['center_column'] = column
		temp.insert(force=True)

	def bypass(self):
		self.setTargets([], 'acquisition', block=True)
		self.setTargets([], 'focus', block=True)

	def applyTargetTemplate(self, centers):
		self.logger.info('apply template')
		imshape = self.hf['original'].shape
		acq_vect = self.settings['acquisition template']
		foc_vect = self.settings['focus template']
		newtargets = {'acquisition':[], 'focus':[]}
		for center in centers:
			self.logger.info('applying template to hole at %s' % (center,))
			for vect in acq_vect:
				target = center[0]+vect[0], center[1]+vect[1]
				tarx = target[0]
				tary = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					self.logger.info('skipping template point %s: out of image bounds' % (vect,))
					continue
				newtargets['acquisition'].append(target)
			for vect in foc_vect:
				target = center[0]+vect[0], center[1]+vect[1]
				tarx = target[0]
				tary = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					self.logger.info('skipping template point %s: out of image bounds' % (vect,))
					continue
				## check if target has good thickness
				if self.settings['focus template thickness']:
					rad = self.settings['focus stats radius']
					tmin = self.settings['focus min mean thickness']
					tmax = self.settings['focus max mean thickness']
					tstd = self.settings['focus max stdev thickness']
					coord = target[1], target[0]
					stats = self.hf.get_hole_stats(self.hf['original'], coord, rad)
					if stats is None:
						self.logger.info('skipping template point %s:  stats region out of bounds' % (vect,))
						continue
					tm = self.icecalc.get_thickness(stats['mean'])
					ts = self.icecalc.get_stdev_thickness(stats['std'], stats['mean'])
					self.logger.info('template point %s stats:  mean: %s, stdev: %s' % (vect, tm, ts))
					if (tmin <= tm <= tmax) and (ts < tstd):
						self.logger.info('template point %s passed thickness test' % (vect,))
						newtargets['focus'].append(target)
						break
				else:
					newtargets['focus'].append(target)
		return newtargets

	def everything(self):
		template = self.makeTemplate()
		if template is None:
			raise RuntimeError('could not make template')
		self.correlateTemplate()
		self.makeAcquisitionTargets()

	def findTargets(self, imdata, targetlist):
		self.setStatus('processing')
		autofailed = None

		## auto or not?
		self.images['original'] = imdata['image']
		self.currentimagedata = imdata
		self.setImage(imdata['image'], 'original')
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

		## store the acquisition target coords in template info
		targets = self.panel.getTargetPositions('acquisition')
		if len(targets) == 1:
			row = targets[0][1]
			col = targets[0][0]
			self.storeTemplateInfo(self.currentimagedata, row, col)
			self.logger.info('New template info stored')
		else:
			self.logger.info('No acquisition target, no new template info stored')

		self.logger.info('Publishing targets...')
		self.publishTargets(imdata, 'acquisition', targetlist)
		self.setStatus('idle')
