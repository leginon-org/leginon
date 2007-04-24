#Defocus pair functions

import peakfinder
import data
#import dbdatakeeper
import correlator
import appionData
import apDB
import selexonFunctions as sf1

#db=dbdatakeeper.DBDataKeeper()
#partdb=dbdatakeeper.DBDataKeeper(db='dbparticledata')
db=apDB.db
partdb=apDB.apdb

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	#this is a temporary fix while Jim fixes peakfinder
	pf=peakfinder.PeakFinder(lpf=lpf)
	pf.subpixelPeak(newimage=image, npix=npix, guess=guess, limit=limit)
	return pf.getResults()

def getDefocusPair(imagedata):
	target=imagedata['target']
	qtarget=data.AcquisitionImageTargetData()
	qtarget['image'] = target['image']
	qtarget['number'] = target['number']
	qsibling=data.AcquisitionImageData(target=qtarget)
	origid=imagedata.dbid
	allsiblings = db.query(qsibling, readimages=False)	
	if len(allsiblings) > 1:
		#could be multiple siblings but we are taking only the most recent
		#this may be bad way of doing things
		for sib in allsiblings:
			if sib.dbid == origid:
				pass
			else:
				defocpair=sib
				#defocpair.holdimages=False
				break
	else:
		defocpair=None
	return(defocpair)

def getShift(imagedata1,imagedata2):
	#assumes images are square
	print "Finding shift between", imagedata1['filename'], 'and', imagedata2['filename']
	dimension1=imagedata1['camera']['dimension']['x']
	binning1=imagedata1['camera']['binning']['x']
	dimension2=imagedata2['camera']['dimension']['x']
	binning2=imagedata2['camera']['binning']['x']
	finalsize=512
	#test to make sure images are at same mag
	if imagedata1['scope']['magnification']!=imagedata2['scope']['magnification']:
		print "Warning: Defocus pairs are at different magnifications, so shift can't be calculated."
		peak=None
	#test to see if images capture the same area
	elif (dimension1 * binning1) != (dimension2 * binning2):
		print "Warning: Defocus pairs do not capture the same imaging area, so shift can't be calculated."
		peak=None
	#images must not be less than finalsize (currently 512) pixels. This is arbitrary but for good reason
	elif dimension1 < finalsize or dimension2 < finalsize:
		print "Warning: Images must be greater than", finalsize, "to calculate shift."
		peak=None
	else:
		shrinkfactor1=dimension1/finalsize
		shrinkfactor2=dimension2/finalsize
		binned1=sf1.binImg(imagedata1['image'],shrinkfactor1)
		binned2=sf1.binImg(imagedata2['image'],shrinkfactor2)
		pc=correlator.phase_correlate(binned1,binned2,zero=True)
		#Mrc.numeric_to_mrc(pc,'pc.mrc')
		peak=findSubpixelPeak(pc, lpf=1.5) # this is a temp fix. 
		#When jim fixes peakfinder, this should be peakfinder.findSubpixelPeak
		subpixpeak=peak['subpixel peak']
		#find shift relative to origin
		shift=correlator.wrap_coord(subpixpeak,pc.shape)
		peak['scalefactor']=dimension2/float(dimension1)
		peak['shift']=(shift[0]*shrinkfactor1,shift[1]*shrinkfactor1)
	return(peak)

def recordShift(params,img,sibling,peak):
	filename=params['session']['name']+'.shift.txt'
	f=open(filename,'a')
	f.write('%s\t%s\t%f\t%f\t%f\t%f\n' % (img['filename'],sibling['filename'],peak['shift'][1],peak['shift'][0],peak['scalefactor'],peak['subpixel peak value']))
	f.close()
	return()

def insertShift(img,sibling,peak):
	shiftq=appionData.ApImageTransformationData()
	shiftq['dbemdata|AcquisitionImageData|image1']=img.dbid
	shiftdata=partdb.query(shiftq)
	if shiftdata:
		print "Warning: Shift values already in database"
	else:
		shiftq['dbemdata|AcquisitionImageData|image2']=sibling.dbid
		shiftq['shiftx']=peak['shift'][1]
		shiftq['shifty']=peak['shift'][0]
		shiftq['scale']=peak['scalefactor']
		shiftq['correlation']=peak['subpixel peak value']
		print 'Inserting shift beteween', img['filename'], 'and', sibling['filename'], 'into database'
		partdb.insert(shiftq)
	return()
