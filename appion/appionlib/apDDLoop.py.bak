#/usr/bin/env python

from appionlib import appionLoop2
from appionlib import apDDprocess
from appionlib import apDisplay
from appionlib import appiondata
from leginon import leginondata

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
		self.parser.add_option("--keepstack", dest="keepstack", default=True,
			action="store_true", help="Clean up frame stack after alignment and sum image upload")
		# String
		self.parser.add_option("--tempdir", dest="tempdir",
			help="Local path for storing temporary stack output, e.g. --tempdir=/tmp/appion/makeddstack",
			metavar="PATH")
		# Integer
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack to restrict ddstack making(optional)", metavar="INT")
		self.parser.add_option("--ddstartframe", dest="startframe", type="int", default=0,
			help="starting frame for summing the frames. The first frame is 0")
		self.parser.add_option("--ddnframe", dest="nframe", type="int",
			help="total frames to consider for direct detector frame sum")
		self.parser.add_option("--alignlabel", dest="alignlabel", default='a',
			help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")
		self.parser.remove_option("--uncorrected")
		self.parser.remove_option("--reprocess")
		self.addBinOption()

		# Dosefgpu_driftcoor options
		self.parser.add_option("--alignoffset", dest="fod", type="int", default=2,
			help="number of frame offset in alignment in dosefgpu_driftcorr")
		self.parser.add_option("--alignccbox", dest="pbx", type="int", default=128,
			help="alignment CC search box size in dosefgpu_driftcorr")

		# Dose weighting, based on Grant & Grigorieff eLife 2015
		self.parser.add_option("--doseweight",dest="doseweight",metavar="bool", default=False,
			action="store_true", help="dose weight the frame stack, according to Tim / Niko's curves")
		self.parser.add_option("--totaldose",dest="totaldose",metavar="float",type=float,
                        help="total dose for the full movie stack in e/A^2. If not specified, will get value from database")

	def addBinOption(self):
		'''
		bin is defined as float for MotionCor2 alignment but as integer in all others.
		'''
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning factor relative to the dd stack (optional)", metavar="INT")

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
		# initialize aligned_imagedata as if not aligned
		self.aligned_imagedata = None
		self.aligned_dw_imagedata = None

	def commitAlignStats(self, aligned_imgdata):
		'''
		commit align stats. Only do so if performing alignment using ApDDAlignStackMaker
		'''
		pass

	def commitToDatabase(self,imgdata):
		if self.aligned_imagedata != None:
			apDisplay.printMsg('Uploading aligned image as %s' % self.aligned_imagedata['filename'])
			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=self.aligned_imagedata,ddstackrun=self.rundata)
			q.insert()
			# Issue #6155 need new query to get timestamp
			self.aligned_imagedata = leginondata.AcquisitionImageData().direct_query(q['result'].dbid)
			self.commitAlignStats(self.aligned_imagedata)
			transferALSThickness(q['source'],q['result'])
			transferZLPThickness(q['source'],q['result'])
	
		if self.aligned_dw_imagedata != None:
			apDisplay.printMsg('Uploading aligned image as %s' % self.aligned_dw_imagedata['filename'])
			q = appiondata.ApDDAlignImagePairData(source=imgdata,result=self.aligned_dw_imagedata,ddstackrun=self.rundata)
			q.insert()
			# Issue #6155 need new query to get timestamp
			self.aligned_dw_imagedata = leginondata.AcquisitionImageData().direct_query(q['result'].dbid)
			transferALSThickness(q['source'],q['result'])
			transferZLPThickness(q['source'],q['result'])

def transferALSThickness(unaligned,aligned):
# transfers aperture limited scattering measurements and parameters from the unaligned image to the aligned image
# should it be here or in a different place???
	obthdata = leginondata.ObjIceThicknessData(image=unaligned).query(results=1)
        if obthdata:
                results = obthdata[0]
               	newobjth = leginondata.ObjIceThicknessData()
               	newobjth['vacuum intensity'] = results['vacuum intensity']
               	newobjth['mfp'] = results['mfp']
               	newobjth['intensity'] = results['intensity']
                newobjth['thickness'] = results['thickness']
                newobjth['image'] = aligned;
	        newobjth.insert()

def transferZLPThickness(unaligned,aligned):
# transfers zero loss peak measurements and parameters from the unaligned image to the aligned image
# should it be here or in a different place???
	zlpthdata = leginondata.ZeroLossIceThicknessData(image=unaligned).query(results=1)
        if zlpthdata:
                results = zlpthdata[0]
		newzlossth = leginondata.ZeroLossIceThicknessData()
                newzlossth['no slit mean'] = results['no slit mean']
                newzlossth['no slit sd'] = results['no slit sd']
 		newzlossth['slit mean'] = results['slit mean']
		newzlossth['slit sd'] = results['slit sd']
		newzlossth['thickness'] = results['thickness']
		newzlossth['image'] = aligned
		newzlossth.insert()

