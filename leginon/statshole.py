#!/usr/bin/env python
import random
import math
from pyami import groupfun
import pyami.circle
from leginon import ice, holeconfigurer

Configurer = holeconfigurer.Configurer

class StatsHole(object):
	def __init__(self, info_dict, index, statskeys={}):
		'''Simple blob object with image and stats as attribute
			center = (row, col) on image
		'''
		center = info_dict['center']
		# stats will be displayed in target panel
		self.stats = {"center":center,"hole_number":index+1} # (r,c)
		for key in statskeys:
			self.stats[key]=info_dict[key]
		self.info_dict = info_dict

	def set_holestats(self, holestats, radius=None):
		self.stats['hole_stat_radius'] = radius
		self.stats['hole_n'] = holestats['n']
		self.stats['hole_mean'] = holestats['mean']
		self.stats['hole_std'] = holestats['std']

class HoleStatsCalculator(Configurer):
	def __init__(self):
		self.circle = pyami.circle.CircleMaskCreator()
		self.setDefaults({'radius':20,'im':None})

	def calc_stats(self, holes):
		bad_indices = []
		im = self.configs['im']
		r = self.configs['radius']
		for i, hole in enumerate(holes):
			center = hole.stats['center']
			holestats = self.calc_center_holestats(center, im, r)
			if holestats is None:
				bad_indices.append(i)
			else:
				hole.set_holestats(holestats, r)
		bad_indices.sort()
		bad_indices.reverse()
		for b in bad_indices:
			holes.pop(b)
		return holes

	def calc_center_holestats(self, coord, im, r):
		'''
		Returns stats centered at coord (r,c)
		'''
		holestats = self.circle.get_circle_stats(im, coord, r)
		return holestats

class GoodHoleFilter(Configurer):
	def filter_good(self, holes):
		return list(filter((lambda x: x.stats['good']), holes))

class HoleIceCalculator(Configurer):
	def __init__(self):
		self.icecalc = ice.IceCalculator()
		self.setDefaults({'i0': None, 'tmin': 0.0, 'tmax': 0.1, 'tstdmin': 0.05,'tstdmax':0.5})

	def configure(self, new_configs):
		super(HoleIceCalculator, self).configure(new_configs)
		if 'i0' in new_configs.keys() and self.configs['i0'] is not None:
			self.icecalc.set_i0(self.configs['i0'])

	def calc_ice(self, holes):
		'''
		Return holes2 that contains only good holes with ice thickness thresholds
		in configs.
		'''
		holes2 = []
		i0 = self.configs['i0']
		self.icecalc.set_i0(i0)
		for hole in holes:
			if 'hole_mean' not in hole.stats:
				## no mean was calculated
				continue
			hole = self.calc_one_ice(hole)
			if hole.stats['good'] == True:
				holes2.append(hole)
		return holes, holes2

	def calc_one_ice(self, hole):
		'''
		Thresholding ice thickness on one hole
		'''
		tmin = self.configs['tmin']
		tmax = self.configs['tmax']
		tstdmax = self.configs['tstdmax']
		tstdmin = self.configs['tstdmin']
		mean = hole.stats['hole_mean']
		std = hole.stats['hole_std']
		tm = self.icecalc.get_thickness(mean)
		hole.stats['thickness-mean'] = tm
		ts = self.icecalc.get_stdev_thickness(std, mean)
		hole.stats['thickness-stdev'] = ts
		if (tmin <= tm <= tmax) and (tstdmin <= ts < tstdmax):
			hole.stats['good'] = True
		else:
			hole.stats['good'] = False
		return hole

class HoleSampler(Configurer):
	def __init__(self):
		# samples -1 means no sampling, i.e. use all
		self.setDefaults({'classes':1,'samples': -1,'category':'center'})

	def sampleHoles(self, holes):
		if not holes:
			return holes
		n_sample = self.configs['samples'] # total samples
		n_class = self.configs['classes']
		if n_sample == 0:
			return []
		if n_sample == -1 or n_sample >= len(holes):
			return holes
		keys = holes[0].stats.keys()
		cat = self.configs['category']
		if cat not in keys:
			raise ValueError('category "%s" used for grouping not in hole stats' % cat)
		holes_in_bins = self._groupHoles(holes, n_class, cat)
		holes = self._samplingInClass(holes_in_bins, n_class, n_sample)
		return sorted(holes, key=lambda x: x.stats['hole_number'], reverse=False)

	def _samplingInClass(self, holes_in_bins, n_class, total_targets_need):
		# get a list at least as long as total_targets_need
		sampling_order = range(n_class)*int(math.ceil(total_targets_need/float(n_class)))
		# truncate the list
		sampling_order = sampling_order[:total_targets_need]
		samples = []
		for s in sampling_order:
			# random sample without replacement
			pick = random.sample(range(len(holes_in_bins[s])),1)[0]
			hole = holes_in_bins[s].pop(pick)
			samples.append(hole)
		return samples

	def _groupHoles(self, holes, n_class, category):
		holes = sorted(holes, key=lambda x: x.stats[category], reverse=True)
		range_list = groupfun.calculateIndexRangesInClassEvenDistribution(len(holes), n_class)
		holes_in_bins = []
		for c in range(n_class):
			start, end = range_list[c]
			holes_in_bins.append(holes[start:end])
		return holes_in_bins

class HoleConvolver(Configurer):
	def __init__(self):
		# samples -1 means no sampling, i.e. use all
		self.setDefaults({'im_shape': None,'conv_vect':None})

	def make_convolved(self, holes):
		imshape = self.configs['im_shape']
		conv_vect = self.configs['conv_vect']
		convolved = []
		for j, hole in enumerate(holes):
			for i, vect in enumerate(conv_vect):
				center = hole.stats['center'] #(r,c)
				target = center[0]+vect[0], center[1]+vect[1]
				tary = target[0]
				tarx = target[1]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					continue
				h = hole.info_dict
				h.update(hole.stats)
				h['center'] = target #(r,c)
				h['convolved'] = True
				n = hole.stats['hole_number'] # (target number base 1)
				# convolved newhole has all old stats items
				newhole = StatsHole(h, n, h.keys())
				convolved.append(newhole)
		return convolved
