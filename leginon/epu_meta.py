#!/usr/bin/env python
import sys
from pyami import xmlfun

fraction_data_map = {
	# sinedon data key:(epu_meta_keys, subkey_map,convertionAttribueName)
	'frame time':(['Fractions',0,'Fraction','ExposureTime'],{},'convertFloat'),
}
tem_data_map = {
	# sinedon data key:(epu_meta_keys, subkey_map,convertionAttribueName)
	'hostname':(['instrument','ComputerName'],{},'convertCap2Lower'),
	'name':(['instrument','ComputerName'],{},'makeTemName'),
}

ccdcam_data_map = {
	# sinedon data key:(epu_meta_keys, subkey_map,convertionAttribueName)
	'hostname':(['instrument','ComputerName'],{},'convertCap2Lower'),
	'name':(['acquisition','camera','Name'],{},'convertCameraName'),
}

scope_em_data_map = {
	# sinedon_data_key:(epu_meta_keys, subkey_map,convertionAttribueName)
	'stage position':(['stage','Position'],{},'convertStagePosition'),
	'high tension':(['gun','AccelerationVoltage'],{},'convertInt'),
	'probe mode':(['optics','ProbeMode'],{},'convertProbeMode'),
	'beam tilt':(['optics','BeamTilt'],{},'convertXYFloat'),
	'beam shift':(['optics','BeamShift'],{},'convertXYFloat'),
	'image shift':(['optics','ImageShift'],{},'convertXYFloat'),
	'diffraction shift':(['optics','DiffractionShift'],{},'convertXYFloat'),
	'stigmator':(['optics',],{'condenser':'CondenserStigmator','objective':'ObjectiveStigmator','diffraction':'DiffractionStigmator'},'convertXYFloat'),
	'magnification':(['optics','TemMagnification','NominalMagnification'],{},'convertInt'),
	'defocus':(['optics','Defocus'],{},'convertFloat'),
	'focus':(['optics','Focus'],{},'convertFloat'),
	'intensity':(['optics','Intensity'],{},'convertFloat'),
	'spot size':(['optics','SpotIndex'],{},'convertInt'),
}

applied_defocus_map = {'defocus':(['CustomData','a:KeyValueOfstringanyType','a:Value'],{},'convertFloat'),
}

camera_em_data_map = {
	# sinedon_data_key:(epu_meta_keys, subkey_map,convertionAttribueName)
	'exposure time':(['acquisition','camera','ExposureTime'],{},'convert2Ms'),
	'binning':(['acquisition','camera','Binning'],{},'convertXYInt'),
	'dimension':(['acquisition','camera','ReadoutArea'],{},'convertDimension'),
	'offset':(['acquisition','camera','ReadoutArea'],{},'convertOffset'),
}

matrix_map = {
	'm':(['ReferenceTransformation','matrix'],{'m11':'a:_m11','m12':'a:_m12','m21':'a:_m21','m22':'a:_m22'},'convertFloat'),
}

class MetaMapping(object):
	def __init__(self):
		self.meta_data_dict = {}
		self.child_index = 0
		self.listing_names = []

	def setXmlFile(self, xml_file):
		self.meta_data_dict = xmlfun.readDictFromXml(xml_file, self.child_index, self.listing_names)

	def convertInt(self, data):
		return int(data)

	def convertFloat(self, data):
		return float(data)

	def convertCap2Lower(self, data):
		return data.lower()

	def convert2Ms(self, data):
		return float(data)*1000

	def convertXYFloat(self, data):
		return {'x':float(data['a:_x']),'y':float(data['a:_y'])}

	def convertXYInt(self, data):
		return {'x':int(data['a:x']),'y':int(data['a:y'])}

	def dataMapping(self, datadict, data_map):
		output_dict = {}
		for k in data_map.keys():
			keys, submaps, attr_name = data_map[k]
			data = datadict.copy()
			for dk in keys:
				data = data[dk]
			if submaps:
				newdata = {}
				for sk in submaps.keys():
					newdata[sk] = getattr(self,attr_name)(data[submaps[sk]])
			else:
				newdata = getattr(self,attr_name)(data)
			output_dict[k] = newdata
		return output_dict

