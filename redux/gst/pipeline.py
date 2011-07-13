#!/usr/bin/env python

import gobject
gobject.threads_init()

# import gst and gtk
import gst
import gtk

import numpygst
import numpy

import scipy.ndimage

class NewElement(gst.Element):
	""" A basic, buffer forwarding gstreamer element """

	#here we register our plugin details
	__gstdetails__ = (
		"NewElement plugin",
		"newelement.py",
		"gst.Element, that passes a buffer from source to sink (a filter)",
		"")
	
	#source pad (template): we send buffers forward through here
	src_caps = gst.Caps('video/x-raw-rgb')
	src_caps[0]['width'] = 182
	src_caps[0]['height'] = 126
	src_caps[0]['framerate'] = gst.Fraction(0)
	src_caps[0]['bpp']=24
	src_caps[0]['depth']=24
	src_caps[0]['endianness'] = 4321
	src_caps[0]['red_mask'] = 16711680
	src_caps[0]['blue_mask'] = 255
	src_caps[0]['green_mask'] = 65280
	#src_caps = gst.caps_new_any()
	_srctemplate = gst.PadTemplate ('src',
		gst.PAD_SRC,
		gst.PAD_ALWAYS,
		src_caps)

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

		try:
			a = numpygst.ndarray_from_gst_buffer(buf)
		except Exception, e:
			print e
			raise

		#b = a.copy()
		## ndimage does not like fields
		print 'AAA', a.dtype, len(a.data), a.strides
		import numpy
		av = a.view(numpy.uint8)
		print 'BBB'
		av.shape = a.shape + (-1,)
		print 'CCC', av.shape
		import scipy.misc
		#b = scipy.ndimage.zoom(av, (0.5,1,1))
		b = scipy.ndimage.zoom(av, (1,0.5,1))
		scipy.misc.imsave('rgb.jpg', b)
		print 'EEE', b.shape, b.dtype, b[25,3]
		#b = numpy.asarray(b, a.dtype)
		b = b.view(a.dtype)
		b = numpy.array(b)
		print 'FFF', b.shape, b[25,3], len(b.data), a.strides
		#b[:,:,2] = 0
		#b[:,:,0] = 0
		try:
			newbuf = numpygst.gst_buffer_from_ndarray(b)
		except Exception, e:
			print e

		try:
			# fixate caps
			src_caps = self.srcpad.get_caps()
			print 'SOURCE CAPS', src_caps
			numpygst.print_caps(src_caps)
			print ''
			newcaps = newbuf.get_caps()
			ret = self.srcpad.fixate_caps(newcaps)
			print 'FIXATE', ret
			ret = self.srcpad.set_caps(newcaps)
			print 'SET', ret
			print 'SOURCE CAPS', src_caps
			numpygst.print_caps(src_caps)
			print ''
		except Exception, e:
			print e

		try:
			print 'BUF LEN', len(newbuf.data)
			ret = self.srcpad.push(newbuf)
			print ''
			print 'BUF', buf.get_caps()
			print ''
			print 'NEWBUF', newbuf.get_caps()
			print ''
			return ret
		except Exception, e:
			print e
			raise

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

pipeline = gst.Pipeline()
if False:
	pipeline.add(filesrc, pngdec, filt, filesink)
	gst.element_link_many(filesrc, pngdec, filt, filesink)
if True:
	pipeline.add(filesrc, pngdec, filt, jpegenc, filesink)
	gst.element_link_many(filesrc, pngdec, filt, jpegenc, filesink)
if False:
	pipeline.add(filesrc, pngdec, jpegenc, filesink)
	gst.element_link_many(filesrc, pngdec, jpegenc, filesink)

# get pipeline's bus
bus = pipeline.get_bus()

def debug1():
	filt_src = filt.get_pad('src')
	caps = filt_src.get_negotiated_caps()
	print ''
	print 'NEGOTIATED'
	numpygst.print_caps(caps)
	print ''
	jpegsink = jpegenc.get_pad('sink')
	caps = jpegsink.get_caps()
	#print 'JPEG SINK CAPS'
	#numpygst.print_caps(caps)
	#print ''

def quit():
	debug1()
	print 'QUIT'
	pipeline.set_state(gst.STATE_NULL)
	gtk.main_quit()

# set up message handler
def handle_message(bus, message, data):
	#print 'HANDLEMESSAGE', message.src, pipeline, message.type
	# check for pipeline EOS
	if message.src is pipeline and message.type is gst.MESSAGE_EOS:
		quit()
	return True

bus.add_watch(handle_message, None)

# set pipeline to playback state
pipeline.set_state(gst.STATE_PLAYING)

gtk.main()
