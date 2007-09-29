#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetPanelBitmaps.py,v $
# $Revision: 1.5 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-29 00:25:42 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import wx

penwidth = 2
iconlength = 15

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
			dc.DrawPoint(1, 7)
		elif shape == '[]':
			dc.DrawLine(1, 1, 1, 14)
			dc.DrawLine(1, 14, 14, 14)
			dc.DrawLine(14, 1, 14, 14)
			dc.DrawLine(1, 1, 14, 1)
		elif shape == 'x':
			dc.DrawLine(1, 1, 13, 13)
			dc.DrawLine(1, 13, 13, 1)
			dc.DrawPoint(1, 7)
		elif shape == '*':
			dc.DrawLine(1, 1, 13, 13)
			dc.DrawLine(1, 13, 13, 1)
			dc.DrawLine(8, 1, 8, 14)
			dc.DrawLine(1, 8, 14, 8)
			dc.DrawPoint(1, 7)
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
def getTargetBitmap(color, shape='+',size=iconlength):
	try:
		return targetbitmaps[color,shape]
	except KeyError:
		if shape == '+':
			bitmap = targetBitmap_plus(color)
		elif shape == '.':
			bitmap = targetBitmap_point(color)
		elif shape == 'x':
			bitmap = targetBitmap_cross(color)
		elif shape == '[]':
			bitmap = targetBitmap_square(color)
		elif shape == '*':
			bitmap = targetBitmap_star(color)
		elif shape == 'o':
			bitmap = targetBitmap_circle(color,diam=size)
		else:
			raise RuntimeError('invalid target shape: '+shape)
		targetbitmaps[color,shape] = bitmap
	return bitmap

#--------------------
def targetBitmap_point(color):
	bitmap = wx.EmptyBitmap(1, 1)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, 1))
	dc.DrawPoint(0,0)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_plus(color):
	bitmap = wx.EmptyBitmap(iconlength, iconlength)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawLine(iconlength/2, 0, iconlength/2, iconlength)
	dc.DrawLine(0, iconlength/2, iconlength, iconlength/2)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_cross(color):
	bitmap = wx.EmptyBitmap(iconlength, iconlength)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawLine(0, 0, iconlength, iconlength)
	dc.DrawLine(0, iconlength, iconlength, 0)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_square(color):
	bitmap = wx.EmptyBitmap(iconlength, iconlength)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawLine(1, 1, iconlength-2, 1)
	dc.DrawLine(1, 1, 1, iconlength-2)
	dc.DrawLine(1, iconlength-2, iconlength-2, iconlength-1)
	dc.DrawLine(iconlength-2, 1, iconlength-2, iconlength-1)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_star(color):
	bitmap = wx.EmptyBitmap(iconlength, iconlength)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	#diagonal lines
	dc.DrawLine(2, 2, iconlength-3, iconlength-3)
	dc.DrawLine(2, iconlength-3, iconlength-3, 2)
	#horiz/vert lines
	dc.DrawLine(iconlength/2, 0, iconlength/2, iconlength)
	dc.DrawLine(0, iconlength/2, iconlength, iconlength/2)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def targetBitmap_circle(color,diam=iconlength):
	bitmap = wx.EmptyBitmap(diam, diam)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.Clear()
	dc.SetBrush(wx.Brush(color, wx.TRANSPARENT))
	dc.SetPen(wx.Pen(color, penwidth))
	dc.DrawCircle(diam/2, diam/2, diam/2-1)
	dc.EndDrawing()
	dc.SelectObject(wx.NullBitmap)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

#--------------------
def getTargetBitmaps(color, shape='+',size=iconlength):
	selectedcolor = wx.Color(color.Red()/2, color.Green()/2, color.Blue()/2)
	return getTargetBitmap(color, shape,size), getTargetBitmap(selectedcolor, shape,size)


