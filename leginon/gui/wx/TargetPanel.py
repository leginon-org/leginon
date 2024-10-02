#!/usr/bin/env python
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/TargetPanel.py,v $
# $Revision: 1.10 $
# $Name: not supported by cvs2svn $
# $Date: 2008-01-18 04:58:49 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import time
import math
import wx
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.TargetPanelTools
import numpy as n

### colors that should be used globally
targettype_colors = {
	'acquisition': wx.GREEN,
	'focus': wx.BLUE,
	'done': wx.RED,
	'reference': wx.Colour(128, 0, 128),
	'position': wx.Colour(218, 165, 32),
	'preview': wx.Colour(255, 128, 255),
	'meter': wx.Colour(255, 255, 0),
	'original': wx.Colour(255, 128, 128),
	'peak': wx.Colour(255, 128, 0),
}

##################################
##
##################################

class TargetImagePanel(leginon.gui.wx.ImagePanel.ImagePanel):
	def __init__(self, parent, id, callback=None, 
			tool=True, imagesize=(512, 512), mode="horizontal"):
		super(TargetImagePanel,self).__init__(parent, id, imagesize, mode)
		self.order = []
		self.reverseorder = []
		self.targets = {}
		self.selectedtype = None
		self.selectedtarget = None
		self.box = 0
		# image vectors is dictionary of image x and y axis vectors in image pixels
		self.imagevectors = {'x':(0,0), 'y':(0,0)}
		self.beamradius = None

	#--------------------
	def _getSelectionTool(self):
		if self.selectiontool is None:
			raise ValueError('No types added')
		return self.selectiontool

	#--------------------
	def addTargetTool(self, name, color=None, **kwargs):
		if color is None:
			if name in targettype_colors:
				color = targettype_colors[name]
			else:
				raise ValueError('Target color must be specified.  No default color for "%s"' % (name,))
		kwargs['display'] = color
		kwargs['toolclass'] = leginon.gui.wx.TargetPanelTools.TargetTypeTool
		self.addTypeTool(name, **kwargs)

	#--------------------
	def getTargets(self, name):
		return self._getSelectionTool().getTargets(name)

	#--------------------
	def addTarget(self, name, x, y):
		return self._getSelectionTool().addTarget(name, x, y)

	#--------------------
	def changeCursorSize(self, name, size):
		return self._getSelectionTool().changeCursorSize(name, size)

	#--------------------
	def insertTarget(self, name, pos, x, y):
		return self._getSelectionTool().insertTarget(name, pos, x, y)

	#--------------------
	def deleteTarget(self, target):
		return self._getSelectionTool().deleteTarget(target)

	#--------------------
	def clearTargetType(self, targettype):
		return self._getSelectionTool().clearTargetType(targettype)

	#--------------------
	def clearAllTargetTypes(self):
		return self._getSelectionTool().clearAllTargetTypes()

	#--------------------
	def setTargets(self, name, targets):
		return self._getSelectionTool().setTargets(name, targets)

	#--------------------
	def getTargetPositions(self, name):
		return self._getSelectionTool().getTargetPositions(name)

	#--------------------
	def setDisplayedTargets(self, type, targets):
		if targets is None:
			if type in self.targets:
				del self.targets[type]
				self.order.remove(type)
		else:
			targets = list(targets)
			for t in targets:
				if not isinstance(t, leginon.gui.wx.TargetPanelTools.Target):
					raise TypeError
			self.targets[type] = targets
			if type not in self.order:
				self.order.append(type)
		self.reverseorder = list(self.order)
		self.reverseorder.reverse()
		self.UpdateDrawing()

	#--------------------
	def setDisplayedNumbers(self, type, targets):
		self.setDisplayedTargets(type, targets)

	#--------------------
	def _drawTargets(self, dc, bitmap, targets, scale):
		memorydc = wx.MemoryDC()
		#memorydc.BeginDrawing()
		memorydc.SelectObject(bitmap)

		width = bitmap.GetWidth()
		height = bitmap.GetHeight()
		if self.scaleImage():
			xscale, yscale = (1.0, 1.0)
		else:
			xscale, yscale = self.getScale()
			dc.SetUserScale(xscale, yscale)

		halfwidth = width/2.0
		halfheight = height/2.0

		xv, yv = self.biggerView()

		for target in targets:
			x, y = self.image2view((target.x, target.y))
			dc.Blit(int(round(x/xscale - halfwidth)),
							int(round(y/xscale - halfheight)),
							width, height,
							memorydc, 0, 0,
							wx.COPY, True)

		dc.SetUserScale(1.0, 1.0)
		memorydc.SelectObject(wx.NullBitmap)
		#memorydc.EndDrawing()

	#--------------------
	def drawTargets(self, dc):
		scale = self.getScale()
		for type in self.order:
			targets = self.targets[type]
			if targets:
				if type.shape == 'polygon':
					self.drawPolygon(dc, type.color, targets)
				elif type.shape == 'spline':
					self.drawPolygon(dc, type.color, targets, close=False)
				else:
					if type.shape == 'numbers':
						self.drawNumbers(dc, type.color, targets)
					elif type.shape == 'area':
						self.drawImageArea(dc, type.color, targets)
					elif type.shape == 'exp':
						self.drawImageExposure(dc, type.color, targets, typename=type.name)
					else:
						self._drawTargets(dc, type.bitmaps['default'], targets, scale)

		if self.selectedtarget is not None:
			if self.selectedtarget.type in self.targets and type.shape != 'polygon' and type.shape != 'spline' and type.shape != 'numbers' and type.shape != 'area' and type.shape != 'exp':
				try:
					bitmap = self.selectedtarget.type.bitmaps['selected']
					self._drawTargets(dc, bitmap, [self.selectedtarget], scale)
				except AttributeError:
					pass

	#--------------------
	def drawPolygon(self, dc, color, targets, close=True):
		dc.SetPen(wx.Pen(color, 3))
		dc.SetBrush(wx.Brush(color, wx.SOLID))
		#if self.scaleImage():
		if False:
			xscale = self.scale[0]
			yscale = self.scale[1]
			scaledpoints = []
			for target in targets:
				point = target.x/xscale, target.y/yscale
				scaledpoints.append(point)
		else:
			if isinstance(targets[-1], leginon.gui.wx.TargetPanelTools.StatsTarget) and close is False:
				scaledpoints=[]
				for target in targets:
					scaledpoints.append([target.x,target.y,target.stats])
			else:
				scaledpoints = [(target.x,target.y,0) for target in targets]
		if len(scaledpoints)>=1:
			p1 = self.image2view(scaledpoints[0])
			dc.DrawCircle(p1[0],p1[1],1)
			
		for i,p1 in enumerate(scaledpoints[:-1]):
			p2 = scaledpoints[i+1]
			pi1 = self.image2view(p1)
			pi2 = self.image2view(p2)
			dc.DrawCircle(pi2[0],pi2[1],1)
			# for multiple splines
			if p1[2]==p2[2]:
				dc.DrawLine(pi1[0], pi1[1], pi2[0], pi2[1])
		# close it with final edge if not a spline
		if close is True:
			p1 = scaledpoints[-1]
			p2 = scaledpoints[0]
			p1 = self.image2view(p1)
			p2 = self.image2view(p2)
			dc.DrawLine(p1[0], p1[1], p2[0], p2[1])

	#--------------------
	def drawNumbers(self, dc, color, targets):
		#dc.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD))
		#dc.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
		dc.SetTextForeground(color) 
		#dc.SetPen(wx.Pen(color, 20))
		scaledpoints = [(target.x,target.y) for target in targets]
		for i,p1 in enumerate(scaledpoints):
			p1 = self.image2view(p1)
			dc.DrawText(str(i+1), p1[0], p1[1])

	#--------------------
	def drawImageArea(self, dc, color, targets):
		# general
		dc.SetPen(wx.Pen(color, 1))
		dc.SetBrush(wx.Brush(color, wx.SOLID))
		scale = self.getScale()
		scaledpoints = [(target.x,target.y) for target in targets]
		imagevectors = self.imagevectors
		self._drawArea(dc, imagevectors, scaledpoints)

	def _drawArea(self, dc, imagevectors, scaledpoints):
		scale = self.getScale()
		# vector1 (+,+) corner
		v1 = (scale[0]*(imagevectors['x'][0]/2+imagevectors['y'][0]/2), scale[1]*(imagevectors['x'][1]/2+imagevectors['y'][1]/2))
		# vector2 (+,-) corner
		v2 = (scale[0]*(imagevectors['x'][0]/2-imagevectors['y'][0]/2), scale[1]*(imagevectors['x'][1]/2-imagevectors['y'][1]/2))
		v1 = (int(v1[0]),int(v1[1]))
		v2 = (int(v2[0]),int(v2[1]))
		for p1 in scaledpoints:
			p1 = self.image2view(p1)
			dc.DrawLine(p1[0]-v1[0], p1[1]-v1[1], p1[0]-v2[0], p1[1]-v2[1])
			dc.DrawLine(p1[0]-v2[0], p1[1]-v2[1], p1[0]+v1[0], p1[1]+v1[1])
			dc.DrawLine(p1[0]+v1[0], p1[1]+v1[1], p1[0]+v2[0], p1[1]+v2[1])
			dc.DrawLine(p1[0]+v2[0], p1[1]+v2[1], p1[0]-v1[0], p1[1]-v1[1])

	def drawBeamSize(self, dc, color, targets):
		# general
		dc.SetPen(wx.Pen(color, 1))
		dc.SetBrush(wx.Brush(color, wx.SOLID))
		scale = self.getScale()
		scaledpoints = [(target.x,target.y) for target in targets]
		# beam size
		if self.beamradius:
			for p1 in scaledpoints:
				p1 = self.image2view(p1)
				self.drawEmptyCircle(dc,p1[0],p1[1],scale[0]*self.beamradius)

	def drawImageExposure(self, dc, color, targets, typename=None):
		'''
		Exp tool type calls this to show both area and beam size
		'''
		# area
		self.drawImageArea(dc, color, targets)
		self.drawBeamSize(dc, color, targets)


	def drawEmptyCircle(self,dc,row,col,radius):
		'''
		Draw a circle without filling.
		'''
		radius = max([1,int(radius)])
		p1 = (row,col-radius)
		p2 = (row,col-radius)
		for r in range(-radius,radius+1):
			angle = math.acos((r+0.0)/radius)
			delta = int(radius * math.sin(math.acos((r+0.0)/radius)))
			p11 = (row+delta,col+r)
			p22 = (row-delta,col+r)
			dc.DrawLine(p1[0],p1[1],p11[0],p11[1])
			dc.DrawLine(p2[0],p2[1],p22[0],p22[1])
			p1 = p11
			p2 = p22

	#--------------------
	def Draw(self, dc):
		#now = time.time()
		leginon.gui.wx.ImagePanel.ImagePanel.Draw(self, dc)
		#dc.BeginDrawing()
		self.drawTargets(dc)
		#dc.EndDrawing()

	#--------------------
	def _onLeftClick(self, evt):
		if self.selectedtype is not None:
			x, y = self.view2image((evt.GetX(), evt.GetY()))
			self.addTarget(self.selectedtype.name, x, y)

	#--------------------
	def _onRightClick(self, evt):
		if self.selectedtarget is not None :
			if self.selectedtype == self.selectedtarget.type:
				self.deleteTarget(self.selectedtarget)

	#--------------------
	def _onShiftRightClick(self, evt):
		if self.selectedtarget is not None :
			if self.selectedtype == self.selectedtarget.type:
				self.clearTargetType(self.selectedtype)

	#--------------------
	def _onShiftCtrlRightClick(self, evt):
		self.clearAllTargetTypes()

	#--------------------
	def closestTarget(self, type, x, y):
		minimum_magnitude = 10

		if self.scaleImage():
			xscale, yscale = self.getScale()
			minimum_magnitude /= xscale

		closest_target = None

		if type is not None:
			for target in self.targets[type]:
				magnitude = math.hypot(x - target.x, y - target.y)
				if magnitude < minimum_magnitude:
					minimum_magnitude = magnitude
					closest_target = target

		if closest_target is None:
			for key in self.reverseorder:
				if key == type:
					continue
				for target in self.targets[key]:
					magnitude = math.hypot(x - target.x, y - target.y)
					if magnitude < minimum_magnitude:
						minimum_magnitude = magnitude
						closest_target = target
				if closest_target is not None:
					break

		return closest_target

	#--------------------
	def _onMotion(self, evt, dc):
		leginon.gui.wx.ImagePanel.ImagePanel._onMotion(self, evt, dc)
