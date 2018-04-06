# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx

import leginon.gui.wx.Choice
import leginon.gui.wx.Events
import leginon.gui.wx.Node
import leginon.gui.wx.Presets
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Dialog

class AlignDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, node):
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, 'Align Grid Atlas')
		self.imsize = 384
		self.node = node
		self.parent = parent
		self.targets = {}
		self.choices = {}
		self.old_session_choices = {}


		szmain = wx.GridBagSizer(2, 2)
		box = wx.StaticBox(self, -1)
		sbsz = wx.StaticBoxSizer(box, wx.HORIZONTAL)
		bsz = wx.BoxSizer(wx.HORIZONTAL)
		# target image panels
		szimages = wx.BoxSizer(wx.HORIZONTAL)
		for key in ('old','new'):
			sz = self.createTargetPanelSizer(key)
			szimages.Add(sz, 1, wx.EXPAND)
		
		szbutton = self.createButtons()

		atlas_names = self.node.getAlignerOldMosaicNames()
		self.setOldMosaicChoices(atlas_names)

		szmain = wx.GridBagSizer(5,5)
		szmain.Add(szimages, (0, 0), (1, 1), wx.EXPAND)
		szmain.Add(szbutton, (1, 0), (1, 1), wx.ALL, border=5)

		szmain.AddGrowableRow(0)
		szmain.AddGrowableCol(0)

		self.SetSizerAndFit(szmain)
		self.SetAutoLayout(True)
		self.onInit()

	def onInit(self):
		# bindings
		self.Bind(wx.EVT_BUTTON, self.onLoad, self.bload)
		self.Bind(wx.EVT_BUTTON, self.onStart, self.bstart)
		self.Bind(leginon.gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(wx.EVT_BUTTON, self.onAccept, self.baccept)
		self.Bind(wx.EVT_CHOICE, self.onOldSessionSelected, self.oldsession_selector)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.enableLoad()
		self.setNewMosaicSelection()
		self.targets['new'].selectiontool.setDisplayed('target', True)
		self.targets['old'].selectiontool.setDisplayed('target', True)

	def setNewMosaicSelection(self):
		self.choices['new'].SetStringSelection(self.node.getMosaicName())
		self.choices['new'].Disable()
		# initialize old with current mosaic
		self.choices['old'].SetStringSelection(self.node.getMosaicName())

	def createOldSessionSizer(self):
		label = wx.StaticText(self, -1, 'From Session:')
		all_keys, current_key = self.node.getAlignerOldSessionKeys()
		self.oldsession_selector = leginon.gui.wx.Choice.Choice(self, -1, choices=all_keys)
		self.oldsession_selector.SetStringSelection(current_key)
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.oldsession_selector, (0, 1), (1, 1))
		return sz

	def createNewSessionSizer(self):
		label = wx.StaticText(self, -1, 'In This Session')
		current_key = self.node.getAlignerNewSessionKey()
		fake_selector = leginon.gui.wx.Choice.Choice(self, -1, choices=[current_key,])
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(fake_selector, (0, 1), (1, 1))
		return sz

	def createTargetPanelSizer(self,key):	
		# Choice
		atlas_names = self.node.getMosaicNames()
		label = wx.StaticText(self, -1, '%s Atlas ' % (key,))
		self.choices[key] = leginon.gui.wx.Choice.Choice(self, -1, choices=atlas_names)

		self.targets[key] = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1,mode='vertical',imagesize=(self.imsize,self.imsize))
		self.targets[key].addTargetTool('guide', color=wx.GREEN, target=True,numbers=True)
		self.targets[key].addTargetTool('target', color=wx.RED, numbers=True)
		self.targets[key].setTargets('guide', [])
		self.targets[key].setTargets('target', [])
		sz = wx.BoxSizer(wx.VERTICAL)
		szatlas = wx.GridBagSizer(2, 2)
		szatlas.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szatlas.Add(self.choices[key], (0, 1), (1, 1))
		if key == 'old':
			szold = self.createOldSessionSizer()
			szatlas.Add(szold, (1, 0), (1, 2))
		else:
			sznew = self.createNewSessionSizer()
			szatlas.Add(sznew, (1, 0), (1, 2))
		sz.Add(szatlas, 0, wx.EXPAND)
		sz.Add(self.targets[key], 1, wx.EXPAND)
		return sz

	def onOldSessionSelected(self, evt):
		session_key = self.oldsession_selector.GetStringSelection()
		atlas_names = self.node.onSelectOldSession(session_key)
		self.setOldMosaicChoices(atlas_names)

	def setOldMosaicChoices(self,names):
		# This part is needed for wxpython 2.8.  It can be replaced by Set function in 3.0
		self.choices['old'].Clear()
		if len(names) == 0:
			self.disableAll()
		else:
			self.enableLoad()
		for name in names:
			self.choices['old'].Append(name)

	def createButtons(self):
		self.bload = wx.Button(self, -1, 'Load')
		self.bload.Enable(True)
		self.bstart = wx.Button(self, -1, 'Transfer Targets')
		self.baccept = wx.Button(self, -1, 'Accept')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bload, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bstart, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.baccept, (0, 2), (1, 1), wx.ALIGN_CENTER)
		return szbutton	
		
	def onLeftImageClicked(self, evt):
		self.node.onAlignImageClicked('left', evt.xy)

	def onRightImageClicked(self, evt):
		self.node.onAlignImageClicked('right', evt.xy)

	def onLoad(self,evt):
		current_choice = self.choices['old'].GetStringSelection()
		self.loadOld(current_choice)
		self.loadNew()
		self.enableStart()

	def loadOld(self,mosaic_name):
		key = 'old'
		self.node.setAlignerOldMosaic(mosaic_name)
		self.targets[key].setImage(self.node.getAlignerOldMosaicImage())
		self.targets[key].selectiontool.tools['guide'].togglebuttons['numbers'].SetValue(True)
		self.targets['old'].setTargets('target', self.node.getAlignerOldTargets())
		self.targets[key].selectiontool.setTargeting('target',True)
		# The last one to setTargeting to True will also set to select
		self.targets[key].selectiontool.setTargeting('guide',True)

	def loadNew(self):
		key = 'new'
		self.targets[key].setImage(self.node.getAlignerNewMosaicImage())
		self.targets[key].selectiontool.setTargeting('guide',True)
		self.targets[key].selectiontool.tools['guide'].togglebuttons['numbers'].SetValue(True)

	def onStart(self, evt):
		oldguides = self.targets['old'].getTargets('guide')
		newguides = self.targets['new'].getTargets('guide')

		self.enableStartAccept()
		affine_matrix, residual = self.node.calculateTransform(oldguides, newguides)
		newtargets = self.node.transformTargets(affine_matrix,self.targets['old'].getTargets('target'))
		self.targets['new'].setTargets('target', newtargets)

	def onSetImage(self, evt):
		if evt.typename == 'left':
			self.targets['old'].setImage(evt.image)
		else:
			self.targets['new'].setImage(evt.image)

	def disableAll(self):
		self.bload.Enable(False)
		self.bstart.Disable()
		self.baccept.Disable()

	def enableLoad(self):
		self.choices['old'].Enable(True)
		self.bload.Enable(True)
		self.bstart.Disable()
		self.baccept.Disable()

	def enableStart(self):
		self.choices['old'].Enable(True)
		self.bstart.Enable(True)
		self.baccept.Disable()

	def enableStartAccept(self):
		self.enableStart()
		self.baccept.Enable(True)

	def enableAccept(self):
		self.bstart.Disable()
		self.baccept.Enable(True)

	def onAccept(self, evt):
		targets = self.targets['new'].getTargets('target')
		self.node.acceptResults(targets)
		self.onClose(evt)

	def onClose(self, evt):
		self.enableStart()
		self.EndModal(0)

