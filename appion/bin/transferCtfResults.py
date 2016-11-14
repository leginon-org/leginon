#!/usr/bin/env python

#pythonlib
import os
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apDBImage
from appionlib import apFile
from appionlib.apCtf import ctfdb
#pyami
from pyami import fileutil

class TransferCtfResults(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		### strings
		self.parser.add_option("--session", "--sessionname", dest="sessionname",
			help="Session name", metavar="NAME")

		self.parser.add_option("--preset", "--presetname", dest="preset",
			help="Name of Preset to transfer to", metavar="NAME")

		self.parser.add_option("--frompreset", "--frompreset", dest="frompreset",
			help="Name of Preset to transfer to", metavar="NAME")

		self.parser.add_option("--sort", "--sort", dest="sorttype", default="res80",
			help="bestdb ctf sort criteria", metavar="NAME")

		### int
		self.parser.add_option("--ctfrunid", dest="ctfrunid", type="int",
			help="Ctf run to be transferred", metavar="#")

		### true / false
		self.parser.add_option("--bestdb", dest="bestdb", default=False,
			action="store_true", help="transfer best ctf")


	#=====================
	def checkConflicts(self):
		### check for requirement
		if self.params['ctfrunid'] is None and self.params['bestdb'] is False:
			apDisplay.printError("Please provide either a ctfrun or use best ctf in db to transfer")
		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a Session name, e.g., --session=09feb12b")
		if self.params['projectid'] is None:
			apDisplay.printError("Please provide a Project database ID, e.g., --projectid=42")
		#if self.params['description'] is None:
		#	apDisplay.printError("Please provide a Description, e.g., --description='awesome data'")

	#=====================
	def onInit(self):
		"""
		standard appionScript
		"""
		self.sessiondata = self.getSessionData()
		self.rundata = None
		return

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#=====================
	def start(self):
		self.rundata = self.makeNewCtfRun()
		# go through images
		images = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['frompreset'])
		for imgdata in images:
			# Transfer only on non-rejected images
			if apDatabase.getImgCompleteStatus(imgdata) == False:
				apDisplay.printWarning('Skip hidden %s' % apDisplay.short(imgdata['filename']))
				continue
			ctfdata = self.getFromCtfData(imgdata)
			if not ctfdata:
				apDisplay.printWarning('No CTF result for %s' % apDisplay.short(imgdata['filename']))
				continue
			#
			siblings = apDBImage.getAlignedSiblings(imgdata)
			to_imgdata = self.selectImageAtPreset(self.params['preset'], siblings)
			if not to_imgdata:
				apDisplay.printWarning('No corresponding image for %s with preset %s' % (apDisplay.short(imgdata['filename']),self.params['preset']))
				continue
			if self.params['commit']:
				self.transferViewerStatus(imgdata,to_imgdata)
				self.commitToDatabase(ctfdata,to_imgdata)

	#=====================
	#===================== custom functions
	#=====================
	def transferViewerStatus(self,oldimage, newimage):
		status = apDatabase.getImgViewerStatus(oldimage)
		apDatabase.setImgViewerStatus(newimage, status)

	def commitToDatabase(self,old_ctfdata, to_imgdata):
		'''
		copy the graphs and insert the ctf run based on the same params
		'''

		apDisplay.printMsg('transfer ctf result to %s' % apDisplay.short(to_imgdata['filename']))
		old_graphdir = os.path.join(old_ctfdata['acerun']['path']['path'],'opimages')
		new_graphdir = os.path.join(self.rundata['path']['path'],'opimages')
		fileutil.mkdirs(new_graphdir)
		# insert new result
		ctfq = appiondata.ApCtfData(initializer=old_ctfdata)
		ctfq['acerun'] = self.rundata
		ctfq['image'] = to_imgdata
		# copy up to 4 diagnosis graphs
		for i in (1,2,3,4):
			graphid = 'graph%d' % i
			old_graphname = old_ctfdata[graphid]
			if not old_graphname:
				continue
			new_graphname = old_graphname.replace(apDisplay.short(old_ctfdata['image']['filename']), apDisplay.short(to_imgdata['filename']))
			source = os.path.join(old_graphdir, old_graphname)
			destination = os.path.join(new_graphdir, new_graphname)
			if os.path.isfile(source):
				apFile.safeCopy(source, destination)
		ctfq.insert()
		

	def makeNewCtfRun(self):
		'''
		Make new ApAceRunData based on input.
		'''
		# initialize
		q = appiondata.ApAceTransferParamsData(frompreset=self.params['frompreset'],topreset=self.params['preset'])
		if self.params['bestdb']:
			q['criteria'] = 'bestdb '+self.params['sorttype']
		if self.params['ctfrunid']:
			q['criteria'] = 'runid'
			q['run'] = appiondata.ApAceRunData().direct_query(self.params['ctfrunid'])
		newrun = appiondata.ApAceRunData(transfer_params=q)
		newrun['name'] = self.params['runname']
		newrun['path'] = appiondata.ApPathData(path=self.params['rundir'])
		newrun.insert()
		
		return newrun

	def selectImageAtPreset(self, presetname, images):
		for imgdata in images:
			if presetname == 'manual':
				if imgdata['preset'] is None:
					return imgdata
			else:
				if imgdata['preset'] is not None and imgdata['preset']['name']==presetname:
					return imgdata

	def getFromCtfData(self,imgdata):
		### get all CTF parameters,
		if self.params['bestdb']:
			return self.getBestCtfValue(imgdata, False)
		elif self.params['ctfrunid'] is not None:
			return ctfdb.getCtfValueForCtfRunId(imgdata, self.params['ctfrunid'], msg=False)
		else:
			return None

	def getBestCtfValue(self, imgdata, msg=False):
		return ctfdb.getBestCtfValue(imgdata, sortType=self.params['sorttype'], method=None, msg=msg)

#=====================
#=====================
#=====================
if __name__ == '__main__':
	app = TransferCtfResults()
	app.start()
	app.close()