#		if self.selectedtype is not None:
		viewoffset = self.panel.GetViewStart()
		x, y = self.view2image((evt.GetX(), evt.GetY()))
		self.selectedtarget = self.closestTarget(self.selectedtype, x, y)
#		else:
#			self.selectedtarget = None

	#--------------------
	def _getToolTipStrings(self, x, y, value):
		strings = leginon.gui.wx.ImagePanel.ImagePanel._getToolTipStrings(self, x, y, value)
		selectedtarget = self.selectedtarget
		if selectedtarget is not None:
			name = selectedtarget.type.name
			position = selectedtarget.position
			if not self.box:
				strings.append('%s (%g, %g)' % (name, position[0], position[1]))
			else:
				boxsum = self._getIntegratedIntensity(position[0],position[1])
				strings.append('%s (%g, %g) %e' % (name, position[0], position[1],boxsum))
			if isinstance(selectedtarget, leginon.gui.wx.TargetPanelTools.StatsTarget):
				try:
					for key, value in list(selectedtarget.stats.items()):
						if type(value) is float:
							strings.append('%s: %g' % (key, value))
						else:
							strings.append('%s: %s' % (key, value))
				except:
					pass
		return strings

	def _getIntegratedIntensity(self,x,y):
			box = self.box
			boxarray = self.imagedata[y-box:y+box,x-box:x+box]
			sum = boxarray.sum()
			return sum
