#!/usr/bin/env python
import Numeric
import imagefun
import convolver
import Mrc

lpf = convolver.Convolver(kernel=convolver.gaussian_kernel(5,1.4))

class SquareFinder(object):
	def __init__(self):
		self.convolver = convolver.Convolver()

	def lowPassFilter(self, lpn, lpsig, image):
		kernel = convolver.gaussian_kernel(lpn, lpsig)
		self.convolver.setKernel(kernel)
		return self.convolver.convolve(image=image)

	def threshold(self, image):
		min = imagefun.min(image)
		max = imagefun.max(image)
		cutoff = (max - min) / 10.0
		return imagefun.threshold(image, cutoff)

	def findblobs(self, image, mask, border, maxblobs, maxblobsize):
		blobs = imagefun.find_blobs(image, mask, border, maxblobs, maxblobsize) 
		centers = []
		for blob in blobs:
			center = tuple(blob.stats['center'])
			centers.append((center[1], center[0]))
		return centers

'''
def save_mrc(image, filename):
	Mrc.numeric_to_mrc(image, filename)

class Blob(object):
	def __init__(self):
		self.pixels = []
		self.captives = {}
		self.eaten = False
		self.stats = {}

	def add_point(self, row, col):
		self.pixels.append((row,col))

	def capture(self, other):
		self.captives[other] = None

	def eat(self):
		for other in self.captives:
			other.eat()
			self.pixels.extend(other.pixels)
			other.eaten = True

	def calc_stats(self):
		if self.stats:
			return
		pixel_array = Numeric.array(self.pixels, Numeric.Float32)
		sum = Numeric.sum(pixel_array)
		squares = pixel_array**2
		sumsquares = Numeric.sum(squares)
		n = len(pixel_array)
		self.stats['n'] = n

		## center
		self.stats['center'] = sum / n

		## size
		if n > 1:
			tmp1 = n * sumsquares - sum * sum
			tmp2 = (n - 1) * n
			self.stats['size'] = Numeric.sqrt(tmp1 / tmp2)
		else:
			self.stats['size'] = Numeric.zeros((2,),Numeric.Float32)

		## need to calculate value list here
		# this is fake:
		self.value_list = [2]

		value_array = Numeric.array(self.value_list, Numeric.Float32)
		valuesum = Numeric.sum(value_array)
		valuesquares = value_array ** 2
		sumvaluesquares = Numeric.sum(valuesquares)

		## mean pixel value
		self.stats['mean'] = valuesum / n

		## stddev pixel value
		if n > 1:
			tmp1 = n * sumvaluesquares - valuesum * valuesum
			if tmp1 < 0:
				tmp1 = 0.0
			self.stats['stddev'] = float(Numeric.sqrt(tmp1 / tmp2))
		else:
			self.stats['stddev'] = 0.0

	def print_stats(self):
		for stat in ('n', 'center', 'size', 'mean', 'stddev'):
			print '\t%s:\t%s' % (stat, self.stats[stat])


neighbor_rows = Numeric.array((-1,-1,-1,0), Numeric.Int)
neighbor_cols = Numeric.array((-1,0,1,-1), Numeric.Int)

def find_blobs(input, border=0):
	shape = input.shape
	blobs = []

	## zero out tmpmask outside of border
	if border:
		input[:border] = 0
		input[-border:] = 0
		input[:,:border] = 0
		input[:,-border:] = 0

	## create a label map
	labelmap = Numeric.zeros(shape, Numeric.UInt16)

	## labeling loop
	for row in range(border,shape[0]-border):
		nrows = neighbor_rows + row
		for col in range(border,shape[1]-border):
			ncols = neighbor_cols + col
			if input[row,col]:
				## check neighbors for labels
				neighbor_labels = {}
				done_neighbors = zip(nrows,ncols)
				for neighbor in done_neighbors:
					neighbor_label = int(labelmap[neighbor])
					if neighbor_label:
						neighbor_labels[neighbor_label] = None

				if neighbor_labels:
					mylabel,none = neighbor_labels.popitem()
					myblob = blobs[mylabel-1]
					for label in neighbor_labels:
						myblob.capture(blobs[label-1])
				else:
					myblob = Blob()
					blobs.append(myblob)
					mylabel = len(blobs)
					myblob.label = mylabel
				myblob.add_point(row,col)
				labelmap[row,col] = mylabel

	print 'Found %s blobs before merge' % (len(blobs),)
	for i in range(20):
		print 'BLOB %s' % (id(blobs[i]),), blobs[i].label
		print '	CAPTURED', map(id, blobs[i].captives)
	for blob in blobs:
		if blob.eaten:
			continue
		blob.eat()

	final_blobs = list(blobs)
	for blob in blobs:
		if blob.eaten:
			final_blobs.remove(blob)
	print 'Found %s blobs.' % (len(final_blobs),)
	return final_blobs


def find_squares(input):
	## low pass filter
	print 'low pass filter'
	smoothed = lpf.convolve(image=input)
	save_mrc(smoothed, 'smoothed.mrc')

	## threshold
	print 'thresholding'
	min = imagefun.min(smoothed)
	max = imagefun.max(smoothed)
	cutoff = (max - min) / 10.0
	mask = imagefun.threshold(smoothed, cutoff)
	save_mrc(mask, 'mask.mrc')

	## find blobs
	print 'finding blobs'
	blobs = find_blobs(mask, border=2)

	marked = Numeric.array(input)
	centers = []
	for blob in blobs:
		blob.calc_stats()
		center = blob.stats['center']
		centers.append(center)
		imagefun.mark_image(marked, center, max)
	save_mrc(marked, 'marked.mrc')

	return centers

if __name__ == '__main__':
	import Mrc
	im = Mrc.mrc_to_numeric('testsquarefinder.mrc')
	squares = find_squares(im)
	print 'Square Centers'
	print squares
'''

