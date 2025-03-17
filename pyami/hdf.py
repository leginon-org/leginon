#!/usr/bin/env python

import os
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
class HdfFile(object):
	#----------------------------
	def __init__(self, filename):
		self.filename = filename
		self.apix = None
		self.imagic = True
		self.hdfheader = None
		self.boxsize = None
		self.debug = False
		pass

	#----------------------------
	def setApix(self, apix):
		self.apix = apix

	#----------------------------
	def addImageToHdf(self, imagedata, partnum):
		if self.debug is True:
			print("addImageToHdf %d"%(partnum))
		imagegroup = self.images.create_group(str(partnum))

		image = imagegroup.create_dataset('image', data=imagedata, shape=imagedata.shape, dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.datatype', 7, shape=(1,), dtype=numpy.uint32)
		#FIXME not sure about this one above

		imagegroup.attrs.create('EMAN.HostEndian', numpy.string_(sys.byteorder),)
		imagegroup.attrs.create('EMAN.ImageEndian', numpy.string_(sys.byteorder),)
		imagegroup.attrs.create('EMAN.source_path', numpy.string_(self.filename),)
		#imagegroup.attrs.create('EMAN.ptcl_repr', 1, shape=(1,), dtype=numpy.uint32)
		#imagegroup.attrs.create('EMAN.source_n', 1, shape=(1,), dtype=numpy.uint32)

		if self.imagic is True:
			timedata = datetime.datetime.utcnow()
			#datetime.datetime(2016, 8, 9, 15, 38, 25, 228892)
			imagegroup.attrs.create('EMAN.IMAGIC.year', timedata.year, shape=(1,), dtype=numpy.uint32)
			imagegroup.attrs.create('EMAN.IMAGIC.month', timedata.month, shape=(1,), dtype=numpy.uint32)
			imagegroup.attrs.create('EMAN.IMAGIC.mday', timedata.day, shape=(1,), dtype=numpy.uint32)
			imagegroup.attrs.create('EMAN.IMAGIC.hour', timedata.hour, shape=(1,), dtype=numpy.uint32)
			imagegroup.attrs.create('EMAN.IMAGIC.minute', timedata.minute, shape=(1,), dtype=numpy.uint32)
			imagegroup.attrs.create('EMAN.IMAGIC.sec', timedata.second, shape=(1,), dtype=numpy.uint32)

			imagegroup.attrs.create('EMAN.IMAGIC.imgnum', partnum, shape=(1,), dtype=numpy.uint32)
			imagegroup.attrs.create('EMAN.IMAGIC.count', self.numpart-1, shape=(1,), dtype=numpy.uint32)
			#imagegroup.attrs.create('EMAN.IMAGIC.error', 0, shape=(1,), dtype=numpy.uint32) #imagic error code
			#imagegroup.attrs.create('EMAN.IMAGIC.headrec', 1, shape=(1,), dtype=numpy.uint32)

		imagegroup.attrs.create('EMAN.minimum', imagedata.min(), shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.maximum', imagedata.max(), shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.mean', imagedata.mean(), shape=(1,), dtype=numpy.float32)
		nonzero_mean = imagedata.sum()/(imagedata != 0).sum()
		imagegroup.attrs.create('EMAN.mean_nonzero', nonzero_mean, shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.sigma', imagedata.std(), shape=(1,), dtype=numpy.float32)
		nonzero_sigma = (imagedata != 0).std()
		imagegroup.attrs.create('EMAN.sigma_nonzero', nonzero_sigma, shape=(1,), dtype=numpy.float32)
		imagegroup.attrs.create('EMAN.square_sum', (imagedata**2).sum(), shape=(1,), dtype=numpy.float32)

		if self.apix is not None:
			imagegroup.attrs.create('EMAN.apix_x', self.apix, shape=(1,), dtype=numpy.float32)
			imagegroup.attrs.create('EMAN.apix_y', self.apix, shape=(1,), dtype=numpy.float32)
			imagegroup.attrs.create('EMAN.apix_z', self.apix, shape=(1,), dtype=numpy.float32)

		#imagegroup.attrs.create('EMAN.euler_alt', 0, shape=(1,), dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.euler_az', 0, shape=(1,), dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.euler_phi', 0, shape=(1,), dtype=numpy.float32)
		#imagegroup.attrs.create('EMAN.is_complex', 0, shape=(1,), dtype=numpy.uint32)
		#imagegroup.attrs.create('EMAN.is_complex_ri', 1, shape=(1,), dtype=numpy.uint32)
		#imagegroup.attrs.create('EMAN.is_complex_x', 0, shape=(1,), dtype=numpy.uint32)
		#imagegroup.attrs.create('EMAN.changecount', 0, shape=(1,), dtype=numpy.uint32)
		#imagegroup.attrs.create('EMAN.orientation_convention', numpy.string_('EMAN'),)

		imagegroup.attrs.create('EMAN.nx', imagedata.shape[0], shape=(1,), dtype=numpy.uint32)
		imagegroup.attrs.create('EMAN.ny', imagedata.shape[1], shape=(1,), dtype=numpy.uint32)
		imagegroup.attrs.create('EMAN.nz', 1, shape=(1,), dtype=numpy.uint32)
		return

	#----------------------------
	def write(self, a):
		if self.debug is True:
			print("write %s"%(str(a.shape)))
		shape = a.shape
		self.dset = h5py.File(self.filename, 'w')
		mdf = self.dset.create_group('MDF')
		self.images = mdf.create_group('images')
		if len(shape) == 2:
			self.numpart = 1
			self.images.attrs.create('imageid_max', self.numpart-1, shape=(1,), dtype=numpy.uint32)
			self.addImageToHdf(a, 0)
		elif len(shape) == 3:
			self.numpart = shape[0]
			self.images.attrs.create('imageid_max', self.numpart-1, shape=(1,), dtype=numpy.uint32)
			for i in range(self.numpart):
				imagedata = a[i]
				self.addImageToHdf(imagedata, i)
		else:
			raise NotImplementedError('wrong dimension for hdf5 file')
		self.dset.close()

	#----------------------------
	def append(self, a):
		if self.debug is True:
			print("append %s"%(str(a.shape)))
		shape = a.shape
		self.dset = h5py.File(self.filename, 'r+')
		self.images = self.dset['MDF']['images']
		self.numpart = int(self.images.attrs['imageid_max'])+1
		if self.debug is True:
			print("numpart", self.numpart)
		if len(shape) == 2:
			self.addImageToHdf(a, self.numpart)
			self.numpart += 1
			self.images.attrs.modify('imageid_max', self.numpart-1)
		elif len(shape) == 3:
			for i in range(self.numpart, self.numpart+shape[0]):
				imagedata = a[i-self.numpart]
				self.addImageToHdf(imagedata, i)
			self.numpart += shape[0]
			self.images.attrs.modify('imageid_max', self.numpart-1)
		else:
			raise NotImplementedError('wrong dimension for hdf5 file')
		self.dset.close()

	#----------------------------
	def readAllParticleHeaders(self):
		if not os.path.isfile(self.filename) or self.getFileSize() < 10:
			print("file not found")
			return
		if self.debug is True:
			print("readAllParticleHeaders")
		self.dset = h5py.File(self.filename, 'r')
		images = self.dset['MDF']['images']
		self.numpart = int(images.attrs['imageid_max'])+1
		if self.debug is True:
			print("numpart", self.numpart)
		headerTree = list(range(self.numpart)) #will become list of dicts
		for partnum in range(self.numpart):
			if self.debug is True:
				sys.stderr.write(".")
			partnumstr = str(partnum)
			imagegroup = images[partnumstr]
			attrDict = dict(imagegroup.attrs)
			if self.imagic is False:
				for key in list(attrDict.keys()):
					if key.startswith('EMAN.IMAGIC'):
						del attrDict[key]
			headerTree[partnum] = attrDict
		self.dset.close()
		return headerTree

	#----------------------------
	def readFirstParticleHeader(self):
		if not os.path.isfile(self.filename) or self.getFileSize() < 10:
			print("file not found")
			return
		if self.debug is True:
			print("readFirstParticleHeader")
		self.dset = h5py.File(self.filename, 'r')
		images = self.dset['MDF']['images']
		self.numpart = int(images.attrs['imageid_max'])+1
		if self.debug is True:
			print("numpart", self.numpart)
		imagegroup = images['0']
		attrDict = dict(imagegroup.attrs)
		if self.imagic is False:
			for key in list(attrDict.keys()):
				if key.startswith('EMAN.IMAGIC'):
					del attrDict[key]
		self.dset.close()
		#print(attrDict)
		return attrDict

	#----------------------------
	def read(self, particleNumbers=None):
		"""
		read a list of particles into memory
		particles numbers start at 0
		"""
		if not os.path.isfile(self.filename) or self.getFileSize() < 10:
			print("file not found")
			return
		self.dset = h5py.File(self.filename, 'r')
		imageDict = self.dset['MDF']['images']
		self.numpart = int(imageDict.attrs['imageid_max'])+1
		if self.debug is True:
			print("numpart", self.numpart)
		if particleNumbers is None:
			particleNumbers = list(imageDict.keys())
		if self.debug is True:
			print("read len %d"%(len(particleNumbers)))
		images = []
		for partnum in particleNumbers:
			#print("----------")
			#print(partnum)
			partnumstr = str(partnum)
			if self.debug is True:
				sys.stderr.write(".")
			image = imageDict[partnumstr]['image']
			imagedata = image[:]
			#print(imagedata)
			images.append(imagedata)
		self.dset.close()
		return numpy.array(images)

	################################################
	# Reporter functions for this class
	################################################
	def getFileSize(self):
		self.filesize = int(os.stat(self.filename)[6])
		if self.debug is True:
			print("getFileSize %d"%(self.filesize))
		return self.filesize
	def getNumberOfParticles(self):
		if self.debug is True:
			print("getNumberOfParticles %d"%(self.numpart))
		self.dset = h5py.File(self.filename, 'r')
		self.images = self.dset['MDF']['images']
		return int(self.images.attrs.get('imageid_max', -1))+1
	def getBoxSize(self):
		if self.boxsize is None:
			self.hdfheader = self.readFirstParticleHeader()
			if self.hdfheader is None:
				return
			self.boxsize = int(self.hdfheader.get('EMAN.nx',0))
		if self.debug is True:
			print("getBoxSize %d"%(self.boxsize))
		return self.boxsize
	def getPixelSize(self):
		if self.apix is None:
			self.hdfheader = self.readFirstParticleHeader()
			if self.hdfheader is None:
				return
			self.apix = int(self.hdfheader.get('EMAN.apix_x',0))
		if self.debug is True:
			print("getPixelSize %.5f"%(self.apix))
		return self.apix

#----------------------------
#----------------------------
#----------------------------

if __name__ == '__main__':
	a = numpy.array(numpy.random.random((3,128,128)), dtype=numpy.float32)
	#print(a)
	print(a.shape)
	print("\nwriting random.hdf")
	rhdf = HdfFile('random.hdf')
	rhdf.write(a)

	print("\nreading random.hdf")
	rhdf = HdfFile('random.hdf')
	b = rhdf.readFirstParticleHeader()
	b = rhdf.read()
	rhdf.append(a)
	#print(b)
	print(b.shape)

	print("\ndiff")
	c = a-b
	print("%.8f +/- %.8f"%(c.mean(), c.std()))

	sys.exit(1)

# h5dump -H start.hdf | head -n 256 > start.header
# ./hdf.py; h5dump -H random.hdf > random.header
# sdiff -daWiB random.header start.header  | colordiff
# e2proc2d.py random.hdf eman.hdf
# sdiff -daWiB val1.txt val2.txt  | colordiff
