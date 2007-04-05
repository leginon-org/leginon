#!/usr/bin/python -O
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import sys
import os
import data
import apLoop
import apCrud
import apParticle

data.holdImages(False)

if __name__ == '__main__':
	(images,stats,params,donedict) = apLoop.startNewAppionFunction(sys.argv)
	params=apCrud.modifyParams(params)
	run_dir=params["outdir"]+"/"+params["runid"]+"/"
	# create "run" directory if doesn't exist
	if not (os.path.exists(run_dir)):
		os.mkdir(run_dir)

	if params['commit']:
		maskruns=[]
		# Insertion is repeated until the query result is not empty
		# This is necessary because insertion can be slow
		while len(maskruns) == 0:
			maskruns=apParticle.insertMakeMaskParams(params)
		maskrun=maskruns[0]
	else:
		# create "regioninfo" directory if doesn't exist
		info_dir=run_dir+"/regions/"
		if not (os.path.exists(info_dir)):
			os.mkdir(info_dir)

		# remove region info file if it exists
		if (os.path.exists(info_dir+"*.region")):
			os.remove(info_dir+"*.region")
	
	notdone=True
	while notdone:
		while images:
			img = images.pop(0)
			imgname=img['filename']
			stats['imagesleft'] = len(images)

			#CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if( apLoop.startLoop(img, donedict, stats, params)==False ):
				continue
			mask,regioninfos=apCrud.makeMask(params,imgname)
			if params['commit']:
				apCrud.writeRegionInfoToDB(maskrun,img,params['session'].dbid,regioninfos)
			else:
				# remove region info file if it exists
				if (os.path.exists(info_dir+imgname+".region")):
					os.remove(info_dir+imgname+".region")
				apCrud.writeRegionInfo(imgname,info_dir,regioninfos)
			if not params['test']:
				apCrud.writeMaskImage(imgname,run_dir,mask)
					
			#NEED TO DO SOMETHING ELSE IF particles ARE ALREADY IN DATABASE
			apLoop.writeDoneDict(donedict,params,imgname)
			apLoop.printSummary(stats, params)
			#END LOOP OVER IMAGES
		notdone,images = apLoop.waitForMoreImages(stats, params)
		#END NOTDONE LOOP	
	apLoop.completeLoop(stats)
