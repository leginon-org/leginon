#!/usr/bin/env python
###########################################################
###########################################################
#### NOTE:  this has been replaced by correlator.py and peakfinder.py
###########################################################
###########################################################

import Numeric
import fftengine

## create a fft engine for the cross correlations
## turning off estimate will optimize, but planning takes longer
#planshapes = ((512,512),)
#fftfftw = fftengine.fftFFTW(planshapes, estimate=1)
fftnumeric = fftengine.fftNumeric()

#def correlation(image1, image2, ccflag=True, pcflag=True, subpixelflag=True):
def correlation(image1, image2, ccflag=1, pcflag=1, subpixelflag=1, ffteng=fftnumeric):
	val = {}

	if not (ccflag or pcflag):
		return val

	if image1.shape != image2.shape:
		raise ValueError('images not same dimensions')
	
	# FFT of the two images
	ffts = (ffteng.transform(image1), ffteng.transform(image2))
	print 'ffts shape'
	print ffts[0].shape
	print 'ffts'
	#print ffts[0]

	# elementwise cross-correlation = conjugate(ffts[0]) * ffts[1]
	ccfft = Numeric.multiply(Numeric.conjugate(ffts[0]), ffts[1])

	if ccflag:
		# invert correlation to use
		cc = ffteng.itransform(ccfft)
		print 'CC SHAPE', cc.shape

		ccdict = findPeak(cc, subpixelflag)
		val['cross correlation peak'] = ccdict['peak']
		val['cross correlation shift'] = ccdict['shift']
		val['cross correlation image'] = cc

	if pcflag:
		# elementwise phase-correlation =
		# cross-correlation / magnitude(cross-correlation

		ab = Numeric.absolute(ccfft)

		print 'ccfft type', ccfft.typecode()
		print 'ccfft shape', ccfft.shape
		print 'ab type', ab.typecode()
		print 'ab shape', ab.shape
		#print ab

		pcfft = ccfft / ab
		#print pcfft

		pc = ffteng.itransform(pcfft)

		pcdict = findPeak(pc, subpixelflag)
		val['phase correlation peak'] = pcdict['peak']
		val['phase correlation shift'] = pcdict['shift']
		val['phase correlation index'] = findPeak(pc, 0)['peak']
		val['phase correlation image'] = pc

	return val

def findPeak(image, subpixelflag):
	wraplimit = (image.shape[0]/2, image.shape[1]/2)
	val = {}
	try:
		if subpixelflag:
			print 'image shape', image.shape
			peak = quadraticPeak(image)
		else:
			peak = matrixMax(image)
		val['peak'] = peak

		# if peak is past halfway, shift is negative, wrap
		val['shift'] = []
		for dim in (0,1):
			if peak[dim] < wraplimit[dim]:
				wrapped = peak[dim]
			else:
				wrapped = peak[dim] - image.shape[dim]
			val['shift'].append(wrapped)
	except:
		val['peak'] = ()
		val['shift'] = ()
		print 'error finding peak'
	return val

def matrixMax(m):
	maxval = 0
	peak = None
	ind = 0
	for val in m.flat:
		if val > maxval:
			maxval = val
			peak = ind
		ind += 1
	if peak is None:
		raise RuntimeError('no peak in matrix')
	# convert 1-d index to 2-d index
	rows,cols = m.shape
	peakrow = peak / rows
	peakcol = peak % rows
	return peakrow, peakcol

def wrap(value, range):
	if value < 0:
		return range + value
	else:
		return value

def quadraticPeak(m):
	from LinearAlgebra import linear_least_squares

	## if fitting quadratic to peak, use this many pixels in each direction
	npix = 9

	## find the max pixel indices (row,col)
	peakrow,peakcol = matrixMax(m)
	print 'SINGLE PIXEL PEAK', peakrow, peakcol

	rows,cols = m.shape

	rowrange = (peakrow-npix/2, peakrow+npix/2+1)
	rowinds = Numeric.arrayrange(rowrange[0], rowrange[1])
	## fill in rowvals, wrap around array if necessary
	rowvals = []
	for row in rowinds:
		if row < 0:
			rowvals.append(m[rows + row, peakcol])
		elif row >= rows:
			rowvals.append(m[row - rows, peakcol])
		else:
			rowvals.append(m[row, peakcol])
	rowvals = Numeric.array(rowvals)

	colrange = (peakcol-npix/2, peakcol+npix/2+1)
	colinds = Numeric.arrayrange(colrange[0], colrange[1])
	## fill in colvals, wrap around array if necessary
	colvals = []
	for col in colinds:
		if col < 0:
			colvals.append(m[peakrow, cols + col])
		elif col >= cols:
			colvals.append(m[peakrow, col - cols])
		else:
			colvals.append(m[peakrow, col])
	colvals = Numeric.array(colvals)

	## create quadratic design matrix for row data
	row_dm = Numeric.zeros(npix * 3, Numeric.Float)
	row_dm.shape = (npix, 3)
	i = 0
	for row in rowinds:
		row_dm[i] = (1.0, row, row*row)
		i += 1

	## fit and find zero
	rowfit = linear_least_squares(row_dm, rowvals)
	rowcoeffs = rowfit[0]
	rowzero = -rowcoeffs[1] / 2 / rowcoeffs[2]

	## create quadratic design matrix for col data
	col_dm = Numeric.zeros(npix * 3, Numeric.Float)
	col_dm.shape = (npix, 3)
	i = 0
	for col in colinds:
		col_dm[i] = (1.0 ,col, col*col)
		i += 1

	## fit and find zero
	colfit = linear_least_squares(col_dm, colvals)
	colcoeffs = colfit[0]
	colzero = -colcoeffs[1] / 2 / colcoeffs[2]

	return (rowzero, colzero)

if __name__ == '__main__':
	from mrc.Mrc import mrc_to_numeric, numeric_to_mrc
	im1 = mrc_to_numeric('test1.mrc')
	im2 = mrc_to_numeric('test2.mrc')
	#im1 = mrc_to_numeric('small.mrc')
	#im2 = mrc_to_numeric('small.mrc')
	#im1 = im1[:4,:4]
	#im2 = im2[:4,:4]

	c = correlation(im1, im2, 0, 1, 1)
	print 'peak', c['phase correlation peak']
	print 'shift', c['phase correlation shift']
	im = c['phase correlation image']
	numeric_to_mrc(im, 'phasecor.mrc')
