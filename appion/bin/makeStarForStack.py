#!/usr/bin/env python

from appionlib import appionScript
from appionlib import starFile
from appionlib import apDisplay
from appionlib import apStack
from appionlib.apCtf import ctfdb
import sys
import os


class MakeStarForStack(appionScript.AppionScript):
	#=====================
	def __init__(self):
		"""
		Starts a new function and gets all the parameters
		overrides appionScript
		"""
		appionScript.AppionScript.__init__(self)
	
	def setupParserOptions(self):
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int", help="Stack database id", metavar="ID#")
		self.parser.add_option("-o", dest="outstar", type="str", help="Output star file name")
		
	def checkConflicts(self):
		pass
	
	def start(self):
		"""
		for each particle in the stack, get the information that RELION needs
		"""
		stackPartList = apStack.getStackParticlesFromId(self.params['stackid'])
		nptcls=len(stackPartList)
		currentImageId = stackPartList[0]['particle']['image'].dbid
		count = 0
		imagenumber=1
		partParamsList = []
		sys.stderr.write("reading stack particle data\n")
		
		#create list of dictionaries that will be passed to starFile maker later
		for stackPart in stackPartList:
			count += 1
			if count % 100 == 0:
				sys.stderr.write(".")
			if count % 10000 == 0:
				sys.stderr.write("\nparticle %d of %d\n"%(count, nptcls))
			
			# extra particle number information not read by Relion
			if count != stackPart['particleNumber']:
				apDisplay.printWarning("particle number in database is not in sync")
							
			partParams = {}
			partParams['ptclnum'] = count
			
			### get image data
			imagedata = stackPart['particle']['image']
			if imagedata.dbid != currentImageId:
				imagenumber+=1
				currentImageId=imagedata.dbid
			partParams['filmNum'] = imagenumber
			#print partParams['filmNum']
			partParams['kv'] = imagedata['scope']['high tension']/1000.0
			partParams['cs'] =imagedata['scope']['tem']['cs']*1000
			### get CTF data from image			
			ctfdata = ctfdb.getBestCtfValue(imagedata, msg=False, sortType='maxconf')
			if ctfdata is not None:
				# use defocus & astigmatism values
				partParams['defocus1'] = abs(ctfdata['defocus1']*1e10)
				partParams['defocus2'] = abs(ctfdata['defocus2']*1e10)
				partParams['angle_astigmatism'] = ctfdata['angle_astigmatism']
				partParams['amplitude_contrast'] = ctfdata['amplitude_contrast']
			else:
				apDisplay.printError("No ctf information for particle %d in image %s"%(count, imagedata['filename']))
			partParamsList.append(partParams)
		
		###now make star file
		
		#first make header
		star = starFile.StarFile(self.params['outstar'])
		labels = ['_rlnImageName', '_rlnMicrographName',
			'_rlnDefocusU', '_rlnDefocusV', '_rlnDefocusAngle', '_rlnVoltage',
			'_rlnSphericalAberration', '_rlnAmplitudeContrast', 
		]

		valueSets = [] #list of strings for star file
		
		###now make particle data
		for partParams in partParamsList:
			relionDataLine = ("%d@start.mrcs mic%d %.6f %.6f %.6f %d %.6f %.6f"
				%( partParams['ptclnum'], partParams['filmNum'],
					partParams['defocus2'], partParams['defocus1'], partParams['angle_astigmatism'], 
					partParams['kv'], partParams['cs'], partParams['amplitude_contrast'],
									
				))
			valueSets.append(relionDataLine)
		star.buildLoopFile( "data_", labels, valueSets )
		star.write()


if __name__ == '__main__':
	makeStarForStack=MakeStarForStack()
	makeStarForStack.start()
	makeStarForStack.close()
	
