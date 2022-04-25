#!/usr/bin/env python
from appionlib import appionScript
from appionlib import appiondata
from leginon import leginondata
import sys

class ContourTubeCircleFileGenerator(appionScript.AppionScript):
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

		file = open('contourpickerTubeCircleData-' + sessionname + '.txt','w')
		file.write('experiment_name ' + sessionname + '\n')
		file.write('experiment_description ' + sessiond[0]['comment'] + '\n')

		numimages = 0
		for imgdata in imgtree:
			partq['image'] = imgdata
			partd = partq.query()
			if len(partd)>0:
				numimages+=1
		file.write('nimages ' + str(numimages) + '\n')

		numparticles = 0.0
		numcircles = 0.0
		numtubes = 0.0
		for imgdata in imgtree:
			partq['image'] = imgdata
			partd = partq.query()
			maxversion = 0
			for part in partd:
				if int(part['version'])>maxversion and part['runname']==runname:
					maxversion = int(part['version'])
			for part in partd:
				if int(part['version'])==maxversion and part['runname']==runname:
					numparticles+=1
					if part['particleType']=='Circle':
						numcircles+=1	
					if part['particleType']=='Tube':
						numtubes+=1	
		file.write('nparticles ' + str(numparticles) + '\n')
		if numparticles == 0:
			precenttubes = 0
			file.write('%tubes ' + str(0.0))
		else:
			percenttubes = numtubes/numparticles
			percent = percenttubes*100
			percent *= 100
			percent = int(percent)
			percent = percent / 100.0
			file.write('%tubes ' + str(percent))

#=====================
#=====================
if __name__ == '__main__':
	s = ContourTubeCircleFileGenerator()
	s.start()
	s.close()