##################################
##
##################################


class ClickAndTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, imagesize=(512,512), mode="horizontal"):
		super(ClickAndTargetImagePanel,self).__init__(parent, id, imagesize, mode)
		if mode == "vertical":
			self.clicktool = self.addTool(leginon.gui.wx.ImagePanelTools.ClickTool(self, self.toolsizer, disable))
		else:
			self.clicktool = self.addTool(leginon.gui.wx.ImagePanelTools.ClickTool(self, self.toolsizer2, disable))
		self.Bind(leginon.gui.wx.ImagePanel.EVT_IMAGE_CLICK_DONE, self.onImageClickDone)
		self.sizer.Layout()
		self.Fit()
		#self.SetSizerAndFit(self.sizer)

	#--------------------
	def onImageClickDone(self, evt):
		self.clicktool.onImageClickDone(evt)

class ShapeTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, imagesize=(512,512), mode="horizontal"):
		super(ShapeTargetImagePanel, self).__init__(parent, id, imagesize, mode)
		self.shapetool = self.addTool(leginon.gui.wx.ImagePanelTools.FitShapeTool(self, self.toolsizer))
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.sizer.Layout()
		self.Fit()

class TraceTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, imagesize=(512,512), mode="horizontal"):
		super(TraceTargetImagePanel, self).__init__(parent, id, imagesize, mode)
		self.tracetool = leginon.gui.wx.ImagePanelTools.TraceTool(self, self.toolsizer)
		self.addTool(self.tracetool)
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.sizer.Layout()
		self.Fit()

