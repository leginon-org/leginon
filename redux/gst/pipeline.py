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
		#b = scipy.ndimage.zoom(av, (0.5,0.5,1))
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
			ret = self.srcpad.push(newbuf)
			print 'BUF', buf.get_caps()
			print 'NEWBUF', newbuf.get_caps()
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

def quit():
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
