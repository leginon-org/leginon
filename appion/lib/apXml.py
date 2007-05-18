import sys
import apDisplay
import re
import xml.dom.minidom

#taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/409899
#Title: xmlreader2
#Submitter: Peter Neish (other recipes) 
#HEAVILY modified by Neil

def nodeToDict(node):
	"""
	nodeToDic() scans through the children of node and makes a
	dictionary from the content.
	two cases are differentiated:
	- if the node contains no other nodes, it is a text-node
	  and {nodeName:text} is merged into the dictionary.
	- else, nodeToDic() will call itself recursively on
	  the children nodes.
	Duplicate entries are overwritten
	"""
	xmldict = {}
	for n in node.childNodes:
		if n.nodeType != n.ELEMENT_NODE:
			continue
		text = False
		if len(n.childNodes) == 1 and n.childNodes[0].nodeType == n.TEXT_NODE:
			text = str(n.childNodes[0].nodeValue)
			if len(text) > 0:
				xmldict.update({str(n.nodeName): text})
			else:
				xmldict.update({str(n.nodeName): None})
		elif len(n.childNodes) > 0:
			xmldict.update({str(n.nodeName): nodeToDict(n)})
	return xmldict

def readConfig(filename):
	dom = xml.dom.minidom.parse(filename)
	xmldict = nodeToDict(dom.childNodes[0])
	return xmldict

### END BORROWED CODE

def readTwoXmlFiles(file1,file2):
	"""
	reads two XML files and creates a dictionary
	"""
	xmldict  = readConfig(file1)
	xmldict2 = readConfig(file2)
	xmldict = overWriteDict(xmldict,xmldict2)

	fillMissingInfo(xmldict)
	updateXmlDict(xmldict)

	return xmldict


def fillMissingInfo(xmldict):
	xmldict.copy()
	for p in xmldict:
		if not 'nargs' in xmldict[p]:
			xmldict[p]['nargs'] = 1
	return

def overWriteDict(dict1, dict2):
	"""
	merges dict2 into dict1 by inserting and overwriting values
	"""
	if len(dict2) > 0:
		for p in dict2:
			if p in dict1:
				dict1[p].update(dict2[p])
			else:
				dict1[p] = dict2[p]
	return dict1

def generateParams(xmldict):
	"""
	generated the parameter dictionary based on the default values
	"""
	params = {}
	for p in xmldict:
		if 'default' in xmldict[p] and xmldict[p]['default'] != None:
			value = xmldict[p]['default']
			vtype = xmldict[p]['type']
			nargs = xmldict[p]['nargs']
			params[p] = _convertParamToType(value, vtype, nargs)
		else:
			params[p] = None
	return params

def checkParamDict(paramdict,xmldict):
	"""
	checks the parameter dictionary for type, limits, and conflicts
	"""
	for p in paramdict:
		if 'type' in xmldict[p] and 'nargs' in xmldict[p]:
			paramdict[p] = _convertParamToType(paramdict[p], xmldict[p]['type'], xmldict[p]['nargs'])
		elif 'type' in xmldict[p]:
			paramdict[p] = _convertParamToType(paramdict[p], xmldict[p]['type'])
		if 'limits' in xmldict[p]:
			minval,maxval = re.split(",",xmldict[p]['limits'])
			if paramdict[p] < float(minval):
				apDisplay.printError("parameter "+p+" is less than minimum allowed value: "+\
					str(paramdict[p])+"<"+str(minval))
			elif paramdict[p] > float(maxval):
				apDisplay.printError("parameter "+p+" is greater than maximum allowed value: "+\
					str(paramdict[p])+">"+str(maxval))
	return paramdict

