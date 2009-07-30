#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetPanel.py,v $
# $Revision: 1.10 $
# $Name: not supported by cvs2svn $
# $Date: 2008-01-18 04:58:49 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import time
import math
import wx
import Image
import gui.wx.ImagePanel
import gui.wx.ImagePanelTools
import gui.wx.TargetPanelTools

##################################
##
##################################

class TargetImagePanel(gui.wx.ImagePanel.ImagePanel):
	def __init__(self, parent, id, callback=None, 
			tool=True, imagesize=(256, 256), mode="horizontal"):
		gui.wx.ImagePanel.ImagePanel.__init__(self, parent, id, imagesize, mode)
		self.order = []
		self.reverseorder = []
		self.targets = {}
		self.selectedtype = None
		self.selectedtarget = None

	#--------------------
	def _getSelectionTool(self):
		if self.selectiontool is None:
			raise ValueError('No types added')
		return self.selectiontool

	#--------------------
	def addTargetTool(self, name, color, **kwargs):
		kwargs['display'] = color
		kwargs['toolclass'] = gui.wx.TargetPanelTools.TargetTypeTool
		self.addTypeTool(name, **kwargs)

	#--------------------
	def getTargets(self, name):
		return self._getSelectionTool().getTargets(name)

	#--------------------
	def addTarget(self, name, x, y):
		return self._getSelectionTool().addTarget(name, x, y)

	#--------------------
	def insertTarget(self, name, pos, x, y):
		return self._getSelectionTool().insertTarget(name, pos, x, y)

	#--------------------
	def deleteTarget(self, target):
		return self._getSelectionTool().deleteTarget(target)

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
				if not isinstance(t, gui.wx.TargetPanelTools.Target):
					raise TypeError
			self.targets[type] = targets
			if type not in self.order:
				self.order.append(type)
		self.reverseorder = list(self.order)
		self.reverseorder.reverse()
		self.UpdateDrawing()

	#--------------------
	def setDisplayedNumbers(self, type, targets):
		if targets is None:
			if type in self.targets:
				del self.targets[type]
				self.order.remove(type)
		else:
			targets = list(targets)
			for t in targets:
				if not isinstance(t, gui.wx.TargetPanelTools.Target):
					raise TypeError
			self.targets[type] = targets
			if type not in self.order:
				self.order.append(type)
		self.reverseorder = list(self.order)
		self.reverseorder.reverse()
		self.UpdateDrawing()

	#--------------------
	def _drawTargets(self, dc, bitmap, targets, scale):
		memorydc = wx.MemoryDC()
		memorydc.BeginDrawing()
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
		memorydc.EndDrawing()

	#--------------------
	def drawTargets(self, dc):
		scale = self.getScale()

		for type in self.order:
			targets = self.targets[type]
			if targets:
				if type.shape == 'polygon':
					self.drawPolygon(dc, type.color, targets)
				else:
					if type.shape == 'numbers':
						self.drawNumbers(dc, type.color, targets)
					else:
						self._drawTargets(dc, type.bitmaps['default'], targets, scale)

		if self.selectedtarget is not None:
			if self.selectedtarget.type in self.targets and type.shape != 'polygon' and type.shape != 'numbers':
				try:
					bitmap = self.selectedtarget.type.bitmaps['selected']
					self._drawTargets(dc, bitmap, [self.selectedtarget], scale)
				except AttributeError:
					pass

	#--------------------
	def drawPolygon(self, dc, color, targets):
		dc.SetPen(wx.Pen(color, 3))
		dc.SetBrush(wx.Brush(color, 1))
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
			scaledpoints = [(target.x,target.y) for target in targets]

		if len(scaledpoints)>=1:
			p1 = self.image2view(scaledpoints[0])
			dc.DrawCircle(p1[0],p1[1],1)
			
		for i,p1 in enumerate(scaledpoints[:-1]):
			p2 = scaledpoints[i+1]
			p1 = self.image2view(p1)
			p2 = self.image2view(p2)
			dc.DrawCircle(p2[0],p2[1],1)
			dc.DrawLine(p1[0], p1[1], p2[0], p2[1])
		# close it with final edge
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
		#print "drawing text of "+str(len(scaledpoints))+" targets"
		for i,p1 in enumerate(scaledpoints):
			p1 = self.image2view(p1)
			dc.DrawText(str(i+1), p1[0], p1[1])

	#--------------------
	def Draw(self, dc):
		#now = time.time()
		gui.wx.ImagePanel.ImagePanel.Draw(self, dc)
		dc.BeginDrawing()
		self.drawTargets(dc)
		dc.EndDrawing()
		#print 'Drawn', time.time() - now

	#--------------------
	def _onLeftClick(self, evt):
		if self.selectedtype is not None:
			x, y = self.view2image((evt.m_x, evt.m_y))
			self.addTarget(self.selectedtype.name, x, y)

	#--------------------
	def _onRightClick(self, evt):
		if self.selectedtarget is not None :
			if self.selectedtype == self.selectedtarget.type:
				self.deleteTarget(self.selectedtarget)

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
		gui.wx.ImagePanel.ImagePanel._onMotion(self, evt, dc)
