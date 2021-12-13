#!/usr/bin/env python
"""
Collection of functions to help group items in a list.
"""
import math

def calculateIndexRangesInClassEvenDistribution(total, n_class):
	'''
	Return a index range list of (start, end) to create a most evenly
	distributed classes from a list with given total count.
	total: number of items in the list to be divided.
	n_class: number of classes/groups to divide into.
	'''
	sampling_order = range(n_class)*int(math.ceil(total/float(n_class)))
	# truncate the list. This helps even distribution and garantee total number
	# is correct.
	sampling_order = sampling_order[:total]
	# number_of_samples_in_classes
	nsample_in_classes = map((lambda x: sampling_order.count(x)), range(n_class))
	last_c = 0
	fake_list = range(total)
	range_list = []
	for c in range(n_class):
		start = last_c
		end = start+nsample_in_classes[c]
		indices =fake_list[start:end]
		last_c += len(indices)
		range_list.append((start,end))
	return range_list
