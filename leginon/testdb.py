#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import sys
from leginon import leginondata
import sqldb
import numpy

 #initializer = {'name': 'voici'}
initializer = {'name': 'Session Test 2' }
session = leginondata.SessionData(initializer=initializer)

a = numpy.array((1,2,3,4,5,6,))
a.shape = 2,3

initializer = {'matrix': a}
db = leginondata.db
#r=db.diffData(session)
# r=db.insert(data.MatrixCalibrationData(initializer=initializer))
# r=db.query(data.MatrixCalibrationData(), results=1)
r=db.insert(data.SessionData(session))
r=db.query(data.SessionData())
initializer = {'session': None, 'dimension': {'y': None, 'x': None}, 'binning': {'y': None, 'x': None}, 'offset': {'y': None, 'x': None}}
r = db.query(data.CorrectorCamstateData(initializer))

print '--------------------------------------'
print r



sys.exit()






db = SQLDict(host='stratocaster')

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
			{'Field': 'IShiftY', 'Type': 'float(10,4)'},
			{'Field': 'AX', 'Type': 'float(10,4)'},
			{'Field': 'AZ', 'Type': 'float(10,4)'}]

db.createSQLTable('PRESET_TEST', presetDefinition)




db.Preset = db.Table('PRESET_TEST', [ 'Name', 'Width', 'Height', 'Binning', 'ExpTime', 'Dose',
		'BeamCurrent', 'LDButton', 'Mag', 'PixelSize', 'Defocus', 'SpotSize',
		'Intensity', 'BShiftX', 'BShiftY', 'IShiftX', 'IShiftY' ])

db.Preset.Name= db.Preset.Index(['Name'])
db.Preset.Name['expo2']

db.Preset.NoInd= db.Preset.Index([])

presetdata1 = ['focus2', 256, 256, 1, 0.3000, 41.6200, 0,'search', 66000, 0.2994, -2000, 3, 42414.5117, 106.9400, 28.7300, 198.0000, 4542.0000]


db.Preset2 = db.Table('PRESET', ['Name', 'Mag', 'Defocus', 'Dose'])
db.Preset2.Name = db.Preset2.Index(['Name'],
			orderBy = {'fields':('id',),'sort':'DESC'})
dr = db.Preset2.Name['expo2'].fetchone()
drs = db.Preset2.Name['expo2'].fetchall()



# Example of a python preset class

class Preset(ObjectBuilder):
	table = "PRESET"
	columns = ['Name', 'Mag', 'Defocus', 'Dose']
	indices = [ ('Name', ['Name'], {'orderBy':{'fields':('id',)}} ),
		    ('NameMag', ['Name', 'Mag'] )
		  ]

myp1 = Preset().register(db)
p1 = Preset('foc', 66000, -20,0.67543)

# d= myp1.Name['expo1']
# myp1.Name['expo1'] = {'Mag': 66000}
# myp1.NameMag['expo1', '6600']
# p1d = p1.dumpdict()
