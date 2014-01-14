#/usr/bin/env python

from appionlib import appionLoop2
from appionlib import apDDprocess

class DDStackLoop(appionLoop2.AppionLoop):
	'''
	Base Class for MakeFrameStack and AlignDDStack.
	This is a virtual class.  Do not use alone
	'''
	#=======================
	def setupParserOptions(self):
		# Boolean
		self.parser.add_option("--no-keepstack", dest="keepstack", default=True,
			action="store_false", help="Clean up frame stack after alignment and sum image upload")
		# String
		self.parser.add_option("--tempdir", dest="tempdir",
			help="Local path for storing temporary stack output, e.g. --tempdir=/tmp/appion/makeddstack",
			metavar="PATH")
		# Integer
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack to restrict ddstack making(optional)", metavar="INT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning factor relative to the dd stack (optional)", metavar="INT")
		self.parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")
		self.parser.add_option("--ddstartframe", dest="startframe", type="int", default=0,
			help="starting frame for summing the frames. The first frame is 0")
		self.parser.add_option("--ddnframe", dest="nframe", type="int",
			help="total frames to consider for direct detector frame sum")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")

		# Dosefgpu_driftcoor options
		self.parser.add_option("--alignoffset", dest="fod", type="int", default=2,
			help="number of frame offset in alignment in dosefgpu_driftcorr")
		self.parser.add_option("--alignbfactor", dest="bft", type="float", default=100.0,
			help="alignment B-factor in pix^2 in dosefgpu_driftcorr")

	def getUnAlignedImageIds(self,imageids):
		'''
		Convert the input image id list to an unaligned image id list
		if the input is aligned.
		'''
		ddproc = apDDprocess.DirectDetectorProcessing()
		newimageids = []
		for imageid in imageids:
			ddproc.setImageId(imageid)
			imagepairdata = ddproc.getAlignImagePairData(None,False)
			if imagepairdata:
				newimageids.append(imagepairdata['source'].dbid)
			else:
				# imageid is unaligned
				newimageids.append(imageid)
		return newimageids

	def checkConflicts(self):
		pass

	#=======================
	def processImage(self, imgdata):
		pass
