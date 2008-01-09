#Defocus pair functions

import numpy
#pyami
import pyami.peakfinder as peakfinder
import pyami.correlator as correlator
#leginon
import leginondata

#appion
import appionData
import apDB
import apImage
import apDisplay

leginondb = apDB.db
appiondb  = apDB.apdb

def getShiftFromImage(imgdata, params):
	sibling = getDefocusPair(imgdata)
	if sibling:
		shiftpeak = getShift(imgdata, sibling)
		recordShift(params, imgdata, sibling, shiftpeak)
	else:
		apDisplay.printWarning("No sibling found")
		shiftpeak=None
	return sibling, shiftpeak

def getDefocusPair(imgdata):
	target=imgdata['target']
	if target is None:
		return None
	qtarget=leginondata.AcquisitionImageTargetData()
	qtarget['image'] = target['image']
	qtarget['number'] = target['number']
	qsibling=leginondata.AcquisitionImageData(target=qtarget)
	origid=imgdata.dbid
	allsiblings = leginondb.query(qsibling, readimages=False)	
	defocpair=None
	if len(allsiblings) > 1:
		#could be multiple siblings but we are taking only the most recent
		for sib in allsiblings:
			if sib.dbid != origid:
				defocpair=sib
				break
	return defocpair

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
		peak=None
	#test to see if images capture the same area
	elif (dimension1 * binning1) != (dimension2 * binning2):
		apDisplay.printWarning("Defocus pairs do not capture the same imaging area, so shift can't be calculated.")
		peak=None
	#images must not be less than finalsize (currently 512) pixels. This is arbitrary but for good reason
	elif dimension1 < finalsize or dimension2 < finalsize:
		apDisplay.printWarning("Images must be greater than "+finalsize+" pixels to calculate shift.")
		peak=None
	else:
		shrinkfactor1=dimension1/finalsize
		shrinkfactor2=dimension2/finalsize
		binned1 = apImage.binImg(imgdata1['image'], shrinkfactor1)
		binned2 = apImage.binImg(imgdata2['image'], shrinkfactor2)
		pc=correlator.phase_correlate(binned1,binned2,zero=True)
		#apImage.arrayToMrc(pc,imgdata1['filename']+'.corr.mrc')
		peak = peakfinder.findSubpixelPeak(pc, lpf=1.5) # this is a temp fix. 
		subpixpeak = peak['subpixel peak']
		shift=correlator.wrap_coord(subpixpeak,pc.shape)
		peak['scalefactor']=dimension2/float(dimension1)
		peak['shift']= numpy.array((shift[0]*shrinkfactor1, shift[1]*shrinkfactor1))
	return peak

def recordShift(params,img,sibling,peak):
	filename=params['session']['name']+'.shift.txt'
	f=open(filename,'a')
	f.write('%s\t%s\t%f\t%f\t%f\t%f\n' % (img['filename'],sibling['filename'],peak['shift'][1],peak['shift'][0],peak['scalefactor'],peak['subpixel peak value']))
	f.close()
	return()

def insertShift(imgdata,siblingdata,peak):
	if not siblingdata or not peak:
		apDisplay.printWarning("No sibling or peak found. No database insert")
		return False
	shiftq=appionData.ApImageTransformationData()
	shiftq['image1']=imgdata
	shiftdata=appiondb.query(shiftq)
	if shiftdata:
		apDisplay.printWarning("Shift values already in database")
		return False
	shiftq['image2']=siblingdata
	shiftq['shiftx']=peak['shift'][1]
	shiftq['shifty']=peak['shift'][0]
	shiftq['scale']=peak['scalefactor']
	shiftq['correlation']=peak['subpixel peak value']
	apDisplay.printMsg("Inserting shift beteween "+apDisplay.short(imgdata['filename'])+\
		" and "+apDisplay.short(siblingdata['filename'])+" into database")
	appiondb.insert(shiftq)
	return True

def getTransformedDefocPair(imgdata,direction):
	simgq=appionData.ApImageTransformationData()
	base = 'image'
	direction = str(direction)
	if direction =='2':
		sfrom = base + '2'
		sto = base+ '1'
	if direction == '1':
		sfrom = base+ '1'
		sto = base+ '2'
	simgq[sfrom]=imgdata
	simgresults=appiondb.query(simgq,readimages=False)
	if simgresults:
		sbimgref = simgresults[0].special_getitem(sto,dereference = False)
		sbimgdata = leginondb.direct_query(leginondata.AcquisitionImageData,sbimgref.dbid, readimages = False)
	else:
		return None
	return sbimgdata

