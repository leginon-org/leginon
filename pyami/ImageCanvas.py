#!/usr/bin/env python

from Tkinter import *
from NumericImage import *
import time

class ImageCanvas(Frame):
	def __init__(self, *args, **kargs):
		Frame.__init__(self, *args, **kargs)
		self.__build()
		self.bindings()
		self.zoomfactor = 1.0
		self.cursorinfo = CursorInfo(self)
		self.scalingwidget = []
		self.numimage = None

	def bindings(self):
		self.canvas.bind('<Configure>', self.configure_callback)
		self.canvas.bind('<Motion>', self.motion_callback)
		self.canvas.bind('<Leave>', self.leave_callback)
		self.canvas.bind('<Enter>', self.enter_callback)

	def __build(self):
		bgcolor = self['background']
		can = self.canvas = Canvas(self, bg=bgcolor)
		self.canimage = can.create_image(0, 0, anchor=NW)
		hs = self.hscroll = Scrollbar(self, orient=HORIZONTAL, background=bgcolor, troughcolor=bgcolor)
		vs = self.vscroll = Scrollbar(self, orient=VERTICAL, background=bgcolor, troughcolor=bgcolor)

		## connect canvas to scrollbars
		can.config(xscrollcommand=hs.set, yscrollcommand=vs.set)
		hs.config(command=can.xview)
		vs.config(command=can.yview)
		can.grid(row=0, column=0, sticky=NSEW)
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

		self.hscroll_state(ON)
		self.vscroll_state(ON)

	def hscroll_state(self, switch):
		if switch == ON:
			self.hscroll.grid(row=1, column=0, sticky=NSEW)
		elif switch == OFF:
			self.hscroll.grid_remove()
		self.scroll_switched = 1

	def vscroll_state(self, switch):
		if switch == ON:
			self.vscroll.grid(row=0, column=1, sticky=NSEW)
		elif switch == OFF:
			self.vscroll.grid_remove()
		self.scroll_switched = 1

	def configure_callback(self, event):

		### check if container is bigger than canvas
		if self.winfo_width() < int(self.canvas['width']):
			self.hscroll_state(ON)
		else:
			self.hscroll_state(OFF)

		if self.winfo_height() < int(self.canvas['height']):
			self.vscroll_state(ON)
		else:
			self.vscroll_state(OFF)

	def getdata(self, numcoord):
		"""returns data value of the numeric array given the 
		photo image pixel coords"""
		return self.numimage.get(numcoord)

	def canvasxy_to_imagexy(self, coord):
		"""
		Return the image coords given the canvas coords.
		Normally (0,0) of image is anchored to (0,0) of canvas
		so there is a direct mapping of canvas to image coords
		"""
		### If anchoring image other than NW->(0,0), 
		### this should become more complicated
		return coord

	def extrema(self):
		if self.numimage:
			print self.numimage.extrema
			return self.numimage.extrema
		else:
			print 'no numimage'
			return None

	def resize(self, x1, y1, x2, y2):
		newwidth = x2 - x1
		newheight = y2 - y1
		self.canvas['width'] = newwidth
		self.canvas['height'] = newheight
		self.canvas['scrollregion'] = (x1,y1,x2,y2)

	def use_numeric(self, ndata):
		## use the old value of clip
		oldclip = self.clip()
		self.numimage = NumericImage(ndata,clip=oldclip)
		self.update_scaling_widgets()
		self.update_canvas()

	def update_scaling_widgets(self):
		for sw in self.scalingwidget:
			sw.set_from_imagecanvas()

	def clip(self, newclip=None):
		if newclip:
			self.__set_numimage_clip(newclip)
			self.update_canvas()

		return self.__get_numimage_clip()

	def __set_numimage_clip(self, newclip):
		if self.numimage:
			self.numimage.transform['clip'] = newclip

	def __get_numimage_clip(self):
		if self.numimage:
			return self.numimage.transform['clip']
		else:
			return None

	def update_canvas(self):
		self.numimage.update_image()
		self.photo = self.numimage.photoimage()
		newwidth = self.photo.width()
		newheight = self.photo.height()
		self.resize(0,0,newwidth,newheight)
		self.canvas.itemconfig(self.canimage, image=self.photo)
		self.update()

	def zoom(self, factor):
		self.zoomfactor = self.zoomfactor * factor
		oldsize = self.numimage.orig_size
		newsizex = int(round(oldsize[0] * self.zoomfactor))
		newsizey = int(round(oldsize[1] * self.zoomfactor))
		self.numimage.transform['output_size'] = (newsizex, newsizey)
		self.update_canvas()

	def canvasx(self, *args, **kargs):
		return self.canvas.canvasx(*args, **kargs)

	def canvasy(self, *args, **kargs):
		return self.canvas.canvasy(*args, **kargs)

	def leave_callback(self, event):
		self.cursorinfo.clear()

	def enter_callback(self, event):
		self.canvas['cursor'] = 'crosshair'

	def motion_callback(self, event):
		x = event.x
		y = event.y
		canx = int(self.canvas.canvasx(x))
		cany = int(self.canvas.canvasy(y))
		self.cursorinfo.query( (canx,cany) )

	def cursorinfo_widget(self, parent, *args, **kargs):
		return self.cursorinfo.widget(parent, *args, **kargs)


