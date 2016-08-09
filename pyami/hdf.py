#!/usr/bin/env python

import sys
import h5py
import numpy
import datetime

### EMAN2 spec on HDF5 format:
# http://blake.bcm.edu/emanwiki/Eman2HDF
### H5py specs on Groups
# http://docs.h5py.org/en/latest/high/group.html
# http://docs.h5py.org/en/latest/quick.html#attributes
### Input and output numpy arrays to h5py
# http://stackoverflow.com/questions/20928136/input-and-output-numpy-arrays-to-h5py
### Accessing data range with h5py
# http://stackoverflow.com/questions/15091112/accessing-data-range-with-h5py

"""
HDF5 "refine_05/classes_01_even.hdf" {
GROUP "/" {
	GROUP "MDF" {
		GROUP "images" {
			ATTRIBUTE "imageid_max" {
				DATATYPE  H5T_STD_I32LE
				DATASPACE  SIMPLE { ( 1 ) / ( 1 ) }
				DATA {
				(0): 70
				}
			}
			GROUP "0" {
				ATTRIBUTE "EMAN.apix_x" {
					DATATYPE  H5T_IEEE_F64LE
					DATASPACE  SIMPLE { ( 1 ) / ( 1 ) }
					DATA {
					(0): 2.1
					}
				}
				...  other attributes

				DATASET "image" {
					DATATYPE  H5T_IEEE_F32LE
					DATASPACE  SIMPLE { ( 168, 168 ) / ( 168, 168 ) }
					DATA {
					(0,0): -0.0727458, -0.0415057, -0.040645, -0.0567185,
					(0,4): -0.0407567, -0.0624736, -0.0837779, -0.048533,
					... rest of image

				}
			GROUP "1" {
			...
"""

