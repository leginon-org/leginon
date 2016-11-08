#!/usr/bin/env python
import shutil
import os

from pyami import mrc
from appionlib import appionScript
from appionlib import apRelion
from appionlib import starFile
from appionlib import apStackFile
from appionlib import appiondata
from appionlib import apDisplay
from appionlib import apImagicFile
from appionlib import apFile

class ReplaceRelion2DAlignedRefs(appionScript.AppionScript):
	'''
	This is a script to replace the unweighted class average generated before revision
	e9277ff8 with Relion generated ones after alignment among them.
	'''
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --alignstack=ID")
		self.parser.add_option("-s", "--alignstack", dest="alignstackid", type="int",
			help="Stack database id", metavar="ID#")

	def checkConflicts(self):
		self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignstackid'])
		self.alignref_file = self.alignstackdata['refstackfile']
		self.params['timestamp'] = self.alignref_file.split('part')[1].split('_')[0]
		self.lastiter = self.alignstackdata['iteration']

	def readRefStarFile(self):
		'''
		Read orientation of the references as the result of refalign.
		'''
		reflist = []
		#ref16may17u43_it030_data.star
		inputfile = "ref%s_final_data.star"%(self.params['timestamp'])
		lastiterfile = "ref%s_it%03d_data.star"%(self.params['timestamp'], self.lastiter)
		if not os.path.isfile(lastiterfile):
			# may be in refalign after file sorting but did not upload properly
			lastiterfile = os.path.join("refalign", lastiterfile)
		shutil.copy(lastiterfile, inputfile)

		starData = starFile.StarFile(inputfile)
		starData.read()
		dataBlock = starData.getDataBlock('data_images')
		particleTree = dataBlock.getLoopDict()

		fakereflist = [{ 'xshift': 0, 'yshift':0, 'inplane':0}]
		for relionpartdict in particleTree:
			refdict = apRelion.adjustPartDict(relionpartdict, fakereflist)
			reflist.append(refdict)
		apDisplay.printMsg("read rotation and shift parameters for "+str(len(reflist))+" references")
		if len(reflist) < 1:
			apDisplay.printError("Did not find any particles in star file: "+inputfile)
		return reflist


	def start(self):
		reflist = self.readRefStarFile()
		alignref_imagicfile = self.alignstackdata['refstackfile']

		# convert unaligned refstack from mrc to imagic format
		unaligned_refstack_mrc = os.path.join('iter%03d' % self.lastiter,'part%s_it%03d_classes.mrcs' % (self.params['timestamp'], self.lastiter))
		unaligned_refstack_imagic = 'part%s_it%03d_classes.hed' % (self.params['timestamp'], self.lastiter)
		stackarray = mrc.read(unaligned_refstack_mrc)
		apImagicFile.writeImagic(stackarray, unaligned_refstack_imagic)

		# createAlignedStack
		temp_imagicfile = apStackFile.createAlignedStack(reflist, unaligned_refstack_imagic,'temp_aligned_ref')
		apFile.moveStack(temp_imagicfile,alignref_imagicfile)
		# clean up
		apFile.removeStack(temp_imagicfile, warn=False)
		apFile.removeStack(unaligned_refstack_imagic, warn=False)

#=====================
if __name__ == "__main__":
	app = ReplaceRelion2DAlignedRefs()
	app.start()
	app.close()