if __name__ == '__main__':
	from pyami import numpil
	from pyami import affine
	import numpy

	class Node(object):
		atlases = {'old':{},'new':{}}
		def getMosaicNames(self):
			return self.atlases.keys()

		def getMosaicName(self):
			return 'old'

		def getAlignerOldMosaicNames(self):
			return self.getMosaicNames()
		def setAlignerOldMosaic(self,name):
			pass
		def getAlignerNewMosaicImage(self):
			return self.readImage('../../sq_example.jpg')
		def getAlignerOldMosaicImage(self):
			return self.getAlignerNewMosaicImage()
		def getAlignerOldTargets(self):
			return [(100,100),(300,300),(100,300)]
		def acceptResults(self,targets):
			print 'transformed target c,r: ', map((lambda t: (t.x,t.y)),targets)
		def readImage(self,filepath):
			return numpil.read(filepath)
		def getAlignerNewSessionKey(self):
			return 'new session'
		def getAlignerOldSessionKeys(self):
			return ['old session','new session'], 'new session'
		def calculateTransform(self, targets1, targets2):
			points1 = map((lambda t: (t.x,t.y)),targets1)
			points2 = map((lambda t: (t.x,t.y)),targets2)
			if len(points1) < 3:
				return numpy.matrix([(1,0,0),(0,1,0),(0,0,1)]),0.0
			print 'from',points1
			print 'to',points2
			A, residule = affine.solveAffineMatrixFromImageTargets(points1,points2)
			self.Affine_matrix = A
			print A
			return A, residule

		def transformTargets(self, affine_matrix, targets1):
			points1 = map((lambda t: (t.x,t.y)),targets1)
			points2 = affine.transformImageTargets(affine_matrix, points1)
			return points2

	class App2(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Align Mosaic Test')
			node = Node()
			dialog = AlignDialog(frame, node)
			dialog.Show()
			panel = wx.Panel(frame, -1)
			return True

	app = App2(0)
	app.MainLoop()
	app.Close()
