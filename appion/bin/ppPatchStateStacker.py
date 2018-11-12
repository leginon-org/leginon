#!/usr/bin/env python

#pythonlib
import os
import numpy
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apDBImage
from appionlib import apFile
from appionlib.apCtf import ctfdb
#pyami
from pyami import mrc, imagefun
from leginon import leginondata

class PhasePlateTestStacker(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		### strings
		#self.parser.add_option("--session", "--sessionname", dest="sessionname",
		#	help="Session name", metavar="NAME")

	#=====================
	def checkConflicts(self):
		pass
	'''
		### check for requirement
		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a Session name, e.g., --session=09feb12b")
		if self.params['projectid'] is None:
			apDisplay.printError("Please provide a Project database ID, e.g., --projectid=42")
		#if self.params['description'] is None:
		#	apDisplay.printError("Please provide a Description, e.g., --description='awesome data'")
	'''
	#=====================
	def onInit(self):
		"""
		standard appionScript
		"""
		self.sessiondata = self.getSessionData()
		return

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "pptest"

	#=====================
	def start(self):
		for pp_number in range(1,self.getTotalPhasePlates()+1):
			ppimages = self.getPPTestImages(pp_number)
			print pp_number, ppimages.keys()
			apDisplay.printMsg('Phase Plate %d patch state test contains %d images' % (pp_number, len(ppimages.keys())))
			if len(ppimages.keys()):
				outputfile = os.path.join(self.params['rundir'],'%s_ph%d_power.mrc' % (self.sessiondata['name'], pp_number))
				self.stackPowerSpectra(ppimages, outputfile, (2048,2048), self.getPatchesPerPlate())

	#=====================
	#===================== custom functions
	#=====================
	def getPPTestImages(self, pp_number=1):
		allimages = apDatabase.getAllImagesFromDB(self.sessiondata['name'])
		tem = allimages[0]['scope']['tem']
		logs = self.getPPTestLogs(tem, pp_number)
		ppimage_dict = self.organizeLogdata(logs)
		return ppimage_dict

	def getTotalPhasePlates(self):
		# Shoule come from instruments.cfg
		return 6

	def getPatchesPerPlate(self):
		return 76

	def getPPTestLogs(self, temdata, pp_number=1):
		q = leginondata.PhasePlateTestLogData(tem=temdata)
		q['phase plate number'] = pp_number
		q['test type'] = 'patch state'
		r = q.query()
		if not r:
			return []
		logs = []
		for logdata in r:
			if logdata['image']['session'].dbid == self.sessiondata.dbid:
				logs.append(logdata)
		return logs

	def organizeLogdata(self,datalist):
		rdict = {}
		for logdata in datalist:
			rdict[logdata['patch position']] = logdata['image']
			alignedimage = self.getRecentAlignedImage(logdata['image'])
			if alignedimage:
				rdict[logdata['patch position']] = alignedimage
		return rdict

	def getRecentAlignedImage(self, imagedata):
		r = appiondata.ApDDAlignImagePairData(source=imagedata).query(results=1)
		if r:
			return r[0]['result']

	def stackPowerSpectra(self, ppimages, outputfile, shape=(2048,2048), totalpatch=76, images_per_row=19):
		if not ppimages:
			return
		for i in range(1,totalpatch+1):
			if i in ppimages.keys():
				print ppimages[i]['filename']
				a = ppimages[i]['image'][:shape[0],:shape[1]]
				calc_stats = True
			else:
				a = numpy.zeros(shape)
				calc_stats = False
			power = imagefun.power(a)
			a = imagefun.bin(power,4)
			if i == 1:
				mrc.write(a,outputfile)
			else:
				mrc.append(a,outputfile, calc_stats)
		rows = totalpatch / images_per_row
		h = mrc.readHeaderFromFile(outputfile)
		headerdict = {'my':h['my']*images_per_row,'ny':h['ny']*images_per_row,'nz':rows}
		mrc.update_file_header(outputfile, headerdict)
		print outputfile

#=====================
#=====================
#=====================
if __name__ == '__main__':
	app = PhasePlateTestStacker()
	app.start()
	app.close()