def _convertParamToType(val, vtype, nargs=None):
	"""
	converts a value (val) into a type (vtype)
	"""
	if val is None:
		return val
	if nargs is None or nargs == 1:
		if vtype[:3].lower() == "int":
			return int(val)
		elif vtype.lower() == "float":
			return float(val)
		elif vtype[:4].lower() == "bool":
			return str2bool(val)
		elif vtype[:3].lower() == "str" or vtype[:4].lower() == "path":
			return val
		else:
			apDisplay.printError("unknown type (type='"+vtype+"') in XML file")
	else:
		if type(val) != type([]):
			vallist = val.split(',')
		else:
			vallist = val
		if vtype[:3].lower() == "int":
			for i in range(len(vallist)):
				vallist[i] = int(vallist[i])
			return vallist
		elif vtype.lower() == "float":
			for i in range(len(vallist)):
				vallist[i] = float(vallist[i])
			return vallist
		elif vtype[:4].lower() == "bool":
			for i in range(len(vallist)):
				vallist[i] = str2bool(vallist[i])
			return vallist
		elif vtype[:3].lower() == "str" or vtype[:4].lower() == "path":
			for i in range(len(vallist)):
				vallist[i] = str(vallist[i])
			return vallist
		else:
			apDisplay.printError("unknown type (type='"+vtype+"') in XML file")
	return

def updateXmlDict(xmldict):
	"""
	converts all xml parameters into their desired type
	"""
	for param in xmldict.keys():
		if('default' in xmldict[param] and xmldict[param]['default'] != None):
			xmldict[param]['default'] = _convertParamToType(xmldict[param]['default'], xmldict[param]['type'], xmldict[param]['nargs'])
	return xmldict

def str2bool(string):
	"""
	converts a string into a bool
	""" 
	if string == True:
		return True
	if string == False or string[:1].lower() == 'f' or string[:1].lower() == 'n':
		return False
	else:
		return True

def printHelp(xmldict):
	"""
	print out help info for a function with XML file
	"""
	paramlist = xmldict.keys()
	paramlist.sort()
	maxlen = 0
	maxlentype = 0
	for param in paramlist:
		if len(param) > maxlen: 
			maxlen = len(param)
		if 'type' in xmldict[param] and len(xmldict[param]['type']) > maxlentype: 
			maxlentype = len(xmldict[param]['type'])
	for param in paramlist:
		if not 'alias' in xmldict[param] and \
			(not 'modify' in xmldict[param] or str2bool(xmldict[param]['modify']) == True):
			outstr = " "
			outstr += apDisplay.color(apDisplay.rightPadString(param,maxlen),"green")
			outstr += " :"
			if 'type' in xmldict[param] and xmldict[param]['type'] != None:
				outstr += " ("+apDisplay.rightPadString(xmldict[param]['type']+")",maxlentype+1)
				outstr += " :"
			if 'required' in xmldict[param] and str2bool(xmldict[param]['required']) == True:
				outstr += apDisplay.color(" REQ","red")
			if 'description' in xmldict[param] and xmldict[param]['description'] != None:
				outstr += " "+xmldict[param]['description']
			elif 'name' in xmldict[param] and xmldict[param]['name'] != None:
				outstr += " "+xmldict[param]['name']
			if 'default' in xmldict[param] and xmldict[param]['default'] != None:
				if 'nargs' in xmldict[param] and xmldict[param]['nargs'] is not None and xmldict[param]['nargs'] > 1:
					defstr = " (default: "
					for i in range(len(xmldict[param]['default'])):
						defstr += str(xmldict[param]['default'][i])+","
					defstr = defstr[:-1]+")"
					outstr += apDisplay.color(defstr,"cyan")
				else:
					outstr += apDisplay.color(" (default: "+str(xmldict[param]['default'])+")","cyan")
			if 'example' in xmldict[param] and xmldict[param]['example'] != None:
				outstr += " (example: "+str(xmldict[param]['example'])+")"
			print outstr
	sys.exit(1)


def fancyPrintDict(pdict):
	"""
	prints out two levels of a dictionary
	"""
	pkeys = pdict.keys()
	pkeys.sort()
	maxlen = 0
	print "----------"
	for p in pkeys:
		if len(p) > maxlen: maxlen = len(p)
	for p in pkeys:
		print " ",apDisplay.rightPadString(p+":",maxlen+2),\
			apDisplay.colorType(pdict[p])
	print "----------"

