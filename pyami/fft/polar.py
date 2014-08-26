#!/usr/bin/env python
'''
Functions to do polar transform on FFT image
'''

import numpy
import scipy.ndimage
import pyami.mrc

def bin(input, nbins_r, nbins_t):
	'''
Polar binning of a power spectrum.
input: a FFT or power spectrum shaped and ordered like the output from
fft.calculator.forward or fft.calculator.power
nbins_r: number of radial bins.
nbins_t: the number of angular bins.
Returns:  (bins, r_centers, t_centers)
     where:
          bins: result 2-D image with r on the first axis, t on the second axis
          r_centers: The sequence of radial values represented in the bins
          t_centers: The sequence of angular values represented in the bins
	'''

	## Full radial range (result will have empty bins):
	#r_min = 0.0
	#r_max = numpy.hypot(input.shape[0] / 2.0, input.shape[1])

	## Trim off the low radial end where some bins are empty
	## Trim off the high radial end where some angles go off the input image
	r_min = 0.02 * input.shape[1]
	r_max = max(input.shape[0] / 2.0, input.shape[1])

	r_bins,r_inc = numpy.linspace(r_min, r_max, num=nbins_r+1, retstep=True)
	r_centers = r_bins[1:] - r_inc/2.0

	## Full angular range from -pi/2 to pi/2
	t_min = -numpy.pi / 2.0
	t_max = numpy.pi / 2.0
	t_bins,t_inc = numpy.linspace(t_min, t_max, num=nbins_t+1, retstep=True)
	t_centers = t_bins[1:] - t_inc/2.0

	## Determine coordinates on the strange FFT result layout
	indices = numpy.indices(input.shape)
	begin_split_row = (input.shape[0]+1) / 2 # integer division intended
	# bottom half of FFT rows are actually the "negative" rows.
	indices[0][begin_split_row:] -= input.shape[0]

	## Determine r,theta polar coords of each row,column coord.
	r_indices = numpy.hypot(*indices)
	t_indices = numpy.arctan2(*indices)

	## split up image into bins by radius and angle
	r_labels = numpy.digitize(r_indices.flat, r_bins) - 1
	r_labels.shape = r_indices.shape
	t_labels = numpy.digitize(t_indices.flat, t_bins) - 1
	t_labels.shape = t_indices.shape

	## combine r_labels and t_labels into full set of labels:
	rt_labels = nbins_t * r_labels + t_labels + 1

	## calculate mean value of each bin
	rt_bins = scipy.ndimage.mean(input, rt_labels, numpy.arange(nbins_r*nbins_t)+1)
	## TODO:  
	## If any empty bins (like near r=0), fill them in with interpolated value
	## For now we are trying to ignore them by cutting off lower radial range
	## (see first few lines of this function)

	## turn result into 2-D array
	rt_bins = numpy.asarray(rt_bins)
	rt_bins.shape = nbins_r, nbins_t

	return rt_bins, r_centers, t_centers

def test():
	import pyami.mrc
	import pyami.fft
	import numpy
	# bad one
	#filename = '/ami/data00/leginon/11mar21a/rawdata/11mar21a_00061ma_1.mrc'
	filename = '/ami/data00/leginon/11mar21a/rawdata/11mar21a_00043fc.mrc'
	a = pyami.mrc.read(filename)
	#a = a[1:]
	f = pyami.fft.calculator.power(a)
	fabs = numpy.absolute(f)
	pyami.mrc.write(fabs, 'fabs.mrc')

	nr = 80  # number of radial bins
	nt = 8    # number of angular bins (set to 1 for full radial average)

	pbin, r_centers, t_centers = bin(fabs, nr, nt)

	## make an array with column labels and radii for CVS output
	final = numpy.zeros((nr+1, nt+1), dtype=numpy.float32)
	final[0,1:] = t_centers
	final[1:,0] = r_centers
	final[1:,1:] = pbin

	## floating point formatting needs help here
	## To get openoffice calc to import this CVS, you have to select
	## "Detect special numbers" in the text import dialog
	numpy.savetxt('final.csv', final, fmt="%1.4e", delimiter=',')

if __name__ == '__main__':
	test()
