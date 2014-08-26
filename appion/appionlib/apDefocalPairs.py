#Defocus pair functions

import sys
import numpy
#pyami
import pyami.peakfinder as peakfinder
import pyami.correlator as correlator
from pyami import mrc
#leginon
import leginon.leginondata
#appion
from appionlib import appiondata
from appionlib import apImage
from appionlib import apDisplay
from appionlib import apEMAN

##===================
##===================
def getShiftFromImage(imgdata, sessionname):
	sibling = getDefocusPair(imgdata)
	if sibling:
		shiftpeak = getShift(imgdata, sibling)
		recordShift(sessionname, imgdata, sibling, shiftpeak)
	else:
		apDisplay.printWarning("No sibling found")
		shiftpeak=None
	return sibling, shiftpeak

##===================
##===================
def getDefocusPair(imgdata):
	if imgdata['preset'] is not None and imgdata['preset']['name'] != 'upload':
		sibling = getDefocusPairFromTarget(imgdata)
	else:
		sibling = getManualDefocusPair(imgdata)
	return sibling

def getDefocusPairFromTarget(imgdata):
	origid = imgdata.dbid
	allsiblings = getAllSiblings(imgdata)
	defocpair = None
	if len(allsiblings) > 1:
		#could be multiple siblings but we are taking only the most recent
		for sib in allsiblings:
			if sib.dbid != origid:
				defocpair=sib
				break
	return defocpair

def getAllSiblings(imgdata):
	'''
	get all sibling image data, including itself, from the same parent image and target number
	'''
	target = imgdata['target']
	if target is None or target['image'] is None:
		return [imgdata]
	qtarget = leginon.leginondata.AcquisitionImageTargetData()
	qtarget['image'] = target['image']
	qtarget['number'] = target['number']
	qsibling = leginon.leginondata.AcquisitionImageData(target=qtarget)
	allsiblings = qsibling.query(readimages=False)
	return allsiblings

##===================
##===================
def getManualDefocusPair(imgdata):
  # This is only for manual defocus pair
	filename = imgdata['filename']
	namelist = filename.split('_')
	if namelist[-1]=='1':
		namelist[-1] = '2'
	newfilename = '_'.join(namelist)
	qimage=leginon.leginondata.AcquisitionImageData(session=imgdata['session'],filename=newfilename)
	allimages = qimage.query(readimages=False)
	if len(allimages) != 1:
		return
	return allimages[0]

##===================
##===================
def getShift(imgdata1 ,imgdata2):
	#assumes images are square
	print "Finding shift between", apDisplay.short(imgdata1['filename']), "and", apDisplay.short(imgdata2['filename'])
	dimension1 = imgdata1['camera']['dimension']['x']
	binning1   = imgdata1['camera']['binning']['x']
	dimension2 = imgdata2['camera']['dimension']['x']
	binning2   = imgdata2['camera']['binning']['x']
	finalsize=512

	#test to make sure images are at same mag
	if imgdata1['scope']['magnification'] != imgdata2['scope']['magnification']:
		apDisplay.printWarning("Defocus pairs are at different magnifications, so shift can't be calculated.")
		return None

	#test to see if images capture the same area
	if (dimension1 * binning1) != (dimension2 * binning2):
		apDisplay.printWarning("Defocus pairs do not capture the same imaging area, so shift can't be calculated.")
		return None

	#images must not be less than finalsize (currently 512) pixels. This is arbitrary but for good reason
	if dimension1 < finalsize or dimension2 < finalsize:
		apDisplay.printWarning("Images must be greater than "+finalsize+" pixels to calculate shift.")
		return None

	#low pass filter 2 images to twice the final pixelsize BEFORE binning
	shrinkfactor1=dimension1/finalsize
	shrinkfactor2=dimension2/finalsize
	binned1 = apImage.filterImg(imgdata1['image'],1.0,shrinkfactor1*2)
	binned2 = apImage.filterImg(imgdata2['image'],1.0,shrinkfactor2*2)

	#now bin 2 images
	binned1 = apImage.binImg(binned1, shrinkfactor1)
	binned2 = apImage.binImg(binned2, shrinkfactor2)
	
	### fix for non-square images, correlation fails on non-square images
	mindim = min(binned1.shape)
	binned1 = binned1[:mindim,:mindim]
	binned2 = binned2[:mindim,:mindim]

	### use phase correlation, performs better than cross
	pc=correlator.phase_correlate(binned1,binned2)
	apImage.arrayToMrc(pc,"phaseCorrelate.mrc")

	### find peak, filtering to 10.0 helps
	peak = peakfinder.findSubpixelPeak(pc, lpf=10.0)
	subpixpeak = peak['subpixel peak']
	shift=correlator.wrap_coord(subpixpeak, pc.shape)
	peak['scalefactor'] = dimension2/float(dimension1)
	#print shift[0]*shrinkfactor1, shift[1]*shrinkfactor1
	xshift = int(round(shift[0]*shrinkfactor1))
	yshift = int(round(shift[1]*shrinkfactor1))
	peak['shift'] = numpy.array((xshift, yshift))
	apDisplay.printMsg("Determined shifts: %f %f"%(peak['shift'][0],peak['shift'][1]))
	#print peak['shift']
	#sys.exit(1)
	return peak

##===================
##===================
def recordShift(sessionname,img,sibling,peak):
	filename=sessionname+'.shift.txt'
	f=open(filename,'a')
	f.write('%s\t%s\t%f\t%f\t%f\t%f\n' % (img['filename'],sibling['filename'],peak['shift'][1],peak['shift'][0],peak['scalefactor'],peak['subpixel peak value']))
	f.close()
	return()

##===================
##===================
def insertShift(imgdata,siblingdata,peak):
	if not siblingdata or not peak:
		apDisplay.printWarning("No sibling or peak found. No database insert")
		return False
	shiftq=appiondata.ApImageTransformationData()
	shiftq['image1']=imgdata
	shiftdata=shiftq.query()
	if shiftdata:
		apDisplay.printWarning("Shift values already in database")
		return False
	shiftq['image2']=siblingdata
	shiftq['shiftx']=peak['shift'][1]
	shiftq['shifty']=peak['shift'][0]
	shiftq['scale']=peak['scalefactor']
	if not peak['subfailed']:
		shiftq['correlation']=peak['subpixel peak value']
	else:
		shiftq['correlation']=0.0
	apDisplay.printMsg("Inserting shift beteween "+apDisplay.short(imgdata['filename'])+\
		" and "+apDisplay.short(siblingdata['filename'])+" into database")
	shiftq.insert()
	return True

##===================
##===================
def getTransformedDefocPair(imgdata, direction):
	simgq=appiondata.ApImageTransformationData()
	base = 'image'
	direction = str(direction)
	if direction =='2':
		sfrom = base + '2'
		sto = base+ '1'
	if direction == '1':
		sfrom = base+ '1'
		sto = base+ '2'
	simgq[sfrom]=imgdata
	simgresults=simgq.query(readimages=False)
	if simgresults:
		sbimgref = simgresults[0].special_getitem(sto,dereference = False)
		sbimgdata = leginon.leginondata.AcquisitionImageData.direct_query(sbimgref.dbid, readimages = False)
	else:
		return None
	return sbimgdata


