#!/usr/bin/env python
from leginon import leginondata
from leginon import ptolemyhandler as ph
from appionlib import appionScript, apDisplay
from appionlib import apDDResult
from appionlib.apCtf import ctfdb


class PtolemySessionUploader(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --projectid=## --runname=<runname> --session=<session> "
			+"--preset=<preset>' --commit [options]")
		self.parser.add_option("--preset", dest="preset",
			help="Image preset associated with processing run, e.g. --preset=en", metavar="PRESET")
		self.parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")

	#=====================
	def checkConflicts(self):
		if self.params['sessionname'] and self.params['expid']:
			if leginondata.SessionData(name=self.params['session']).query(results=1)[0] != self.params['expId']:
				apDisplay.printError('--session and --expid not on the same session.')
		if not self.params['sessionname'] and self.params['expid']:
			s = leginondata.SessionData().direct_query(self.params['expid'])
			self.params['session'] = s['name']
		if self.params['preset']:
			p = leginondata.PresetData(name=self.params['preset']).query(results=1)
			if not p:
				apDisplay.printError('Preset %s not found in this session' % self.params['preset'])

	#=====================.
	def start(self):
		self.short_hole_image_ids = []
		atlases = self.getGridAtlasList()
		for a in atlases:
			print(a.dbid)
			self.processGridAtlas(a)
		self.processVisitedHoles()

	def getGridAtlasList(self):
		atlases = leginondata.ImageTargetListData(session=self.sessiondata, mosaic=True).query()
		atlases.reverse()
		return atlases

	def processGridAtlas(self, imagetargetlist):
		imagelists = leginondata.ImageListData(targets=imagetargetlist).query()
		for imagelist in imagelists:
			self._processGridAtlasImageList(imagelist)

	def _processGridAtlasImageList(self, imagelist):
		grid_id = imagelist.dbid
		squares = leginondata.PtolemySquareData(session=self.sessiondata,grid_id=grid_id).query()
		tile_ids = list(set(map((lambda x: x['tile_id']), squares)))
		tile_ids.sort()
		print('processing %d tiles from mosaic %s' % (len(tile_ids), imagelist['targets']['label']))
		for t in tile_ids:
			print('processing tile image %d' % t)
			tile_image = leginondata.AcquisitionImageData().direct_query(t)
			ph.push_lm(tile_image)
		if len(tile_ids) > 0:
			self.processMm(imagelist)

	def processMm(self, imagelist):
		grid_id = imagelist.dbid
		square_q = leginondata.PtolemySquareData(session=self.sessiondata,grid_id=grid_id)
		holes = leginondata.PtolemyHoleData(session=self.sessiondata).query()
		hole_image_ids = list(set(map((lambda x: x['image'].dbid), holes)))
		hole_image_ids.sort()
		# you may shorten the list by using a subset
		self.short_hole_image_ids = list(hole_image_ids)
		for t in self.short_hole_image_ids:
			print('processing mm image %d' % t)
			hole_image = leginondata.AcquisitionImageData().direct_query(t)
			pref = leginondata.ScoreTargetFinderPrefsData(image=hole_image).query(results=1)
			if not pref:
				print('hole has no pref', hole_image['filename'])
				continue
			ice0 = pref[0]['ice-zero-thickness']
			ph.set_noice_hole_intensity(ice0)
			ph.push_and_evaluate_mm(hole_image)

	def processVisitedHoles(self):
		preset_q = leginondata.PresetData(session=self.sessiondata, name=self.params['preset'])
		images = leginondata.AcquisitionImageData(preset=preset_q).query()
		images.reverse()
		print('processing %d exposure images' % len(images))
		for imgdata in images:
			self.unaligned = None
			self.processImage(imgdata)
			self.commitToDatabase(imgdata)

	#======================
	def processImage(self, imgdata):
		if not imgdata['target']['ptolemy_hole']:
			apDisplay.printWarning('Not ptolemy active learning image')
			self.icedata = None
			self.ctfvalue = None
			return
		if imgdata['target']['image'].dbid not in self.short_hole_image_ids:
			apDisplay.printWarning('Not from short list of hole image')
			self.icedata = None
			self.ctfvalue = None
			return
		if imgdata['camera']['align frames']:
			dd = apDDResult.DDResults(imgdata)
			self.unaligned = dd.getAlignImagePairData()['source']
		else:
			self.unaligned = imgdata
		apDisplay.printMsg('processing %s' % (imgdata['filename']))
		self.icedata = self.getIceThicknessData(self.unaligned)
		ctfvalue, conf = ctfdb.getBestCtfValueForImage(imgdata)
		self.ctfvalue = ctfvalue

	#======================
	def commitToDatabase(self, imgdata):
		if not self.unaligned or not self.unaligned['target']['ptolemy_hole']:
			# Not valid to learn
			return
		if not self.ctfvalue or not self.icedata:
			# Not valid to learn
			return
		# post ctf resolution and ice thickness to ptolemy
		ctf_res = min(self.ctfvalue['resolution_50_percent'], self.ctfvalue['ctffind4_resolution']) #Angstrom
		thickness = self.icedata[0]['thickness']*1e9 #??? nm
		hole_ids = [self.unaligned['target']['ptolemy_hole']['hole_id'],]
		ctfs = [ctf_res,]
		ice_thicknesses = [thickness,]
		ph.visit_holes(hole_ids, ctfs, ice_thicknesses)
		apDisplay.printMsg('inserted %d visited holes in session %s' % (len(hole_ids), self.unaligned['session']['name']))
		return

	def getIceThicknessData(self, imgdata):
		return leginondata.ObjIceThicknessData(image=imgdata).query(results=1)

#=====================
if __name__ == "__main__":
	tester = PtolemySessionUploader()
	tester.start()
	tester.close()
