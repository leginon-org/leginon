#!/usr/bin/env python
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apDisplay
from leginon import leginondata
import os
import sys

class ContourFileGenerator(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		### Set usage
		self.parser.set_usage("Usage: %prog --projectid=## --runname=<runname> --session=<session> preset=<preset>"
			+"--preset=<preset> --description='<text>' --commit [options]")
		### Input value options
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
#		self.parser.add_option("--runid", dest="contourrunid", type="int",
#			help="contour run id", metavar="#")
		self.parser.add_option("--preset", dest="preset", type="str",
			help="preset name to be process, e.g. --preset=en", metavar="NAME")
		pass

	def checkConflicts(self):
		pass

	def setProcessingDirName(self):
		self.processdirname = 'extract'

	#=====================
	def start(self):
		sessionname = self.params['sessionname']
		runname = self.params['runname']
		preset = self.params['preset']

		sessionq = leginondata.SessionData(name=sessionname)
		presetq=leginondata.PresetData(name=preset)
		imgquery = leginondata.AcquisitionImageData()
		imgquery['preset']  = presetq
		imgquery['session'] = sessionq
		imgtree = imgquery.query(readimages=False)
		partq = appiondata.ApContourData()
		sessiond = sessionq.query()
		selectionid = apParticle.getSelectionIdFromName(runname, sessionname)
		if not selectionid:
			apDisplay.printWarning('No Object Tracing Run found in database, Skipping.......')
			return
		selectionrundata = apParticle.getSelectionRunDataFromID(selectionid)


		file = open('contourpickerData-' + sessionname + '.txt','w')
		file.write('session_id ' + runname + '\n')
		file.write('usr_id ' + os.getlogin() + '\n')
		file.write('experiment_name ' + sessionname + '\n')
		file.write('experiment_description ' + sessiond[0]['comment'].strip() + '\n')
		file.write('nimages ' + str(len(imgtree)) + '\n')

		for imgdata in imgtree:
			file.write('START_IMAGE' + '\n')
			partq['image'] = imgdata
			partq['selectionrun'] = selectionrundata
			partd = partq.query()
			if len(partd)>0:
				file.write('image_refID ' + str(partd[0]['image'].dbid) + '\n') 
			file.write('image_name ' + imgdata['filename'] + '\n') 
			if len(partd)>0:
				file.write('time_roi ' + str(partd[0].timestamp) + '\n') 
			#file.write('time_roi ' + partd[0]['DEF_timestamp'] + '\n') 
			file.write('dfac = 1\n')
			maxversion = 0
			numparticles = 0
			for part in partd:
				if int(part['version'])>maxversion:
					maxversion = int(part['version'])
			for part in partd:
				if int(part['version'])==maxversion:
					numparticles+=1
			file.write('version_id ' + str(maxversion) + '\n')
			file.write('ncontours ' + str(numparticles) + '\n')
			pointq = appiondata.ApContourPointData()
			for part in partd:
				if int(part['version'])==maxversion:
			#		file.write('contour_number ' + )
					file.write('method_used ' + part['method'] + ' ')
					pointq['contour'] = part
					pointd = pointq.query()
					for point in pointd:
						file.write(str(point['x']) + ',' + str(point['y']) + ';')
					file.write('\n')
			file.write('END_IMAGE' + '\n')
			
#=====================
#=====================
if __name__ == '__main__':
	s = ContourFileGenerator()
	s.start()
	s.close()
