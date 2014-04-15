#!/usr/bin/env python
import math
import sys
import os
import xml.dom.minidom
import xml.etree.ElementTree as et

class FalconFrameConfigXmlMaker(object):
	def __init__(self):
		self.base_frame_time = 0.055771
		self.frame_time = 0.055771
		self.format_version = 1.0
		self.base_frame_path = 'E:\\frames'
		self.frame_path = 'E:\\frames'
		self.configxml_path = 'C:\Titan\Data\Falcon'
		self.total_output_frames = 7

	def setFrameTime(self,second):
		self.frame_time = second

	def getFrameTime(self):
		return self.frame_time

	def setFramePath(self,path):
		self.frame_path = path

	def getFramePath(self):
		return self.frame_path

	def setNFrames(self,nframes):
		self.total_output_frames = nframes

	def getNFrames(self):
		return self.total_output_frames

	def setFrameRange(self,exposure_time,frame_offset=1):
		'''
		frame number range to output.  Frame 0  is the first frame with
		shutter roll-in.
		'''
		total_output_frames = self.total_output_frames
		end_frames = []

		# available number of frames
		available_nframes = int(exposure_time / self.base_frame_time)
		# avoid roll-in
		equal_step = (available_nframes-frame_offset) / total_output_frames
		spare_frames = available_nframes - equal_step * total_output_frames - frame_offset
		frames_in_step = []
		if equal_step > 0:
			frames_in_step = total_output_frames * [equal_step,]
			for i in range(1,spare_frames+1):
				frames_in_step[-1*i] += 1
		else:
			frames_in_step = total_output_frames * [1,]
		end_frames = map((lambda x:sum(frames_in_step[:x+1])),range(len(frames_in_step)))
		start_frames = map((lambda x:end_frames[x]+1),range(len(end_frames)-1))
		start_frames.insert(0,frame_offset)
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
		print xmlstr
		f = open(os.path.join(self.configxml_path,'IntermediateConfig.xml'),'w')
		f.write(xmlstr)
		f.close()

	def getFrames(self):
		return range(1,8,1)

	def makeConfigFromExposureTime(self,second):
		start_frames,end_frames = self.setFrameRange(second,1)
		self.writeConfigXml(start_frames,end_frames)

	def makeDummyConfig(self):
		self.setNFrames(1)
		self.setFramePath(os.path.join(self.base_frame_path,'dummy'))
		self.makeConfigFromExposureTime(self.base_frame_time)

if __name__ == '__main__':
		if len(sys.argv) != 2:
			print 'usage: falconframe.py exposure_time_in_second'
			print 'default to 0.5 second'
			exposure_second = 0.5
		else:
			exposure_second = float(sys.argv[1])
		app = FalconFrameConfigXmlMaker()
		#app.makeDummyConfig()
		app.setNFrames(7)
		app.makeConfigFromExposureTime(exposure_second)
