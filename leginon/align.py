import math
import Mrc
import imagefun
import numarray
import numarray.fft
import numarray.nd_image
import correlator
import peakfinder

def _minmax(coor, minc, maxc):
    if coor[0] < minc[0]:
        minc[0] = coor[0]
    if coor[0] > maxc[0]:
        maxc[0] = coor[0]
    if coor[1] < minc[1]:
        minc[1] = coor[1]
    if coor[1] > maxc[1]:
        maxc[1] = coor[1]
    return minc, maxc

def rotate(input, angle, axes = (-1, -2), reshape = True,
           output_type = None, output = None, order = 3,
           mode = 'constant', cval = 0.0, prefilter = True):
    """Rotate an array.

    The array is rotated in the plane definde by the two axes given
    by the axes parameter using spline interpolation of the requested
    order. The angle is given in degrees. Points outside the
    boundaries of the input are filled according to the given
    mode. The output type can optionally be given. If not given it is
    equal to the input type. If reshape is true, the output shape is
    adapted so that the input array is contained completely in the
    output. Optionally an output array can be provided that must
    match the requested output shape and type. The parameter
    prefilter determines if the input is pre-filtered before
    interpolation, if False it is assumed that the input is already
    filtered.
    """
    input = numarray.asarray(input)
    angle = numarray.pi / 180 * angle
    if axes[0] < axes[1]:
        a1 = axes[0]
        a2 = axes[1]
    else:
        a1 = axes[1]
        a2 = axes[0]
    m11 = math.cos(angle)
    m12 = math.sin(angle)
    m21 = -math.sin(angle)
    m22 = math.cos(angle)
    matrix = numarray.identity(input.rank, type = numarray.Float64)
    matrix[a1, a1] = m11
    matrix[a1, a2] = m12
    matrix[a2, a1] = m21
    matrix[a2, a2] = m22
    oshape = list(input.shape)
    ix = input.shape[a1]
    iy = input.shape[a2]
    if reshape:
        mtrx = [[m11, -m21], [-m12, m22]]
        minc = [0, 0]
        maxc = [0, 0]
        coor = numarray.matrixmultiply(mtrx, [0, ix])
        minc, maxc = _minmax(coor, minc, maxc)
        coor = numarray.matrixmultiply(mtrx, [iy, 0])
        minc, maxc = _minmax(coor, minc, maxc)
        coor = numarray.matrixmultiply(mtrx, [iy, ix])
        minc, maxc = _minmax(coor, minc, maxc)
        oy = int(maxc[0] - minc[0] + 0.5)
        ox = int(maxc[1] - minc[1] + 0.5)
        oshape[a1] = ox
        oshape[a2] = oy
    else:
        ox = oshape[a1]
        oy = oshape[a2]
    offset = numarray.zeros((input.rank,), type = numarray.Float64)
    offset[a1] = float(ox) / 2.0 - 0.5
    offset[a2] = float(oy) / 2.0 - 0.5
    offset = numarray.matrixmultiply(matrix, offset)
    tmp = numarray.zeros((input.rank,), type = numarray.Float64)
    tmp[a1] = float(ix) / 2.0 - 0.5
    tmp[a2] = float(iy) / 2.0 - 0.5
    offset = tmp - offset
    #return affine_transform(input, matrix, offset, oshape, output_type,
    return numarray.nd_image.affine_transform(input, matrix, offset, oshape, output_type,
                            output, order, mode, cval, prefilter)

def normalize(image):
	r = imagefun.minmax(image)
	return (image - r[0])/r[1]

