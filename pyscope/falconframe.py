#!/usr/bin/env python
import math
import sys
import os
import time
import xml.dom.minidom
import xml.etree.ElementTree as et
import itertools

class FalconFrameMaker(object):
	'''
	Base class for making Falcon frame range for given exposure time
	either when frames to be saved and not.
	The raw frames are put in limited number of bins.
	'''
	def __init__(self,simu=False):
		'''
		i/o time unit is second
		'''
		self.simulation = simu
		self.idcounter = itertools.cycle(range(100))
		self.base_frame_time = 0.055771
		self.format_version = 1.0
		self.no_save_frame_path = 'not_a_real_path'
		self.fei_image_storage_path = 'E:\\'
		self.base_frame_path = 'frames'
		self.frame_name_prefix = ''
		# almost limitless
		self.output_bin_limit = 1000
		self.output_bins = self.output_bin_limit + 0
		self.equal_distributed_frame = 0
		self.resetParams()

	def resetParams(self):
		self.frame_path = self.no_save_frame_path
		self.frames_name = ''
		# Readout delay of one means frame 0 (shutter roll-in) is  not readout
		self.internal_readout_delay = 1
		self.frame_readout_delay = 1
		self.equally_distributed_frame = 0

	def getBaseFrameTime(self):
		return self.base_frame_time

	def setBaseFrameTime(self,time_s):
		self.base_frame_time = time_s

	def getNumberOfBinLimit(self):
		return self.output_bin_limit

	def setFrameNamePrefix(self,prefix):
		if prefix is not None:
			self.frame_name_prefix = str(prefix)

	def getFrameNamePrefix(self):
		return self.frame_name_prefix
	
	def makeFrameDirName(self,use_timestamp):
		if use_timestamp:
			prefix = self.frame_name_prefix
			frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
			self.frames_name = prefix + frames_name + '%02d' % (self.idcounter.next(),)
		else:
			self.frames_name = 'dummy'
		return self.frames_name

	def getFrameDirName(self):
		'''
		older interface makes single files in this directory.
		'''
		return self.frames_name

	def getSubPathFramePattern(self):
		'''
		returns SubPathPattern required by advanced TEM scripting.
		'''
		return self.subpath_pattern

	def setFeiImageStoragePath(self,path):
		if path.endswith(':'):
			# Windows does not join path from drive preperly.
			path += '\\'
		self.fei_image_storage_path = path

	def setBaseFramePath(self,base_path):
		self.base_frame_path = base_path

	def getBaseFramePath(self):
		return self.base_frame_path

	def createFramePath(self,base_path):
		full_base_path = os.path.join(self.fei_image_storage_path, base_path)
		if not os.path.isdir(full_base_path):
			raise ValueError('Base Path %s not exists. Please create first' % full_base_path)
		return self._createFramePath(base_path)

	def _createFramePath(self, base_path):
		'''
		Directory of fullpath_pattern created here for TIA_Falcon style frames.
		'''
		full_base_path = os.path.join(self.fei_image_storage_path, base_path)
		if os.path.isdir(full_base_path) or self.simulation:
			new_frame_name = self.makeFrameDirName(True)
			# real path including existing base_path becomes the subpath_pattern
			self.subpath_pattern = os.path.join(base_path,new_frame_name)
			self.fullpath_pattern = os.path.join(self.fei_image_storage_path,self.subpath_pattern)
			if not self.simulation:
				os.makedirs(self.fullpath_pattern)
		else:
			# dummy path will keep the frames from being written
			self.makeFrameDirName(False)
			self.fullpath_pattern = full_base_path

	def getFramePath(self):
		return self.frame_path

	def validateExposureTime(self,second):
		'''
		Exposure time in second is valid only if it allows one frame to be
		saved after readout delay.
		'''
		if second < self.base_frame_time * (self.frame_readout_delay - 0.5):
			return False
		return True

	def setExposureTime(self,second):
		'''
		Set Exposure Time in second.  The time must be validated first.
		'''
		self.exposure_time = second

	def setMaxNumberOfFrameBins(self,nframes):
		'''
		Set maximal bins to output frames
		'''
		self.output_bins = min(self.output_bin_limit,nframes)

	def setEquallyDistributedStartFrame(self,frame_number):
		'''
		Set start of equal distribution to output frames
		'''
		self.equally_distributed_frame = frame_number

	def getNumberOfFrameBins(self):
		'''
		Get number of frame bins saved without running self.distributeFramesInBins()
		Exposure time must be set first.
		'''
		available_nframes = self.getNumberOfAvailableFrames()
		usable_nframes = available_nframes -self.frame_readout_delay
		return min(self.output_bins,max(usable_nframes,1))

	def setFrameReadoutDelay(self,value=1):
		self.frame_readout_delay = value

	def getFrameReadoutDelay(self):
		return self.frame_readout_delay

	def getNumberOfAvailableFrames(self):
		'''
		Available frames include the roll-in frame since exposure time does not include that.
		'''
		half_frame_time = self.base_frame_time / 2.0
		return int((self.exposure_time + half_frame_time) / self.base_frame_time) + self.internal_readout_delay

	def distributeFramesInBins(self):
		'''
		return list of number of frames in each output bin.
		'''
		eframe = max((self.equally_distributed_frame - self.frame_readout_delay,0))

		available_nframes = self.getNumberOfAvailableFrames()
		# usable number of frames does not include those not read for output
		usable_nframes = available_nframes -self.frame_readout_delay

		# initialize with single frames
		frames_in_bins = map((lambda x:1),range(eframe))
		# equally distribute the rest
		usable_equal_frames = usable_nframes - len(frames_in_bins)
		equal_bins = self.output_bins - len(frames_in_bins)
		frames_in_bins.extend(self._distributeItemsInBins(usable_equal_frames, equal_bins))
		return frames_in_bins

	def _distributeItemsInBins(self,n_items,bins):
		'''
		Distribute items in bins as evenly as possible.
		Fill spare items from the end
		'''
		# keep bin as equally occupied as possible
		equal_step = n_items / bins
		spare_frames = n_items - equal_step * bins
		n_items_in_bins = []
		if equal_step > 0:
			n_items_in_bins = bins * [equal_step,]
			# spare items are filled-in from the last bins
			for i in range(1,spare_frames+1):
				n_items_in_bins[-1*i] += 1
		else:
			# not enough items to fill all bins
			n_items_in_bins = n_items * [1,]
		return n_items_in_bins

	def setFrameRange(self):
		'''
		frame number range to output.  Frame 0  is the first frame with
		shutter roll-in.
		'''
		nframe_in_bins = self.distributeFramesInBins()
		if self.simulation:
			print 'number of base frames in bin', nframe_in_bins
		end_frames = []
		offset = self.frame_readout_delay - self.internal_readout_delay
		if False:
			return [0],[0]
		else:
			end_frames = map((lambda x:offset+sum(nframe_in_bins[:x+1])),range(len(nframe_in_bins)))
			start_frames = map((lambda x:end_frames[x]+1),range(len(end_frames)-1))
			start_frames.insert(0,self.frame_readout_delay)
		self.output_bins = len(start_frames)
		return start_frames, end_frames

