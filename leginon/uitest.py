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

bar1 = uidata.UIContainer('bar 1')
bar2 = uidata.UIContainer('bar 2')
server.addUIObject(bar2)
foo1 = uidata.UIContainer('foo 1')
foo2 = uidata.UIContainer('foo 2')
foo2.addUIObject(uidata.UIInteger('Test Int', 42, 'rw'))
bar1.addUIObject(foo1)
bar1.addUIObject(foo2)
server.addUIObject(bar1)
testdata = uidata.UIString('Testing 1', 'this is a test string', 'rw')
bar1.addUIObject(testdata)
bar1.addUIObject(uidata.UIString('Testing 2', 'this is a test string', 'rw'))
testdata.set('set string')
#bar1.deleteUIObject('Testing 2')
#bar1.deleteUIObject('foo 2')

#image1 = uidata.UIImage('Image 1', open('test.jpg', 'rb').read(), 'rw')
#image1 = uidata.UIImage('Image 1', '', 'rw')
import Numeric
image1 = uidata.UIImage('Image 1', Numeric.ones((50,50), Numeric.UInt8), 'rw')
image2 = uidata.UITargetImage('Target Image 1', Numeric.ones((50,50), Numeric.UInt8), [(4,4), (40,40)])
bar2.addUIObject(image1)
bar2.addUIObject(image2)
foo1.addUIObject(uidata.UIMethod('Method 1', bar))
foo1.addUIObject(uidata.UIBoolean('Boolean 1', 1, 'rw'))
foo1.addUIObject(uidata.UIBoolean('Boolean 2', 0, 'rw'))
foo1.addUIObject(uidata.UISelectFromList('List Select 1', [1,2,3], [1], 'rw'))
struct = {'a': 1,
					'b': {'a': 'foo', 'b': 'bar'},
					'c': 'asdf',
					'd': {'x': 1, 'y': 2},
					'e': 55.7777,
					'f': {'foo': {'bar': 2, 'foobar': 67.7}}}
bar1.addUIObject(uidata.UIStruct('Struct 1', struct, 'rw'))
bar1.addUIObject(uidata.UISelectFromStruct('SFT 1', struct, []))
bar1.addUIObject(uidata.UIMessageDialog('MD 1', 'This is a dialog'))

client = uiclient.wxUIClient(server.hostname, server.port)

