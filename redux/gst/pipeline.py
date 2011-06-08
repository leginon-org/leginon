#!/usr/bin/env python

import gobject
gobject.threads_init()

# import gst and gtk
import gst
import gtk

import numpy

class NewElement(gst.Element):
	""" A basic, buffer forwarding gstreamer element """

	#here we register our plugin details
	__gstdetails__ = (
		"NewElement plugin",
		"newelement.py",
		"gst.Element, that passes a buffer from source to sink (a filter)",
		"")
	
	#source pad (template): we send buffers forward through here
	_srctemplate = gst.PadTemplate ('src',
		gst.PAD_SRC,
		gst.PAD_ALWAYS,
		gst.caps_new_any())

	#sink pad (template): we recieve buffers from our sink pad
	_sinktemplate = gst.PadTemplate ('sink',
		gst.PAD_SINK,
		gst.PAD_ALWAYS,
		gst.caps_new_any())
	
	#register our pad templates
	__gsttemplates__ = (_srctemplate, _sinktemplate)

	def __init__(self, *args, **kwargs):   
		#initialise parent class
		gst.Element.__init__(self, *args, **kwargs)
		
		#source pad, outgoing data
		self.srcpad = gst.Pad(self._srctemplate)
		
		#sink pad, incoming data
		self.sinkpad = gst.Pad(self._sinktemplate)
		self.sinkpad.set_setcaps_function(self._sink_setcaps)
		self.sinkpad.set_chain_function(self._sink_chain)
		
		#make pads available
		self.add_pad(self.srcpad)
		self.add_pad(self.sinkpad)
	
	def _sink_setcaps(self, pad, caps):
		#we negotiate our capabilities here, this function is called
		#as autovideosink accepts anything, we just say yes we can handle the
		#incoming data
		return True
	
	def _sink_chain(self, pad, buf):
		#this is where we do filtering
		#and then push a buffer to the next element, returning a value saying
		# it was either successful or not.
		print ''
		print 'DIR BUF'
		print dir(buf)
		print 'CAPS'
		caps = buf.get_caps()[0]
		print 'KEYS', caps.keys()
		width = caps['width']
		height = caps['height']
		bpp = caps['bpp']
		print 'depth', caps['depth']
		print 'endianness', caps['endianness']
		# keys:  ['width', 'height', 'bpp', 'framerate', 'depth', 'endianness', 'red_mask', 'green_mask', 'blue_mask']
		print 'DATA'
		print type(buf.data)
		print dir(buf.data)
		print 'LEN', len(buf.data)
		print ''

		dt = numpy.dtype(numpy.uint8)
		input_array = numpy.frombuffer(buf.data, dt)
		bytes_per_pixel = bpp / 8
		input_shape = height, width, bytes_per_pixel
		print 'INPUT SHAPE', input_shape
		input_array.shape = input_shape
		print 'ARRAY'
		print input_array

		'''
		newbuf = gst.Buffer()
		output_array = numpy.frombuffer(newbuf.data, dt)
		self.process(input_array, output_array)
		'''

		return self.srcpad.push(buf)

	def process(self, array):
		pass


#here we register our class with glib, the c-based object system used by
#gstreamer
gobject.type_register(NewElement)

# first create individual gstreamer elements

filesrc = gst.element_factory_make("filesrc")
filesrc.set_property('location', 'example.png')
pngdec = gst.element_factory_make("pngdec")

filt = NewElement()

jpegenc = gst.element_factory_make("jpegenc")
filesink = gst.element_factory_make("filesink")
filesink.set_property('location', 'test.jpg')

# create the pipeline

p = gst.Pipeline()
p.add(filesrc, pngdec, filt, jpegenc, filesink)
gst.element_link_many(filesrc, pngdec, filt, jpegenc, filesink)
# set pipeline to playback state

p.set_state(gst.STATE_PLAYING)

gtk.main()