class CursorInfo:
	"""
	CursorInfo(imagecanvas)
	Maintains info about what is under the cursor.
	"""
	def __init__(self, imagecanvas):
		self.imagecanvas = imagecanvas
		self.numx = IntVar()
		self.numy = IntVar()
		self.numdata = DoubleVar()
		self.imagelevel = IntVar()

	def clear(self):
		self.numx.set('')
		self.numy.set('')
		self.numdata.set('')

	def query(self, cancoord):
		imcan = self.imagecanvas

		imcoord = imcan.canvasxy_to_imagexy( cancoord )
		if not imcan.numimage:
			return
		numcoord = imcan.numimage.imagexy_to_numericxy(imcoord)

		if numcoord:
			self.numx.set(numcoord[0])
			self.numy.set(numcoord[1])
			numdata = imcan.getdata(numcoord)
			numdata = float(numdata)
			self.numdata.set('%.4f' % numdata)
		else:
			self.clear()

	def widget(self, parent, *args, **kargs):
		return CursorInfoWidget(parent, self, *args, **kargs)
		
class CursorInfoWidget(Frame):
	def __init__(self, parent, cursorinfo, *args, **kargs):
		Frame.__init__(self,parent, *args, **kargs)
		self.xlab = Label(self, textvariable=cursorinfo.numx, width=6)
		self.ylab = Label(self, textvariable=cursorinfo.numy, width=6)
		self.ilab = Label(self, textvariable=cursorinfo.numdata, width=9)
		self['bg'] = parent['bg']
		self.xlab['bg'] = parent['bg']
		self.ylab['bg'] = parent['bg']
		self.ilab['bg'] = parent['bg']
		self.xlab.pack(side=LEFT)
		self.ylab.pack(side=LEFT)
		self.ilab.pack(side=LEFT)

class ScalingWidget(Frame):
	def __init__(self, parent, *args, **kargs):
		Frame.__init__(self, parent, *args, **kargs)
		self.imagecanvas = []
		self.rangemin = DoubleVar()
		self.rangemax = DoubleVar()
		self.limit_from = None
		self.limit_to = None
		self.minscalevalue = None
		self.maxscalevalue = None
		self.__build()
		self.__callbacks_off()

	def add_imagecanvas(self, imagecanvas):
		self.imagecanvas.append(imagecanvas)
		imagecanvas.scalingwidget.append(self)
		self.set_from_imagecanvas()

	def del_imagecanvas(self, imagecanvas):
		imagecanvas.scalingwidget.remove(self)
		self.imagecanvas.remove(imagecanvas)
		self.set_from_imagecanvas()

	def __build(self):
		self.minscale = Scale(self, orient=HORIZONTAL, showvalue=NO, width=8, length=300)
		self.maxscale = Scale(self, orient=HORIZONTAL, showvalue=NO, width=8, length=300)
		self.minlab = Label(self, textvariable=self.rangemin)
		self.maxlab = Label(self, textvariable=self.rangemax)

		print 'minrepeatdelay', self.minscale['repeatdelay']
		print 'maxrepeatdelay', self.maxscale['repeatdelay']

		self.minscale.grid(column=0, row=0)
		self.maxscale.grid(column=0, row=1)
		self.minlab.grid(column=1, row=0)
		self.maxlab.grid(column=1, row=1)

	def set_from_imagecanvas(self):
		"""
		This is called when a new imagecanvas is added
		Makes sure limits of scalebars are able to handle
		all data in the new imagecanvas.
		"""
		### find the min and max data of all imagecanvases
		minmin,maxmax = None,None
		for ican in self.imagecanvas:
			extrema = ican.extrema()
			if extrema:
				thismin,thismax = extrema
				## treat first good image different
				if minmin == None:
					minmin,maxmax = extrema
					cur_clip = ican.clip()
				else:
					if thismin < minmin:
						minmin = thismin
					if thismax > maxmax:
						maxmax = thismax

		if minmin == None:
			return

		self.__set_limits( (minmin, maxmax) )
		self.update()
		self.__callbacks_on()

	def __set_limits(self, newlimits):
		newmin = newlimits[0]
		newmax = newlimits[1]
		newres = (newmax - newmin) / 256.0
		self.minscale['resolution'] = newres
		self.maxscale['resolution'] = newres
		self.minscale['from'] = newmin
		self.maxscale['from'] = newmin
		self.minscale['to'] = newmax
		self.maxscale['to'] = newmax

	def __set_values(self, newvalues):
		self.minscale.set(newvalues[0])
		self.maxscale.set(newvalues[1])

	def __callbacks_on(self):
		self.minscale['command'] = self._minscale_callback
		self.maxscale['command'] = self._maxscale_callback

	def __callbacks_off(self):
		self.minscale['command'] = None
		self.maxscale['command'] = None

	def _minscale_callback(self, newval=None):
		### turn off this callback while it is running
		self.minscale['command'] = ''
		if self.minscalevalue == newval:
			self.minscale['command'] = self._minscale_callback
			return
		self.minscalevalue = newval
		self.rangemin.set(newval)
		self.__update_imagecanvas()
		self.minscale['command'] = self._minscale_callback

	def _maxscale_callback(self, newval=None):
		### turn off this callback while it is running
		self.maxscale['command'] = ''
		if self.maxscalevalue == newval:
			self.maxscale['command'] = self._maxscale_callback
			return
		self.maxscalevalue = newval

		self.rangemax.set(newval)
		self.__update_imagecanvas()
		self.maxscale['command'] = self._maxscale_callback

	def __update_imagecanvas(self):
		"""update the clipping on the imageitem"""
		rangemin = self.minscale.get()
		rangemax = self.maxscale.get()
		newrange = (rangemin, rangemax)
		for ic in self.imagecanvas:
			ic.clip(newrange)

if __name__ == '__main__':
	mycan = ImageCanvas(None,bg='darkgrey')
	mycan.pack(expand=YES,fill=BOTH)

	from mrc.Mrc import *
	ndata = mrc_to_numeric('float.mrc')
	mycan.use_numeric(ndata)
	mycan.update_canvas()

	newwin = Toplevel()
	sw = ScalingWidget(newwin)
	sw.pack()

	sw.add_imagecanvas(mycan)

	mycan.mainloop()
