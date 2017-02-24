#!/usr/bin/env python

from leginon import leginondata
import sys

class AtlasCopier(object):
	def __init__(self,old_sessionname, new_sessionname,gr_filename):
		has_error = self.setSessions(old_sessionname,new_sessionname)
		if has_error:
			sys.exit(1)
		has_error = self.setOldTargetList(gr_filename)
		if has_error or self.hasNewGrImage(gr_filename):
			sys.exit(1)
		self.run()

	def setSessions(self,old_sessionname,new_sessionname):
		try:
			self.old_session = leginondata.SessionData(name=old_sessionname).query()[0]
			self.new_session = leginondata.SessionData(name=new_sessionname).query()[0]
		except:
			print 'Error: At least one session names Not found. Create new session first'
			return True

	def setOldTargetList(self,gr_filename):
		try:
			grimage = leginondata.AcquisitionImageData(session=self.old_session,filename=gr_filename.split('.mrc')[0]).query()[0]
			self.old_targetlist = grimage['target']['list']
			if not self.old_targetlist['mosaic']:
				raise ValueError
		except:
			print 'Error: Filename not found in a grid atlas of the old session'
			return True

	def hasNewGrImage(self,old_filename):
		new_filename = self.getNewImageFileName(old_filename)
		new_images = leginondata.AcquisitionImageData(session=self.new_session,filename=new_filename).query()
		if new_images:
			print 'Error: Image %s exists in new session %s, can not repeat' % (new_filename,self.new_session['name'])
			return True
		return False


	def run(self):
		q = leginondata.ImageTargetListData(initializer=self.old_targetlist)
		q['session'] = self.new_session
		q.insert()
		self.new_targetlist = leginondata.ImageTargetListData().direct_query(q.dbid)
		old_grimages = self.getImagesFromTargetList(self.old_targetlist)
		old_grimages.reverse()
		self.makeNewImagesFromOld(old_grimages)
		new_grimages = self.getImagesFromTargetList(self.new_targetlist)
		new_grimages.reverse()
		self.insertNewMosaicTiles(new_grimages)
		self.transferTargetsOnAtlas(old_grimages,new_grimages)

	def makeNewImagesFromOld(self,old_grimages):
		for imagedata in old_grimages:
			self.insertNewTarget(imagedata['target'],'new')
			processing_target = self.insertNewTarget(imagedata['target'],'processing')

			imageq = leginondata.AcquisitionImageData(initializer=imagedata)
			imageq['session'] = self.new_session
			imageq['target'] = processing_target
			imageq['image'] = imagedata['image']
			imageq['filename'] = self.getNewImageFileName(imagedata['filename'])
			imageq.insert()
			print 'New image saved as %s in session %s' % (imageq['filename'],imageq['session']['name'])
			self.insertNewTarget(imagedata['target'],'done')
		print ''
		return

	def getNewImageFileName(self,old_filename):
		return old_filename.replace(self.old_session['name'],self.new_session['name'])
		
	def insertNewTarget(self,old_target,new_status):
			targetq = leginondata.AcquisitionImageTargetData(initializer=old_target)
			targetq['session'] = self.new_session
			targetq['list'] = self.new_targetlist
			targetq['status'] = new_status
			targetq.insert()
			return targetq

	def getImagesFromTargetList(self,targetlist,status=None):
		targetq = leginondata.AcquisitionImageTargetData(list=targetlist,status=status)
		images = leginondata.AcquisitionImageData(target=targetq).query()
		return images

	def insertNewMosaicTiles(self,images):
		for imagedata in images:
			q = leginondata.MosaicTileData(session=self.new_session,list=imagedata['list'],image=imagedata)
			q.insert()

	def transferTargetsOnAtlas(self,old_images,new_images):
		for i in range(len(old_images)):
			old_targets = leginondata.AcquisitionImageTargetData(image=old_images[i]).query()
			if not old_targets:
				continue
			print 'Transfering targets from %s' % (old_images[i]['filename'])
			# old first
			old_targets.reverse()
			# make new target list
			qlist = leginondata.ImageTargetListData(session=self.new_session,image=new_images[i])
			qlist.insert()
			# new targets
			for old in old_targets:
				q = leginondata.AcquisitionImageTargetData(initializer=old)
				q['session'] = self.new_session
				q['list'] = qlist
				q['image'] = new_images[i]
				q.insert()
			print 'Transfered targets to %s' % (new_images[i]['filename'])
			print ''


if __name__ == '__main__':
	if len(sys.argv)!= 4:
		print 'Usage: python copyatlas.py <old_session_name> <new_session_name> <image filename>'
		print 'Sessions must exists'
		print '<image filename> is of an image belong to the grid atlas to be copied'
		sys.exit(1)

	old_sessionname = sys.argv[1]
	new_sessionname = sys.argv[2]
	gr_filename = sys.argv[3]

	app = AtlasCopier(old_sessionname, new_sessionname, gr_filename)