class EpuFractionMapping(MetaMapping):
	def __init__(self):
		super(EpuFractionMapping, self).__init__()
		self.child_index = 1
		self.listing_names = ['Fractions',]

	def getFractionFrameTimeData(self, datadict):
		self.dataMapping(datadict,fraction_data_map)

	def run(self):
		print self.getFractionFrameTimeData(self.meta_data_dict)

class EpuMetaMapping(MetaMapping):
	def convertDimension(self, data):
		binning = self.convertXYInt(self.meta_data_dict['microscopeData']['acquisition']['camera']['Binning']) 
		# This is my guess of how dimension is converted
		return {'x':int(data['a:width'])/binning['x'],'y':int(data['a:height'])/binning['y']}
		
	def convertOffset(self, data):
		binning = self.convertXYInt(self.meta_data_dict['microscopeData']['acquisition']['camera']['Binning']) 
		# This is my guess of how offset is converted
		return {'x':int(data['a:x'])/binning['x'],'y':int(data['a:y'])/binning['y']}
		
	def makeTemName(self, hostname):
		name = hostname.split('-')[0].lower()
		first = name[0].upper()
		name = first+name[1:]
		if self.meta_data_dict['microscopeData']['optics']['EFTEMOn'] == 'true':
			name = 'EF-'+name
		if self.meta_data_dict['microscopeData']['optics']['ProjectorMode'] == 'diffraction':
			name = 'Diffr'+name
		return name

	def convertCameraName(self, data):
		if data.startswith('BM-'):
			data = data[3:]
		if data == 'Falcon':
			data = 'Falcon3'
		return data

	def convertStagePosition(self, data):
		return {'a':float(data['A']),'b':float(data['B']),'x':float(data['X']),'y':float(data['Y']),'z':float(data['Z'])}

	def convertProbeMode(self, data):
		return data[:-5].lower()



	def getTemData(self, datadict):
		# InstrumentData tem type
		# Missing cs
		return self.dataMapping(datadict,tem_data_map)

	def getCCDCameraData(self, datadict):
		# InstrumentData camera type
		return self.dataMapping(datadict,ccdcam_data_map)

	def getScopeEMData(self, datadict):
		# ScopeEMData is the scope parameter for an image
		scopemap = self.dataMapping(datadict,scope_em_data_map)
		applied_defocus_dict = self.dataMapping(self.meta_data_dict,applied_defocus_map)
		scopemap['defocus']=applied_defocus_dict['defocus']
		return scopemap

	def getCameraEMData(self, datadict):
		# CameraEMData is the image parameter for an image
		return self.dataMapping(datadict,camera_em_data_map)

	def getMatrix(self, datadict):
		return self.dataMapping(datadict,matrix_map)

	def run(self):
		#print self.getTemData(self.meta_data_dict['microscopeData'])
		#print self.getCCDCameraData(self.meta_data_dict['microscopeData'])
		print self.getScopeEMData(self.meta_data_dict['microscopeData'])
		#print self.getCameraEMData(self.meta_data_dict['microscopeData'])
		#print self.getMatrix(self.meta_data_dict)

if __name__=='__main__':
	xml_file='/Users/acheng/nis/epu_transfer/epu_data/WBG1G20JUN15S/Images-Disc1/GridSquare_15025733/GridSquare_20200615_184111.xml'
	#xml_file='/Users/acheng/nis/epu_transfer/epu_data/WBG1G20JUN15A/Images-Disc1/GridSquare_15025733/Data/FoilHole_15039809_Data_15029686_15029688_20200616_224220_Fractions.xml'
	app = EpuMetaMapping()
	app.setXmlFile(xml_file)
	app.run()
