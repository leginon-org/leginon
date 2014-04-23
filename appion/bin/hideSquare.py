#!/usr/bin/env python

import os
import sys
import time
import sinedon
import MySQLdb
from appionlib import apDisplay
from appionlib import apDatabase
import leginon.leginondata

def hideImage(imgid):
	imgdata=leginon.leginondata.AcquisitionImageData.direct_query(imgid)
	apDatabase.setImgViewerStatus(imgdata, False)

if __name__ == '__main__':
	# 898749
	if len(sys.argv) < 2:
		print "Usage: hideSquare.py <square id>"
	squareid = int(sys.argv[1])

	dbconf = sinedon.getConfig('leginon.leginondata')
	db     = MySQLdb.connect(**dbconf)
	db.autocommit(True)
	cursor = db.cursor()

	query = ( "SELECT "
		+" image.`DEF_id`, image.filename "
		+" FROM AcquisitionImageData AS image "
		+" LEFT JOIN AcquisitionImageTargetData AS target "
		+"   ON image.`REF|AcquisitionImageTargetData|target` = target.`DEF_id` "
		+" WHERE target.`REF|AcquisitionImageData|image` = '"+str(squareid)+"' "
	)
	print query
	cursor.execute(query)
	results = cursor.fetchall()
	print "results: ", len(results)
	if len(results) == 0:
		apDisplay.printError("No images found")

	for r in results:
		print r[0], apDisplay.short(r[1])
		time.sleep(0.2)
		hideImage(int(r[0]))
		
