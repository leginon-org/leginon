#!/usr/bin/python -O

import os
import sys
from pyami import quietscipy
import apImage
from apTilt import apTiltShift


def runTestShift(img1name, img2name, imgpath, tiltdiff, coord):
	img1path = os.path.join(imgpath, img1name)
	img2path = os.path.join(imgpath, img2name)
	print img1path
	print img2path

	img1 = apImage.binImg(apImage.mrcToArray(img1path),4)
	img2 = apImage.binImg(apImage.mrcToArray(img2path),4)

	apImage.arrayToMrc(img1,"img1a-raw.mrc")
	apImage.arrayToMrc(img2,"img2a-raw.mrc")

	origin, newpart, snr = apTiltShift.getTiltedCoordinates(img1, img2, tiltdiff, coord)
	apImage.arrayToJpegPlusPeak(img1, "img1a-guess.jpg", (origin[1], origin[0]))
	apImage.arrayToJpegPlusPeak(img2, "img2a-guess.jpg", (newpart[1], newpart[0]))

	#origin, newpart, snr = apTiltShift.getTiltedCoordinates(img2, img1, -1.0*tiltdiff, coord)
	#apImage.arrayToJpegPlusPeak(img1, "img1b-guess.jpg", (origin[1], origin[0]))
	#apImage.arrayToJpegPlusPeak(img2, "img2b-guess.jpg", (newpart[1], newpart[0]))


if __name__ == "__main__":
	### groEL RCT data
	img1name = "08sep22b_atlas_00022gr_00003sq_v01_00002sq_01_00004en_01.mrc" #untilted
	img2name = "08sep22b_atlas_00022gr_00003sq_v01_00002sq_v01_00004en_00.mrc" #tilted
	imgpath = "/ami/data00/leginon/08sep22b/rawdata/"
	tiltdiff = 55.0
	coord = [(680,500),(681,500),]
	#correct is: 540, 460
	#runTestShift(img1name, img2name, imgpath, tiltdiff, coord)

	### harshey RCT data
	img1name = "07dec11a_00025gr_00037sq_v01_00002sq_v01_00020en_01.mrc" #untilted
	img2name = "07dec11a_00025gr_00037sq_v01_00002sq_v02_00020en_00.mrc" #tilted
	imgpath = "/ami/data15/leginon/07dec11a/rawdata/"
	tiltdiff = 60.0
	coord = [(500,500),(501,500),]
	#correct is: 350, 620
	#runTestShift(img1name, img2name, imgpath, tiltdiff, coord)

	### brian RCT data
	img1name = "08sep18b_a_00025gr_00007sq_v01_00002cs_01_00076en_01.mrc" #untilted
	img2name = "08sep18b_a_00025gr_00007sq_v01_00002cs_v01_00076en_00.mrc" #tilted
	imgpath = "/ami/data00/leginon/08sep18b/rawdata/"
	tiltdiff = 50.0
	coord = [(100,100),(101,100),]
	#correct is: ??, ??
	#runTestShift(img1name, img2name, imgpath, tiltdiff, coord)

	### ribosome RCT data
	img1name = "08oct24d_00010sq_v01_00002cs_01_00024en_01.mrc" #untilted
	img2name = "08oct24d_00010sq_v01_00002cs_00_00024en_00.mrc" #tilted
	imgpath = "/ami/data00/leginon/08oct24d/rawdata/"
	tiltdiff = 50.0
	coord = [(500,500),(501,500),]
	#correct is: ??, ??
	runTestShift(img1name, img2name, imgpath, tiltdiff, coord)

	### yarden RCT data
	img1name = "08oct28a_a_00032gr_00034sq_00002cs_01_00015en_01.mrc" #untilted
	img2name = "08oct28a_a_00032gr_00034sq_00002cs_00_00015en_00.mrc" #tilted
	imgpath = "/ami/data00/leginon/08oct28a/rawdata/"
	tiltdiff = 50.0
	coord = [(500,500),(501,500),]
	#correct is: ??, ??
	#runTestShift(img1name, img2name, imgpath, tiltdiff, coord)

	### pick-wei OTR data
	img1name = "08aug02a_00025sq_v01_00002cs_01_00010en_01.mrc" #otr1
	img2name = "08aug02a_00025sq_v01_00002cs_00_00010en_00.mrc" #otr2
	imgpath = "/ami/data00/leginon/08aug02a/rawdata/"
	tiltdiff = 1.0
	coord = [(400,600),(401,600),]
	#correct is: 600, 690
	#runTestShift(img1name, img2name, imgpath, tiltdiff, coord)

	### groEL SAT data
	img1name = "08mar29a_00037gr_00012sq_v01_00002cs_00_00020en_00.mrc" #untilted
	img2name = "08mar29a_00037gr_00012sq_v01_00002cs_01_00020en_01.mrc" #tilted
	imgpath = "/ami/data15/leginon/08mar29a/rawdata/"
	tiltdiff = 15.0
	coord = [(400,600),(401,600),]
	#correct is: 345, 620
	#runTestShift(img1name, img2name, imgpath, tiltdiff, coord)
	#runTestShift(img1name, img2name, imgpath, tiltdiff, [])
	


