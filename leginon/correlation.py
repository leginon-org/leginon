import Numeric
import FFT

def correlation(image1, image2, ccflag = True, pcflag = True):

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

		val['cross correlation'] = cc

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

		val['phase correlation'] = pc

	return val

