import Numeric
import FFT

#def correlation(image1, image2, ccflag=True, pcflag=True, subpixelflag=True):
def correlation(image1, image2, ccflag=1, pcflag=1, subpixelflag=1):

	val = {}

	if not (ccflag or pcflag):
		return val

	dim = (len(image1), len(image1[0]))
	if dim != (len(image2), len(image2[0])):
		raise ValueError

	center = (dim[0]/2, dim[1]/2)
	
	# FFT of the two images
	ffts = (FFT.real_fft2d(image1), FFT.real_fft2d(image2))

	# create cross-correlation matrix w/same size
	ccfft = Numeric.zeros((len(ffts[0]), len(ffts[0][0]))).astype(Numeric.Complex)

	# elementwise cross-correlation = conjugate(ffts[0]) * ffts[1]
	Numeric.multiply(Numeric.conjugate(ffts[0]), ffts[1], ccfft)

	if ccflag:
		# invert correllation to use
		uncenteredcc = FFT.inverse_real_fft2d(ccfft)

		cc = Numeric.zeros(dim, Numeric.Float)

		cc[center[0]:, center[1]:] = uncenteredcc[:center[0], :center[1]]
		cc[:center[0], :center[1]] = uncenteredcc[center[0]:, center[1]:]
		cc[center[0]:, :center[1]] = uncenteredcc[:center[0], center[1]:]
		cc[:center[0], center[1]:] = uncenteredcc[center[0]:, :center[1]]

		print "cc =", cc

		if subpixelflag:
			peak = quadraticPeak(cc)
			val['cross correlation peak'] = peak
			val['cross correlation shift'] = (peak[0] - center[0] - 0.5, \
																				peak[1] - center[1] - 0.5)
		else:
			peak = matrixMax(cc)
			val['cross correlation peak'] = peak
			val['cross correlation shift'] = (peak[0] - center[0], \
																				peak[1] - center[1])

	if pcflag:
		pcfft = Numeric.zeros((len(ffts[0]), \
			len(ffts[0][0]))).astype(Numeric.Complex)

		# elementwise phase-correlation =
		# cross-correlation / magnitude(cross-correlation
		Numeric.divide(ccfft, Numeric.sqrt(Numeric.multiply(Numeric.add(ffts[0], \
			ffts[1]), Numeric.conjugate(Numeric.add(ffts[0], ffts[1])))), pcfft)

		uncenteredpc = FFT.inverse_real_fft2d(pcfft)

		pc = Numeric.zeros(dim, Numeric.Float)

		pc[center[0]:, center[1]:] = uncenteredpc[:center[0], :center[1]]
		pc[:center[0], :center[1]] = uncenteredpc[center[0]:, center[1]:]
		pc[center[0]:, :center[1]] = uncenteredpc[:center[0], center[1]:]
		pc[:center[0], center[1]:] = uncenteredpc[center[0]:, :center[1]]

		print "pc =", pc

		if subpixelflag:
			peak = quadraticPeak(pc)
			val['phase correlation peak'] = peak
			val['phase correlation shift'] = (peak[0] - center[0] - 0.5, \
																				peak[1] - center[1] - 0.5)
		else:
			peak = matrixMax(pc)
			val['phase correlation peak'] = peak
			val['phase correlation shift'] = (peak[0] - center[0], \
																				peak[1] - center[1])

	return val

def matrixMax(m):
	maxval = 0.
	maxindex = (0, 0)
	for rowindex in xrange(len(m)):
		rowmaxval = max(m[rowindex])
		if rowmaxval > maxval:
			maxval = rowmaxval
			maxindex = (rowindex, m[rowindex].tolist().index(maxval))
	return maxindex

def quadraticPeak(m):
	from Scientific.Functions.LeastSquares import polynomialLeastSquaresFit

	peak = matrixMax(m)
	if (peak[0] == 0) or (peak[0] == len(m) - 1):
		raise ValueError
	if (peak[1] == 0) or (peak[1] == len(m[0]) - 1):
		raise ValueError

	fcolumn = polynomialLeastSquaresFit((0., 0., 0.),
		[(-1, m[peak[0] - 1][peak[1]]),
			(0, m[peak[0]][peak[1]]),
			(1, m[peak[0] + 1][peak[1]])])

	column = fcolumn[0][1] / 2*fcolumn[0][2]

	frow = polynomialLeastSquaresFit((0., 0., 0.),
		[(-1, m[peak[0]][peak[1] - 1]),
			(0, m[peak[0]][peak[1]]),
			(1, m[peak[0]][peak[1] + 1])])

	row = frow[0][1] / 2*frow[0][2]

	npeak = (peak[0] + 0.5 + row, peak[1] + 0.5 + column)

	return npeak