class FalconFrameConfigXmlMaker(FalconFrameMaker):
	def __init__(self,simu=False):
		'''
		i/o time unit is second
		'''
		self.simulation = simu
		self.idcounter = itertools.cycle(range(100))
		self.base_frame_time = 0.055771
		self.format_version = 1.0
		self.no_save_frame_path = 'not_a_real_path'
		self.fei_image_storage_path = 'E:\\'
		self.base_frame_path = 'frames'
		self.frame_name_prefix = ''
		self.configxml_path = 'C:\Titan\Data\Falcon'
		# Falcon 2 software can save frames in at most 7 bins
		self.output_bin_limit = 7
		self.output_bins = self.output_bin_limit + 0
		self.equal_distributed_frame = 0
		self.resetParams()

	def writeConfigXml(self,start_frames,end_frames):
		rt = et.Element('IntermediateConfig')
		fv = et.SubElement(rt,'FormatVersion')
		fv.text = '%.1f' % self.format_version
		sp = et.SubElement(rt,'StoragePath')
		sp.text = self.fullpath_pattern
		ifb = {}
		for i in range(len(start_frames)):
			ifb[i] = et.SubElement(rt,'InterFrameBoundary')
			start = self.base_frame_time * (start_frames[i]+0.5)
			end = self.base_frame_time * (end_frames[i]+0.5)
			ifb[i].text = '%.3f - %.3f' % (start, end)
		# pretty print
		roughstr =  et.tostring(rt,'utf-8')
		reparsed = xml.dom.minidom.parseString(roughstr)
		xmlstr = reparsed.toprettyxml(indent="\t",newl='\n',encoding="utf-8")
		if not self.simulation:
			f = open(os.path.join(self.configxml_path,'IntermediateConfig.xml'),'w')
			f.write(xmlstr)
			f.close()
		else:
			print xmlstr

	def makeConfigXML(self):
		start_frames,end_frames = self.setFrameRange()
		self.writeConfigXml(start_frames,end_frames)

	def makeRealConfigFromExposureTime(self,second,equal_distr_frame=0,delay=None):
		'''
		Make Useful Frame saving config.xml.
		Minimal is 2 base_frame_time
		'''
		self.resetParams()
		self.setMaxNumberOfFrameBins(7)
		self.setEquallyDistributedStartFrame(equal_distr_frame)
		if delay is not None:
			self.setFrameReadoutDelay(delay)
		status = self.validateExposureTime(second)
		if status is False:
			return False
		self.setExposureTime(second)
		self.makeConfigXML()
		return True

	def makeDummyConfig(self,second):
		'''
		Non-frame saving can be achieved by saving
		the frames to a directory under a non-existing
		directory
		'''
		self.resetParams()
		self.setMaxNumberOfFrameBins(1)
		self.setFrameReadoutDelay(1)
		status = self.validateExposureTime(second)
		if status is False:
			return status
		self.setExposureTime(self.base_frame_time)
		# self.no_save_frame_path needs to be on not existing
		# since FalconIntermediateImage program is capable of
		# making a directory below existing ones
		self.createFramePath(os.path.join(self.no_save_frame_path,'dummy'))
		self.makeConfigXML()
		return True