def findRotation(image1, image2):
	ac1 = imagefun.auto_correlate(image1)
	ac2 = imagefun.auto_correlate(image2)
	ac1 = imagefun.swap_quadrants(ac1)
	ac2 = imagefun.swap_quadrants(ac2)

	thetas = numarray.zeros((2, 180))
	for i in range(thetas.shape[1]):
		theta = math.radians(i)
		sintheta = math.sin(theta)
		costheta = math.cos(theta)
		for rho in range(ac1.shape[1]/8, ac1.shape[1]/2):
			row = int(round(ac1.shape[0]/2.0 + rho*sintheta))
			column = int(round(ac1.shape[1]/2.0 + rho*costheta))
			thetas[0, i] += ac1[row, column]
		for rho in range(ac2.shape[1]/8, ac2.shape[1]/2):
			row = int(round(ac2.shape[0]/2.0 + rho*sintheta))
			column = int(round(ac2.shape[1]/2.0 + rho*costheta))
			thetas[1, i] += ac2[row, column]

	ft1 = numarray.fft.real_fft(thetas[0])
	ft2 = numarray.fft.real_fft(thetas[1])
	xc = numarray.multiply(ft2.conjugate(), ft1)
	xc = numarray.fft.inverse_real_fft(xc)
	theta = numarray.argmax(numarray.absolute(xc))

	theta = theta % 90
	if theta > 45:
		theta -= 90

	return theta

def padAndRotate(image1, image2, theta):

	rotated = rotate(image2, -theta)

	shape = (max(rotated.shape[0], image1.shape[0])*2,
						max(rotated.shape[1], image1.shape[1])*2)
	i1 = numarray.zeros(shape, numarray.Float32)
	i2 = numarray.zeros(shape, numarray.Float32)
	i1[(i1.shape[0] - image1.shape[0])/2:
			(i1.shape[0] - image1.shape[0])/2 + image1.shape[0],
			(i1.shape[1] - image1.shape[1])/2:
			(i1.shape[1] - image1.shape[1])/2 + image1.shape[1]] = image1
	i2[(i2.shape[0] - rotated.shape[0])/2:
			(i2.shape[0] - rotated.shape[0])/2 + rotated.shape[0],
			(i2.shape[1] - rotated.shape[1])/2:
			(i2.shape[1] - rotated.shape[1])/2 + rotated.shape[1]] = rotated

	return i1, i2

def correlate(image1, image2):
	c = correlator.Correlator()
	p = peakfinder.PeakFinder()

	c.insertImage(image1)
	c.insertImage(image2)
	correlation = c.phaseCorrelate()

	p.setImage(correlation)
	p.pixelPeak()
	results = p.getResults()

	return correlator.wrap_coord(results['pixel peak'], correlation.shape)

def shiftImage(image1, image2, shift):
	shape = (image2.shape[0] + abs(shift[0]), image2.shape[1] + abs(shift[1]))
	offset1 = [0, 0]
	offset2 = [0, 0]
	if shift[0] > 0:
		offset1[0] = shift[0]
	else:
		offset2[0] = -shift[0]
	if shift[1] > 0:
		offset1[1] = shift[1]
	else:
		offset2[1] = -shift[1]
	image = numarray.zeros(shape, numarray.Float32)
	image[offset1[0]:offset1[0] + image1.shape[0],
				offset1[1]:offset1[1] + image1.shape[1]] += image1
	image[offset2[0]:offset2[0] + image2.shape[0],
				offset2[1]:offset2[1] + image2.shape[1]] += image2
	return image

for i in range(16):
#for i in [0]:
	#for j in range(9):
	for j in [4]:
		f1 = '04dec17b_000%d_0000%dgr.mrc' % (749 + i, j + 1)
		f2 = '05jan20a_000%d_0000%dgr.mrc' % (749 + i, j + 1)

		image1 = Mrc.mrc_to_numeric(f1)
		image2 = Mrc.mrc_to_numeric(f2)

		image1 = normalize(image1)
		image2 = normalize(image2)

		theta = findRotation(image1, image2)
		image1, image2 = padAndRotate(image1, image2, theta)
		shift = correlate(image1, image2)

		image = shiftImage(image1, image2, shift)
		Mrc.numeric_to_mrc(image, '%d_%d.mrc' % (749 + i, j + 1))
		print 'grid ID %d, image %d: rotation %d degrees, shift %s pixels' % (749 + i, j + 1, theta, shift)

