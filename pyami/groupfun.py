#!/usr/bin/env python
"""
Collection of functions to help group items in a list.
"""
import math
import random

def calculateIndexRangesInClassEvenDistribution(total, n_class):
	'''
	Return a index range list of (start, end) to create a most evenly
	distributed classes from a list with given total count.
	total: number of items in the list to be divided.
	n_class: number of classes/groups to divide into.
	'''
	sampling_order = range(n_class)*int(math.floor(total/float(n_class)))
	# fill the rest with random sample. This helps unbiased even distribution
	if len(sampling_order) < total:
		rest = random.sample(range(n_class), total - len(sampling_order))
		sampling_order.extend(rest)
	# number_of_samples_in_classes
	nsample_in_classes = map((lambda x: sampling_order.count(x)), range(n_class))
	last_c = 0
	fake_list = range(total)
	range_list = list(n_class*[False])
	for c in range(n_class):
		start = last_c
		end = start+nsample_in_classes[c]
		indices =fake_list[start:end]
		last_c += len(indices)
		range_list[c] = (start,end)
	return range_list

def calculateIndexRangesInClassValue(all_codes, n_class, min_val, max_val):
	'''
	Return an index ranage list of (start, end) to create equal value group.
	'''
	values = map((lambda x: int(x.split('@')[0])), all_codes)
	total = len(all_codes)
	range_list = list(n_class*[False])
	# divide into n_class value ranges
	delta_value = (max_val - min_val) / float(n_class)
	last_end = 0
	# in case min_val > values.min()
	for i in range(total):
		if values[i] >= min_val:
			last_end = i
			break
		if i == total-1:
			# nothing in range.
			return range_list
	# populate range_list of the classes
	for c in range(n_class):
		for i in range(total-last_end):
			start = last_end
			j = i + start
			threshold = min_val + (c+1)*delta_value
			if values[j] >= threshold:
				range_list[c] = (start, j)
				last_end = j
				break
			# never exceed threshold
			if j == total-1:
				range_list[c] = (start, total)
				last_end = total
	return range_list

class BlobIndexGrouper(object):
	group_method = 'target count'
	def __init__(self, blobs, n_class, statskey):
		self.blobs = blobs
		self.statskey = self._mapStatsKey(statskey)
		self.n_class = n_class
		self.code_scale = self._getCodeScale()
		self.index_groups = n_class*[]

	def _mapStatsKey(self, statskey):
		if self.blobs:
			valid_keys = self.blobs[0].stats.keys()
			for k in valid_keys:
				if k in (statskey, statskey.lower()):
					return k
			raise ValueError('%s not found as a key in the existing blob.stats' % statskey)

	def _getCodeScale(self):
		if self.statskey != 'score':
			# default scale when values can be classified properly as integers
			return 1
		else:
			# score is 0.0 to 1.0. multiply by 1000 so it can be coded as an integer.
			return 1000

	def groupBlobIndex(self):
		group_key = self.statskey
		blobs = self.blobs
		s = self._getCodeScale()
		group_method = self.group_method
		codes = list(map((lambda x: '%08d@%05d' % (int(s*blobs[x].stats[group_key]),x)), range(len(blobs))))
		codes.sort()
		sorted_indices = list(map((lambda x: int(x.split('@')[-1])), codes))
		if self.n_class == 1:
				self.index_groups = [sorted_indices,]
		range_list = self._getIndexRange(codes)
		# convert range start, end to blob_indices
		blob_index_in_bins = []
		for c in range(self.n_class):
			if range_list[c] is False:
				blob_index_in_bins.append([])
			else:
				start, end = range_list[c]
				blob_index_in_bins.append(sorted_indices[start:end])
		self.index_groups = blob_index_in_bins

class EqualValueDeltaIndexGrouper(BlobIndexGrouper):
	'''
	Group blobs to have equal value delta in each group.
	'''
	group_method = 'value delta'
	def __init__(self, blobs, n_class, statskey):
		super(EqualValueDeltaIndexGrouper,self).__init__(blobs, n_class, statskey)
		self.value_min = None
		self.value_max = None

	def setValueMinMax(self, value_min, value_max):
		self.value_min = value_min * self.code_scale
		self.value_max = value_max * self.code_scale

	def _getIndexRange(self, codes):
		if self.value_min is None or self.value_max is None or self.value_min >= self.value_max:
			raise ValueError('Invalid value range (min, max) (%s, %s)' % (self.value_min, self.value_max))
		return calculateIndexRangesInClassValue(codes, self.n_class, self.value_min, self.value_max)

