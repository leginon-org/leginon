#!/usr/bin/env python

import numpy
import scipy.ndimage
from pyami import mrc

if __name__ == "__main__":
	## using scipy.ndimage to find blobs
	labelstruct = numpy.ones((3,3,3))
	def scipyblobs(im,mask):
		labels,n = scipy.ndimage.label(mask, labelstruct)
		## too bad ndimage module is inconsistent with what is returned from
		## the following functions.  Sometiems a list, sometimes a single value...
		if n==0:
			centers = []
			sizes = []
			stds = []
			means = []
		else:
			centers = scipy.ndimage.center_of_mass(im,labels,range(1,n+1))
			sizes = scipy.ndimage.histogram(labels,1,n+1,n)
			stds = scipy.ndimage.standard_deviation(im,labels,range(1,n+1))
			means = scipy.ndimage.mean(im,labels,range(1,n+1))
			if n==1:
				centers = [centers]
				stds = [stds]
				means = [means]
			else:
				centers = map(numpy.array, centers)

		blobs = []
		for i in range(n):
			blobs.append({'center':centers[i], 'n':sizes[i], 'mean':means[i],'stddev':stds[i]})
		return blobs

	# input parameters
	scale_factor = 60.0 #scale the map so that the we can pretend the atom sphere as a gold bead
	threshold = -6172+float((14509+6172)*(170))/256 #map intensity threshold to generate blobs
	minsize = 5 #minimal blob size to be considered as a gold cluster
	# end of input variables

	input1 = raw_input('Enter the .mrc for pdb conversion: ') 
	image = mrc.read(input1)
	output1 = raw_input('Enter the destination name: ')
	out = open(output1,'w')
	line = "HEADER " + output1 + "\n"
	out.write(line)
	shape = image.shape
	print shape

	scale = float(scale_factor)/min(shape)
	lattice = [shape[0]*scale,shape[1]*scale,shape[2]*scale]

	lattice.extend([90.0,90.0,90.0])
	# lattice parameter and transformation output in pdb format
	line = "CRYST1%9.3f%9.3f%9.3f%7.2f%7.2f%7.2f  P 1        1\n" %tuple(lattice)
	line += "ORIGX1%10.6f%10.6f%10.6f%10.5f\n" %(1.0,0.0,0.0,0.0)
	line += "ORIGX2%10.6f%10.6f%10.6f%10.5f\n" %(0.0,1.0,0.0,0.0)
	line += "ORIGX3%10.6f%10.6f%10.6f%10.5f\n" %(0.0,0.0,1.0,0.0)
	line += "SCALE1%10.6f%10.6f%10.6f%10.5f\n" %(1.0/shape[0],0.0,0.0,0.0)
	line += "SCALE2%10.6f%10.6f%10.6f%10.5f\n" %(0.0,1.0/shape[1],0.0,0.0)
	line += "SCALE3%10.6f%10.6f%10.6f%10.5f\n" %(0.0,0.0,1.0/shape[2],0.0)
	out.write(line)

	maskimg = numpy.where(image>=threshold,1,0)
	blobs = scipyblobs(image,maskimg)
	print "total blobs of any size=",len(blobs)
	i = 0
	if len(blobs) > 1:
		for blob in blobs:
			if blob['n'] > minsize:
				i = i+1
				center = blob['center']*scale
				# this line output each blob center as a Chloride ion in pdb format
				line = "HETATM%5d  CL   CL  %4d%12.3f%8.3f%8.3f  1.00  0.00           AU\n" %(i,i,center[0],center[1],center[2])
				out.write(line)
		out.write('END\n')
		out.close()
		print i
	else:
		print blobs
		print "too few blobs"
