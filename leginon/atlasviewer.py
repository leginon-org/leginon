# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/atlasviewer.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2005-01-28 01:07:41 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import data
import node
import targethandler
import gui.wx.AtlasViewer

class AtlasViewer(node.Node, targethandler.TargetHandler):
	panelclass = gui.wx.AtlasViewer.Panel
	eventinputs = (
		node.Node.eventinputs +
		targethandler.TargetHandler.eventinputs
	)
	eventoutputs = (
		node.Node.eventoutputs +
		targethandler.TargetHandler.eventinputs
	)
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.start()

	def getMosaicTileData(self):
		print 'getMosaicTileData...'
		querydata = data.MosaicTileData(session=self.session)
		tiledatalist = self.research(datainstance=querydata)
		for tiledata in tiledatalist:
			print tiledata['list']
		print 'getMosaicTileData done'

