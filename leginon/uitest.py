#!/usr/bin/env python
import uidata
import uiserver
import uiclient
import threading
import xmlrpclib

def bar():
	print 'commanded'

server = uiserver.UIServer()
print 'UI server location =', server.hostname, server.port
server2 = uiserver.UIServer('client test')

#bar1 = uidata.UIContainer('bar 1')
#bar2 = uidata.UIContainer('bar 2')
foo = uidata.UIClientContainer('client test', (server2.hostname, server2.port))
server.addUIObject(foo)
server2.addUIObject(uidata.UIString('asdf', 'asdfkjlaksdf', 'rw'))
bar1 = uidata.UIMediumContainer('bar 1')
bar2 = uidata.UIMediumContainer('bar 2')
foo1 = uidata.UIMediumContainer('foo 1')
foo2 = uidata.UIMediumContainer('foo 2')
foo2.addUIObject(uidata.UIInteger('Test Int', 42, 'r'))
server2.addUIObject(foo1)
server2.addUIObject(foo2)
server.addUIObject(bar1)
testdata = uidata.UIString('Testing 1', 'this is a test string', 'rw')
bar1.addUIObject(testdata)
bar1.addUIObject(uidata.UIString('Testing 2', 'this is a test string', 'rw'))
testdata.set('set string')
#bar1.deleteUIObject('Testing 2')
#bar1.deleteUIObject('foo 2')

server.addUIObject(bar2)

#image1 = uidata.UIImage('Image 1', None, 'rw')
import Numeric
import Mrc
import Image
image = Mrc.mrc_to_numeric('test2.mrc')
image1 = uidata.UIImage('Image 1', image)
image2 = uidata.UITargetImage('Target Image 1', image)

image2.addTargetType('Foo', [(200, 120)])
image2.addTargetType('Bar', [])
image2.addTargetType('Foo Bar', [(120, 200), (50, 78)])

#bar2.addUIObject(image1)
bar2.addUIObject(image2)

foo1.addUIObject(uidata.UIMethod('Method 1', bar))
foo1.addUIObject(uidata.UIBoolean('Boolean 1', 1, 'r'))
foo1.addUIObject(uidata.UIBoolean('Boolean 2', 0, 'rw'))
foo1.addUIObject(uidata.UISelectFromList('List Select 1', [1,2,3], [1], 'rw'))
struct = {'a': 1,
					'b': {'a': 'foo', 'b': 'bar'},
					'c': 'asdf',
					'd': {'x': 1, 'y': 2},
					'e': 55.7777,
					'f': {'foo': {'bar': 2, 'foobar': 67.7}}}
bar1.addUIObject(uidata.UIStruct('Struct 1', struct, 'r'))
#bar1.addUIObject(uidata.UIStruct('Struct 2', struct, 'rw'))
bar1.addUIObject(uidata.UISelectFromStruct('SFT 1', struct, []))
#bar1.addUIObject(uidata.UIMessageDialog('MD 1', 'This is a dialog'))

client = uiclient.UIApp(server.hostname, server.port)
#import time
#time.sleep(10.0)
#server.deleteUIObject('client test')
#server2.deleteUIObject('foo 2')

