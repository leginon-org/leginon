import math
import Mrc
import imagefun
import numarray
import numarray.fft
import numarray.nd_image
import correlator
import peakfinder

def findRotation(image1, image2):
	ac1 = imagefun.auto_correlate(image1)
	ac2 = imagefun.auto_correlate(image2)
	ac1 = imagefun.swap_quadrants(ac1)
	ac2 = imagefun.swap_quadrants(ac2)
	thetas = numarray.zeros(ac1.shape[1]/2)
	for rho in range(ac1.shape[1]/2):
		a = 360
		theta1 = numarray.zeros(a, numarray.Float32)
		theta2 = numarray.zeros(a, numarray.Float32)
		for theta in range(a):
			row = ac1.shape[0]/2.0 + rho*math.sin(math.radians(theta/2))
			column = ac1.shape[1]/2.0 + rho*math.cos(math.radians(theta/2))
			theta1[theta] = ac1[int(round(row)), int(round(column))]
			theta2[theta] = ac2[int(round(row)), int(round(column))]
		ft1 = numarray.fft.real_fft(theta1)
		ft2 = numarray.fft.real_fft(theta2)
		xc = numarray.multiply(ft2.conjugate(), ft1)
		xc = numarray.fft.inverse_real_fft(xc)
		thetas[rho] = numarray.argmax(numarray.absolute(xc))/2
	return filterMean(thetas)

def filterMean(values):
	m = values.mean()
	s = values.stddev()
	t = []
	for value in values:
		if value <= m + s and value >= m - s:
			t.append(value)
	return numarray.array(t).mean()

c = correlator.Correlator()
p = peakfinder.PeakFinder()

def info(image1, image2):
	theta = findRotation(image1, image2)
	theta = theta % 90
	if theta > 45:
		theta -= 90

	r1 = numarray.nd_image.rotate(image2, -theta, reshape=False)

	n = (int(image1.shape[0]/(2*math.sqrt(2))),
				int(image1.shape[1]/(2*math.sqrt(2))))

	c.insertImage(image1[n[0]:-n[0], n[1]:-n[1]])
	c.insertImage(r1[n[0]:-n[0], n[1]:-n[1]])
	xc = c.crossCorrelate()
	p.setImage(xc)
	p.subpixelPeak(npix=9)
	results = p.getResults()
	shift = correlator.wrap_coord(results['subpixel peak'], xc.shape)
	pv = results['pixel peak value']
	print '%s %g %g (%g, %g)' % ((f1[9:], theta, pv) + shift)

	return image1[n[0]:-n[0], n[1]:-n[1]], r1[n[0]:-n[0], n[1]:-n[1]]

for i in range(16):
	for j in range(9):
		f1 = '04dec17b_000%d_0000%dgr.mrc' % (749 + i, j + 1)
		f2 = '05jan20a_000%d_0000%dgr.mrc' % (749 + i, j + 1)
		image1 = Mrc.mrc_to_numeric(f1)
		image2 = Mrc.mrc_to_numeric(f2)
		r1, r2 = info(image1, image2)
		info(r1, r2)