class EqualCountBlobIndexGrouper(BlobIndexGrouper):
	'''
	Group blobs to have almost equal item counts in each group.
	'''
	group_method = 'target count'
	def _getIndexRange(self, codes):
		total_blobs = len(codes)
		return calculateIndexRangesInClassEvenDistribution(total_blobs, self.n_class)

class BlobSampler(object):
	'''
	Sample blobs already have group assignment. Get the blobs and grouping from
	the Grouper. Group method does affect the sampling algorithm.
	'''
	def __init__(self, grouper_obj, total_targets, logger):
		self.blobs = grouper_obj.blobs
		self.index_groups = grouper_obj.index_groups
		self.statskey = grouper_obj.statskey
		self.group_method = grouper_obj.group_method
		self.logger = logger
		self.n_class = grouper_obj.n_class
		self.total_targets = total_targets

	def _sampling(self, indices, n_class_sample, current_class):
		raise NotImplemented

	def _getNumberOfSamplesInClasses(self, n_item_in_classes):
		'''
		Return a list of number of samples assigned to each of the n_class.
		'''
		# use even distribution algorithm to calculate number of samples in classes
		# This randomize which class has one extra sample to reach total
		range_list = calculateIndexRangesInClassEvenDistribution(self.total_targets, self.n_class)
		# number_of_samples_in_classes
		nsample_in_classes = list(map((lambda x: x[1]-x[0]), range_list))
		if self.group_method == 'value delta':
			# o.k. to have more samples than number of targets in class.
			return nsample_in_classes
		elif self.group_method == 'target count':
			# samples should not be less than number of items available in each class.
			nsample_min = int(math.floor(self.total_targets/float(self.n_class)))
			nsample_max = nsample_min + 1
			n_item_min = min(n_item_in_classes)
			n_item_max = max(n_item_in_classes)
			if n_item_min >= nsample_max:
				# have enough for all classes to be sampled as nsample_in_classes.
				pass
			else:
				# maxim
				for i in range(self.n_class):
					if n_item_in_classes[i] == nsample_min:
						nsample_in_classes[i] = nsample_min
					else:
						nsample_in_classes[i] = nsample_max
			return nsample_in_classes

	def sampleBlobs(self):
		'''
		sampling based on blob stats
		'''
		total_targets_need = self.total_targets
		total_blobs = len(self.blobs)
		if total_blobs <= self.total_targets:
			# Nothing to do
			self.logger.info('Number of filtered blobs (%d) < number of requested targets (%d). Use all.' % (total_blobs, total_targets_need))
			return self.blobs
		n_class = self.n_class
		n_available_in_classes = map((lambda x: len(self.index_groups[x])), range(n_class))
		nsample_in_classes = self._getNumberOfSamplesInClasses(n_available_in_classes)
		# get a list at least as long as total_targets_need
		samples = []
		for c in range(n_class):
			n_sample = nsample_in_classes[c]
			indices = self.index_groups[c]
			if n_sample > len(indices):
				self.logger.info('not enough blobs in group %d: (want %d, has %d)' % (c+1, n_sample, len(indices)))
				sampled_blobs = list(map((lambda x: self.blobs[x]),indices))
			else:
				sampled_blobs = self._sampling(indices, n_sample, c)
			samples.extend(sampled_blobs)
		return samples

class BlobRandomSizeSampler(BlobSampler):
	def _sampling(self, indices, n_sample, current_class):
			'''
			Random Sampling blobs at indices.
			'''
			# random sample without replacement
			picks = random.sample(indices,n_sample)
			return list(map((lambda x: self.blobs[x]),picks))

class BlobTopScoreSampler(BlobSampler):
	def _sampling(self, indices, n_sample, current_class_index):
		if not indices:
			return []
		# use dictionary key sorting to get top scored blobs
		blob_indices_at_score_in_class = {}
		for i in indices:
			score = self.blobs[i].stats['score']
			if score not in blob_indices_at_score_in_class.keys():
				blob_indices_at_score_in_class[score] = []
			blob_indices_at_score_in_class[score].append(i)
		# sort the blobs by score in float
		keys = blob_indices_at_score_in_class.keys()
		keys.sort()
		keys.reverse()
		sample_blobs_in_class = []
		sample_indices = []
		for j, score in enumerate(keys):
			if len(sample_indices) >= n_sample:
					break
			# there may be multiple blobs at the same score
			for i in blob_indices_at_score_in_class[score]:
				sample_blobs_in_class.append(self.blobs[i])
				sample_indices.append(i)
				if len(sample_indices) == n_sample:
					break
		self.logger.info('score range sampled (%d of %d) for group %d: %.3f to %.3f' % (n_sample, len(indices), current_class_index+1, keys[0], keys[j]))
		return sample_blobs_in_class
