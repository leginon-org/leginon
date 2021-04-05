#!/usr/bin/env python
import leginondata
'''
Module for general functions that use Node and Binding Specs of an Application
'''

def getNodeSpecData(appdata,node_alias):
	'''
	Return node data.
	'''
	q = leginondata.NodeSpecData(application=appdata,alias=node_alias)
	r = q.query()
	if not r:
		# no node of this name
		return None
	return r[0]

def getLastNodeThruBinding(appdata,to_node_alias,binding_name,last_node_baseclass_name):
	'''
	Use the binding in the application to get the last/previous node of a defined base class.
	'''
	# Not to do  global import so that it does not import when the module is loaded
	import noderegistry
	last_class = noderegistry.getNodeClass(last_node_baseclass_name)
	is_direct_bound = False
	# Try 10 iteration before giving up
	for iter_bound in range(10):
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
					if iter_bound == 0:
						is_direct_bound = True
					return {'node':lastnodedata, 'is_direct_bound':is_direct_bound}
			# next bound node is a filter.  Try again from there.
			to_node_alias = last_alias
			continue

def getNextNodeThruBinding(appdata,from_node_alias,binding_name,next_node_baseclass_name):
	'''
	Use the binding in the application to get the next node of a defined base class.
	'''
	# Not to do  global import so that it does not import when the module is loaded
	import noderegistry
	next_class = noderegistry.getNodeClass(next_node_baseclass_name)
	is_direct_binding = False
	# Try 10 iteration before giving up
	for iter_bound in range(10):
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
					if iter_bound == 0:
						is_direct_bound = True
					return {'node':nextnodedata, 'is_direct_bound':is_direct_bound}
			# next bound node is a filter.  Try again from there.
			from_node_alias = next_alias
			continue