#		if self.selectedtype is not None:
		viewoffset = self.panel.GetViewStart()
		x, y = self.view2image((evt.m_x, evt.m_y))
		self.selectedtarget = self.closestTarget(self.selectedtype, x, y)
#		else:
#			self.selectedtarget = None

	#--------------------
	def _getToolTipStrings(self, x, y, value):
		strings = gui.wx.ImagePanel.ImagePanel._getToolTipStrings(self, x, y, value)
		selectedtarget = self.selectedtarget
		if selectedtarget is not None:
			name = selectedtarget.type.name
			position = selectedtarget.position
			strings.append('%s (%g, %g)' % (name, position[0], position[1]))
			if isinstance(selectedtarget, gui.wx.TargetPanelTools.StatsTarget):
				for key, value in selectedtarget.stats.items():
					if type(value) is float:
						strings.append('%s: %g' % (key, value))
					else:
						strings.append('%s: %s' % (key, value))
		return strings

##################################
##
##################################


class ClickAndTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, mode="horizontal"):
		TargetImagePanel.__init__(self, parent, id, mode)
		if mode == "vertical":
			self.clicktool = self.addTool(gui.wx.ImagePanelTools.ClickTool(self, self.toolsizer, disable))
		else:
			self.clicktool = self.addTool(gui.wx.ImagePanelTools.ClickTool(self, self.toolsizer2, disable))
		self.Bind(gui.wx.ImagePanel.EVT_IMAGE_CLICK_DONE, self.onImageClickDone)
		self.sizer.Layout()
		self.Fit()

	#--------------------
	def onImageClickDone(self, evt):
		self.clicktool.onImageClickDone(evt)

class EllipseTargetImagePanel(TargetImagePanel):
	def __init__(self, parent, id, disable=False, mode="horizontal"):
		TargetImagePanel.__init__(self, parent, id, mode)
		self.addTool(gui.wx.ImagePanelTools.RecordMotionTool(self, self.toolsizer))
		self.panel.Bind(wx.EVT_MOTION, self.OnMotion)
		self.sizer.Layout()
		self.Fit()

	def setEllipseParams(self,params):
		if params:
			self.parent.setEllipseParams(params)
##################################
##
##################################

class TargetOutputPanel(TargetImagePanel):
	def __init__(self, parent, id, callback=None, tool=True):
		TargetImagePanel.__init__(self, parent, id, callback=callback, tool=tool)

		self.quit = wx.Button(self, -1, 'Quit')
		self.Bind(wx.EVT_BUTTON, self.onQuit, self.quit)
		self.sizer.Add(self.quit, (0, 0), (1, 1), wx.EXPAND)

	#--------------------
	def onQuit(self, evt):
		targets = self.getTargets('Target Practice')
		for target in targets:
			print '%s\t%s' % (target.x, target.y)
		wx.Exit()


if __name__ == '__main__':
	import sys

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = None

	class MyApp(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Viewer')
			self.sizer = wx.BoxSizer(wx.VERTICAL)

			#self.panel = gui.wx.ImagePanel.ImagePanel(frame, -1)
			#self.panel = gui.wx.ImagePanel.ClickImagePanel(frame, -1)
			#self.panel.Bind(EVT_IMAGE_CLICKED, lambda e: self.panel.setImage(self.panel.imagedata))
			#self.panel = TargetImagePanel(frame, -1)

			self.panel = TargetOutputPanel(frame, -1)
			self.panel.addTargetTool('Target Practice', color=wx.RED, target=True)
			self.panel.setTargets('Target Practice', [])

			self.sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL)
			frame.SetSizerAndFit(self.sizer)
			self.SetTopWindow(frame)
			frame.Show(True)
			return True

	app = MyApp(0)
	if filename is None:
		app.panel.setImage(None)
	elif filename[-4:] == '.mrc':
		image = mrc.read(filename)
		app.panel.setImage(image.astype(numpy.float32))
	else:
		app.panel.setImage(Image.open(filename))
	app.MainLoop()

