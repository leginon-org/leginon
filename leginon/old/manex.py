#!/usr/bin/env python

import nodenet
import sys, signal

class ManagerUser(object):
	pass

man = nodenet.Manager()


### create test bindings
import event
repr = event.YourEvent.class_xmlrpc_repr()
man.EXPORT_addBinding(0, 0, repr)
repr = event.MyEvent.class_xmlrpc_repr()
man.EXPORT_addBinding(0, 1, repr)


try:
	signal.pause()
except:
	del(man)
	sys.exit(0)