class FalconFrameRangeListMaker(FalconFrameMaker):
	def __init__(self,simu=False):
		'''
		i/o time unit is second
		Based on the behavior of Advanced Scripting for Falcon III
		'''
		self.simulation = simu
		self.idcounter = itertools.cycle(range(100))
		self.base_frame_time = 0.025
		self.number_of_available_frames = 1
		self.format_version = 1.0
		self.no_save_frame_path = ''
		self.fei_image_storage_path = 'Z:\\'
		self.base_frame_path = 'frames'
		self.frame_name_prefix = ''
		self.output_bin_limit = 1000
		self.output_bins = self.output_bin_limit + 0
		self.equal_distributed_frame = 0
		# Falcon III delay is zero
		self.setFrameReadoutDelay(0)
		self.resetParams()

	def _createFramePath(self, base_path):
		'''
		Overwrite base class _createFramePath to just assign attributes.
		No path or directory creation involved.
		'''
		new_frame_name = self.makeFrameDirName(True)
		# real path including existing base_path becomes the subpath_pattern
		self.subpath_pattern = os.path.join(base_path,new_frame_name)
		self.fullpath_pattern = os.path.join(self.fei_image_storage_path,self.subpath_pattern)

	def makeFrameDirName(self,use_timestamp):
		'''
		make frame stack name without mrc extension.
		For advanced tem scripting, this is the stack name not directory name.
		'''
		# no dummy
		prefix = self.frame_name_prefix
		frames_name = time.strftime('%Y%m%d_%H%M%S', time.localtime())
		self.frames_name = prefix + frames_name + '%02d' % (self.idcounter.next(),)
		return self.frames_name

	def getNumberOfAvailableFrames(self):
		return self.number_of_available_frames

	def setNumberOfAvailableFrames(self,number):
		self.number_of_available_frames = number

	def makeRangeList(self, starts, ends):
		length = len(starts)
		rangelist = []
		for i in range(length):
			rangelist.append((starts[i],ends[i]+1))
		return rangelist

	def makeRangeListFromNumberOfBaseFramesAndFrameTime(self, n_base_frames, frame_time_second):
		'''
		Distribute number of base frames by frame time.
		'''
		self.setNumberOfAvailableFrames(n_base_frames)
		exposure_second = n_base_frames * self.base_frame_time
		return self.makeRangeListFromExposureAndFrameTime(exposure_second, frame_time_second)

	def makeRangeListFromExposureAndFrameTime(self, exposure_second, frame_time_second):
		'''
		Distribute exposure time by frame time.
		'''
		self.setExposureTime(exposure_second)
		bin_second = frame_time_second
		bins = int(math.ceil(exposure_second*1000 / (bin_second*1000)))
		self.setMaxNumberOfFrameBins(bins)
		starts, ends = self.setFrameRange()
		rangelist = self.makeRangeList(starts, ends)
		return rangelist

	def test(self):
		starts, ends = self.setFrameRange()
		rangelist = self.makeRangeList(starts, ends)
		print rangelist

