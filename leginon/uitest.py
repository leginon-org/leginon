#!/usr/bin/env python
import uidata
import uiserver
import uiclient
import threading
import xmlrpclib

def bar():
	print 'commanded'

server = uiserver.Server()
print 'UI server location =', server.hostname, server.port

foo = uidata.MediumContainer('Foo')
server.addObject(foo)
foo.addObject(uidata.Integer('Test Int', 42, 'rw'))

server2 = uiserver.Server('client test')
#bar1 = uidata.Container('bar 1')
#bar2 = uidata.Container('bar 2')
foo = uidata.ClientContainer('client test', (server2.hostname, server2.port))
server.addObject(foo)
server.addObject(uidata.Integer('asdf', 39, 'rw'))
server2.addObject(uidata.String('asdf', 'asdfkjlaksdf', 'rw'))
bar1 = uidata.MediumContainer('bar 1')
bar2 = uidata.ExternalContainer('bar 2')
ls = uidata.SelectFromList('List Select X', [5,3,'b',2,3,5,6,7], [2])
bar1.addObject(ls)
def har():
	ls.setList(ls.getList() + [1])
bar1.addObject(uidata.Method('add', har))
foo1 = uidata.MediumContainer('foo 1')
foo2 = uidata.MediumContainer('foo 2')
foo2.addObject(uidata.Integer('Test Int', 42, 'r'))
foo2.addObject(uidata.Sequence('Test Seq', ['asdf', 1, 5.6, 'asdf2', 2, 4, 5]))
server2.addObject(foo1)
server2.addObject(foo2)
server.addObject(bar1)
testdata = uidata.String('Testing 1', 'this is a test string', 'rw')
bar1.addObject(testdata)
bar1.addObject(uidata.String('Testing 2', 'this is a test string', 'rw'))
testdata.set('set string')
#bar1.deleteObject('Testing 2')
#bar1.deleteObject('foo 2')

p = uidata.Progress('Progress Bar', 25)
bar1.addObject(p)

'''
server.addObject(bar2)
#bar1.addObject(uidata.MessageDialog('MD 1', 'This is a dialog'))
foo1.addObject(uidata.SingleSelectFromList('List Select 1', [1,2,3], 1))

#image1 = uidata.Image('Image 1', None, 'rw')
import Numeric
import Mrc
import Image
image = Mrc.mrc_to_numeric('test1.mrc')
image1 = uidata.Image('Image 1', image)
bar2.addObject(image1)
image2 = uidata.TargetImage('Target Image 1', image)

image2.addTargetType('Foo', [(200, 120)])
image2.addTargetType('Bar', [])
image2.addTargetType('Foo Bar', [(120, 200), (50, 78)])


bar2.addObject(image2)

def gar(foo):
	print foo


clickimage = uidata.ClickImage('Click Image', gar, image)
bar1.addObject(clickimage)
'''

foo1.addObject(uidata.Method('Method 1', bar))
foo1.addObject(uidata.Boolean('Boolean 1', 1, 'r'))
foo1.addObject(uidata.Boolean('Boolean 2', 0, 'rw'))
struct = {'a': 1,
					'b': {'a': 'foo', 'b': 'bar'},
					'c': 'asdf',
					'd': {'x': 1, 'y': 2},
					'e': 55.7777,
					'f': {'foo': {'bar': 2, 'foobar': 67.7}}}
bar1.addObject(uidata.Struct('Struct 1', struct, 'r'))
bar1.addObject(uidata.Struct('Struct 2', struct, 'rw'))
bar1.addObject(uidata.SelectFromStruct('SFT 1', struct, []))

client = uiclient.UIApp(server.hostname, server.port)

