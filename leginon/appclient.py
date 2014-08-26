#!/usr/bin/env python
import leginondata
import noderegistry
'''
Module for general functions that use Node and Binding Specs of an Application
'''

def getLastNodeThruBinding(appdata,to_node_alias,binding_name,last_node_baseclass_name):
	'''
	Use the binding in the application to get the last/previous node of a defined base class.
	'''
	last_class = noderegistry.getNodeClass(last_node_baseclass_name)
	# Try 10 iteration before giving up
	for iter in range(10):
		q = leginondata.BindingSpecData(application=appdata)
		q['event class string'] = binding_name
		q['to node alias'] = to_node_alias
		r = q.query()
		if not r:
			# no node bound by the binding
			return None
		if len(r) > 1:
			# Should always bound to one node, right?
			return False
		last_alias = r[0]['from node alias']
		q = leginondata.NodeSpecData(application=appdata,alias=last_alias)
		r = q.query()
		if r:
			for lastnodedata in r:
				if issubclass(noderegistry.getNodeClass(lastnodedata['class string']),last_class):
					return lastnodedata
			# next bound node is a filter.  Try again from there.
			to_node_alias = last_alias
			continue

def getNextNodeThruBinding(appdata,from_node_alias,binding_name,next_node_baseclass_name):
	'''
	Use the binding in the application to get the next node of a defined base class.
	'''
	next_class = noderegistry.getNodeClass(next_node_baseclass_name)
	# Try 10 iteration before giving up
	for iter in range(10):
		q = leginondata.BindingSpecData(application=appdata)
		q['event class string'] = binding_name
		q['from node alias'] = from_node_alias
		r = q.query()
		if not r:
			# no node bound by the binding
			return None
		if len(r) > 1:
			# Should always bound to one node, right?
			return False
		next_alias = r[0]['to node alias']
		q = leginondata.NodeSpecData(application=appdata,alias=next_alias)
		r = q.query()
		if r:
			for nextnodedata in r:
				if issubclass(noderegistry.getNodeClass(nextnodedata['class string']),next_class):
					return nextnodedata
			# next bound node is a filter.  Try again from there.
			from_node_alias = next_alias
			continue