if __name__ == '__main__':
		equal_distr_frame = 0
		if len(sys.argv) < 2:
			print 'usage: falconframe.py exposure_time_in_second equal_distr_frame delay_number_frames'
			print 'default to 0.5 second'
			print 'default equal_distr_frame is the first non-single frame'
			print '  including which will be equally distributed'
			print 'delay_number_frames default is 1'
			exposure_second = 0.5
			delay = 1
		else:
			exposure_second = float(sys.argv[1])
			if len(sys.argv) >= 3:
				equal_distr_frame = int(sys.argv[2])
			else:
				equal_distr_frame = 0
			if len(sys.argv) == 4:
				delay = int(sys.argv[3])
			else:
				delay = 1
		fei_image_storage_path = os.getcwd()
		def testFalcon3():
			'''
			Test of the Advanced Scriptins RangeList making
			'''
			app = FalconFrameRangeListMaker(False)
			app.setFeiImageStoragePath(fei_image_storage_path)
			app.setBaseFramePath('framecam')
			app.createFramePath(app.base_frame_path)
			app.setFrameNamePrefix('f')
			app.setExposureTime(exposure_second)
			frame_time_second = 0.2
			bins = int(exposure_second / frame_time_second)
			app.setMaxNumberOfFrameBins(bins)
			n_base_frames = int(math.floor(exposure_second*1000 / (app.base_frame_time*1000)))
			print 'number of base frames: ',n_base_frames
			rangelist2 = app.makeRangeListFromNumberOfBaseFramesAndFrameTime(n_base_frames, frame_time_second)
			print 'range list: ',rangelist2
			print 'SubPathPattern: ', app.getSubPathFramePattern()
			print 'frame name: ',app.getFrameDirName()

		def testFalcon2():
			'''
			# Test of the Falcon2 Config Xml file making
			'''
			app = FalconFrameConfigXmlMaker(True)
			app.setFeiImageStoragePath(fei_image_storage_path)
			app.setBaseFramePath('framecam')
			#is_success = app.makeDummyConfig(exposure_second)
			is_success = app.makeRealConfigFromExposureTime(exposure_second, equal_distr_frame,delay)
			print 'is successful: ',is_success
			print 'frame name: ',app.getFrameDirName()

		testFalcon3()
