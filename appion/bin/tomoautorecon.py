#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import math
#appion
from appionlib import appionTiltSeriesLoop
from appionlib import appiondata
from appionlib import apTomo
from appionlib import apDisplay

#=====================
#=====================
class TomoAlignReconLooper(appionTiltSeriesLoop.AppionTiltSeriesLoop):
	def setupParserOptions(self):
		self.alignmethods = ( "imod-shift", "protomo" )
		self.parser.add_option("--alignmethod", dest="alignmethod",
			type="choice", choices=self.alignmethods, default="protomo" )
		self.parser.add_option("--alignsample", dest="alignsample", default=4.0, type="float",
			help="Protomo only: Align sample rate, e.g. --alignsample=2.0", metavar="float")
		self.parser.add_option("--alignregion", dest="alignregion", default=50, type="int",
			help="Protomo only: Percentage of image length used in alignment, e.g. --alignregion=80", metavar="int")
		self.parser.add_option("--reconthickness", dest="reconthickness", default=100, type="int",
			help="Full tomo reconstruction thickness before binning, e.g. --thickness=200", metavar="int")
		self.parser.add_option("--reconbin", dest="reconbin", default=1, type="int",
			help="Extra binning from original images, e.g. --bin=2", metavar="int")
		return

	def checkConflicts(self):
		return

	def commitToDatabase(self,tiltseriesdata):
		# nothing to commit right now.
		return

	def isBadTiltSeries(self, tiltseriesdata):
		# no need to process if only a small number of images are taken
		imagelist = apTomo.getImageList([tiltseriesdata,])
		tilts,ordered_imagelist,ordered_mrc_files,refimg = apTomo.orderImageList(imagelist)
		imgshape = apTomo.getTomoImageShape(ordered_imagelist[refimg])
		corr_bin = apTomo.getCorrelatorBinning(imgshape)
		shifts = apTomo.getLeginonRelativeShift(ordered_imagelist, corr_bin, refimg)
		distances =  []
		for shift in shifts:
			distance = math.hypot(shift['x'],shift['y'])
			distances.append(distance)
		if len(imagelist) < 5: 
			apDisplay.printWarning("Less than 5 images in Series %d" % (tiltseriesdata['number']))
			return True
		if max(distances[2:-2]) > min(imgshape) / (corr_bin*3):
			apDisplay.printWarning("Tracked feature in Series %d jumps over 1/3 of the image" % (tiltseriesdata['number']))
			return True
		return False

	def processTiltSeries(self, tiltseriesdata):
		seriesnumber = tiltseriesdata['number']
		pieces = self.params['rundir'].split('/')
		tomobasepath = '/'.join(pieces[:-1])
		tiltseriesdirname = "tiltseries%d" % seriesnumber
		tiltseriespath = os.path.join(tomobasepath,tiltseriesdirname)
		if self.params['commit']:
			commitstr = '--commit'
		else:
			commitstr = '--no-commit'
		if self.params['description'] is None:
			self.params['description'] = 'auto recon '+self.params['runname']
		
		# align the tilt series
		alignrundir = os.path.join(tiltseriespath,'align',self.params['runname'])
		alignlogpath = os.path.join(alignrundir,self.params['runname']+'.appionsub.log')
		command = 'tomoaligner.py' + ' ' + '--projectid=%d' % (self.params['projectid']) + ' ' + '--session=' + self.params['sessionname'] + ' ' + '--runname=' + self.params['runname'] + ' ' + '--rundir=' + alignrundir + ' ' + '--tiltseriesnumber=%d' % (seriesnumber) + ' ' + '--alignmethod=%s' % self.params['alignmethod'] + ' ' + '--sample=%.3f' % (self.params['alignsample']) + ' ' + '--region=%d' % (self.params['alignregion']) + ' ' + '--description="%s"' % (self.params['description'],) + ' ' + commitstr
		return_code = self.runAppionScriptInSubprocess(command,alignlogpath)

		# reconstruct full tomogram with the alignments
		aligners = apTomo.getAlignersFromTiltSeries(tiltseriesdata,self.params['runname'])
		for alignerdata in aligners:
			reconrunname = self.params['runname']+'_a%d'% alignerdata.dbid
			reconrundir = os.path.join(tiltseriespath,reconrunname)
			reconlogpath = os.path.join(reconrundir,reconrunname+'.appionsub.log')
			command = 'tomomaker.py' + ' ' + '--projectid=%d' % (self.params['projectid']) + ' ' + '--session=' + self.params['sessionname'] + ' ' + '--runname=' + reconrunname + ' ' + '--rundir=' + reconrundir + ' ' + '--alignerid=%d' % alignerdata.dbid + ' ' + '--bin=%d' % self.params['reconbin'] + ' ' + '--thickness=%d' % self.params['reconthickness'] + ' ' + '--description="%s using aligner %d"' % (self.params['description'],alignerdata.dbid) + ' ' + commitstr
			return_code = self.runAppionScriptInSubprocess(command,reconlogpath)

#=====================
if __name__ == '__main__':
	app = TomoAlignReconLooper()
	app.run()
	app.close()



