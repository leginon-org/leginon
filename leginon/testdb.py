from sqldict import *

dbc = MySQLdb.connect(host='localhost', db='test', user='anonymous', passwd='')
db = SQLDict(dbc)

presetDefinition = [{'Field': 'id', 'Type': 'int(16)', 'Key': 'PRIMARY', 'Extra':'auto_increment'},
			{'Field': 'Name', 'Type': 'varchar(30)'},
			{'Field': 'Width', 'Type': 'int(11)'},
			{'Field': 'Height','Type': 'int(11)'},
			{'Field': 'Binning', 'Type': 'int(11)'},
			{'Field': 'ExpTime', 'Type': 'float(10,4)'},
			{'Field': 'Dose', 'Type': 'float(10,4)'},
			{'Field': 'BeamCurrent', 'Type': 'float'},
			{'Field': 'LDButton', 'Type': 'varchar(20)'},
			{'Field': 'Mag', 'Type': 'int(11)'},
			{'Field': 'PixelSize', 'Type': 'float(10,4)'},
			{'Field': 'Defocus', 'Type': 'int(11)'},
			{'Field': 'SpotSize', 'Type': 'int(11)'},
			{'Field': 'Intensity', 'Type': 'float(10,4)'},
			{'Field': 'BShiftX', 'Type': 'float(10,4)'},
			{'Field': 'BShiftY', 'Type': 'float(10,4)'},
			{'Field': 'IShiftX', 'Type': 'float(10,4)'},
			{'Field': 'IShiftY', 'Type': 'float(10,4)'}]

db.createSQLTable('PRESET', presetDefinition)

db.Preset = db.Table('PRESET', [ 'Name', 'Width', 'Height', 'Binning', 'ExpTime', 'Dose',
		'BeamCurrent', 'LDButton', 'Mag', 'PixelSize', 'Defocus', 'SpotSize',
		'Intensity', 'BShiftX', 'BShiftY', 'IShiftX', 'IShiftY' ])

presetdata1 = ['focus2', 256, 256, 1, 0.3000, 41.6200, 0,'search', 66000, 0.2994, -2000, 3, 42414.5117, 106.9400, 28.7300, 198.0000, 4542.0000]


# Example of a python preset class

class Preset(ObjectBuilder):
	table = "PRESET"
	columns = ['Name', 'Mag', 'Defocus', 'Dose']
	indices = [ ('Name', ['Name']), ('NameMag', ['Name', 'Mag']) ]

myp1 = Preset().register(db)
p1 = Preset('foc', 66000, -20,0.67543)

p1d = p1.dumpdict()