##################################
class FFTTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, imagesize=(512,512), mode="horizontal"):
		super(FFTTargetImagePanel, self).__init__(parent, id, imagesize, mode)
		self.addTool(leginon.gui.wx.ImagePanelTools.ResolutionTool(self, self.toolsizer))
		self.addTool(leginon.gui.wx.ImagePanelTools.FitShapeTool(self, self.toolsizer))
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.sizer.Layout()
		self.Fit()

##################################
##
##################################

class TargetOutputPanel(TargetImagePanel):
	def __init__(self, parent, id, callback=None, imagesize=(512,512), tool=True):
		super(TargetOutputPanel, self).__init__(parent, id, callback=callback, imagesize=imagesize, tool=tool)

		self.quit = wx.Button(self, -1, 'Quit')
		self.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.sizer.Add(self.quit, (0, 0), (1, 1), wx.EXPAND)

	#--------------------
	def onQuit(self, evt):
		targets = self.getTargets('Target Practice')
		for target in targets:
			print('%s\t%s' % (target.x, target.y))
		wx.Exit()
		
		
class TomoTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, imagesize=(512,512), mode="horizontal"):
		TargetImagePanel.__init__(self, parent, id, imagesize, mode)
		# image vectors is dictionary of image x and y axis vectors in image pixels
		self.trackimagevectors = {'x':(0,0),'y':(0,0)}
		self.trackbeamradius = None
		self.focusimagevectors = {'x':(0,0),'y':(0,0)}
		self.focusbeamradius = None
		self.targetmap = {}				# keeps account of relationship between acquition, focus, and track targets

	def drawImageExposure(self, dc, color, targets, typename=None):
		scale = self.getScale()
		dc.SetPen(wx.Pen(color, 1))
		dc.SetBrush(wx.Brush(color, wx.SOLID))
		scaledpoints = [(target.x,target.y) for target in targets]
		if typename == 'track':
			imagevectors = self.trackimagevectors
			beamradius = self.trackbeamradius
			stretch = self.parent.node.settings['stretch track beam']
		elif typename == 'focus':
			imagevectors = self.focusimagevectors
			beamradius = self.focusbeamradius
			stretch = self.parent.node.settings['stretch focus beam']
		else:
			imagevectors = self.imagevectors
			beamradius = self.beamradius
			stretch = self.parent.node.settings['stretch tomo beam']
		
		if stretch:
			tiltrange = n.deg2rad(self.parent.node.getTiltRange())
			tiltang = n.abs(tiltrange[0] - tiltrange[1]) / 2
			tiltaxis = self.parent.node.getTiltAxis()
		else:
			tiltrange = None
		
		if stretch and not tiltrange is None: 
			for p in scaledpoints:
				p = self.image2view(p)
				if beamradius:
					radn = 1/n.cos(tiltang)*beamradius
					radm = beamradius
					self.drawEmptyEllipse(dc,p[1],p[0],radn,radm,tiltaxis + n.pi/2)
		else:
			self._drawArea(dc, imagevectors, scaledpoints)
			for p1 in scaledpoints:
				p1 = self.image2view(p1)
				if beamradius:
					self.drawEmptyCircle(dc,p1[0],p1[1],scale[0]*beamradius)

	def drawEmptyEllipse(self,dc,row,col,radm,radn,ang,n_points=1000):
		assert (radm >= radn)
		c = n.cos(ang)
		s = n.sin(ang)
		the = n.linspace(0,2*n.pi,n_points)
		x=radm*n.cos(the)*c-s*radn*n.sin(the)+col;
		y=radm*n.cos(the)*s+c*radn*n.sin(the)+row;
		#p= radm*n.cos(the)*c-s*radn*n.sin(the)+col,radm*n.cos(the)*s+c*radn*n.sin(the)+row)
		for i,j in zip(x,y):
			dc.DrawPoint(i,j)

	def getTargetMap(self):
		return self.targetmap
	
	def clearTargetMap(self):			# remove all targets
		self.targetmap = {}
	
	def clearAcquitionTargetMap(self, acquisition_t):
		self.targetmap.pop(acquisition_t)
	
	def clearFocusTargetMap(self):		# remove focus targets
		for key in list(self.targetmap.keys()):
			self.targetmap[key]['focus'] = None
			
	def clearTrackTargetMap(self):		# remove track targets
		for key in list(self.targetmap.keys()):
			self.targetmap[key]['track'] = None
			
	def addFocusTargetMap(self, focus_t, acquisition_t):	# add focus target to a given acquisition target
		self.targetmap[acquisition_t]['focus'] = focus_t
		
	def addFocusTargetMapAll(self, focus_t):							# add focus target to all acquisition targets
		for key in list(self.targetmap.keys()):
			self.targetmap[key]['focus'] = focus_t
	
	def addTrackTargetMap(self, track_t, acquisition_t):
		self.targetmap[acquisition_t]['track'] = track_t
			
	def isAutoFocus(self):
		return self.parent.node.settings['auto focus target']
	
	def getTrackType(self):
		if hasattr(self,'tracktype'):
			return self.tracktype
		else:
			# TODO: this is sketchy
			tracktype = [key for key in list(self.targets.keys()) if key.name =='track']
			if tracktype:
				self.tracktype = tracktype[0]
				return self.tracktype
			else:
				return None			

	def getFocusType(self):
		
		if hasattr(self,'focustype'):
			return self.focustype
		else:
			# TODO: this is sketchy
			focustype = [key for key in list(self.targets.keys()) if key.name =='focus']
			if focustype:	
				self.focustype = focustype[0]
				return self.focustype
			else:
				return None
		
	def getAcquisitionType(self):
		if hasattr(self,'acquisition'):
			return self.acquisitiontype
		else:
			acquisitiontype = [key for key in list(self.targets.keys()) if key.name =='acquisition']
			self.acquisitiontype = acquisitiontype[0]
			return self.acquisitiontype

	#--------------------
	def _onLeftClick(self, evt):
		if self.selectedtype is not None:
			if self.selectedtype.name == 'track':
				pass
			
			elif self.selectedtype.name == 'focus':
				# (1) if AutoFocus, pass
				# (2) if not, remove all association with acquisition target in 
				# (3) remove all focus targets
				# (4) make new focus target
				# (5) associate new focus target with acquition targets
				if self.isAutoFocus():									# (1)
					pass
				else:
					focustype = self.getFocusType()
					self.clearFocusTargetMap()							# (2)
					self.clearTargetType(focustype)						# (3)
					x, y = self.view2image((evt.GetX(), evt.GetY()))
					self.addTarget('focus', x, y)						# (4)
					focus_t = self.getTargets('focus')[0]
					self.addFocusTargetMapAll(focus_t)					# (5)
					
			elif self.selectedtype.name == 'acquisition':
				x, y = self.view2image((evt.GetX(), evt.GetY()))
				self.addTarget(self.selectedtype.name, x, y)
				acquisition_t = self.getTargets('acquisition')[-1]
				assert(acquisition_t.position == (x,y))	
				self.targetmap[acquisition_t] = {'focus':None,'track':None}	
				x_, y_ = self.getTrackPosition(x,y)						# add tracking target
				self.addTarget('track', x_, y_)
				track_t = self.getTargets('track')[-1]
				self.addTrackTargetMap(track_t,acquisition_t)
				
				if self.isAutoFocus():
					x_, y_ = self.getFocusPosition(x,y)
					self.addTarget('focus', x_, y_)
					focus_t = self.getTargets('focus')[-1]
					self.addFocusTargetMap(focus_t,acquisition_t)
				else:
					focus_ts = self.getTargets('focus')
					assert(len(focus_ts) <= 1)
					if len(focus_ts) == 0:
						pass
					elif len(focus_ts) == 1:
						self.addFocusTargetMap(focus_ts[0],acquisition_t)
					else:
						raise Exception
			else:
				x, y = self.view2image((evt.GetX(), evt.GetY()))
				self.addTarget(self.selectedtype.name, x, y)
			
	#--------------------
	def _onRightClick(self, evt):
		if self.selectedtarget is not None:
			if self.selectedtarget.type.name == 'track':
				pass
			elif self.selectedtarget.type.name == 'focus':
				if self.isAutoFocus():
					pass
				else:
					if self.selectedtype == self.selectedtarget.type:
						self.clearFocusTargetMap()					# clear association
						self.deleteTarget(self.selectedtarget)		# remove focus target
			elif self.selectedtype == self.selectedtarget.type:
				if self.selectedtype.name == 'acquisition':
					if self.isAutoFocus():							# only delete focus target if it belongs only to this target
						focus_t = self.targetmap[self.selectedtarget]['focus']
						self.deleteTarget(focus_t)
					track_t = self.targetmap[self.selectedtarget]['track']
					self.deleteTarget(track_t)
					self.clearAcquitionTargetMap(self.selectedtarget)
				# any matched type. i.e., all except focus and track
				self.deleteTarget(self.selectedtarget)
					
	#--------------------
	def _onShiftRightClick(self, evt):
		if self.selectedtarget is not None :
			if self.selectedtarget.type.name == 'track':
				pass
			elif self.selectedtarget.type.name == 'focus':
				if self.isAutoFocus():
					pass
				else:
					if self.selectedtype == self.selectedtarget.type:
						self.clearFocusTargetMap()						# clear association
						self.deleteTarget(self.selectedtarget)			# remove focus target
			else:
				if self.selectedtype == self.selectedtarget.type:
					if self.selectedtype.name == 'acquisition':
						self.clearTargetMap()
						self.clearTargetType(self.getTrackType())
						if self.isAutoFocus() and self.getFocusType():	# TODO: this is sketchy
							self.clearTargetType(self.getFocusType())
					# any matched type. i.e., all except focus and track
					self.clearTargetType(self.selectedtype)

	def resetFocusTargets(self,state,offset):
		# redraw focus targets
		# (1) remove all targets
		# (2) if state is True, add targets with value
		# (3) display if set to display in target tool
		focustype = self.getFocusType()
		if focustype:
			self.clearFocusTargetMap()
			self.clearTargetType(focustype)				
			
			if not state:								# user defined focus spot
				pass
			else:
				acquisition_ts = self.getTargets('acquisition')
				for aq_t in acquisition_ts:
					x, y = aq_t.position						# this is relative to current camera and binning
					x_, y_ = self.getFocusPosition(x, y, offset)
					self.addTarget('focus', x_, y_)
					focus_t = self.getTargets('focus')[-1]
					self.addFocusTargetMap(focus_t, aq_t)
		else:
			pass
		
	def resetTrackTargets(self,offset):
		# redraw tracking targets
		# (1) remove all targets
		# (2) display if set to display in target tool
		tracktype = self.getTrackType()
		if tracktype:
			self.clearTrackTargetMap()
			self.clearTargetType(tracktype)
			acquisition_ts = self.getTargets('acquisition')
			for aq_t in acquisition_ts:
				x, y = aq_t.position
				x_, y_ = self.getTrackPosition(x, y, offset)
				self.addTarget('track', x_, y_)
				track_t = self.getTargets('track')[-1]
				self.addTrackTargetMap(track_t, aq_t)
		else:
			pass
				
	#--------------------
	def _onShiftCtrlRightClick(self, evt):
		self.clearAllTargetTypes()
	
	def getTrackPosition(self, x, y, offset=None):
		dy,dx = self.parent.node.getTrackOffset(offset)
		return (x+dx,y+dy)

	def getFocusPosition(self, x, y, offset=None):
		dy,dx = self.parent.node.getFocusOffset(offset)
		return (x+dx,y+dy)

