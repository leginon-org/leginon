#!/usr/bin/env python
import math
import sys
import os
import xml.dom.minidom
import xml.etree.ElementTree as et

class FalconFrameConfigXmlMaker(object):
	'''
	Create Falcon IntermediateConfig.xml for given exposure time
	either when frames to be saved and not.
	The raw frames are put in limited number of bins.
	'''
	def __init__(self):
		'''
		i/o time unit is second
		'''
		self.base_frame_time = 0.055771
		self.frame_time = 0.055771
		self.format_version = 1.0
		self.no_save_frame_path = 'E:\\not_a_real_path'
		self.base_frame_path = 'E:\\frames'
		self.frame_path = 'E:\\frames'
		self.configxml_path = 'C:\Titan\Data\Falcon'
		# Falcon 2 software can save frames in at most 7 bins
		self.output_bin_limit = 7
		self.output_bins = self.output_bin_limit + 0
		# Readout delay of one means frame 0 (shutter roll-in) is  not readout
		self.frame_readout_delay = 1

	def getNumberOfBinLimit(self):
		return self.output_bin_limit

	def setFrameTime(self,second):
		self.frame_time = second

	def getFrameTime(self):
		return self.frame_time

	def setFramePath(self,path):
		self.frame_path = path

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

	def getNumberOfFrameBins(self):
		'''
		Get number of frame bins saved without running self.distributeFramesInBins()
		Exposure time must be set first.
		'''
		available_nframes = self.getNumberOfAvailableFrames()
		usable_nframes = available_nframes -self.frame_readout_delay
		return min(self.output_bins,max(usable_nframes,1))

	def setFrameReadOutDelay(self,value=1):
		self.frame_readout_delay = value

	def getFrameReadOutDelay(self):
		return self.frame_readout_delay

	def getNumberOfAvailableFrames(self):
		'''
		Available frames include the offset frames since exposure time does not include that.
		'''
		half_frame_time = self.base_frame_time / 2.0
		return int((self.exposure_time + half_frame_time) / self.base_frame_time) + self.getFrameReadOutDelay()

	def distributeFramesInBins(self):
		'''
		return list of number of frames in each output bin.
		'''
		output_bins = self.output_bins

		available_nframes = self.getNumberOfAvailableFrames()
		# usable number of frames does not include those not read
		usable_nframes = available_nframes -self.frame_readout_delay
		return self._distributeItemsInBins(usable_nframes,output_bins)

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
		end_frames = []
		if self.frame_readout_delay == 0:
			return [0],[0]
		else:
			end_frames = map((lambda x:sum(nframe_in_bins[:x+1])),range(len(nframe_in_bins)))
			start_frames = map((lambda x:end_frames[x]+1),range(len(end_frames)-1))
			start_frames.insert(0,self.frame_readout_delay)
		self.output_bins = len(start_frames)
		return start_frames, end_frames

	def writeConfigXml(self,start_frames,end_frames):
		rt = et.Element('IntermediateConfig')
		fv = et.SubElement(rt,'FormatVersion')
		fv.text = '%.1f' % self.format_version
		sp = et.SubElement(rt,'StoragePath')
		sp.text = self.frame_path
		ifb = {}
		for i in range(len(start_frames)):
			ifb[i] = et.SubElement(rt,'InterFrameBoundary')
			start = self.frame_time * (start_frames[i]+0.5)
			end = self.frame_time * (end_frames[i]+0.5)
			ifb[i].text = '%.3f - %.3f' % (start, end)
		# pretty print
		roughstr =  et.tostring(rt,'utf-8')
		reparsed = xml.dom.minidom.parseString(roughstr)
		xmlstr = reparsed.toprettyxml(indent="\t",newl='\n',encoding="utf-8")
		f = open(os.path.join(self.configxml_path,'IntermediateConfig.xml'),'w')
		f.write(xmlstr)
		f.close()

	def getFrames(self):
		return range(1,8,1)

	def makeConfigXML(self):
		start_frames,end_frames = self.setFrameRange()
		self.writeConfigXml(start_frames,end_frames)

	def makeRealConfigFromExposureTime(self,second):
		'''
		Make Useful Frame saving config.xml.
		Minimal is 2 base_frame_time
		'''
		self.setMaxNumberOfFrameBins(7)
		self.setFrameReadOutDelay(1)
		status = self.validateExposureTime(second)
		if status is False:
			return False
		self.setExposureTime(second)
		self.setFramePath(self.base_frame_path)
		self.makeConfigXML()
		return True

	def makeDummyConfig(self,second):
		'''
		Non-frame saving can be achieved by saving
		the frames to a directory under a non-existing
		directory
		'''
		self.setMaxNumberOfFrameBins(1)
		self.setFrameReadOutDelay(1)
		status = self.validateExposureTime(second)
		if status is False:
			return status
		self.setExposureTime(self.base_frame_time)
		# self.no_save_frame_path needs to be on not existing
		# since FalconIntermediateImage program is capable of
		# making a directory below existing ones
		self.setFramePath(os.path.join(self.no_save_frame_path,'dummy'))
		self.makeConfigXML()
		return True

if __name__ == '__main__':
		if len(sys.argv) != 2:
			print 'usage: falconframe.py exposure_time_in_second'
			print 'default to 0.5 second'
			exposure_second = 0.5
		else:
			exposure_second = float(sys.argv[1])
		app = FalconFrameConfigXmlMaker()
		#is_success = app.makeDummyConfig(exposure_second)
		is_success = app.makeRealConfigFromExposureTime(exposure_second)
		print is_success
