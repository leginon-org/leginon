import Numeric
import FFT

#def correlation(image1, image2, ccflag=True, pcflag=True, subpixelflag=True):
def correlation(image1, image2, ccflag=1, pcflag=1, subpixelflag=1):
	val = {}

	if not (ccflag or pcflag):
		return val

	if image1.shape != image2.shape:
		raise ValueError('images not same dimensions')

	
	# FFT of the two images
	ffts = (FFT.real_fft2d(image1), FFT.real_fft2d(image2))

	# create cross-correlation matrix w/same size
	ccfft = Numeric.zeros((len(ffts[0]), len(ffts[0][0]))).astype(Numeric.Complex)

	# elementwise cross-correlation = conjugate(ffts[0]) * ffts[1]
	Numeric.multiply(Numeric.conjugate(ffts[0]), ffts[1], ccfft)

	wraplimit = (image1.shape[0]/2, image1.shape[1]/2)

	## if fitting quadratic to peak, use this many pixels in each direction
	npix = 9

	if ccflag:
		# invert correlation to use
		cc = FFT.inverse_real_fft2d(ccfft)

		try:
			if subpixelflag:
				peak = quadraticPeak(cc, npix)
			else:
				peak = matrixMax(cc)
			val['cross correlation peak'] = peak

			# if peak is past halfway, shift is negative, wrap
			val['cross correlation shift'] = []
			for dim in (0,1):
				if peak[dim] < wraplimit[dim]:
					wrapped = peak[dim]
				else:
					wrapped = peak[dim] - image1.shape[dim]
				val['cross correlation shift'].append(wrapped)
		except:
			val['cross correlation peak'] = None
			val['cross correlation shift'] = None
			print 'error finding peak'

		val['cross correlation image'] = cc

	if pcflag:
		pcfft = Numeric.zeros((len(ffts[0]), \
			len(ffts[0][0]))).astype(Numeric.Complex)

		# elementwise phase-correlation =
		# cross-correlation / magnitude(cross-correlation
		Numeric.divide(ccfft, Numeric.sqrt(Numeric.multiply(Numeric.add(ffts[0], \
			ffts[1]), Numeric.conjugate(Numeric.add(ffts[0], ffts[1])))), pcfft)

		pc = FFT.inverse_real_fft2d(pcfft)

		try:
			if subpixelflag:
				peak = quadraticPeak(pc, npix)
			else:
				peak = matrixMax(pc)
			val['phase correlation peak'] = peak

			# if peak is past halfway, shift is negative, wrap
			val['phase correlation shift'] = []
			for dim in (0,1):
				if peak[dim] < wraplimit[dim]:
					wrapped = peak[dim]
				else:
					wrapped = peak[dim] - image1.shape[dim]
				val['phase correlation shift'].append(wrapped)
		except:
			val['phase correlation peak'] = None
			val['phase correlation shift'] = None
			print 'error finding peak'
		val['phase correlation image'] = pc

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

def quadraticPeak(m, npix):
	from LinearAlgebra import linear_least_squares

	## find the max pixel indices (row,col)
	peakrow,peakcol = matrixMax(m)

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
	print 'ROWFIT', rowfit
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
	print 'COLFIT', colfit
	colcoeffs = colfit[0]
	colzero = -colcoeffs[1] / 2 / colcoeffs[2]

	return (rowzero, colzero)