#----------------------------
#----------------------------
#----------------------------
#----------------------------
class HdfClass(object):
	#----------------------------
	def __init__(self, filename):
		self.filename = filename
		self.apix = 1.0
		pass

	#----------------------------
	def addImageToHdf(self, imagedata, partnum, imagic=False):
		
		print imagedata.shape
		#sys.exit(1)

		#image = mainhdf.create_dataset(str(partnum), data=a)
		imagegroup = self.images.create_group(str(partnum))

		image = imagegroup.create_dataset('image', data=imagedata, shape=imagedata.shape, dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.datatype', 7, shape=(1,), dtype=numpy.int32)
		#FIXME not sure about this one above

		imagegroup.attrs.create('EMAN.HostEndian', numpy.string_(sys.byteorder),)
		imagegroup.attrs.create('EMAN.ImageEndian', numpy.string_(sys.byteorder),)
		imagegroup.attrs.create('EMAN.source_path', numpy.string_(self.filename),)
		#imagegroup.attrs.create('EMAN.ptcl_repr', 1, shape=(1,), dtype=numpy.int32)
		#imagegroup.attrs.create('EMAN.source_n', 1, shape=(1,), dtype=numpy.int32)

		if imagic is True:
			timedata = datetime.datetime.utcnow()
			#datetime.datetime(2016, 8, 9, 15, 38, 25, 228892)
			imagegroup.attrs.create('EMAN.IMAGIC.year', timedata.year, shape=(1,), dtype=numpy.int32)
			imagegroup.attrs.create('EMAN.IMAGIC.month', timedata.month, shape=(1,), dtype=numpy.int32)
			imagegroup.attrs.create('EMAN.IMAGIC.mday', timedata.day, shape=(1,), dtype=numpy.int32)
			imagegroup.attrs.create('EMAN.IMAGIC.hour', timedata.hour, shape=(1,), dtype=numpy.int32)
			imagegroup.attrs.create('EMAN.IMAGIC.minute', timedata.minute, shape=(1,), dtype=numpy.int32)
			imagegroup.attrs.create('EMAN.IMAGIC.sec', timedata.second, shape=(1,), dtype=numpy.int32)

			imagegroup.attrs.create('EMAN.IMAGIC.imgnum', partnum, shape=(1,), dtype=numpy.int32)
			imagegroup.attrs.create('EMAN.IMAGIC.count', self.numpart-1, shape=(1,), dtype=numpy.int32)
			#imagegroup.attrs.create('EMAN.IMAGIC.error', 0, shape=(1,), dtype=numpy.int32) #imagic error code
			#imagegroup.attrs.create('EMAN.IMAGIC.headrec', 1, shape=(1,), dtype=numpy.int32)
	

		imagegroup.attrs.create('EMAN.minimum', imagedata.min(), shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.maximum', imagedata.max(), shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.mean', imagedata.mean(), shape=(1,), dtype=numpy.float32)
		nonzero_mean = imagedata.sum()/(imagedata != 0).sum()
		imagegroup.attrs.create('EMAN.mean_nonzero', nonzero_mean, shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.sigma', imagedata.std(), shape=(1,), dtype=numpy.float32)
		nonzero_sigma = (imagedata != 0).std()
		imagegroup.attrs.create('EMAN.sigma_nonzero', nonzero_sigma, shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.square_sum', (imagedata**2).sum(), shape=(1,), dtype=numpy.float32)

		imagegroup.attrs.create('EMAN.apix_x', self.apix, shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.apix_y', self.apix, shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.apix_z', self.apix, shape=(1,), dtype=numpy.float32)

		#imagegroup.attrs.create('EMAN.euler_alt', 0, shape=(1,), dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.euler_az', 0, shape=(1,), dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.euler_phi', 0, shape=(1,), dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.is_complex', 0, shape=(1,), dtype=numpy.int32)
		#imagegroup.attrs.create('EMAN.is_complex_ri', 1, shape=(1,), dtype=numpy.int32)
		#imagegroup.attrs.create('EMAN.is_complex_x', 0, shape=(1,), dtype=numpy.int32)
		#imagegroup.attrs.create('EMAN.changecount', 0, shape=(1,), dtype=numpy.int32)
		#imagegroup.attrs.create('EMAN.orientation_convention', numpy.string_('EMAN'),)

		imagegroup.attrs.create('EMAN.nx', imagedata.shape[0], shape=(1,), dtype=numpy.int32)
		imagegroup.attrs.create('EMAN.ny', imagedata.shape[1], shape=(1,), dtype=numpy.int32)
		imagegroup.attrs.create('EMAN.nz', 1, shape=(1,), dtype=numpy.int32)
		return

	#----------------------------
	def write(self, a):
		shape = a.shape
		self.dset = h5py.File(self.filename, 'w')
		mdf = self.dset.create_group('MDF')
		self.images = mdf.create_group('images')
		if len(shape) == 2:
			self.numpart = 1
			self.images.attrs.create('imageid_max', self.numpart-1, shape=(1,), dtype=numpy.int32)
			self.addImageToHdf(a, 0)
		elif len(shape) == 3:
			self.numpart = shape[0]
			self.images.attrs.create('imageid_max', self.numpart-1, shape=(1,), dtype=numpy.int32)
			for i in range(self.numpart):
				imagedata = a[i]
				self.addImageToHdf(imagedata, i)
		else:
			raise NotImplementedError('wrong dimension for hdf5 file')
		self.dset.close()
	
	#----------------------------
	def readHeader(self, imagic=False):
		self.dset = h5py.File(self.filename, 'r')
		images = self.dset['MDF']['images']
		numpart = int(images.attrs['imageid_max'])+1
		print "numpart", numpart
		headerTree = range(numpart) #will become list of dicts
		for partnum in range(numpart):
			sys.stderr.write(".")
			partnumstr = str(partnum)
			imagegroup = images[partnumstr]
			attrDict = dict(imagegroup.attrs)
			if imagic is False:
				for key in attrDict.keys():
					if key.startswith('EMAN.IMAGIC'):
						del attrDict[key]
			headerTree[partnum] = attrDict
			if partnum == 0:
				print attrDict
			else:
				break
		self.dset.close()
		return headerTree
	
	#----------------------------
	def read(self):
		self.dset = h5py.File(self.filename, 'r')
		imageDict = self.dset['MDF']['images']
		images = []
		for partnum in imageDict.keys():
			print "----------"
			print partnum
			image = imageDict[partnum]['image']
			imagedata = image[:]
			print imagedata
			images.append(imagedata)
		self.dset.close()
		return numpy.array(images)

#----------------------------
#----------------------------
#----------------------------

if __name__ == '__main__':
	a = numpy.array(numpy.random.random((10,128,128)), dtype=numpy.float32)
	print a

	print "\nwriting random.hdf"
	rhdf = HdfClass('random.hdf')
	rhdf.write(a)

	print "\nreading random.hdf"
	rhdf = HdfClass('random.hdf')
	b = rhdf.read()[0]
	print b
	print a-b

	#sys.exit(1)
	rhdf = HdfClass('random.hdf')
	b = rhdf.readHeader()

	shdf = HdfClass('start.hdf')
	c = shdf.readHeader()
	import pprint
	print "\n\n"
	f = open('val1.txt', 'w')
	pprint.pprint( b[0], f )
	f.close()
	g = open('val2.txt', 'w')
	pprint.pprint( c[0], g )
	g.close()

# h5dump -H start.hdf | head -n 256 > start.header
# ./hdf.py; h5dump -H random.hdf > random.header
# sdiff -daWiB random.header start.header  | colordiff
# e2proc2d.py random.hdf eman.hdf
# sdiff -daWiB val1.txt val2.txt  | colordiff