#!/usr/bin/env python

import Numeric
import data

import dbdatakeeper

size = 8
im = Numeric.arrayrange(size*size).astype(Numeric.Float32)
im.shape = (size,size)

dataid = ('asdf',5)

scopedict = {'magnification': 5000, 'beam shift': {'x': 2.0, 'y':3.0}}
cameradict = {'dimension': {'x':256, 'y':256}}
presetdict = {'name': 'test', 'magnification': 5000, 'spot size': 3, 'intensity':567}
presetdata = data.PresetData(('asdfsdf',11), initializer=presetdict)


cimage = data.CameraImageData(dataid, image=im, scope=scopedict, camera=cameradict)

pdict = dict(presetdata)
del pdict['id']
del pdict['session']
print 'PDICT', pdict
#pdict = {'aaa': 5}
pimage = data.PresetImageData(dataid, initializer=cimage, preset=pdict)

dbdk = dbdatakeeper.DBDataKeeper(('dbdk',3), 'session1')
print 'PIMAGE'
print pimage
print ''
dbdk.insert(pimage)
