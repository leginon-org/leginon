#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetPanelBitmaps.py,v $
# $Revision: 1.8 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-05 21:00:48 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import wx
import sys

penwidth = 2
global_width = 16

targeticonbitmaps = {}

#--------------------
def getTargetIconBitmap(color, shape='+'):
	try:
		return targeticonbitmaps[color,shape]
	except KeyError:
		bitmap = targetIcon(color, shape)
		targeticonbitmaps[color,shape] = bitmap
		return bitmap

#--------------------
def targetIcon(color, shape):
		bitmap = wx.EmptyBitmap(16,16)
		dc = wx.MemoryDC()
		dc.SelectObject(bitmap)
		dc.BeginDrawing()
		dc.Clear()
		dc.SetPen(wx.Pen(color, 2))
		if shape == '.':
			for point in ((0,8),(8,0),(8,8),(8,9),(9,8)):
				dc.DrawPoint(*point)
		elif shape == '+':
			dc.DrawLine(8, 1, 8, 14)
			dc.DrawLine(1, 8, 14, 8)
		elif shape == '[]':
			dc.DrawRectangle(1, 1, 14, 14)
			#dc.DrawLine(1, 1, 1, 14)
			#dc.DrawLine(1, 14, 14, 14)
			#dc.DrawLine(14, 1, 14, 14)
			#dc.DrawLine(1, 1, 14, 1)
		elif shape == '<>':
			dc.DrawLines(((1, 7), (7, 14), (14, 7), (7, 1), (1, 7)))
			#dc.DrawLine(1, 7, 7, 14)
			#dc.DrawLine(7, 14, 14, 7)
			#dc.DrawLine(14, 7, 7, 1)
			#dc.DrawLine(7, 1, 1, 7)
		elif shape == 'x':
			dc.DrawLine(1, 1, 13, 13)
			dc.DrawLine(1, 13, 13, 1)
		elif shape == '*':
			dc.DrawLine(1, 1, 13, 13)
			dc.DrawLine(1, 13, 13, 1)
			dc.DrawLine(8, 1, 8, 14)
			dc.DrawLine(1, 8, 14, 8)
		elif shape == 'o':
			dc.DrawCircle(7, 7, 7)
		elif shape == 'numbers':
			dc.DrawText("#", 0, 0)
		elif shape == 'polygon':
			dc.DrawLine(3, 1, 13, 1)
			dc.DrawLine(13, 1, 13, 13)
			dc.DrawLine(13, 13, 7, 13)
			dc.DrawLine(7, 13, 3, 1)
		dc.EndDrawing()
		dc.SelectObject(wx.NullBitmap)
		bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
		return bitmap

targetbitmaps = {}

#--------------------
def getTargetBitmap(color, shape='+', size=global_width):
	try:
		return targetbitmaps[color,shape]
	except KeyError:
		if shape == '+':
			bitmap = targetBitmap_plus(color, width=size)
		elif shape == '.':
			bitmap = targetBitmap_point(color, width=size)
		elif shape == 'x':
			bitmap = targetBitmap_cross(color, width=size)
		elif shape == '[]':
			bitmap = targetBitmap_square(color, width=size)
		elif shape == '<>':
			bitmap = targetBitmap_diamond(color, width=size)
		elif shape == '*':
			bitmap = targetBitmap_star(color, width=size)
		elif shape == 'o':
			bitmap = targetBitmap_circle(color, width=size)
		else:
			raise RuntimeError('invalid target shape: '+shape)
		targetbitmaps[color,shape] = bitmap
	return bitmap

#--------------------
def targetBitmap_point(color, width=global_width):
	actual_width = int(width/8)+1
	bitmap = wx.EmptyBitmap(actual_width, actual_width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, 1))
	for i in range(actual_width):
		for j in range(actual_width):
			dc.DrawPoint(i,j)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_plus(color, width=global_width):
	bitmap = wx.EmptyBitmap(width, width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawLine(width/2, 0, width/2, width)
	dc.DrawLine(0, width/2, width, width/2)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_cross(color, width=global_width):
	bitmap = wx.EmptyBitmap(width, width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawLine(0, 0, width, width)
	dc.DrawLine(0, width, width, 0)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_square(color, width=global_width):
	bitmap = wx.EmptyBitmap(width, width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawRectangle(1, 1, width-2, width-2)
	#dc.DrawLine(1, 1, width-2, 1)
	#dc.DrawLine(1, 1, 1, width-2)
	#dc.DrawLine(1, width-2, width-2, width-1)
	#dc.DrawLine(width-2, 1, width-2, width-1)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_diamond(color, width=global_width):
	bitmap = wx.EmptyBitmap(width, width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	half = int((width-1)/2)
	full = width-1
	dc.DrawLines(((1, half), (half, full), (full-1, half), (half, 1), (1, half)))
	#dc.DrawLine(1, half, half, full)
	#dc.DrawLine(half, full, full, half-1)
	#dc.DrawLine(full, half-1, half, 1)
	#dc.DrawLine(half, 1, 1, half)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_star(color, width=global_width):
	bitmap = wx.EmptyBitmap(width, width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	#diagonal lines
	dc.DrawLine(2, 2, width-3, width-3)
	dc.DrawLine(2, width-3, width-3, 2)
	#horiz/vert lines
	dc.DrawLine(width/2, 0, width/2, width)
	dc.DrawLine(0, width/2, width, width/2)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_circle(color, width=global_width):
	bitmap = wx.EmptyBitmap(width, width)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawCircle(width/2, width/2, width/2-1)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def getTargetBitmaps(color, shape='+', size=global_width):
	selectedcolor = wx.Color(color.Red()/2, color.Green()/2, color.Blue()/2,)
	return getTargetBitmap(color, shape, size), getTargetBitmap(selectedcolor, shape, size)