if __name__ == '__main__':
	import sys
	import numpy
	from pyami import mrc 

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None
	try:
		box = sys.argv[2]
		box = int(box)
	except IndexError:
		box = 0

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			#self.panel = leginon.gui.wx.ImagePanel.ImagePanel(frame, -1)
			#self.panel = leginon.gui.wx.ImagePanel.ClickImagePanel(frame, -1)
			#self.panel.Bind(EVT_IMAGE_CLICKED, lambda e: self.panel.setImage(self.panel.imagedata))
			#self.panel = TargetImagePanel(frame, -1)

			self.panel = TargetOutputPanel(frame, -1)
			self.panel.addTargetTool('Target Practice', color=wx.RED, target=True)
			self.panel.setTargets('Target Practice', [])
			# integration half box size
			self.panel.box = box

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True
	array = None
	if filename is None:
		filename = input('Enter file path: ')
	if not filename:
		array = None
	elif filename[-4:] == '.mrc' or filename[-5:] == '.mrcs':
		h = mrc.readHeaderFromFile(filename)
		if h['mz'] == 0:
			print('invalid mz, assumes 1')
			h['mz'] = 1
		nframes = h['nz']/h['mz']
		frame = 0
		# 2D image stack
		if h['mz'] == 1:
			if nframes > 1:
				# mrc2014 image stack
				frame_str = input('This is an image stack of %d frames.\n Enter 0 to %d to select a frame to load: ' % (nframes,nframes-1))
				frame = int(frame_str)
		else:
			if nframes > 1:
				slice_str = input('This is a stack of %d volume.\n Enter 0 to %d to select a slice to load: ' % (nframes,h['nz']-1))
			else:
				slice_str = input('This is a volume.\n Enter 0 to %d to select a slice to load: ' % (h['nz']-1))
			frame = int(slice_str)
		image = mrc.read(filename,frame)
		array = image.astype(numpy.float32)

	elif filename[-4:] == '.tif':
		# This is only for RawImage tiff files taken from DirectElectron DE camera
		import tifffile
		tif = tifffile.TIFFfile(filename)
		a = tif.asarray()
		a = numpy.asarray(a,dtype=numpy.float32)
		# DE RawImage tiff files is mirrored horizontally from Leginon
		array = a[:,::-1]
	else:
		from pyami import numpil
		array = numpil.read(filename)
	#start gui
	app = MyApp(0,box)
	app.panel.setImage(array)
	app.MainLoop()

