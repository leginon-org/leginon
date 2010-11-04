#!/usr/bin/python -O

import os
import sys

from pyami import mrc, imagefun
import wx
import Image
from PIL import Image
import time
import math
import random
import numpy
import scipy
from scipy import ndimage
import threading
#import pyami
from pyami import arraystats

#import subprocess
import manualpicker
from appionlib import particleLoop2
from appionlib import apFindEM
from appionlib import appiondata
from appionlib import apParticle
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apMask
from appionlib import apImage
from appionlib import apParam
from appionlib import apPeaks

#Leginon
import leginon.polygon
from leginon.gui.wx import ImagePanel, ImagePanelTools, TargetPanel, TargetPanelTools, SelectionTool
from leginon import leginondata

## need better way to generate a list of easy to distinguish colors
pick_colors = [
	(255,0,0),
	(0,255,0),
	(0,0,255),
	(255,255,0),
	(255,0,255),
	(0,255,255),
	(128,128,0),
	(255,128,128),
]

class ContourPickerPanel(TargetPanel.TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		TargetPanel.TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

	def addTypeTool(self, name, **kwargs):
		if self.selectiontool is None:
			self.selectiontool = SelectionTool.SelectionTool(self)
			if self.mode == "vertical":
				#NEILMODE
				self.statstypesizer.Add(self.selectiontool, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)
			else:
				self.statstypesizer.Add(self.selectiontool, (2, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 3)
		self.selectiontool.addTypeTool(name, **kwargs)
		self.selectiontool.SetSize((300,175))
		self.sizer.SetItemMinSize(self.selectiontool, self.selectiontool.GetSize())
		self.sizer.Layout()

	def addTarget(self, name, x, y):
		super(ContourPickerPanel,self).addTarget(name,x,y)
		if name == self.picker.s:
			self.picker.addManualPoint()

	def deleteTarget(self, target):
		self.picker.deleteTarget(target)
		super(ContourPickerPanel,self).deleteTarget(target)

	def setPickerApp(self,app):
		self.picker = app

	def openImageFile(self, filename):
		self.filename = filename
		if filename is None:
			self.setImage(None)
		elif filename[-4:] == '.mrc':
			image = mrc.read(filename)
			self.setImage(image.astype(numpy.float32))
		else:
			self.setImage(Image.open(filename))

	def getImage(self, filename):
		if filename is None:
			image = None;
		elif filename[-4:] == '.mrc':
			image = mrc.read(filename)
			image = image.astype(numpy.float32)
		else:
			image = Image.open(filename)
		return image

	def _onMotion(self, evt, dc):
		if len(self.selectiontool.getTargets('Tube'))>=2:
			targets = []
			for p in self.selectiontool.getTargets('Tube'):
				targets.append((p.x,p.y))
			tubemem = self.selectiontool.getTargets('TubeMemory')
			tubemem.append(targets[0])
			self.selectiontool.setTargets('TubeMemory', tubemem)
			self.picker.tubeTargets.append(targets)
			self.selectiontool.setTargets('Tube',[])
		self.picker.onMoved(evt)
		super(ContourPickerPanel,self)._onMotion(evt,dc)

	def _onRightClick(self, evt):
		if self.selectedtarget is not None :
			self.deleteTarget(self.selectedtarget)
		super(ContourPickerPanel,self)._onRightClick(evt)

	def _onLeftClick(self, evt):
		if self.selectedtype is not None:
			x, y = self.view2image((evt.m_x, evt.m_y))
			self.addTarget(self.selectedtype.name, x, y)
		if self.selectiontool.isTargeting('Select Particles') or self.selectiontool.isTargeting('Circle') or self.selectiontool.isTargeting('Tube'):
			self.picker.addSinglePoint(evt)
		else:
			self.picker.onEdgeFinding(evt)
		#if self.selectedtype.name == self.picker.s:
		#	self.picker.addManualPoint()

	def Draw(self, dc):
	#	now = time.time()
		super(ContourPickerPanel,self).Draw(dc)
		self.picker.doGraphics()
	#	print 'Drawn', time.time() - now

	def drawContour(self, color, targets, thickness=1):
		dc = wx.MemoryDC()
		dc.SelectObject(self.buffer)
		dc.BeginDrawing()

		dc.SetPen(wx.Pen(color, thickness))
		dc.SetBrush(wx.Brush(color, thickness))
		#if self.scaleImage():
		if False:
			xscale = self.scale[0]
			yscale = self.scale[1]
			#print 'scaled', xscale, yscale
			scaledpoints = []
			for target in targets:
				point = target.x/xscale, target.y/yscale
				scaledpoints.append(point)
		else:
			scaledpoints = [(target[0],target[1]) for target in targets]

		if len(scaledpoints)>=1:
			p1 = self.image2view(scaledpoints[0])
	#		dc.DrawCircle(p1[0],p1[1],1)
			
		for i,p1 in enumerate(scaledpoints[:-1]):
			p2 = scaledpoints[i+1]
			p1 = self.image2view(p1)
			p2 = self.image2view(p2)
	#		dc.DrawCircle(p2[0],p2[1],1)
			dc.DrawLine(p1[0], p1[1], p2[0], p2[1])
		# close it with final edge
		p1 = scaledpoints[-1]
		p2 = scaledpoints[0]
		p1 = self.image2view(p1)
		p2 = self.image2view(p2)
		dc.DrawLine(p1[0], p1[1], p2[0], p2[1])
		

##################################
##
##################################
class PixelCurveMaker:
	class PixelCurveSubData:
		id = 0
		def _init_(self, i):
			self.id = i
			self.radiiToValues = {}

		def addData(self,radius,value):
			self.radiiToValues[radius] = value

		def getData(self):
			return self.radiiToValues

		def smoothData(self):
			for i in self.radiiToValues.keys():
				index = self.radiiToValues.keys().index(i)
				pi = index-1
				if pi<0:
					pi = len(self.radiiToValues.keys())-1
				ni = index+1
				if ni>=len(self.radiiToValues.keys()):
					ni = 0
				average = (self.radiiToValues[i]+self.radiiToValues[self.radiiToValues.keys()[pi]]+self.radiiToValues[self.radiiToValues.keys()[ni]])/3
				self.radiiToValues[i] = average

	class Contour:#stores all the info about one contour
		def _init_(self,size,rangeSize,curveMaker,id):
			self.id = id
			self.maker = curveMaker
			self.thetaToMap = {}
			id = 0
			self.thetalist = []
			self.size = size
			self.rangeSize = rangeSize
			for i in range(size):
				i+=0
				i*=math.pi*2/rangeSize
				self.thetalist.append(i)
				self.thetaToMap[i] = PixelCurveMaker.PixelCurveSubData()
				self.thetaToMap[i]._init_(id)
				id+=1
			self.goodValues = {}
			self.exactValues = {}
			self.average = 0;
		
		def sortedDictValues1(self,adict):
			items = adict.items()
			items.sort()
			return [value for key, value in items]

		def sortedDictValues2(self,adict):
			keys = adict.keys()
			keys.sort()
			return [dict[key] for key in keys]

		def makeCalculations(self):
		#	for p in self.thetaToMap.values():
		#		p.smoothData()
			self.average = 0;
			self.exactValues = {}
			self.goodValues = {}
			num = 0;
			flag = True
			self.thetalist = sorted(self.thetalist)
			for theta in self.thetalist:
				if flag:
					self.average += self.maker.getRadiusOfMajorChange(theta,self,flag=False,id=self.id)
					self.exactValues[theta] = self.maker.getRadiusOfMajorChange(theta,self,flag=False,id=self.id)
				else:
					self.average += self.maker.getRadiusOfMajorChange(theta,self,flag=False)
					self.exactValues[theta] = self.maker.getRadiusOfMajorChange(theta,self,flag=True)
				flag = False
				num+=1
			self.average /=num
			self.goodValues = self.exactValues
			for i in range(0):
				rrange =  range(len(self.thetalist))
			# random.shuffle(rrange)
				for j in rrange:
					theta = self.thetalist[j]
					self.goodValues[theta] = self.maker.getRadiusOfMajorChange(theta,self,flag=True)
		#	self.smoothData()
		#	self.smoothData()
######need mathmatition's help#######################
#		def circulize(self):
#			def dist(target1,target2):
#				return math.sqrt((target1[0]-target2[0])*(target1[0]-target2[0])+(target1[1]-target2[1])*(target1[1]-target2[1]))
#			cx = 0
#			cy = 0
#			num = len(self.goodValues)
#			for i in self.thetalist:
#				x = math.cos(i)*self.gootValues[i]
#				y = math.sin(i)*self.gootValues[i]
#				cx+=x
#				cy+=y	
#		`	cx/=num
#			cy/=num
#			averageR = 0
#			for i in self.thetalist:
#				averageR+=dist((0,0),(math.cos(i)*self.gootValues[i]-cx,math.sin(i)*self.gootValues[i]-cy))
#			averageR/=num
#			tolerance = 2
#			for i in self.thetalist:
#				r = dist((0,0),(math.cos(i)*self.gootValues[i]-cx,math.sin(i)*self.gootValues[i]-cy))
#				if math.fabs(r-averageR)>tolerance:
					 
		def smoothData(self):
			for theta in self.thetalist:
				f = self.getData(theta)
				nextI = self.thetalist.index(theta) + 1
				if nextI > len(self.thetalist)-1:
					nextI = 0
				prevI = self.thetalist.index(theta) - 1
				if prevI < 0:
					prevI = len(self.thetalist)-1
				sum = (f+2*self.getData(self.thetalist[nextI])+2*self.getData(self.thetalist[prevI]))
				num = 5
				if math.fabs(f-sum/num)>5:
					sum-=f
					num-=1
				if math.fabs(self.getData(self.thetalist[nextI])-sum)>5:
					sum-=self.getData(self.thetalist[nextI])
					num-=1
				if math.fabs(self.getData(self.thetalist[prevI])-sum)>5:
					sum-=self.getData(self.thetalist[prevI])
					num-=1
				self.goodValues[theta] = (f+self.getData(self.thetalist[nextI])+self.getData(self.thetalist[prevI]))/3
	
		def addData(self,theta,radius,value):
			self.thetaToMap[theta].addData(radius,value)

		def getData(self,theta):
			return self.goodValues[theta]

		def averageIntensity(self):
			sum = 0
			num = 0
			for i in range(len(self.thetalist)):
				sum += self.thetaToMap[self.thetalist[i]].getData()[self.getData(self.thetalist[i])]
				#sum += self.goodValues[self.thetalist[i]]
				num += 1
			return sum/num
	
	def _init_(self, size, rangeSize):
		self.thetaToMap = {}
		id = 0
		self.thetalist = []
		self.size = size
		self.rangeSize = rangeSize
		for i in range(size):
			i+=0
			i*=math.pi*2/rangeSize
			self.thetalist.append(i)
			self.thetaToMap[i] = self.PixelCurveSubData()
			self.thetaToMap[i]._init_(id)
			id+=1
		self.contours = []
		for i in range(9):
			c = self.Contour()
			self.contours.append(c)
			c._init_(size,rangeSize,self,i*1)

	def addData(self,theta,radius,value):
		self.thetaToMap[theta].addData(radius,value)
		for c in self.contours:
			c.thetaToMap = self.thetaToMap

	def makeCalculations(self):
		for c in self.contours:
			c.makeCalculations()
		self.theContour = self.choseContour()
		self.theContour.smoothData()
		self.theContour.smoothData()

	def choseContour(self):
		max = 0
		contour = None
		for c in self.contours:
	#		print 'average I -> ', c.averageIntensity()
			if c.averageIntensity()>max:
				contour = c
				max = c.averageIntensity()
		return contour	

	def getSMA(self, theta, iter):
		average = 0
		num = 0
		for i in range(iter):
			nextIndex = self.thetalist.index(theta) - i
			if nextIndex < 0:
				nextIndex = len(self.thetalist)+nextIndex
			average+=self.exactValues[self.thetalist[nextIndex]]
			num+=1
		return average/num

	def getAllData(self):
		return self.contours

	def getData(self,theta):
		return self.theContour.goodValues[theta]

	def getRadiusOfMajorChange(self,theta,contour,flag = True,id = 0):
		maxValue = 0
		maxRadius = -1

		svalues = sorted(self.thetaToMap[theta].getData().values())
		for rad in self.thetaToMap[theta].getData():
			if self.thetaToMap[theta].getData()[rad] == svalues[len(svalues)-(id+1)]:
				maxValue = svalues[len(svalues)-(id+1)]
				maxRadius = rad
#			if self.thetaToMap[theta].getData()[rad] > maxValue:
#				maxValue = self.thetaToMap[theta].getData()[rad]
#				maxRadius = rad
##################average method - deprecated#########################################################################################################
#		if flag:
#			tolerance = 2
#			if math.fabs(maxRadius-contour.average)>tolerance:
#				maxValue = 0
#				maxRadius =0
#				for rad in self.thetaToMap[theta].getData():
#					if math.fabs(rad-contour.average)<tolerance:
#						if self.thetaToMap[theta].getData()[rad] > maxValue:
#							maxValue = self.thetaToMap[theta].getData()[rad]
#							maxRadius = rad
######################################################################################################################################################

##################first derivative method#############################################################################################################
		if flag:
			nextIndex = self.thetalist.index(theta) - 1
			if nextIndex == -1:
				nextIndex = len(self.thetalist)-1
			if self.thetalist[nextIndex] in contour.goodValues:
				value = contour.goodValues[self.thetalist[nextIndex]]
			else:
				value = contour.exactValues[self.thetalist[nextIndex]]
			change = maxRadius-value
			tolerance = 3
			if math.fabs(change)>tolerance:
				maxValue = 0
				maxRadius = -1
				for rad in self.thetaToMap[theta].getData():
					if math.fabs(rad-value)<tolerance:
						if self.thetaToMap[theta].getData()[rad] > maxValue:
							maxValue = self.thetaToMap[theta].getData()[rad]
							maxRadius = rad				
			self.imageedgehenrychange = maxRadius-value
######################################################################################################################################################
		return maxRadius

class PickerApp(wx.App):
	def __init__(self, shape='+', size=16, mask=False, labels=[]):
		self.shape = shape
		self.size = size
		self.mask = mask
		self.labels = labels
		self.pick_colors = iter(pick_colors)
		wx.App.__init__(self)
		self.filters = False
		self.index = 0
		self._onClear()
		self.contourTargetMap = {}

	def OnInit(self):
		self.deselectcolor = wx.Color(40,40,40)

		self.frame = wx.Frame(None, -1, 'Manual Particle Picker')
		self.sizer = wx.FlexGridSizer(2,1)

		### VITAL STATS
		self.vitalstats = wx.StaticText(self.frame, -1, "Vital Stats:  ", style=wx.ALIGN_LEFT)
		#self.vitalstats.SetMinSize((100,40))
		self.sizer.Add(self.vitalstats, 1, wx.EXPAND|wx.ALL, 3)

		### BEGIN IMAGE PANEL
		self.panel = ContourPickerPanel(self.frame, -1)

		self.panel.addTargetTool('Select Particles', color=wx.Color(220,20,20), 
			target=True, shape=self.shape, size=self.size)
		self.panel.setTargets('Select Particles', [])
		self.panel.selectiontool.setTargeting('Select Particles', True)

		self.panel.addTargetTool('Region to Remove', color=wx.Color(20,220,20),
			target=True, shape='polygon')
		self.panel.setTargets('Region to Remove', [])
		self.panel.selectiontool.setDisplayed('Region to Remove', True)
		
		#make 'Select Particles' the initial targeting selection

		#self.panel.SetMinSize((300,600))
		self.sizer.Add(self.panel, 20, wx.EXPAND)
		### END IMAGE PANEL

		### BEGIN BUTTONS ROW
		self.buttonrow = wx.FlexGridSizer(1,9)

		self.next = wx.Button(self.frame, wx.ID_FORWARD, '&Forward')
		self.next.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onNext, self.next)
		self.buttonrow.Add(self.next, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.add = wx.Button(self.frame, wx.ID_REMOVE, '&Remove Region')
		self.add.SetMinSize((150,40))
		self.Bind(wx.EVT_BUTTON, self.onAdd, self.add)
		self.buttonrow.Add(self.add, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.clear = wx.Button(self.frame, wx.ID_CLEAR, '&Clear')
		self.clear.SetMinSize((100,40))
		self.Bind(wx.EVT_BUTTON, self.onClear, self.clear)
		self.buttonrow.Add(self.clear, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.revert= wx.Button(self.frame, wx.ID_REVERT_TO_SAVED, 'Revert to Saved')
		self.revert.SetMinSize((80,40))
		self.Bind(wx.EVT_BUTTON, self.onRevert, self.revert)
		self.buttonrow.Add(self.revert, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		label = wx.StaticText(self.frame, -1, "Image Assessment:  ", style=wx.ALIGN_RIGHT)
		self.buttonrow.Add(label, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)

		self.assessnone = wx.ToggleButton(self.frame, -1, "&None")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleNone, self.assessnone)
		self.assessnone.SetValue(0)
		#self.assessnone.SetBackgroundColour(self.selectcolor)
		self.assessnone.SetMinSize((100,40))
		self.buttonrow.Add(self.assessnone, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assesskeep = wx.ToggleButton(self.frame, -1, "&Keep")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleKeep, self.assesskeep)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetMinSize((100,40))
		self.buttonrow.Add(self.assesskeep, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.assessreject = wx.ToggleButton(self.frame, -1, "&Reject")
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleReject, self.assessreject)
		self.assessreject.SetValue(0)
		self.assessreject.SetMinSize((100,40))
		self.buttonrow.Add(self.assessreject, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.createPolyParticleGUI()#add the buttons needed for the polygon manual picker
		### END BUTTONS ROW

		self.sizer.Add(self.buttonrow, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		self.sizer.AddGrowableRow(1)
		self.sizer.AddGrowableCol(0)
		self.frame.SetSizerAndFit(self.sizer)
		self.SetTopWindow(self.frame)
		self.frame.Show(True)
		return True

	def doGraphics(self):
		#for targets in self.oldPolyTargets:
		#	self.panel.drawContour(wx.Color(220,20,20),targets)	
		for targets in self.polyTargets:
			self.panel.drawContour(wx.Color(220,20,20),targets)	
		for targets in self.tubeTargets:
			self.panel.drawContour(wx.Color(220,220,20), targets, thickness=2)

	def deleteTarget(self, target):
		try:
			if target is not None :
				if target.type.name == self.s:
					points = self.panel.selectiontool.getTargets(self.s)
					points.remove(target)	
				if target.type.name == self.s2:
					#points = self.panel.selectiontool.getTargets(self.s2)
					#points.remove(target)	
					i = self.panel.selectiontool.getTargets(self.s2).index(target)
					del self.polyTargets[i]
					#targets = self.contourTargetMap[target]
					#del targets
				if target.type.name == 'TubeMemory':
					tubeMemTargets = self.panel.selectiontool.getTargets('TubeMemory')
					i = tubeMemTargets.index(target)
					del self.tubeTargets[i]
					self.singleParticleTypeList.remove('Tube')
				if target.type.name == 'Circle':
					self.panel.selectiontool.getTargets('Circle').remove(target)
					self.singleParticleTypeList.remove('Circle')
		except (ValueError,IndexError):
			pass		
		print 'ow'

	def addManualPoint(self):
		'''
		def dist(target1,target2):
			return math.sqrt((target1.x-target2.x)*(target1.x-target2.x)+(target1.y-target2.y)*(target1.y-target2.y))
		targets = self.panel.selectiontool.getTargets(self.s)
		if len(targets)<2:
			return
		target = targets.pop()
		i = 0
		minDist = 99999999 
		for t in targets:
			d = dist(t,target)
			if d<minDist:
				minDist = d
				i = targets.index(t)
		i1 = i+1
		if i1>=len(targets):
			i1=0
		i2 = i-1
		if i2<0:
			i2 = len(targets)-1
		dist1 = dist(targets[i1],target)
		dist2 = dist(targets[i2],target)
		if dist1<dist2:
			targets.insert(i1,target)
		else:
			targets.insert(i,target)	
		self.panel.selectiontool.setTargets(self.s,targets)
		'''
		pass

	def negative(self, ndarray):
		for i in range(len(ndarray)):
			for j in range(len(ndarray[i])):
				ndarray[i][j] = 127-ndarray[i][j]

	def onEdgeFinding(self,evt):	
		if not self.panel.selectiontool.isTargeting('Auto Create Contours'):
			return 
		point = self.panel.view2image((evt.m_x,evt.m_y))

		ndarray = mrc.read(os.path.join(self.appionloop.params['rundir'], self.appionloop.imgtree[self.index]['filename']+'.dwn.mrc'))
		mrc.write(ndarray, os.path.join(self.appionloop.params['rundir'], 'beforefilter'+'.dwn.mrc'))

		negative = False	
		if self.filters:
			ndarray = ndimage.gaussian_filter(ndarray,1)
			ndarray = ndimage.gaussian_gradient_magnitude(ndarray,2)
			markers = []
			for i in range(3):
				for j in range(3):
					if i!=0 or j!=0:
						markers.append((point[0]-1+i,point[1]-1+j))
			markers = (1,2,3,4,5,6,7,8)
			#ndarray = ndimage.watershed_ift(ndarray,markers)
			ndarray = ndimage.laplace(ndarray)
			ndarray = ndimage.gaussian_filter(ndarray,1)
			#ndarray = apImage.preProcessImage(ndarray,params=self.appionloop.params)
			negative = True 
		mrc.write(ndarray, os.path.join(self.appionloop.params['rundir'], 'afterfilter'+'.dwn.mrc'))

		delta = .1
		targets = []
		radius = 20
		size = 50
		rangeSize = 50
		maker = PixelCurveMaker()
		maker._init_(size,rangeSize);
		for theta in range(size):
			theta +=0
			theta*=math.pi*2/rangeSize
			for rad in range(size):
				try:
					if negative:
						maker.addData(theta,rad,127-ndarray[int(point[1]+rad*math.sin(theta))][int(point[0]+rad*math.cos(theta))])
					else:
						maker.addData(theta,rad,ndarray[int(point[1]+rad*math.sin(theta))][int(point[0]+rad*math.cos(theta))])
				except IndexError:
					maker.addData(theta,rad,0)
		maker.makeCalculations()
		s = self.filterSelectorChoices[self.filterSelector.GetSelection()]	
		dilate = 2
		if s == 'Latex Bead':
			dilate = 0
		for theta in range(size):
			theta += 0
			theta*=math.pi*2/rangeSize
			targets.append((point[0]+(dilate+maker.getData(theta))*math.cos(theta),point[1]+(dilate+maker.getData(theta))*math.sin(theta)))
		self.addPolyParticle(targets)
		#this section draws all of the contours that the algorithm considers - useful for debugging
		'''
		contours = maker.getAllData()
		targets = []
		for c in contours:
			for theta in range(size):
				theta*=math.pi*2/size
				targets.append((point[0]+(dilate+c.goodValues[theta])*math.cos(theta),point[1]+(dilate+c.goodValues[theta])*math.sin(theta)))
			self.addPolyParticle(targets)
			targets = []
		'''

	def loadOld(self, points, singlePoints):
		self._onClear()
		self.panel.setTargets(self.s2,points[0])
		i = 0
		for target in points[0]:
			self.contourTargetMap[target] = points[1][i]
			i+=1
		for p in points[1]:
			self.polyTargets.append(p)
		self.particleTypeList = points[2]
		singleTargets = []
		singleCircles = []
		singleTubes = []
		i = 0
		for point in singlePoints[0]:
			if singlePoints[1][i]=='Tube':
				singleTubes.append(point)
			elif singlePoints[1][i]=='Circle':
				singleCircles.append(point)
			else:
				singleTargets.append(point)
			i+=1
		self.panel.setTargets(self.s3,singleTargets)
		self.panel.setTargets('Tube', singleTubes)
		self.panel.setTargets('Circle', singleCircles)
		self.singleParticleTypeList = singlePoints[1]
		self.tubeTargets = []
		self.tubeTargets = singlePoints[2]
		self.panel.selectiontool.setTargets('Tube',[])
		
		for target in self.tubeTargets:
			tubemem = self.panel.selectiontool.getTargets('TubeMemory')
			tubemem.append(target[0])
			self.panel.selectiontool.setTargets('TubeMemory', tubemem)
		#self.oldPolyTargets = points[1]

	def createPolyParticleGUI(self):#creates a main tool to select the points and adds a button to move onto the next particle
		self.panel.setPickerApp(self)
		self.polyTargets = []
		self.polyTargetsLabels = []
		self.s3 = 'Select Particles'	
		self.s = 'Manually Create Contours'
		self.panel.addTargetTool(self.s, color=wx.Color(20,220,20),
			target=True, shape='polygon')
		self.panel.setTargets(self.s, [])
		self.panel.selectiontool.setDisplayed(self.s, True)

		self.s2 = 'Auto Create Contours'
		self.panel.addTargetTool(self.s2, color=wx.Color(20,220,20),
			target=True, shape='.')
		self.panel.setTargets(self.s2, [])
		self.panel.selectiontool.setDisplayed(self.s2, True)
		self.panel.selectiontool.setTargeting(self.s2, True)

		self.add = wx.Button(self.frame, wx.ID_ADD, '&Add Particle')
		self.add.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onSelected, self.add)
		self.buttonrow.Add(self.add, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)


		self.removeLast = wx.Button(self.frame, wx.ID_REMOVE, 'Remove &Last Partice')
		self.add.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onTakeBack, self.removeLast)
		self.buttonrow.Add(self.removeLast, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		

		self.switch = wx.Button(self.frame, wx.ID_ANY, 'Switch Selection &Mode')
		self.add.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onSwitch, self.switch)
		self.buttonrow.Add(self.switch, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.textFile = wx.Button(self.frame, wx.ID_ANY, 'Make &Text File')
		self.add.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onMakeFile, self.textFile)
		self.buttonrow.Add(self.textFile, 0,wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.tcTextFile = wx.Button(self.frame, wx.ID_ANY, 'Make TubeCircle &Text File')
		self.add.SetMinSize((200,40))
		self.Bind(wx.EVT_BUTTON, self.onMakeTCFile, self.tcTextFile)
		self.buttonrow.Add(self.tcTextFile, 0,wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)

		self.filterSelectorChoices = ['Virus Like Particle','Latex Bead']
		self.filterSelector = wx.ComboBox(self.frame,wx.CB_DROPDOWN,choices=self.filterSelectorChoices)
		self.filterSelector.SetMinSize((200,40))
		self.Bind(wx.EVT_TEXT, self.onSelectorTriggered, self.filterSelector)
		self.buttonrow.Add(self.filterSelector, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3) 
	
		self.particleType = 'Blank'
		self.typeSelectorChoices = ['Blank','Circle','Tube']
		self.typeSelector = wx.ComboBox(self.frame,wx.CB_DROPDOWN,choices=self.typeSelectorChoices)
		self.typeSelector.SetMinSize((200,40))
		self.Bind(wx.EVT_COMBOBOX, self.onTypeChanged, self.typeSelector)
		self.buttonrow.Add(self.typeSelector, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
		
		self.panel.addTargetTool('Circle', color=wx.Color(20,20,220),
			target=True, shape='o', size=self.size)
		self.panel.setTargets('Circle', [])
		self.panel.selectiontool.setTargeting('Circle', True)

		self.panel.addTargetTool('Tube', color=wx.Color(220,220,20),
			target=True, shape='polygon', size=self.size)
		self.panel.setTargets('Tube', [])
		self.panel.selectiontool.setTargeting('Tube', True)

		self.panel.addTargetTool('TubeMemory', color=wx.Color(20,20,220),
			target=True, shape='.', size=self.size)
		self.panel.setTargets('TubeMemory', [])
		self.panel.selectiontool.setTargeting('TubeMemory', True)

	def onMakeTCFile(self,evt):
		session = self.appionloop.params['sessionname']	
		###change later
		os.system('contourpickerTubeCircleTextFileGenerator.py ' + str(session) + ' ' + self.appionloop.params['runid'] + ' ' + self.appionloop.params['preset'])

	def onMakeFile(self,evt):
		session = self.appionloop.params['sessionname']	
		###change later
		os.system('contourpickerTextFileGenerator.py ' + str(session) + ' ' + self.appionloop.params['runname'] + ' ' + self.appionloop.params['preset'])

	def onTypeChanged(self, evt):
		self.particleType = self.typeSelectorChoices[self.typeSelector.GetSelection()]

	def onSelectorTriggered(self, evt):
		s = self.filterSelectorChoices[self.filterSelector.GetSelection()]	
		if s == 'Virus Like Particle':
			self.filters = False 
		else:
			self.filters = True

	def onSwitch(self, evt):
		s = 'Manually Create Contours'
		s2 = 'Auto Create Contours'
		

		if self.panel.selectiontool.isTargeting(s):
			self.panel.selectiontool.setTargeting(s, False)
			self.panel.selectiontool.setTargeting(s2, True)
		else:
			self.panel.selectiontool.setTargeting(s2, False)
			self.panel.selectiontool.setTargeting(s, True)

	def onMoved(self, evt):
		s = 'Manually Create Contours'
		s2 = 'Auto Create Contours'
		flag = False
		if evt.RightIsDown():
	#		if self.panel.selectiontool.isTargeting(s):
	#			self.onSwitch(evt)
	#			flag = True
			self.panel._onRightClick(evt)
	#		if flag:
	#			self.onSwitch(evt)

	def onTakeBack(self,evt):
		s2 = 'Auto Create Contours'
		self.polyTargets.pop()
		savedTargets = self.panel.getTargets(s2)
		savedTargets.pop()
		self.panel.setTargets(s2, savedTargets)

	def addSinglePoint(self, evt):
		if self.panel.selectiontool.isTargeting('Circle'):
			self.particleType = 'Circle'
		elif self.panel.selectiontool.isTargeting('Tube'):
			self.particleType = 'Tube'
			if len(self.panel.selectiontool.getTargets('Tube'))==1:
				return
		else:
			self.particleType = 'Blank'
		self.singleParticleTypeList.append(self.particleType)

	def addPolyParticle(self, targets):#this function adds a tool for every particle that stores the points and handels the painting
		
		s = 'Manually Create Contours'
		s2 = 'Auto Create Contours'
		s3 = 'Select Particles'
		if self.panel.selectiontool.isTargeting(s):
			points = self.panel.selectiontool.getTargets(s2)
			points.append(targets[0])
			self.panel.selectiontool.setTargets(s2,points)
		t = self.panel.getTargets(s2)
		self.contourTargetMap[t[len(t)-1]] = targets
		self.polyTargets.append(targets)
		self.panel.selectiontool.setTargets(s2,self.panel.selectiontool.getTargets(s2))
		self.particleTypeList.append(self.particleType)
	def onQuit(self, evt):
		targets = self.panel.getTargets('Select Particles')
		for target in targets:
			print '%s\t%s' % (target.x, target.y)
		wx.Exit()

	def onSelected(self, evt):#event for the add particle button - clears the main 'manually select particle' tool and calls 'addPolyParticle' to handel the data
		vertices = []
		vertices = self.panel.getTargetPositions('Manually Create Contours');
		if len(vertices)>0:
			self.addPolyParticle(vertices);
		self.panel.setTargets('Manually Create Contours', []);
		
	def onAdd(self, evt):
		vertices = []
		vertices = self.panel.getTargetPositions('Region to Remove')
		def reversexy(coord):
			clist=list(coord)
			clist.reverse()
			return tuple(clist)
		vertices = map(reversexy,vertices)
		
		maskimg = leginon.polygon.filledPolygon(self.panel.imagedata.shape,vertices)
		type(maskimg)
		targets = self.panel.getTargets('Select Particles')
		eliminated = 0
		newparticles = []
		for target in targets:
			coord = (target.y,target.x)
			if maskimg[coord] != 0:
				eliminated += 1
			else:
				newparticles.append(target)
		print eliminated,"particle(s) eliminated due to masking"
		self.panel.setTargets('Select Particles',newparticles)
		self.panel.setTargets('Region to Remove', [])
		
	def onNext(self, evt):
		#targets = self.panel.getTargets('Select Particles')
		#for target in targets:
		#	print '%s\t%s' % (target.x, target.y)
		self.appionloop.targets = self.panel.getTargets('Select Particles')
		self.appionloop.assess = self.finalAssessment()
		self.index+=1
		if len(self.appionloop.imgtree)==self.index:
			print "There Are No More Images"
		self.Exit()

	def finalAssessment(self):
		if self.assessnone.GetValue() is True:
			return None
		elif self.assesskeep.GetValue() is True:
			return True
		elif self.assessreject.GetValue() is True:
			return False
		return None

	def setAssessStatus(self):
		if self.appionloop.assess is True:
			self.onToggleKeep(None)
		elif self.appionloop.assess is False:
			self.onToggleReject(None)
		else:
			self.onToggleNone(None)

	def onToggleNone(self, evt):
		self.assessnone.SetValue(1)
		self.assessnone.SetBackgroundColour(wx.Color(200,200,0))
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = None

	def onToggleKeep(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(1)
		self.assesskeep.SetBackgroundColour(wx.Color(0,200,0))
		self.assessreject.SetValue(0)
		self.assessreject.SetBackgroundColour(self.deselectcolor)
		self.assess = True


	def onToggleReject(self, evt):
		self.assessnone.SetValue(0)
		self.assessnone.SetBackgroundColour(self.deselectcolor)
		self.assesskeep.SetValue(0)
		self.assesskeep.SetBackgroundColour(self.deselectcolor)
		self.assessreject.SetValue(1)
		self.assessreject.SetBackgroundColour(wx.Color(200,0,0))
		self.assess = False
	def _onClear(self):
		self.polyTargets = []
		self.panel.setTargets('Auto Create Contours', [])
		self.panel.setTargets('Select Particles', [])
		self.panel.setTargets('Manually Create Contours', [])
		self.panel.setTargets('Region to Remove',[])
		self.tubeTargets = []
		self.panel.setTargets('Tube', [])
		self.panel.setTargets('Circle', [])
		self.panel.setTargets('TubeMemory', [])
		self.singleParticleTypeList = []
		self.particleTypeList = []

	#	for s in self.particles:
	#		self.panel.setTargets(s, [])
	#	self.particlesSize = 0
		
	def onClear(self, evt):
		self._onClear()

	def onRevert(self, evt):
		self.panel.setTargets('Select Particles', self.panel.originaltargets)


##################################
##################################
##################################
## APPION LOOP
##################################
##################################
##################################

class ContourPicker(manualpicker.ManualPicker):
	def checkConflicts(self):
		if self.params['shuffle'] != True:
			apDisplay.printWarning("Shuffle is always set to True for contourpicker")
			self.params['shuffle'] = True
		for i,v in enumerate(self.outtypes):
			if self.params['outtype'] == v:
				self.params['outtypeindex'] = i
		if self.params['outtypeindex'] is None:
			apDisplay.printError("outtype must be one of: "+str(self.outtypes)+"; NOT "+str(self.params['outtype']))
		return

	def setApp(self):
		self.app = PickerApp(
			shape = self.canonicalShape(self.params['shape']),
			size =  self.params['shapesize'],
			labels = self.labels,
		)

	def runManualPicker(self, imgdata):
		#reset targets
		self.app.panel.setTargets('Select Particles', [])
		self.targets = []
		#set the assessment and viewer status
		self.assessold = apDatabase.checkInspectDB(imgdata)
		self.assess = self.assessold
		self.app.setAssessStatus()
					
		#open new file
		imgname = imgdata['filename']+'.dwn.mrc'
		imgpath = os.path.join(self.params['rundir'],imgname)
		if not self.params['checkMask']:
			self.app.panel.openImageFile(imgpath)
		else:
			self.showAssessedMask(imgpath,imgdata)

		targets = self.getParticlePicks(imgdata)
		if targets:
			print "inserting ",len(targets)," targets"
			self.app.panel.setTargets('Select Particles', targets)
			self.app.panel.originaltargets = targets

		#set vital stats
		self.app.vitalstats.SetLabel("Vital Stats: Image "+str(self.stats['count'])
			+" of "+str(self.stats['imagecount'])+", inserted "+str(len(targets))+" picks, "
			+" image name: "+imgdata['filename'])
		#run the picker
		self.loadOld(imgdata)
		self.app.MainLoop()

		#targets are copied to self.targets by app
		#assessment is copied to self.assess by app
		#parse and return the targets in peaktree form
		self.app.panel.openImageFile(None)
		peaktree=[]
		for target in self.targets:
			peaktree.append(self.XY2particle(target.x, target.y))
		
		targetsList = self.getPolyParticlePoints()
		contourTargets = self.app.panel.getTargets('Auto Create Contours')

		circles = self.app.panel.getTargets('Circle')
		tubes = self.app.tubeTargets
		index = len(tubes)-1
		blanks = self.app.panel.getTargets(self.app.s3)
		singleTargets = []
		for i in self.app.singleParticleTypeList:
			if i=='Tube':
				singleTargets.append(tubes[index][0])
				index-=1
			if i=='Circle':
				singleTargets.append(circles.pop())
			if i=='Blank':
				singleTargets.append(blanks.pop())
		counter = len(self.app.tubeTargets)-1
		c = None
		print 'length of list : ', str(len(self.app.singleParticleTypeList))
		print self.app.singleParticleTypeList
		for i in range(len(singleTargets)):
			try:
				c=appiondata.ApContour(name="contour"+str(int(self.startPoint)+i), image=imgdata, x=singleTargets[i].x, y=singleTargets[i].y,version=self.maxVersion+1, method='single', particleType=self.app.singleParticleTypeList[i], runID = self.params['runname'])
			except AttributeError:
				c=appiondata.ApContour(name="contour"+str(int(self.startPoint)+i), image=imgdata, x=singleTargets[i][0], y=singleTargets[i][1],version=self.maxVersion+1, method='single', particleType=self.app.singleParticleTypeList[i], runID=self.params['runname'])
			c.insert()
			if self.app.singleParticleTypeList[i]=='Tube':
				for point in self.app.tubeTargets[counter]:
					point1=appiondata.ApContourPoint(x=point[0], y=point[1], contour=c)
					point1.insert()
				counter-=1
		counter = 0
		for i in range(len(targetsList)):
			c=appiondata.ApContour(name="contour"+str(int(self.startPoint)+i+len(singleTargets)), image=imgdata, x=contourTargets[counter].x, y=contourTargets[counter].y,version=self.maxVersion+1, method='auto', particleType=self.app.particleTypeList[counter], runID=self.params['runname'])
			c.insert()
			counter += 1
			for point in targetsList[i]:
				point1=appiondata.ApContourPoint(x=point[0], y=point[1], contour=c)
				point1.insert()

		return peaktree

	def loadOld(self,imgdata):
		partq = appiondata.ApContour()
		partq['image'] = imgdata
		partd = partq.query()
		try: 
			name = partd[0]['name']
			self.startPoint = name.lstrip('contour')
		except IndexError:
			self.startPoint = 0		
		points = appiondata.ApContourPoint()
		oldPolyPoints = []
		contourPoints = []
		types = []
		singleTypes = []
		singleTargets = []
		tubePoints = []
		self.maxVersion = -1
		for i in partd:
			if not i['version']==None and int(i['version'])>self.maxVersion and i['runID']==self.params['runname']:
				self.maxVersion = int(i['version'])
		for i in partd:
			if not i['version']==None and int(i['version'])==self.maxVersion and not i['method']=='single' and i['runID']==self.params['runname']:
				contourPoints.append((i['x'],i['y']))
				types.append(i['particleType'])
				contour = i['name']
				points['contour'] = i
				point = points.query()
				contourList = []
				for j in point:
					contourList.append((j['x'], j['y']))
				oldPolyPoints.append(contourList)
			if not i['version']==None and int(i['version'])==self.maxVersion and i['method']=='single' and i['runID']==self.params['runname']:
				singleTypes.append(i['particleType'])
				singleTargets.append((i['x'],i['y']))
				if i['particleType']=='Tube':
					contour = i['name']
					points['contour'] = i
					point = points.query()
					contourList = []
					for j in point:
						contourList.append((j['x'], j['y']))
					tubePoints.append(contourList)
		return self.app.loadOld((contourPoints,oldPolyPoints,types),(singleTargets,singleTypes,tubePoints))

	def getPolyParticlePoints(self):#get all of the polyparticles into list of points form
		targetsList = []
		for particle in self.app.polyTargets:
				targetsList.append(particle)
		return targetsList

if __name__ == '__main__':
	imgLoop = ContourPicker()
	imgLoop.run()



